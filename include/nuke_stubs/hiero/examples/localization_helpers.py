# Localization Helper Functions
# These methods allow you to Localize Clips on Bins, Shots, Tracks and Sequences
import hiero.core
from PySide2 import (QtCore, QtGui, QtWidgets)

# This is just a convenience method for returning QActions with a title, triggered method and icon.
def createMenuAction(title, method, icon = None ):
  action = QtWidgets.QAction(title,None)
  action.setIcon(QtGui.QIcon(icon))
  action.triggered.connect( method )
  return action

def setlocalizationPolicyOnTrack(track, policy = hiero.core.Clip.kOnLocalize ):
  """Localizes all TrackItems in a Track
  setlocalizationPolicyOnTrack( track, policy = hiero.core.Clip.kOnLocalize ):
  @param: track - a list of hiero.core.Clip objects
  @param: policy - the localization policy (kOnLocalize,kAutoLocalize,kOffLocalize)"""
  if not isinstance(track,(hiero.core.VideoTrack,hiero.core.AudioTrack)):
    hiero.core.log.info('First argument must be a hiero.core.VideoTrack/hiero.core.AudioTrack')
    return
  else:
    for ti in track:
      ti.source().setLocalizationPolicy( policy )


def setlocalizationPolicyOnTrackItem(trackItem, policy = hiero.core.Clip.kOnLocalize ):
  """Localizes all TrackItems in a Track
  setlocalizationPolicyOnTrackItem( track, policy = hiero.core.Clip.kOnLocalize ):
  @param: track - a list of hiero.core.Clip objects
  @param: policy - the localization policy (kOnLocalize,kAutoLocalize,kOffLocalize)"""
  if not isinstance(trackItem,(hiero.core.TrackItem)):
    hiero.core.log.info('First argument must be a hiero.core.TrackItem')
    return
  else:
    trackItem.source().setLocalizationPolicy( policy )

def setlocalizationPolicyOnSequence(sequence, policy = hiero.core.Clip.kOnLocalize ):
  """Localizes all Clips used in a Sequence
  @param: clipList - a list of hiero.core.Clip objects
  @param: policy - the localization policy (kOnLocalize,kAutoLocalize,kOffLocalize)"""
  if not isinstance(sequence,(hiero.core.Sequence)):
    hiero.core.log.info('First argument must be a hiero.core.Sequence')
    return
  else:
    for track in sequence.items():
      for ti in track:
        if isinstance(ti,(hiero.core.TrackItem)):
          clip = ti.source()
          if clip.localizationPolicy != policy:
            clip.setLocalizationPolicy(policy)

def setlocalizationPolicyOnBin(bin, policy = hiero.core.Clip.kOnLocalize, recursive = True ):
  """Localizes all Clips, recursively found in all Sub-Bins
  @param: clipList - a list of hiero.core.Clip objects
  @param: policy - the localization policy (kOnLocalize,kAutoLocalize,kOffLocalize)"""

  clips =[]

  if not isinstance(bin,(hiero.core.Bin)):
    hiero.core.log.info('First argument must be a hiero.core.Bin')
    return  
  else:
    if recursive:
      # Here we're going to walk the entire Bin view, for all Clips contained in this Bin
      clips += hiero.core.findItemsInBin(bin, filter = hiero.core.Clip)
    else:
      # Here we just get Clips at the 1st level of the Bin
      clips = bin.clips()

  for clip in clips:
    if clip.localizationPolicy != policy:
      clip.setLocalizationPolicy(policy)


def setlocalizationPolicyOnClipWithExtension(clip, extensionList = [None], policy = hiero.core.Clip.kOnLocalize ):
  """Localizes Clips in clipList with a given file extension in extensionList
  localizeClipsWithExtension(clipList, extensionList = None, policy = hiero.core.Clip.kOnLocalize ):
  @param: clipList - a list of hiero.core.Clip objects
  @param: extensionList - a list of file extensions, e.g. ['dpx','exr','mov']
  @param: policy - the localization policy (kOnLocalize,kAutoLocalize,kOnDemandLocalize,kOffLocalize)"""

  if type(extensionList) != list:
    print("Please supply a list of file extensions, e.g. extensionList=['dpx','exr','mov']")
    return
  else:
    clipPath = clip.mediaSource().filename()
    hiero.core.log.info('clipPath is'+str(clipPath))
    if clipPath.lower().endswith( tuple(extensionList) ):
      clip.setLocalizationPolicy( policy )

class CustomLocalizationDialog(QtWidgets.QDialog):

  def __init__(self,itemSelection=None,parent=None):
    super(CustomLocalizationDialog, self).__init__(parent)
    self.setWindowTitle("Select File Extensions to Localize")
    self.setWindowIcon(QtGui.QIcon("icons:BlendingDisabled.png"))
    self.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
    
    layout = QtWidgets.QFormLayout()
    self._itemSelection = itemSelection

    self._formatFilterEdit = QtWidgets.QLineEdit()
    self._formatFilterEdit.setToolTip('Enter a comma separated list of file extensions to localize, e.g. dpx, exr')
    self._formatFilterEdit.setText('dpx')
    layout.addRow("Extension: ",self._formatFilterEdit)

    # Standard buttons for Add/Cancel
    self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.Ok).setText("Add")
    self._buttonbox.accepted.connect(self.accept)
    self._buttonbox.rejected.connect(self.reject)
    layout.addRow("",self._buttonbox)
    
    self.setLayout(layout)

  def convertFormatStringToFormatList(self):
    formatString = self._formatFilterEdit.text()
    formats = formatString.split(',')
    return formats
    

  # Set Tag dialog with Note and Selection info. Adds Tag to entire object, not over a range of frames
  def showDialogAndLocalizeSelection(self):
    
    if len(self._itemSelection)<1:
      hiero.core.log.info('No valid selected Items can be localized')
      return

    clips = [item for item in self._itemSelection if isinstance(item, hiero.core.Clip)]
    
    if len(clips)==0:
      return
      
    if self.exec_():
      exts = self.convertFormatStringToFormatList()
      hiero.core.log.info('Got this extension list:'+str(exts))
      for clip in clips:
        setlocalizationPolicyOnClipWithExtension(clip, extensionList = exts)
      return



# Menu which adds a Tags Menu to the Viewer, Project Bin and Timeline/Spreadsheet
class CustomLocalizeMenu:

  def __init__(self):
    self._localizeMenu = None
    self._customLocalizeDialog = None

    # These actions in the viewer are a special case, because they drill down in to what is currrenly being
    self._localizeBinContents = createMenuAction("This Bin", self.localizeBinSelection,icon="icons:Bin.png")
    self._localizeThisBinSequence = createMenuAction("This Sequence", self.localizeBinSelection,icon="icons:TimelineStroked.png")
    self._localizeBinContentsCustom = createMenuAction("This Bin Custom...", self.localizeBinSelectionCustom,icon="icons:BlendingDisabled.png")
    self._localizeThisSequence  = createMenuAction("This Sequence", self.localizeTimelineSpreadsheetSequence,icon="icons:TimelineStroked.png")
    self._localizeThisTrack  = createMenuAction("This Track", self.localizeTimelineSpreadsheetSelection,icon="icons:Tracks.png")
    self._localizeThisShot  = createMenuAction("This Shot", self.localizeTimelineSpreadsheetSelection,icon="icons:Mask.png")

    hiero.core.events.registerInterest("kShowContextMenu/kBin", self.binViewEventHandler)
    hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.timelineSpreadsheetEventHandler)
    hiero.core.events.registerInterest("kShowContextMenu/kSpreadsheet", self.timelineSpreadsheetEventHandler)

  def createLocalizeMenuForView(self, viewName):
    localizeMenu = QtWidgets.QMenu("Custom Localize")
    if viewName == 'kBin':
      localizeMenu.addAction(self._localizeBinContents)
      localizeMenu.addAction(self._localizeBinContentsCustom)
      localizeMenu.addAction(self._localizeThisBinSequence)

    elif viewName == 'kTimeline/kSpreadsheet':
      localizeMenu.addAction(self._localizeThisSequence)
      localizeMenu.addAction(self._localizeThisTrack)
      localizeMenu.addAction(self._localizeThisShot)

    return localizeMenu

  # Called from the Bin View, to a BinItem selection.
  # Note: A mixed selection of Bins AND Sequences is not currently supported.
  def localizeBinSelection(self):
    if self._selection == None:
      return
    elif isinstance(self._selection[0],hiero.core.Bin):
      for bin in self._selection:
        setlocalizationPolicyOnBin(bin)

    elif isinstance(self._selection[0],hiero.core.Sequence):
      for seq in self._selection:
        setlocalizationPolicyOnSequence(seq)

  # Called from the Bin View, to localize all Clips with a custom Extension
  def localizeBinSelectionCustom(self):
    if self._selection == None:
      return
    elif isinstance(self._selection[0],hiero.core.Bin):
      clips = []
      for bin in self._selection:
        clips += hiero.core.findItemsInBin(bin, filter = hiero.core.Clip)
      # Present Custom Localize Dialog:
      if len(clips)>=1:
        CustomLocalizationDialog(itemSelection=clips).showDialogAndLocalizeSelection()

  # Called from the Spreadsheet or Timeline View, to localize all Clips in the Shot or Track
  def localizeTimelineSpreadsheetSelection(self):
    if self._selection == None:
      return
    
    elif isinstance(self._selection[0],hiero.core.TrackItem):
      for ti in self._selection:
        setlocalizationPolicyOnTrackItem(ti)

    elif isinstance(self._selection[0],(hiero.core.VideoTrack,hiero.core.AudioTrack)):
      for track in self._selection:
        setlocalizationPolicyOnTrack(track)

  # Called from the Spreadsheet or Timeline View, to localize all Clips in the current Sequence
  def localizeTimelineSpreadsheetSequence(self):
    if self._selection == None:
      return
    
    # We should only have one Sequence to localize. Take just the first item
    sequenceItem = self._selection[0]
    
    if isinstance(sequenceItem,(hiero.core.VideoTrack,hiero.core.AudioTrack)):
      sequence = sequenceItem.parent()
    elif isinstance(sequenceItem,hiero.core.TrackItem):
      sequence = sequenceItem.parent().parent()

    if isinstance(sequence,hiero.core.Sequence):
      setlocalizationPolicyOnSequence(sequence)

  # This handles events from the Project Bin View
  def binViewEventHandler(self,event):

    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the Bin view which gives a selection.
      return
    s = event.sender.selection()

    # Return if there's no Selection. We won't add the Localize Menu.
    if s == None:
      return

    # Filter the selection to only act on Bins
    binSelection = [item for item in s if isinstance(item, (hiero.core.Bin))]
    binItemSelection = [item for item in s if isinstance(item,hiero.core.BinItem)]
    sequenceSelection = [item.activeItem() for item in binItemSelection if isinstance(item.activeItem(),hiero.core.Sequence)]
    self._selection = binSelection+sequenceSelection
    hiero.core.log.info('selection is'+ str(self._selection))
    
    binsSelected = len(binSelection)>=1
    sequencesSelected = len(sequenceSelection)>=1
      
    if binsSelected and sequencesSelected:
      hiero.core.log.debug('Selection must either be a Bin selection or Sequence Selection')
      return

    # Only add the Menu if Bins or Sequences are selected (this ensures menu isn't added in the Tags Pane)
    if len(self._selection) > 0:
      self._localizeMenu = self.createLocalizeMenuForView('kBin')
      self._localizeBinContents.setEnabled(binsSelected)
      self._localizeBinContentsCustom.setEnabled(binsSelected)
      self._localizeThisBinSequence.setEnabled(sequencesSelected)
      
      # Insert the Tags menu with the Localization Menu
      hiero.ui.insertMenuAction(self._localizeMenu.menuAction(), event.menu)
    return


  # This handles events from the Project Timeline View
  def timelineSpreadsheetEventHandler(self,event):

    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which gives a selection.
      return
    s = event.sender.selection()

    # Return if there's no Selection. We won't add the Tags Menu.
    if s == None:
      return

    # Filter the selection to only act on TrackItems, not Transitions etc.
    shotSelection = [item for item in s if isinstance(item, (hiero.core.TrackItem))]
    trackSelection = [item for item in s if isinstance(item, (hiero.core.VideoTrack,hiero.core.AudioTrack))]
  
    if len(shotSelection)>=1 and len(trackSelection)>=1:
      hiero.core.log.debug('Selection must either be a Shot selection or a Track Selection')
      return
      
    # We don't currently get a mixture of TrackItem and Tracks but combine the two lists to make a selection
    self._selection = shotSelection+trackSelection
    
    if len(self._selection) > 0:
      self._localizeMenu = self.createLocalizeMenuForView('kTimeline/kSpreadsheet')
      self._localizeThisShot.setEnabled(len(shotSelection)>=1)
      self._localizeThisTrack.setEnabled(len(trackSelection)>=1)
      
      # Insert the Tags menu with the Clear Tags Option
      hiero.ui.insertMenuAction(self._localizeMenu.menuAction(),  event.menu)
    return

# Instantiate the Menu to get it to register itself.
customLocalizeMenu = CustomLocalizeMenu()




