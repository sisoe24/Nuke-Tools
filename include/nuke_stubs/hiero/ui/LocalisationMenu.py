# Localization Helper Menu -
# Adds Localize menu to the right-click menu for setting the Policy of localisation at the TrackItem, Track, and Sequence Level
import nuke_internal as nuke
import hiero.core
from PySide2 import QtWidgets
from hiero.ui import findMenuAction, insertMenuAction, createMenuAction


def _localisationEnabled():
  preferencesNode = nuke.toNode( "preferences" )
  knob = preferencesNode.knob( "localizationMode" )
  return knob.value() != "off"
  

class LocaliseMenu:
  """Localization menu which adds right-click options for localising items from the Bin/Timeline/Spreadsheet view"""
  def __init__(self):
      self._localiseMenu = None

      # These actions are added to the right-click menu of the Bin View for a selection of Bins/Sequences.
      self._localiseBinContentsAction = createMenuAction("Bin", self.localiseBinSelection,icon="icons:Bin.png")
      self._localiseBinSequenceAction = createMenuAction("Sequence", self.localiseBinSelection,icon="icons:TimelineStroked.png")
    
      # These actions are added to the right-click menu of the Timeline/Spreadsheet View
      self._localiseSequenceSelectionAction  = createMenuAction("Sequence", self.localiseTimelineSpreadsheetSequence,icon="icons:TimelineStroked.png")
      self._localiseTrackSelectionAction  = createMenuAction("Track", self.localiseTimelineSpreadsheetSelection,icon="icons:Tracks.png")
      self._localiseShotSelectionAction  = createMenuAction("Shot", self.localiseTimelineSpreadsheetSelection,icon="icons:Mask.png")

      hiero.core.events.registerInterest("kShowContextMenu/kBin", self.binViewEventHandler)
      hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.timelineSpreadsheetEventHandler)
      hiero.core.events.registerInterest("kShowContextMenu/kSpreadsheet", self.timelineSpreadsheetEventHandler)
      
      prefsNode = nuke.toNode( "preferences" )
      nuke.addKnobChanged( self.onPrefsKnobChanged, node = prefsNode )


  def onPrefsKnobChanged(self):
    enabled = _localisationEnabled()
    self._localiseSequenceSelectionAction.setEnabled( enabled )
    self._localiseTrackSelectionAction.setEnabled( enabled )
    self._localiseShotSelectionAction.setEnabled( enabled )


  def createLocaliseMenuForView(self, viewName):
    localiseMenu = QtWidgets.QMenu("Localize")
    if viewName == 'kBin':
      localiseMenu.addAction(self._localiseBinContentsAction)
      localiseMenu.addAction(self._localiseBinSequenceAction)

    elif viewName == 'kTimeline/kSpreadsheet':
      localiseMenu.addAction(self._localiseSequenceSelectionAction)
      localiseMenu.addAction(self._localiseTrackSelectionAction)
      localiseMenu.addAction(self._localiseShotSelectionAction)

    return localiseMenu

  # Called from the Bin View, to a BinItem selection.
  # Note: A mixed selection of Bins AND Sequences is not currently supported.
  def localiseBinSelection(self):
    if self._selection == None:
      return
    
    proj = self._selection[0].project()
    with proj.beginUndo("Set Localization Policy"):
      if isinstance(self._selection[0],hiero.core.Bin):
        for bin in self._selection:
          hiero.core.setLocalisationPolicyOnBin(bin, hiero.core.Clip.kOnLocalize)

      elif isinstance(self._selection[0],hiero.core.Sequence):
        for seq in self._selection:
          hiero.core.setLocalisationPolicyOnSequence(seq, hiero.core.Clip.kOnLocalize)

  # Called from the Spreadsheet or Timeline View, to localise all Clips in the Shot or Track
  def localiseTimelineSpreadsheetSelection(self):
    if self._selection == None:
      return

    proj = self._selection[0].project()
    with proj.beginUndo("Set Localization Policy"):
      if isinstance(self._selection[0],hiero.core.TrackItem):
        for ti in self._selection:
          hiero.core.setLocalisationPolicyOnTrackItem(ti, hiero.core.Clip.kOnLocalize )

      elif isinstance(self._selection[0],(hiero.core.VideoTrack,hiero.core.AudioTrack)):
        for track in self._selection:
          hiero.core.setLocalisationPolicyOnTrack(track, hiero.core.Clip.kOnLocalize )

  # Called from the Spreadsheet or Timeline View, to localise all Clips in the current Sequence
  def localiseTimelineSpreadsheetSequence(self):
    if self._selection == None:
      return

    proj = self._selection[0].project()
    with proj.beginUndo("Set Localization Policy"):
      # We should only have one Sequence to localise. Take just the first item
      sequenceItem = self._selection[0]
      
      if isinstance(sequenceItem,(hiero.core.VideoTrack,hiero.core.AudioTrack)):
        sequence = sequenceItem.parent()
      elif isinstance(sequenceItem,hiero.core.TrackItem):
        sequence = sequenceItem.parent().parent()

      if isinstance(sequence,hiero.core.Sequence):
        hiero.core.setLocalisationPolicyOnSequence(sequence, hiero.core.Clip.kOnLocalize)

  # This handles events from the Project Bin View
  def binViewEventHandler(self,event):

    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the Bin view which gives a selection.
      return
    s = event.sender.selection()

    # Return if there's no Selection. We won't add the Localise Menu.
    if s == None:
      return

    # Filter the selection to only act on Bins
    binSelection = [item for item in s if isinstance(item, (hiero.core.Bin))]
    binItemSelection = [item for item in s if isinstance(item,hiero.core.BinItem)]
    sequenceSelection = [item.activeItem() for item in binItemSelection if isinstance(item.activeItem(),hiero.core.Sequence)]
    self._selection = binSelection+sequenceSelection
    hiero.core.log.info('selection is'+ str(self._selection))
    
    if len(binSelection)>=1 and len(sequenceSelection)>=1:
      hiero.core.log.debug('Selection must either be a Bin selection or Sequence Selection')
      return

    # Only add the Menu if Bins or Sequences are selected
    if len(self._selection) > 0:
      self._localiseMenu = self.createLocaliseMenuForView('kBin')
      binsSelected = len(binSelection)>=1
      sequencesSelected = len(sequenceSelection)>=1
      localisationEnabled = _localisationEnabled()
      self._localiseBinContentsAction.setEnabled( localisationEnabled and len(binSelection)>=1)
      self._localiseBinSequenceAction.setEnabled( localisationEnabled and len(sequenceSelection)>=1)
      
      # Insert the Localise menu
      insertMenuAction(self._localiseMenu.menuAction(), event.menu, after = "foundry.timeline.clipMenu")
    return

  # This handles events from the Project Bin View
  def timelineSpreadsheetEventHandler(self,event):

    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the timeline view which gives a selection.
      return
    s = event.sender.selection()

    # Return if there's no Selection. We won't add the Localise Menu.
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
      self._localiseMenu = self.createLocaliseMenuForView('kTimeline/kSpreadsheet')
      localisationEnabled = _localisationEnabled()
      self._localiseShotSelectionAction.setEnabled( localisationEnabled and len(shotSelection)>=1)
      self._localiseTrackSelectionAction.setEnabled( localisationEnabled and len(trackSelection)>=1)
      
      # Insert the Localise menu
      hiero.ui.insertMenuAction(self._localiseMenu.menuAction(),  event.menu, after = "foundry.timeline.clipMenu")
    return

# Instantiate the menu
localiationMenu = LocaliseMenu()
