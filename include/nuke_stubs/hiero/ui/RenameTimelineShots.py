# This item registers for timeline/spreadsheet context menu events and on receiving one,
# inserts itself into the menu. When invoked, it shows a dialog containing
# fields for defining new event names and updates the selected track items.

import hiero.core
import hiero.core.util
import hiero.ui
from PySide2 import (QtCore, QtGui, QtWidgets)
from hiero.ui import findMenuAction, registerAction
import ast

class SearchHistoryLineEdit(QtWidgets.QLineEdit):
  def __init__(self, parent=None):
    super(SearchHistoryLineEdit, self).__init__(parent)

    self.completer = QtWidgets.QCompleter(self)
    self.completer.setMaxVisibleItems(10)    
    self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
    self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.pFilterModel = QtCore.QSortFilterProxyModel(self)
    self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
    self.completer.setPopup(self.view())
    self.setCompleter(self.completer)
    self.textEdited[str].connect(self.pFilterModel.setFilterFixedString)
    self.setModelColumn(0)

  def setModel(self, model):
    self.pFilterModel.setSourceModel(model)
    self.completer.setModel(self.pFilterModel)

  def setModelColumn(self, column):
    self.completer.setCompletionColumn(column)
    self.pFilterModel.setFilterKeyColumn(column)

  def view(self):
    return self.completer.popup()

  def index(self):
    return self.currentIndex()

class RenameShotsDialog(QtWidgets.QDialog):
  kSequentialRename = 'Sequential Rename'
  kFindAndReplace = 'Find and Replace'
  kSimpleRename = 'Simple Rename'
  kMatchSequence = 'Match Sequence'
  kClipName = 'Clip Name'
  kCaseChange = 'Change Case'
  
  # Set Defaults
  if hiero.core.isHieroPlayer():
    modeDefault = kSimpleRename
  else:
    modeDefault = kSequentialRename

  defaults =  { 'state' : modeDefault ,
                'pattern' : u'Shot####' ,
                'start' : 10 ,
                'increment' : 10 ,
                'find' : '{shot}' ,
                'replace' : '{shot}' ,
                'rename' : '{shot}' ,
                'renameAudioTracks' : False,
                'matchSequenceName' : None,
                'recentStrings' : [],
              }
  values = {}

  def __init__(self, parent=None):
    if not parent:
      parent = hiero.ui.mainWindow()
    super(RenameShotsDialog, self).__init__(parent)
    
    autoCompleteKeywords = ['{shot}', '{clip}', '{track}', '{sequence}', '{event}', '{fps}', '{filename}' ]

    # Keyword resolver for using {tokens} in the rename dialog
    self._resolver = hiero.core.FnResolveTable.ResolveTable()
    self._resolver.addResolver("{shot}", "Name of the TrackItem being processed", lambda keyword, task: task.name())
    self._resolver.addResolver("{clip}", "Name of the source Media clip being processed", lambda keyword, task: task.source().name())
    self._resolver.addResolver("{track}", "Name of the track being processed", lambda keyword, task: task.parent().name())
    self._resolver.addResolver("{sequence}", "Name of the Sequence being processed", lambda keyword, task: task.parent().parent().name())
    self._resolver.addResolver("{event}", "Event Number of the shot being processed", lambda keyword, task: str(task.eventNumber()))
    self._resolver.addResolver("{fps}", "Frame rate of the Sequence", lambda keyword, task: str(task.parent().parent().framerate()))
    self._resolver.addResolver("{filename}", "Source filename of the TrackItem", lambda keyword, task: task.source().mediaSource().filename())
  
    resolverTooltip = "<br>You can rename using the following keyword tokens:<br>"
    for i in range(0,self._resolver.entryCount()):
      resolverTooltip+= '<b>%s</b> - %s<br>' % (self._resolver.entryName(i), self._resolver.entryDescription(i))
    
    self._loadSettings()
    self.searchHistoryList = self.getRecentStringsFromSettings()

    layout = QtWidgets.QVBoxLayout()
    
    # Add a Combobox for choosing a sequential rename or simple rename
    self._renameModeComboBox = QtWidgets.QComboBox()
    self._renameModeComboBox.addItem(self.kSimpleRename)
    self._renameModeComboBox.addItem(self.kFindAndReplace)
    self._renameModeComboBox.setToolTip("""
      <b>Simple Rename</b> - Renames all selected shots to name entered.<br>
      <b>Find/Replace All</b> - Replaces all instances of 'Find' name with 'Replace' name.<br>
      For extended renaming modes, please see Hiero.<br>
      %s""" % resolverTooltip)
    if not hiero.core.isHieroPlayer():
      self._renameModeComboBox.addItem(self.kSequentialRename)
      self._renameModeComboBox.addItem(self.kMatchSequence)
      self._renameModeComboBox.addItem(self.kClipName)
      self._renameModeComboBox.addItem(self.kCaseChange)
      self._renameModeComboBox.setToolTip("""
        <b>Simple Rename</b> - Renames all selected shots to name entered.<br>
        <b>Find/Replace All</b> - Replaces all instances of 'Find' name with 'Replace' name.<br>
        <b>Sequential Rename</b> - Renames shots sequentially using a start # and increment. e.g. Shot0010, Shot0020.. Shot0200.<br>
        <b>Match Sequence</b> - Match shots in this sequence to the ones in the selected sequence and set to their shot names.<br>
        <b>Clip Name</b> - Rename each shot to the name of the clip used for the shot.<br>
        <b>Change Case</b> - Rename each shot to lower, UPPER, Title Case, or Capital case names.<br>
        %s""" % resolverTooltip)

    self._renameModeComboBox.currentIndexChanged.connect(self._renameModeChanged)
    layout.addWidget(self._renameModeComboBox, 0, QtCore.Qt.AlignLeft)
    
    # Add a Stacked Widget here which changes depending on the current ComboBox option (see FnExporterBasUI.py)
    self._stackedWidget = QtWidgets.QStackedWidget()

    # Any plain name text can only have alphanumeric, _ - + and . characters.
    namerx = QtCore.QRegExp("[^\/\\\:\*\?]+")
    nameval = QtGui.QRegExpValidator(namerx, self)

    # Simple Rename : Simply renames multiple selected shots to the name specified.
    simpleRenamePage = QtWidgets.QWidget()
    simpleRenameLayout = QtWidgets.QFormLayout()
    simpleRenameLayout.setContentsMargins(0, 0, 0, 0)
    self._renameField = SearchHistoryLineEdit()
    self._renameField.setValidator(nameval)
    self._renameField.textChanged.connect(self._textChanged)
    simpleRenameLayout.addRow("New Name:", self._renameField)
    simpleRenamePage.setLayout(simpleRenameLayout)
    self._stackedWidget.addWidget(simpleRenamePage)
    self._stackedWidget.setMaximumHeight(72)

    # Find and Replace Page : Two fields for Find/Replace.
    findReplacePage = QtWidgets.QWidget()
    findReplaceLayout = QtWidgets.QFormLayout()
    findReplaceLayout.setContentsMargins(0, 0, 0, 0)
    self._findField = SearchHistoryLineEdit()
    self._findField.textChanged.connect(self._textChanged)
    self._replaceField = SearchHistoryLineEdit()
    self._replaceField.setValidator(nameval)
    self._replaceField.textChanged.connect(self._textChanged)
    findReplaceLayout.addRow("Find:", self._findField)
    findReplaceLayout.addRow("Replace:", self._replaceField)
    findReplacePage.setLayout(findReplaceLayout)
    self._stackedWidget.addWidget(findReplacePage)

    
    # Sequential Shot Rename Page : Pattern, Start and Increment fields.
    sequentialRenamePage = QtWidgets.QWidget()
    sequentialRenameLayout = QtWidgets.QFormLayout()
    sequentialRenameLayout.setContentsMargins(0, 0, 0, 0)
    
    # Add a box containing the pattern and its label.
    self._patternField = SearchHistoryLineEdit()
    self._patternField.setToolTip("The pattern to use to rename the selected shots. Only letters, numbers, _ - + and . may be in the name.\nUse one or more # characters to indicate where the number should be placed.")
    self._patternField.textChanged.connect(self._textChanged)
    namepatternrx = QtCore.QRegExp("[^\/\\\:\*\?]*\\#+[^\/\\\:\*\?]*")
    nameval = QtGui.QRegExpValidator(namepatternrx, self)
    self._patternField.setValidator(nameval)
    sequentialRenameLayout.addRow("Pattern:", self._patternField)
    
    # Build a box for the number fields and their labels.
    numrx = QtCore.QRegExp("\\d+")
    numval = QtGui.QRegExpValidator(numrx, self)

    self._startField = QtWidgets.QLineEdit()
    self._startField.setToolTip("The number to insert in the name of the first shot.")
    self._startField.setValidator(numval)
    self._startField.textChanged.connect(self._textChanged)
    sequentialRenameLayout.addRow("Start #:", self._startField)

    self._incField = QtWidgets.QLineEdit()
    self._incField.setToolTip("The increment applied to the number inserted in each shot name.")
    self._incField.setValidator(numval)
    self._incField.textChanged.connect(self._textChanged)
    sequentialRenameLayout.addRow("Increment:", self._incField)      
    sequentialRenamePage.setLayout(sequentialRenameLayout)
      

    # Match Sequence : Find matching edits in the selected sequence and take their shot name.
    matchSequencePage = QtWidgets.QWidget()
    matchSequenceLayout = QtWidgets.QFormLayout()
    matchSequenceLayout.setContentsMargins(0, 0, 0, 0)
    # Add a list of sequences in the project. There may be duplicate names so build a
    # mapping between names and Sequence objects and try to de-dupe names by putting
    # the parent bin name in ().
    self._matchSequenceListWidget = QtWidgets.QListWidget()
    self._matchSequenceListWidget.setToolTip("Search the selected sequence for shots that use the same clip and a range from that clip that overlaps. Rename to the best matching shot's name.")
    self._matchSequenceListWidget.itemSelectionChanged.connect(self._updateOkButtonState)
    matchSequenceLayout.addRow("", self._matchSequenceListWidget)
    matchSequencePage.setLayout(matchSequenceLayout)
    
    # Clip Name : Rename shots to their clip names.
    clipNamePage = QtWidgets.QWidget()
    clipNameLayout = QtWidgets.QFormLayout()
    clipNameLayout.setContentsMargins(0, 0, 0, 0)
    clipNameLayout.addRow("", QtWidgets.QLabel("Rename each shot to its original source Clip name."))
    clipNamePage.setLayout(clipNameLayout)

    # Change Case : Rename shots based on common case change operations
    changeCasePage = QtWidgets.QWidget()
    changeCaseLayout = QtWidgets.QFormLayout()
    changeCaseLayout.setContentsMargins(0, 0, 0, 0)
    self._changeCaseModeComboBox = QtWidgets.QComboBox()
    self._changeCaseModeComboBox.addItem("lowercase")
    self._changeCaseModeComboBox.addItem("UPPERCASE")
    self._changeCaseModeComboBox.addItem("Title Case")
    self._changeCaseModeComboBox.addItem("Capital case")
    changeCaseLayout.addRow("Case:",self._changeCaseModeComboBox)
    changeCasePage.setLayout(changeCaseLayout)

    hieroModes = [sequentialRenamePage, matchSequencePage, clipNamePage, changeCasePage]
    if not hiero.core.isHieroPlayer():
      for mode in hieroModes:
        self._stackedWidget.addWidget(mode)

    # Here, we add the StackedWidget
    layout.addWidget(self._stackedWidget)
    
    # Checkbox for renaming Audio Tracks
    self._renameAudioTracksCheckbox = QtWidgets.QCheckBox("Include Clips From Audio Tracks")
    self._renameAudioTracksCheckbox.setToolTip("Enable this option to rename shots on Audio Tracks.")
    layout.addWidget(self._renameAudioTracksCheckbox)

    # Add the standard ok/cancel buttons, default to ok.
    self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.RestoreDefaults | QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.Ok).setText("Rename")
    self._buttonbox.accepted.connect(self.accept)
    self._buttonbox.rejected.connect(self.reject)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaults)
    layout.addWidget(self._buttonbox)

    self.setLayout(layout)
    self.setWindowTitle("Rename Shots")
    self.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
  
    
  def updateMatchSequenceUI(self,sequence):
    
    # Set up "match sequence" options.
    self._matchSequenceDict = {}
    currentItem = None
    self._matchSequenceListWidget.clear()
    for seq in sequence.project().sequences():
      if seq == sequence: # Use == not "is"; seems we get two different python wrappers.
        continue
      name = seq.name()
      # TODO: Make this recurse up, pre-pending path parts as it goes.
      if name in self._matchSequenceDict:
        name = name + "(" + seq.binItem().parentBin().name() + ")"
      self._matchSequenceDict[name] = seq
      self._matchSequenceListWidget.addItem(name)

  def exec_(self, sequence, shots):
    # Override the standard dialog exec_ to make sure we're set up before showing.
    
    self._shots = shots

    if not hiero.core.isHieroPlayer():
      self.updateMatchSequenceUI(sequence)

    self._setUIFromSettings()
    
    return super(RenameShotsDialog, self).exec_()

  def loadAutocompleter(self):    
    searchmodel = QtGui.QStandardItemModel()
    for i, word in enumerate(set(self.searchHistoryList)):
      item = QtGui.QStandardItem(word)
      searchmodel.setItem(i, 0, item)

    self._renameField.setModel(searchmodel)
    self._renameField.setModelColumn(0)
    self._findField.setModel(searchmodel)
    self._findField.setModelColumn(0)    
    self._replaceField.setModel(searchmodel)
    self._replaceField.setModelColumn(0)

  def _setFocusForCurrentMode(self):
    # Handles the setting of widget focus so that user can start typing straight away when dialog is shown
    
    # Ensure focus is on the Dialog..
    self.setFocus()
    
    # Now handle the widget focus depending on the Rename mode
    renameMode = self.renameMode()
    if renameMode == self.kSequentialRename:
      self._patternField.setFocus()
      self._patternField.selectAll()
    elif renameMode == self.kFindAndReplace:
      self._findField.setFocus()
      self._findField.selectAll()
    elif renameMode == self.kSimpleRename:
      self._renameField.setFocus()
      self._renameField.selectAll()
    elif renameMode == self.kMatchSequence:
      self._matchSequenceListWidget.setFocus()
    elif renameMode == self.kCaseChange:
      self._changeCaseModeComboBox.setFocus()

  def _setUIFromSettings(self, updateMode=True):
    # Set these last so buttons get enabled/disabled correctly by "changed" connections.
    # This is separate from init because it's also called by a button for "restore defaults".
    checked = QtCore.Qt.Unchecked
    if self.values['renameAudioTracks'] is True:
      checked = QtCore.Qt.Checked
    self._renameAudioTracksCheckbox.setCheckState(checked)
        
    if self.values['rename'] is None or len(self._shots) == 1:
      self._renameField.setText(self._shots[0].name())
    else:
      self._renameField.setText(str(self.values['rename']))
      
    if self.values['find'] is not None:
      self._findField.setText(str(self.values['find']))
    if self.values['replace'] is not None:
      self._replaceField.setText(str(self.values['replace']))

    if len(self.searchHistoryList)==0:
      self.searchHistoryList = self.getRecentStringsFromSettings()
      self.values['recentStrings'] = self.searchHistoryList

    if len(self._shots) == 1 and updateMode:
      self.setRenameMode(RenameShotsDialog.kSimpleRename)
    elif updateMode:
      try:
        self.setRenameMode(self.values['state'])
      except:
        self.setRenameMode(RenameShotsDialog.kSimpleRename)

    if not hiero.core.isHieroPlayer():
      self._patternField.setText(self.values['pattern'])
      self._startField.setText(str(self.values['start']))
      self._incField.setText(str(self.values['increment']))
    
      if self.values['matchSequenceName'] is not None:
        for index in range(self._matchSequenceListWidget.count()):
          item = self._matchSequenceListWidget.item(index)
          if item.text() == self.values['matchSequenceName']:
            item.setSelected(True)
            break

    # Update the auto-complete line edit fields
    self.loadAutocompleter()

    # Finally, ensure that the correct widget has focus when shown
    self._setFocusForCurrentMode()
    
  def restoreDefaults(self):
    for k in list(self.defaults.keys()):
      self.values[k] = self.defaults[k]
    
    # Update the boxes but don't change current mode
    self._setUIFromSettings(updateMode=False)

    # Resave the defaults
    self._saveSettings()
      
  def _loadSettings(self):
    settings = hiero.core.ApplicationSettings()
    for k in list(self.defaults.keys()):
      self.values[k] = settings.value("RenameTimelineShots." + k, self.defaults[k])
    
  def _saveSettings(self):
    settings = hiero.core.ApplicationSettings()
    for k in list(self.values.keys()):
      if k != "recentStrings":
        settings.setValue("RenameTimelineShots." + k, self.values[k])
      else:
        # We're only going to save a maximum of 10 search strings
        settings.setValue("RenameTimelineShots." + k, self.values[k][0:10])
  
  def _textChanged(self, newText):
    self._updateOkButtonState()
  
  def _updateOkButtonState(self):
    # Cancel is always an option but only enable Ok if there is some text.
    renameMode = self.renameMode()
    enableOk = False
    if renameMode == self.kSequentialRename:
      enableOk = '#' in self.pattern() and len(self._startField.text()) > 0 and len(self._incField.text()) > 0 and self.increment() > 0
    elif renameMode == self.kFindAndReplace:
      enableOk = len(self.find()) > 0
    elif renameMode == self.kSimpleRename:
      enableOk = len(self.rename()) > 0
    elif renameMode == self.kMatchSequence:
      enableOk = len(self._matchSequenceListWidget.selectedItems()) == 1
    elif renameMode == self.kClipName:
      enableOk = True
    elif renameMode == self.kCaseChange:
      enableOk = True
    
    self._buttonbox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enableOk)

  def _renameModeChanged(self):
    # Update the stackedWidget according to the combobox index and set focus/OK button appropriately
    index = int(self._renameModeComboBox.currentIndex())
    self._stackedWidget.setCurrentIndex(index)
    self._setFocusForCurrentMode()
    self._updateOkButtonState()

  def setRenameMode(self, renameMode):
    index = self._renameModeComboBox.findText(renameMode)
    if index >= 0 and index < self._renameModeComboBox.count():
      self._renameModeComboBox.setCurrentIndex(index)
    else:
      raise ValueError("Invalid rename mode '%s'" % (renameMode,))

  # Methods used with kCaseChange
  def lowerCaseName(self,name):
    return name.lower()

  def upperCaseName(self,name):
    return name.upper()

  def titleCaseName(self,name):
    return name.title()

  def capitalCaseName(self,name):
    return name.capitalize()
      
  def renameMode(self):
    return self._renameModeComboBox.currentText()
  
  def pattern(self):
    return self._patternField.text()

  def start(self):
    return int(self._startField.text())

  def increment(self):
    return int(self._incField.text())
  
  def find(self):
    return str(self._findField.text())
  
  def replace(self):
    return str(self._replaceField.text())
  
  def rename(self):
    return str(self._renameField.text())
  
  def _matchSequenceName(self):
    items = self._matchSequenceListWidget.selectedItems()
    if len(items) > 0:
      return items[0].text()
    else:
      return None
  
  def matchSequence(self):
    """Return the user's match Sequence selection against which we'll match shots to get new names.
       Return None if somehow there's no selection."""
    name = self._matchSequenceName()
    if name is not None:
      return self._matchSequenceDict[name]
    else:
      return None

  def renameAudioTracks(self):
    return bool(self._renameAudioTracksCheckbox.isChecked())

  def getRecentStringsFromSettings(self):
    return ast.literal_eval(hiero.core.ApplicationSettings().value("RenameTimelineShots.recentStrings","[]"))    

  def accept(self):
    # Store the current state to be restored the next time the dialog is opened during this session.
    self.values['state'] = self.renameMode()
    if self.values['state'] == self.kSequentialRename:
      self.values['pattern'] = self.pattern()
      self.values['start'] = self.start()
      self.values['increment'] = self.increment()
    elif self.values['state'] == self.kFindAndReplace:
      self.values['find'] = self.find()
      self.values['replace'] = self.replace()
    elif self.values['state'] == self.kSimpleRename:
      self.values['rename'] = self.rename()
    else:
      self.values['matchSequenceName'] = self._matchSequenceName()

    if self.renameAudioTracks():
      self.values['renameAudioTracks'] = True
    else:
      self.values['renameAudioTracks'] = False
    
    self.values['recentStrings'] = self.searchHistoryList
    self._saveSettings()

    super(RenameShotsDialog, self).accept()
    

class RenameTimelineShotsAction(QtWidgets.QAction):
  def __init__(self):
      QtWidgets.QAction.__init__(self, "Rename Shots...", None)
      self._selection = ()
      self._dialog = None
      self.triggered.connect(self.doit)
      hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.eventHandler)
      hiero.core.events.registerInterest("kShowContextMenu/kSpreadsheet", self.eventHandler)
      self.setObjectName("foundry.timeline.renameshots")
      self.setShortcut("Alt+Shift+/")

  def doit(self):
    # This allows us to get the selection via the keyboard shortcut
    view = hiero.ui.activeView()
    if isinstance(view,(hiero.ui.TimelineEditor, hiero.ui.SpreadsheetView)):
      if hasattr(view,'selection'):
        self._selection = view.selection()
    else:
      return
    # remove any non-trackitem entries (ie transitions)
    shots = [item for item in self._selection if isinstance(item, hiero.core.TrackItem)]
    
    if len(shots) < 1:
      # Do nothing if len(shots)==0
      # For this to happen the selection would have to have been cleared
      # between raising the menu and selecting it which is pretty much
      # impossible and in which case things are probably a mess and raising
      # a message box would just add to the confusion. Let's just pretend
      # we didn't see anything...
      return

    if self._dialog is None:
      self._dialog = RenameShotsDialog()
    if self._dialog.exec_(shots[0].parentSequence(), shots):
      # If not renaming audio track items, rebuild the list of shots throwing any audio items out.
      if not self._dialog.renameAudioTracks():
        # This should copmare to the track's mediaType(), but right now that always returns video.
        shots = [shot for shot in shots if not isinstance(shot.parent(),hiero.core.AudioTrack)]

      if len(shots) < 1:
        return
      project = shots[0].project()
      with project.beginUndo("Shot Rename"):
        mode = self._dialog.renameMode()
        if mode == self._dialog.kSequentialRename:
          pattern = self._dialog.pattern()
          start = self._dialog.start()
          inc = self._dialog.increment()
          shotnum = start
          # A # should always be present thanks to the validator on the field, but be safe just in case.
          if '#' in pattern:
            for shot in shots:
              resolvedName = self._dialog._resolver.resolve(shot,pattern)
              format = hiero.core.util.HashesToPrintf(resolvedName)
              shot.setName(format % shotnum)
              shotnum = shotnum + inc
          else:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText("The pattern must contain at least one # to indicate the position for the shot number.")
            msgBox.exec_()

        elif mode == self._dialog.kFindAndReplace:
          for shot in shots:
            origFind = self._dialog.find()
            origReplace = self._dialog.replace()
            findString = self._dialog._resolver.resolve(shot,origFind)
            replaceString = self._dialog._resolver.resolve(shot,origReplace)
            currentShotName = shot.name()
            newName = currentShotName.replace(findString,replaceString)
            shot.setName(newName)
            if len(self._dialog.searchHistoryList) == 10:
              self._dialog.searchHistoryList.pop(0)
            if origFind not in self._dialog.searchHistoryList:
              self._dialog.searchHistoryList.append(origFind)
            if origReplace not in self._dialog.searchHistoryList:
              self._dialog.searchHistoryList.append(origReplace)

            self._dialog.loadAutocompleter()

        elif mode == self._dialog.kSimpleRename:
          newName = self._dialog.rename()
          for shot in shots:
            shot.setName(self._dialog._resolver.resolve(shot,newName))
          if newName:
            if len(self._dialog.searchHistoryList) == 10:
              self._dialog.searchHistoryList.pop(0)
            if newName not in self._dialog.searchHistoryList:
              self._dialog.searchHistoryList.append(newName)
            else:
              self._dialog.searchHistoryList.pop(self._dialog.searchHistoryList.index(newName))
              self._dialog.searchHistoryList.append(newName)
            self._dialog.loadAutocompleter()    
      
        elif mode == self._dialog.kMatchSequence:
          matchSeq = self._dialog.matchSequence()
          # Shouldn't be able to OK out of dialog with nothing selected but be safe just in case.
          if matchSeq is not None:
            matchShotList = []
            for track in matchSeq.videoTracks():
              for ti in list(track.items()):
                # Grab the source and sourceIn timecode now, too, so we don't need to get at each comparison later.
                clip = ti.source()
                matchShotList.append( (ti, clip, ti.sourceIn() + clip.timecodeStart()) )
          
            name = None
            for shot in shots:
              # Find a shot in match seq that has the same clip name and overlapping timecode range used.
              # Theoretically the match item is the longest cut so shots we are comparing should be
              # sub-ranges of those used in the match seq. But in case they aren't, take the one with
              # the greatest overlap, or the first one with an overlap that covers the whole clip.
              clip = shot.source()
              shotInTC = shot.sourceIn() + clip.timecodeStart()
              bestOverlap = -1 # If we get 0 overlap but name matches, we'll take it.
              bestMatchShot = None
              for (matchShot, matchClip, matchInTC) in matchShotList:
                if clip.name() == matchClip.name():
                  overlapStart = max(shotInTC, matchInTC)
                  overlapEnd = min(shotInTC + shot.duration(), matchInTC + matchShot.duration())
                  overlap = max(0, overlapEnd - overlapStart)
                  if overlap > bestOverlap:
                    bestOverlap = overlap
                    bestMatchShot = matchShot
                  if overlap == shot.duration():
                    # As good a match as we'll ever identify so bail now.
                    break
              if bestMatchShot is not None:
                shot.setName(bestMatchShot.name())
              else:
                hiero.core.log.debug("Match Sequence shot rename didn't find a shot in", matchSeq.name(), "that uses a clip named", clip.name(), "and has overlapping timecode.")
      
        elif mode == self._dialog.kClipName:
          for shot in shots:
            shot.setName(shot.source().name())

        elif mode == self._dialog.kCaseChange:
          caseMode = self._dialog._changeCaseModeComboBox.currentText()
          if caseMode == "lowercase":
            caseChangeMethod = self._dialog.lowerCaseName
          elif caseMode == "UPPERCASE":
            caseChangeMethod = self._dialog.upperCaseName
          elif caseMode == "Title Case":
            caseChangeMethod = self._dialog.titleCaseName
          elif caseMode == "Capital case":
            caseChangeMethod = self._dialog.capitalCaseName
          
          for shot in shots:
            shot.setName(caseChangeMethod(shot.name()))

        # We will save the entries after renaming
        self._dialog._saveSettings()

  def eventHandler(self, event):
    # Check if this actions are not to be enabled
    restricted = []
    if hasattr(event, 'restricted'):      
      restricted = getattr(event, 'restricted');
    if "renameShots" in restricted:
      return
    
    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which gives a selection.
      return
    self._selection = event.sender.selection()

    # We don't need this action if a user has right-clicked on a Track header
    trackSelection = [item for item in self._selection if isinstance(item, (hiero.core.VideoTrack,hiero.core.AudioTrack))]
    if len(trackSelection)>0:
      return
    
    if self._selection is None:
      self._selection = () # We disable on empty selection.

    ## if any item is locked we disable this action
    for ti in self._selection:
      try:
        if ti.parentTrack().isLocked():
          self._selection = ()
          break
      except:
        pass

    self.setEnabled(len(self._selection)>0)
  
    for a in event.menu.actions():
      if a.text().lower().strip() == "editorial":
        hiero.ui.insertMenuAction( self, a.menu(), after = "foundry.timeline.enableItem" )

# Instantiate the action to get it to register itself.
action = RenameTimelineShotsAction()

# We'll register the action, so that the shortcut can be overridden if required
registerAction(action)

# And to enable it via keyboard shortcut, add it to the Menu bar Timeline menu
timelineMenu = findMenuAction("foundry.menu.sequence")
# FIXME: I added this check because the hiero module is loaded when running Nuke (not NukeStudio)
# When running Nuke the hiero menus aren't created so the timelineMenu doesn't exist.
# This check is needed only until we prevent hte hiero module from being loaded when running Nuke
# /Rui
if timelineMenu:
  timelineMenu.menu().addAction(action)
