# TagsMenu - Adds a contextual Tags menu to the Viewer, Timeline, Spreadsheet and Bin views, allowing Tags to be added in context.
# Copyright (c) 2012 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero.core
import hiero.ui
from PySide2 import (QtCore, QtGui, QtWidgets)
from hiero.core import find_items
from hiero.ui import findMenuAction, insertMenuAction, createMenuAction

def visibleShotAtTime(sequence, t):
  """visibleShotAtTime(sequence, t) -> Returns the visible TrackItem in a Sequence (sequence) at a specified frame (time).
  @param: sequence - a core.Sequence
  @param: t - an integer (frame no.) at which to return the current TrackItem
  returns: hiero.core.TrackItem"""
  
  shot = sequence.trackItemAt(t)
  if shot == None:
    return shot
    
  elif shot.isMediaPresent() and shot.isEnabled():
    return shot
  
  else:
    # If we're here, the Media is offline or disabled... work out what's visible on other tracks...
    badTrack = shot.parent()
    vTracks = list(sequence.videoTracks())
    vTracks.remove(badTrack)
    for track in reversed(vTracks):
      trackItems = list(track.items())
      for shotCandidate in trackItems:
        if shotCandidate.timelineIn() <= t and shotCandidate.timelineOut() >= time:
          if shotCandidate.isMediaPresent() and shotCandidate.isEnabled():
            shot = shotCandidate
            break
  
  return shot

class AddTagMenuDialog(QtWidgets.QDialog):

  def __init__(self,itemSelection=None,parent=None):
    if not parent:
      parent = hiero.ui.mainWindow()
    super(AddTagMenuDialog, self).__init__(parent)
    self.setWindowTitle("Add Tag")
    self.setWindowIcon(QtGui.QIcon("icons:TagsIcon.png"))
    self.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )

    layout = QtWidgets.QFormLayout()
    self._itemSelection = itemSelection

    # Add a Combobox for selecting a Tag...
    self._iconCombo = QtWidgets.QComboBox()
    
    self._iconCombo.currentIndexChanged.connect(self.tagIconChanged)
    layout.addRow("Icon: ",self._iconCombo)

    self._noteEdit = QtWidgets.QTextEdit()
    self._noteEdit.setToolTip('Enter notes here.')
    self._noteEdit.setFixedHeight(80)
    layout.addRow("Note: ",self._noteEdit)

    # Standard buttons for Add/Cancel
    self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.Ok).setText("Add")
    self._buttonbox.accepted.connect(self.accept)
    self._buttonbox.rejected.connect(self.reject)
    layout.addRow("",self._buttonbox)
    
    # To-do: Set the focus on the _noteEdit field
    self.setLayout(layout)
    
    # Set the focus to be the Note field
    self._noteEdit.setFocus()
  
  def updateTagComboBox(self):
    # Build a list of Tags from Hiero's Preset Tags Bin...
    self.tags = []
    presetTags = hiero.core.find_items.findProjectTags(hiero.core.project('Tag Presets'))
    hiero.core.log.debug('Refreshing TagComboBox')
  
    # Finally, try to add in any Tags used in the project tagsBin...
    if len(self._itemSelection)>=1:
      proj = self._itemSelection[0].project()
      projectTags = hiero.core.find_items.findProjectTags(proj)
    self.tags = presetTags+projectTags

    self._iconCombo.clear()
    # Populate the Tags Dropdown menu
    for t in self.tags:
      self._iconCombo.addItem(QtGui.QIcon(t.icon()),t.name())

  # Override the exec_ method to update the TagComboBox with any new Project Tags
  def exec_(self,selection):
    hiero.core.log.debug('In exec_, with selection: ' + str(selection))
    self._itemSelection = selection
    self.updateTagComboBox()
    return super(AddTagMenuDialog, self).exec_()

  def tagIconChanged(self,index):
    #update the note field
    note = self.tags[index].note()
    self._noteEdit.setText(note)
    
  # This returns a hiero.core.Tag object, currently described by the AddTagMenuDialog 
  def getTag(self):
    # This gets the contents of the Note field
    tagNote = str(self._noteEdit.toPlainText())

    # We get the index of the current drop-down list entry
    index = self._iconCombo.currentIndex()

    # We get the Tag at 'index', from the tags dictionary list in our dialog
    tag = self.tags[index]

    #copy the tag and set the new note
    T = tag.copy()
    T.setNote(tagNote)

    return T


# Menu which adds a Tags Menu to the Viewer, Project Bin and Timeline/Spreadsheet
class TagsMenu:

  def __init__(self):
      self._tagMenu = QtWidgets.QMenu("Tags")
      self._tagDialog = None
      self.currentClipSequence = None

      # These actions in the viewer are a special case, because they drill down in to what is currrenly being
      self._addTagToCurrentViewerFrame = createMenuAction("Tag this Frame", self.addTagCurrentViewerFrame,icon="icons:TagTiny.png")
      self._addTagToCurrentViewerShot = createMenuAction("Tag this Shot", self.addTagToCurrentViewerShot,icon="icons:Mask.png")
      self._addTagToCurrentViewerClipOrSequence  = createMenuAction("Tag whole Sequence", self.addTagToCurrentViewerSequence,icon="icons:TimelineStroked.png")
      self._clearSequenceTags = createMenuAction("Clear Frame Tags", self.clearCurrentViewerTags,icon="icons:TagBad.png")

      # Action for the Bin view to act upon a selection of BinItems
      self._addTagToBinItemSelection  = createMenuAction("Tag Selection", self.addTagToBinItemSelection,icon="icons:Add.png")

      # Actions for the Timeline/Spreadsheet View
      self._addTagToShotSelection = createMenuAction("Tag Shot Selection", self.addTagToShotSelection,icon="icons:Mask.png")
      self._addTagToTrackFromSelection = createMenuAction("Tag Tracks", self.addTagToTrackFromSelection,icon="icons:Tracks.png")
      self._addTagToSequenceFromSelection = createMenuAction("Tag this Sequence", self.addTagToSequenceFromSelection,icon="icons:TimelineStroked.png")
    
      # Grab hold of the C++ Clear Tags method...
      self._projectClearTags = findMenuAction("foundry.project.clearTags")

      hiero.core.events.registerInterest("kShowContextMenu/kViewer", self.viewerEventHandler)
      hiero.core.events.registerInterest("kShowContextMenu/kBin", self.binViewEventHandler)
      hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.timelineSpreadsheetEventHandler)
      hiero.core.events.registerInterest("kShowContextMenu/kSpreadsheet", self.timelineSpreadsheetEventHandler)

    
  # Set Tag dialog with Note and Selection info. Adds Tag to entire object, not over a range of frames
  def showDialogAndTagItems(self, selection):
    
    if len(selection)<1:
      raise Exception('No valid selected Items can be tagged')
      return

    if not self._tagDialog:
      hiero.core.log.debug('No Tag Dialog Exists.. Creating one.')
      self._tagDialog = AddTagMenuDialog()

    if self._tagDialog.exec_(selection):
      hiero.core.log.debug('exec_ing with selection'+str(selection))
      tag = self._tagDialog.getTag()
      for item in selection:
        item.addTag(tag)

  # Set Tag dialog with Note and Selection info. Adds Tag to entire object, not over a range of frames
  def showDialogAndAddTagCurrentViewerFrame(self):
    if not self._tagDialog:
      currentSequence = hiero.ui.currentViewer().player().sequence()
      self._tagDialog = AddTagMenuDialog()
  
    if not self.currentClipSequence:
      self.currentClipSequence = hiero.ui.currentViewer().player().sequence()

    # Double check that the Item selection has an 'addTag' method
    if not hasattr(self.currentClipSequence, 'addTagToRange'):
      raise Exception('Viewer did not have a valid Clip or Sequence')
    else:
      T = self.currentViewer.time()
      if self._tagDialog.exec_([self.currentClipSequence]):
        tag = self._tagDialog.getTag()
        self.currentClipSequence.addTagToRange(tag,T,T)

  # Shows the Tags Bin Project Bin View
  def showTagsBin(self):
    tagsBinAction = findMenuAction("Tags")
    if isinstance(tagsBinAction,QtWidgets.QAction):
      tagsBinAction.trigger()

  # This just builds the Menu Items on a Per View basis based on a viee Name (kBin,kViewer,kTimeline) in the EventHandler

  def createTagMenuForView(self, viewName):
    tagMenu = QtWidgets.QMenu("Tags")
    if viewName == 'kBin':
      tagMenu.addAction(self._addTagToBinItemSelection)
      tagMenu.addAction(self._projectClearTags)

    elif viewName == 'kViewer':
      tagMenu.addAction(self._addTagToCurrentViewerFrame)
      tagMenu.addAction(self._addTagToCurrentViewerShot)
      tagMenu.addAction(self._addTagToCurrentViewerClipOrSequence)
      tagMenu.addAction(self._clearSequenceTags)

    elif viewName == 'kTimeline/kSpreadsheet':
      tagMenu.addAction(self._addTagToShotSelection)
      tagMenu.addAction(self._addTagToTrackFromSelection)
      tagMenu.addAction(self._addTagToSequenceFromSelection)
      tagMenu.addAction(self._projectClearTags)

    return tagMenu

  ########## BIN ITEM TAG METHODS ##########

  # This method adds a Tag a the activeItem of a BinItem (Clip/Sequence)
  # For use with a future keyboard shortcut
  def addTagToActiveViewItems(self):
  
    currentView = hiero.ui.activeView()
    hiero.core.log.debug('Current View is: ' + str(currentView))
    if hasattr(currentView,'selection'):
      currentSelection = currentView.selection()
      hiero.core.log.debug('Selection is:'+str(currentSelection))
        
    if isinstance(currentView,hiero.ui.BinView):
      binItems = [bi.activeItem() for bi in currentSelection if (isinstance(bi,hiero.core.BinItem) and hasattr(bi,'activeItem'))]
 
      # Check we have a valid selection of BinItems...
      if len(binItems)<1:
       return
      else:
        # Present Add Tags Dialog:
        self.showDialogAndTagItems(binItems)

    elif isinstance(currentView,hiero.ui.Viewer):
      self.currentViewer = currentView
      self.currentClipSequence = currentView.player().sequence()
      self.showDialogAndAddTagCurrentViewerFrame()

    elif isinstance(currentView,hiero.ui.TimelineEditor):

      # Filter the selection to only act on TrackItems, not Transitions etc.
      shotSelection = [item for item in currentSelection if isinstance(item, (hiero.core.TrackItem))]
      trackSelection = [item for item in currentSelection if isinstance(item, (hiero.core.VideoTrack,hiero.core.AudioTrack))]

      # We don't currently get a mixture of TrackItem and Tracks but combine the two lists to make a selection
      self._selection = shotSelection+trackSelection
      
      if len(self._selection) > 0:
        if len(trackSelection)>=1:
          self.addTagToTrackFromSelection()
        elif len(shotSelection)>=1:
          # Present Add Tags Dialog:
          self.showDialogAndTagItems(shotSelection)
  
  # This method adds a Tag a the activeItem of a BinItem (Clip/Sequence)
  def addTagToBinItemSelection(self):
  
    binItems = [bi.activeItem() for bi in self._selection if (isinstance(bi,hiero.core.BinItem) and hasattr(bi,'activeItem'))]
    # Check we have a valid selection of BinItems...
    if len(binItems)<1:
      return
    else:
      # Present Add Tags Dialog:
      self.showDialogAndTagItems(binItems)

  ########## TIMELINE / SPREADSHEET  TAG METHODS ##########
   
  # Add Tags to TrackItems in the Timeline/Spreadsheet View
  def addTagToShotSelection(self):
    hiero.core.log.debug('Adding Tags to Selection of Track Items')

    # Check we have a valid selection of Shots...
    shots = [shot for shot in self._selection if isinstance(shot,hiero.core.TrackItem)]
    if len(shots)<1:
      return
    else:
      # Present Add Tags Dialog:
      self.showDialogAndTagItems(shots)

  # Add Tags to Tracks in the Timeline/Spreadsheet View
  def addTagToTrackFromSelection(self):
    hiero.core.log.debug('Adding Tags to Selection of Tracks')

    # Check we have a valid selection of Shots...
    shotSelection = [shot for shot in self._selection if isinstance(shot, hiero.core.TrackItem)]
    
    # Or Tracks..
    trackSelection = [track for track in self._selection if isinstance(track,(hiero.core.VideoTrack, hiero.core.AudioTrack))]
    
    # There are two cases to handle here...
    # Case 1: User has only selected some TrackItems
    tracks = []
    if len(shotSelection)>=1 and len(trackSelection)==0:
      # For each Shot, build a list of unique Tracks
      for shot in shotSelection:
        track = shot.parent()
        if track not in tracks:
          tracks.append(track)

    # Case 2: User has only selected some Track Headers
    elif len(trackSelection)>=1 and len(shotSelection)==0:
      for track in trackSelection:
        tracks.append(track)
      
    if len(tracks)==0:
      return
    else:
      # Present Add Tags Dialog:
      self.showDialogAndTagItems(tracks)

  # Add Tags to Sequence in the Timeline/Spreadsheet View
  def addTagToSequenceFromSelection(self):

    # Check we have a valid selection.. for adding a Sequence Tag this can be a Track or a TrackItem
    selection = [item for item in self._selection if isinstance(item,(hiero.core.TrackItem, hiero.core.AudioTrack, hiero.core.VideoTrack))]
    
    sequence = []
    if len(selection)<1:
      return
    else:
      # Pick the first item and find its parent Sequence
      sequenceItem = selection[0]
      
      # Check if this item is a TrackItem or Track..
      if isinstance(sequenceItem,hiero.core.TrackItem):
        sequence.append(sequenceItem.parent().parent().binItem().activeItem())
      elif isinstance(sequenceItem,(hiero.core.VideoTrack,hiero.core.AudioTrack)):
        sequence.append(sequenceItem.parent().binItem().activeItem())

    if len(sequence)==0:
      return
    else:
      # Present Add Tags Dialog
      self.showDialogAndTagItems(sequence)

  ########## VIEWER TAG METHODS ########## 

  # This adds a Tag to the current Frame in the Viewer
  def addTagCurrentViewerFrame(self):
    hiero.core.log.debug('Adding Tag to current Viewer frame')
    sequence = []
    if self.currentClipSequence == None:
      return
    else:
      sequence.append(self.currentClipSequence.binItem().activeItem())
      # Current Time of the Current Viewer
      T = self.currentViewer.time()

      hiero.core.log.debug('Adding Tag to sequence at Frame '+str(T))
      self.showDialogAndAddTagCurrentViewerFrame()

  # This adds a Tag to the current Shot visible in the Viewer
  def addTagToCurrentViewerShot(self):
    shot = []
    if self.currentClipSequence == None:
      return
    else:
      sequence = self.currentClipSequence.binItem().activeItem()
      
      # Current Time of the Current Viewer
      T = self.currentViewer.time()
      
      # Check that Media is Online - we won't add a Tag to Offline Media
      currentShot = visibleShotAtTime(sequence,T)
      if not currentShot:
        QtWidgets.QMessageBox.warning(None, "Add Shot Tag", "All Shots at this frame are Offline / Disabled\nNot adding Shot Tag.", QtWidgets.QMessageBox.Ok)
        return
      else:
        shot.append(currentShot)
        
        hiero.core.log.debug('Adding Tag to Shot')
        self.showDialogAndTagItems(shot)

  # This Method is called to Add Sequence Tag (All Frames) to the Sequence/Clip in the Viewer
  def addTagToCurrentViewerSequence(self):
    sequence = []
    if self.currentClipSequence == None:
      return
    else:
      sequence.append(self.currentClipSequence.binItem().activeItem())
      hiero.core.log.debug('Adding Tag to Current Clip/Sequence: '+str(self.currentClipSequence))
      self.showDialogAndAddTagCurrentViewerFrame()
      

  # This clears Tags from the Clip/Sequence in the Current Viewer
  def clearCurrentViewerTags(self):
    # If it's in the Viewer, Clear All Tags from The Current Sequence of Clip
    sequence = []
    if self.currentClipSequence == None:
      return
    else:
      sequence.append(self.currentClipSequence.binItem().activeItem())
      for seq in sequence:
        tags = seq.tags()
        for t in tags:
          seq.removeTag(t)      


  ########## EVENT HANDLERS ##########
  
  # This handles events from the Viewer View (kViewer)
  def viewerEventHandler(self, event):
    # We only Enable Tagging when there is a single Clip available (not in Wipe or Horizontal/Vertical compare modes)
    if hiero.ui.currentViewer().layoutMode() in (hiero.ui.Viewer.LayoutMode.eLayoutFree, hiero.ui.Viewer.LayoutMode.eLayoutStack):
      self.currentClipSequence = None
      self.currentViewer = None
      self.currentPlayer = None
      
      self.currentViewer = event.sender
      self.currentPlayer = self.currentViewer.player()
      self.currentClipSequence = self.currentPlayer.sequence()

      if self.currentClipSequence:
        # We don't include 'Shot Tag' if it's a Clip, only for a Sequeunce.
        if isinstance(self.currentClipSequence.binItem().activeItem(),hiero.core.Sequence):
          self._addTagToCurrentViewerShot.setVisible(True)
          self._addTagToCurrentViewerClipOrSequence.setText('Tag whole Sequence')
        elif isinstance(self.currentClipSequence.binItem().activeItem(),hiero.core.Clip):
          self._addTagToCurrentViewerShot.setVisible(False)
          self._addTagToCurrentViewerClipOrSequence.setText('Tag whole Clip')
        else:
          return

        # Insert the Tags menu after the Next Tag menu
        self._tagMenu = self.createTagMenuForView('kViewer')
        insertMenuAction(self._tagMenu.menuAction(), event.menu, after = "foundry.menu.version")
      
    return


  # This handles events from the Project Bin View
  def binViewEventHandler(self,event):

    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we should only be here if raised
      # by the Bin view which gives a selection.
      return
    s = event.sender.selection()

    # Return if there's no Selection. We won't add the Tags Menu.
    if s == None:
      return

    # Filter the selection to only act on TrackItems, not Transitions etc.
    self._selection = [item for item in s if isinstance(item, hiero.core.BinItem)]

    # Only add the Menu if BinItems are selected (this ensures menu isn't added in the Tags Pane)
    if len(self._selection) > 0:
      self._tagMenu = self.createTagMenuForView('kBin')
      # Insert the Tags menu with the Clear Tags Option
      insertMenuAction(self._tagMenu.menuAction(), event.menu, after = "foundry.menu.version")

    return


  # This handles events from the Project Bin View
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

    # We don't currently get a mixture of TrackItem and Tracks but combine the two lists to make a selection
    self._selection = shotSelection+trackSelection
    
    if len(self._selection) > 0:
      self._tagMenu = self.createTagMenuForView('kTimeline/kSpreadsheet')
      if len(shotSelection)==0:
        self._addTagToShotSelection.setVisible(False)
      elif len(shotSelection)>=1:
        self._addTagToShotSelection.setVisible(True)

      # Insert the Tags menu with the Clear Tags Option
      insertMenuAction(self._tagMenu.menuAction(), event.menu, after = "foundry.menu.version")
    return

# Instantiate the Menu to get it to register itself.
tagsMenu = TagsMenu()
