# Copies the cut positions of shots in a 'From' Track to multiple Destination 'To' Tracks
# Optionally renames the new shots with the Cut names from the 'From' Track.

import hiero.core
import hiero.ui
from PySide2 import (QtCore, QtGui, QtWidgets)

class CopyCutsFromTrackAction(QtWidgets.QAction):

  class CopyCutsFromTrack(QtWidgets.QDialog):
    def __init__(self,  trackItem,  parent=None):
      if not parent:
        parent = hiero.ui.mainWindow()
      super(CopyCutsFromTrackAction.CopyCutsFromTrack, self).__init__(parent)
      self.setWindowTitle("Copy Cuts")
      self.setSizeGripEnabled(False)
      self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
      self.setContentsMargins(5, 0, 5, 0)

      self.layout = QtWidgets.QVBoxLayout()
      self.layout.setContentsMargins(20, 20, 20, 20)

      # This gets the list of current Track names
      self.getTrackNamesFromActiveView()

      self.groupBox = QtWidgets.QGroupBox("Tracks")
      self.groupLayout = QtWidgets.QFormLayout()
      self.groupBox.setLayout(self.groupLayout)

      self._copyTaskType = QtWidgets.QComboBox()
      self._copyTaskType.setToolTip("Choose to copy all cuts on the From Track or only selected cuts.")
      self.groupLayout.addRow("", self._copyTaskType)
      self._copyTaskType.addItem("Copy All Cuts")
      self._copyTaskType.addItem("Copy Selected Cuts")

      self._fromTrackDropdown = QtWidgets.QComboBox()
      self._fromTrackDropdown.setToolTip("The track you wish to copy cuts from.")
      self.groupLayout.addRow("From:", self._fromTrackDropdown)

      self._toTrackDropdown = QtWidgets.QWidget()
      self.verticalLayoutWidget = QtWidgets.QWidget(self)
      self.verticalLayoutWidget.setGeometry(QtCore.QRect(210, 50, 151, 181))
      self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")

      self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
      self.verticalLayout.setContentsMargins(0, 0, 0, 0)
      self.verticalLayout.setObjectName("verticalLayout")

      self.trackListModel = QtGui.QStandardItemModel()
      self.trackListView = QtWidgets.QListView()
      self.trackListView.setToolTip("Selected tracks will have cuts applied to them.")
      self.trackListView.setModel(self.trackListModel)

      # Populate track list
      for track in self.currentTracks:
        self._fromTrackDropdown.addItem(self.getIconForTrack(track),track.name(), track.guid())

      self._fromTrackDropdown.setCurrentIndex(len(hiero.ui.activeView().sequence().videoTracks()) - 1)

      self.excludedTracks = []
      self.lockedTracks = []
      self.emptyTracks = []
      self.sequence = hiero.ui.activeView().sequence()

      self.populateFromTracks()
      self.groupLayout.addRow("To:", self.trackListView)
      self.toggleAll = QtWidgets.QPushButton("Select/Deselect All Tracks")
      self.toggleAll.setToolTip("Selects or Deselects All Tracks except the currently set From Track")
      self.groupLayout.addRow("", self.toggleAll)
      self.toggleAll.clicked.connect(self.toggleAllTracks)

      self.trackListModel.itemChanged.connect(self.trackSelectionChanged)
      self._fromTrackDropdown.currentIndexChanged.connect(self.fromTrackSelectionChanged)

      self.renameBox = QtWidgets.QGroupBox()
      self.nameCopyComboBox = QtWidgets.QComboBox()
      self.nameCopyComboBox.addItem("Using 'From' Shot Names")
      self.nameCopyComboBox.addItem("None")
      self.nameCopyComboBox.setToolTip("Using From Shot Names - will rename newly cut shots with names matching the From shots.\n'None - does not rename the newly cut shots.")

      self.groupLayout.addRow("Rename:",self.nameCopyComboBox)

      # Add the standard ok/cancel buttons, default to ok.
      self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
      self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("OK")
      self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDefault(True)
      self._buttonbox.accepted.connect(self.accept)
      self._buttonbox.rejected.connect(self.reject)
      self.groupLayout.addWidget(self._buttonbox)

      self.setLayout(self.groupLayout)
      self.layout.addWidget(self.groupBox)
      

    # Sets the Video/Audio Icon according to Track Type
    def getIconForTrack(self,track):
      trackIcon = None
      if isinstance(track,hiero.core.AudioTrack):
          trackIcon = QtGui.QIcon("icons:AudioOnly.png")
      elif isinstance(track,hiero.core.VideoTrack):
          trackIcon = QtGui.QIcon("icons:VideoOnly.png")
      return trackIcon

    def populateFromTracks(self):

      audioTracks = self.sequence.audioTracks()

      for track in self.currentTracks:
        item = QtGui.QStandardItem(track.name())
        # Use the track guid to identify tracks throughout the process. There appears to be a bug in PySide2
        # where using setData(track) does not store the object, but somehow returns a list of track.items() instead
        item.setData(track.guid())
        item.setIcon(self.getIconForTrack(track))

        # Get currently locked tracks so we can leave them locked while locking/unlocking other tracks during razoring
        if track.isLocked():
          self.lockedTracks.append(track)

        # Ignore empty tracks
        if len(list(track.items())) == 0:
          self.emptyTracks.append(track)

        # Make an initial list of tracks to exclude
        currentFromIndex = self._fromTrackDropdown.itemData(self._fromTrackDropdown.currentIndex())
        if track.guid() == currentFromIndex:
          currentFromTrack = track
          if currentFromTrack not in self.excludedTracks:
            self.excludedTracks.append(currentFromTrack)

        # Exclude audio by default. Comment this out if you prefer to have audio tracks selected by default.
        if track in audioTracks and not track.isLocked():
          self.excludedTracks.append(track)

        if track in self.excludedTracks:
          item.setCheckState(QtCore.Qt.Unchecked)
        elif track in self.lockedTracks:
          item.setEnabled(False)
          item.setToolTip("%s is Locked. Unlock to apply cuts." % track.name())
        elif track in self.emptyTracks:
          item.setEnabled(False)
          item.setToolTip("%s is Empty." % track.name())
        else:
          item.setCheckState(QtCore.Qt.Checked)

        item.setCheckable(True)
        item.setEditable(False)
        self.trackListModel.appendRow(item)
        self.trackSelectionChanged(item)
      
      
    # Get the initial list of all tracks in the sequence
    def getTrackNamesFromActiveView(self):
      sequence = hiero.ui.activeView().sequence()
      self.currentTracks = []
      for existingtrack in reversed(sequence.videoTracks()):
        self.currentTracks.append(existingtrack)
      for existingtrack in sequence.audioTracks():
        self.currentTracks.append(existingtrack)

    def fromTrackSelectionChanged(self, item):
      currentFromTrack = [track for track in self.sequence if track.guid() in [self._fromTrackDropdown.itemData(self._fromTrackDropdown.currentIndex())]][0]
      self.trackListModel.item(item).setCheckState(QtCore.Qt.Unchecked)
      self._fromTrackDropdown.setCurrentIndex(item)
      self.excludedTracks.append(currentFromTrack)

    def trackSelectionChanged(self, item):
      trackName = [track for track in self.sequence if track.guid() in [item.data()]][0]
      currentFromTrack = [track for track in self.sequence if track.guid() in [self._fromTrackDropdown.itemData(self._fromTrackDropdown.currentIndex())]][0]

      # Uncheck the destination track if it is the 'From Track'
      if trackName == currentFromTrack:
        item.setCheckState(QtCore.Qt.Unchecked)

      if item.checkState() == QtCore.Qt.Checked:
        if trackName in self.excludedTracks:
          self.excludedTracks.remove(trackName)
      else:
        if trackName not in self.excludedTracks:
          self.excludedTracks.append(trackName)

    # Get the list of excluded tracks that are not already locked so we can lock them before applying cuts
    def getExcludedTracks(self, tracklist):
      tracksToExclude = []
      for track in tracklist:
        if track in self.excludedTracks:
          if not track.isLocked():
            tracksToExclude.append(track)
      return tracksToExclude

    def toggleAllTracks(self):
      for row in range(self.trackListModel.rowCount()):
        if self.trackListModel.item(row).checkState() == QtCore.Qt.Checked:
          anySelected = True
          break
        else:
          anySelected = False

      if anySelected:
        for row in range(self.trackListModel.rowCount()):
          self.trackListModel.itemFromIndex(self.trackListModel.index(row, 0)).setCheckState(QtCore.Qt.Unchecked)
      else:
        for row in range(self.trackListModel.rowCount()):
          # Get the current track object by grabbing the data (track guid) stored on the checkbox
          currentTrack = [track for track in self.sequence if track.guid() in [self.trackListModel.itemFromIndex(self.trackListModel.index(row, 0)).data()]][0]
          # Exclude the current 'From Track' by comparing each track's stored checkbox data with the stored dropdown menu data
          if not self.trackListModel.itemFromIndex(self.trackListModel.index(row, 0)).data() == self._fromTrackDropdown.itemData(self._fromTrackDropdown.currentIndex()):
            self.trackListModel.item(row).setCheckState(QtCore.Qt.Checked)
          if currentTrack in self.lockedTracks:
            self.trackListModel.item(row).setEnabled(False)
            self.trackListModel.item(row).setCheckState(QtCore.Qt.Unchecked)
          if len(list(currentTrack.items())) == 0:
            self.trackListModel.item(row).setEnabled(False)
            self.trackListModel.item(row).setCheckState(QtCore.Qt.Unchecked)

  def __init__(self):
    QtWidgets.QAction.__init__(self, "Copy Cuts", None)
    self.triggered.connect(self.doCuts)
    hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.eventHandler)

  def toggleTrackLock(self, tracklist, lockstate=True):
    for track in tracklist:
      if lockstate:
        track.setLocked(True)
      else:
        track.setLocked(False)

  def doCuts(self):
    selection = hiero.ui.activeView().selection()
    sequence = hiero.ui.activeView().sequence()
    dialog = self.CopyCutsFromTrack(selection)

    dialog._copyTaskType.setVisible(self.enableSelectedCutsCopyMode)
    dialog._copyTaskType.setCurrentIndex(0)

    if dialog.exec_():
      # Find the 'From Track' in the dropdown using the guid
      fromTrack = [track for track in sequence if track.guid() in [dialog._fromTrackDropdown.itemData(dialog._fromTrackDropdown.currentIndex())]][0]
      allCuts = []
      for destinationTrack in dialog.currentTracks:
        if destinationTrack not in dialog.excludedTracks:
          toTrack = destinationTrack

          copyAll = True
          copyMode = dialog._copyTaskType.currentText()
          if copyMode == 'Copy Selected Cuts':
            copyAll = False

          # Get all Track Cuts to find durations and cut points to ensure no cut conflicts occur
          def getTrackCuts(seq, fromTrack):
            AllTracks = {}
            for track in seq:
              if track == fromTrack:
                for clip in list(track.items()):
                  AllTracks[clip.guid()] = list(range(clip.timelineIn(), clip.timelineOut()+1))
            return AllTracks

          if copyAll == True:

            allFromTrackCuts = getTrackCuts(sequence, fromTrack)
            toClips = getTrackCuts(sequence, toTrack)
            fromTrackDuration = list(fromTrack.items())[-1].timelineOut()
            fromTrackTimelineIn = list(fromTrack.items())[0].timelineIn()

            # Check for existing cuts on destination track and compare frame ranges to avoid cut conflicts
            for from_clipname,from_cliprange in sorted(list(allFromTrackCuts.items()), key=lambda allFromTrackCuts: allFromTrackCuts[1]):
                for to_clipname, to_cliprange in sorted(list(toClips.items()), key=lambda toClips: toClips[1]):
                    # If destination clip frame range overlaps with source clip frame range
                    if to_cliprange[0] in from_cliprange[1:-1] or to_cliprange[-1] in from_cliprange[1:-1]:
                        QtWidgets.QMessageBox.warning(None, "Copy Cuts", "The selected cuts conflict with existing cuts on Track %s.\nPlease choose a track with no conflicts." % track.name(), QtWidgets.QMessageBox.Ok)
                        self.doCuts()
                        return

            # Warning dialog if the destination track is Disabled - Cuts will still be applied to be consistent with the GUI behaviour of Razor
            if toTrack.isEnabled() == False:
              QtWidgets.QMessageBox.warning(None, "Copy Cuts", "Destination Track %s is Disabled.\nCuts will still be applied." % toTrack.name(), QtWidgets.QMessageBox.Ok)
              pass
              #return

            # Get all TrackItems in the Source Track
            cutItems = list(fromTrack.items())

            # Store the timeline in/out points of each TrackItem, then find TrackItem in toTrack and Cut appropriately...
            allCuts = []
            for fromTrackItem in cutItems:
              tIn = fromTrackItem.timelineIn()
              tOut = fromTrackItem.timelineOut() + 1
              allCuts.append(tIn)
              allCuts.append(tOut)

          # If we want "Selected Cuts" then get selected clip info from the From Track to compare with To Tracks to ensure no conflicts occur
          if copyAll == False:

            if toTrack.isEnabled() == False:
              QtWidgets.QMessageBox.warning(None, "Copy Cuts", "Destination Track %s is Disabled.\nCuts will still be applied." % toTrack.name(), QtWidgets.QMessageBox.Ok)
              pass

            cutItems = [item for item in selection if isinstance(item, hiero.core.TrackItem) and not isinstance(item, hiero.core.Transition)]
            toClips = getTrackCuts(sequence, toTrack)

            selectedCuts = {}
            for clip in cutItems:
              selectedCuts[clip.name()] = list(range( clip.timelineIn(), clip.timelineOut() + 1))

            # Check for existing cuts on destination track and compare frame ranges to avoid cut conflicts
            for from_clipname,from_cliprange in sorted(list(selectedCuts.items()), key=lambda selectedCuts: selectedCuts[1]):
                for to_clipname, to_cliprange in sorted(list(toClips.items()), key=lambda toClips: toClips[1]):
                    # If destination clip frame range overlaps with source clip frame range
                    if to_cliprange[0] in from_cliprange[1:-1] or to_cliprange[-1] in from_cliprange[1:-1]:
                        QtWidgets.QMessageBox.warning(None, "Copy Cuts", "The selected cuts conflict with existing cuts on Track %s.\nPlease choose a track with no conflicts." % toTrack.name(), QtWidgets.QMessageBox.Ok)
                        self.doCuts()
                        return

            # for each item in the selection
            allCuts = []
            origCutNames = []
            for fromTrackItem in cutItems:
              tIn = fromTrackItem.timelineIn()
              tOut = fromTrackItem.timelineOut() + 1
              origCutNames.append(fromTrackItem.name())
              allCuts.append(tIn)
              allCuts.append(tOut)

      tracksToExclude = dialog.getExcludedTracks(dialog.excludedTracks)

      with hiero.core.projects()[-1].beginUndo("Copy Cuts"):
        self.toggleTrackLock(tracksToExclude, lockstate=True)
        sequence.razorAt(allCuts)

        self.toggleTrackLock(tracksToExclude, lockstate=False)
        sequence.editFinished()

      # Now we optionally rename the new cuts
      if 'None' in dialog.nameCopyComboBox.currentText():
        print('Not renaming Tracks')
      else:

        with hiero.core.projects()[-1].beginUndo("Copy Cuts (Rename)"):

          # Build a list of included Tracks.. (not excludedTracks)
          includedTracks = []
          for track in sequence:
            if (track not in tracksToExclude) and (track is not fromTrack):
              includedTracks.append(track)
          
          # Now for each track, and for each TrackItem, we detect in point matches, which dictate the start of a shot.
          # Construct a dict of from Shots, with the from Shot names. The inTime will form the dict key for comparison.
          fromTrackCutDict = {}

          for cut in cutItems:
            fromTrackCutDict[str(cut.timelineIn())]=cut.name()

          print(fromTrackCutDict)
          for includedTrack in includedTracks:
            trackItems = list(includedTrack.items())
            for ti in trackItems:
              if str(ti.timelineIn()) in list(fromTrackCutDict.keys()):
                ti.setName(fromTrackCutDict[str(ti.timelineIn())])

          sequence.editFinished()

  def eventHandler(self, event):
    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which will give a selection.
      return

    # We don't enable Copy Cuts action for a Clip opened in a Timeline View
    if not hiero.ui.activeView() or hiero.ui.activeView().sequence() == None:
      return

    shotSelection = [item for item in event.sender.selection() if isinstance(item,hiero.core.TrackItem)]

    self.enableSelectedCutsCopyMode = True    
    if len(shotSelection) == 0:
      self.enableSelectedCutsCopyMode = False # We disable the Selected Cuts option if no shots are selected
    title = "Copy Cuts..."
    self.setText(title)
  
    for a in event.menu.actions():
      if a.text().lower().strip() == "editorial":
        hiero.ui.insertMenuAction( self, a.menu(), after = "foundry.timeline.enableItem" )

# Instantiate the action to get it to register itself.
copyCutsFromTrackAction = CopyCutsFromTrackAction()
