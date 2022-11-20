
import hiero.ui
import hiero.core
import itertools
import sys
from PySide2 import QtWidgets
from hiero.ui.BuildExternalMediaTrack import *

from .hiero_state import HieroMediaDescriptor

from hiero.ui import SendToNuke



class ProjectShotPresetDialog(QtWidgets.QDialog):
  """ Dialog for selecting a project shot preset. """

  @staticmethod
  def getPresetFromDialog(project, text):
    """ Show a ProjectShotPresetDialog and return the selected preset, or None if the user cancelled. """
    dialog = ProjectShotPresetDialog(project, text)
    if dialog.exec_():
      shotPreset = dialog.selectedPreset()
      project.setShotPresetName(shotPreset.name())
      return shotPreset
    else:
      return None


  def __init__(self, project, text):
    super(ProjectShotPresetDialog, self).__init__(hiero.ui.mainWindow())

    self.setWindowTitle("Project Shot Preset")

    layout = QtWidgets.QVBoxLayout()
    self.setLayout(layout)

    label = QtWidgets.QLabel(text)
    layout.addWidget(label)

    self.comboBox = QtWidgets.QComboBox()
    layout.addWidget(self.comboBox)

    for preset in hiero.core.taskRegistry.nukeShotExportPresets(project):
      self.comboBox.addItem(preset.name(), preset)

    buttonBox = QtWidgets.QDialogButtonBox( QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel )
    buttonBox.accepted.connect( self.accept )
    buttonBox.rejected.connect( self.reject )
    layout.addWidget( buttonBox )


  def selectedPreset(self):
    index = self.comboBox.currentIndex()
    return self.comboBox.itemData(index)


def getProjectShotPreset(project):
  """ Get the project shot preset, prompting the user if the currently selected preset
      does not exist or is invalid. """
  name = project.shotPresetName()

  # If there is no preset currently set, show the selection dialog
  if not name:
    shotPreset = ProjectShotPresetDialog.getPresetFromDialog(project, "Please select a shot export preset:")
    return shotPreset

  # Find the current preset and check if it's valid
  shotPreset = None
  for preset in itertools.chain(hiero.core.taskRegistry.projectPresets(project), hiero.core.taskRegistry.localPresets()):
    if hiero.core.taskRegistry.isNukeShotExportPreset(preset) and name == preset.name():
      shotPreset = preset
      break

  # If no valid preset was found for the current name, show the selection dialog
  if not shotPreset:
    text = "Shot export preset '%s' does not exist or is not valid.  Please select another:" % name
    shotPreset = ProjectShotPresetDialog.getPresetFromDialog(project, text)
    if shotPreset:
      project.setShotPresetName(shotPreset.name())

  return shotPreset
    
class SendToNukeHandler:
  def __init__(self, hieroState):
    hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), self.binContextMenuEventHandler)
    hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kTimeline), self.timelineContextMenuEventHandler)
    hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kSpreadsheet), self.timelineContextMenuEventHandler)

    # override the old send to Nuke handlers, because we're going to call them manually
    if not hiero.core.isHieroPlayer():
      hiero.core.events.unregisterInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), SendToNuke.sendToNukeAction.eventHandler)
      hiero.core.events.unregisterInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), SendToNuke.add32Action.eventHandler)
      hiero.core.events.unregisterInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), SendToNuke.remove32Action.eventHandler)

    self._actions = []
    self._hieroState = hieroState

  def _findBinItemsRecursive(self, container):
    """ Recursively search for clips and sequences inside a bin hierarchy. """
    ret = []

    # For a Bin, return child Clips and Sequences searched recursively
    if isinstance(container, hiero.core.Bin):
      ret.extend([c.activeItem() for c in itertools.chain(container.clips(), container.sequences())])
      childBins = container.bins()
      for i in childBins:
        ret.extend(self._findBinItemsRecursive(i))

    # For a sequence, recursively call its contents
    elif isinstance(container, (list, tuple)):
      for i in container:
        ret.extend(self._findBinItemsRecursive(i))

    # it's not a bin, or an iterable, so check if it's a BinItem
    else:
      if hasattr(container, 'activeItem'):
        item = container.activeItem()
        if isinstance(item, (hiero.core.Clip, hiero.core.Sequence)):
          ret.append(item)

      # check if it has sub items as well
      if hasattr(container, 'items'):
        items = list(container.items())
        for i in items:
          ret.extend(self._findBinItemsRecursive(i))

    return ret

  def _findBinItems(self, items):
    """ From items, get a list of tuples, each tuple containing a name (used for backdrop), and a list of clips/sequences to send to Nuke. """
    result = []
    for item in items:
      result.append( (item.name(), self._findBinItemsRecursive(item)) )
    return result

  def _findItems(self, container, clips, sequences, trackItems, bins, effectItems, annotations):
    if isinstance(container, hiero.core.Bin):
      # it's a bin; make sure it has some clips or sequences somewhere in it
      if container.sequences() or container.clips():
        bins.append(container)
      else:
        childBins = container.bins()
        for i in childBins:
          localSequences = []
          localClips = []
          # find any child sequences or clips on this child bin; don't care about track items and bins in this context, because bins don't store track items and we don't care about bins from here
          self._findItems(i, localClips, localSequences, [], [], [], [])
          if localClips or localSequences:
            bins.append(container)
            return

    # check for track item
    if isinstance(container, hiero.core.TrackItem):
      # only do video, for now
      if container.mediaType() == hiero.core.TrackItem.kVideo:
        trackItems.append(container)

    # Check if it's an effect item
    elif isinstance(container, hiero.core.EffectTrackItem):
      effectItems.append(container)

    # Check if it's an annotation
    elif isinstance(container, hiero.core.Annotation):
      annotations.append(container)

    # check if this is an iterable item, that may contain multiple things
    if isinstance(container, (list, tuple)):
      for i in container:
        self._findItems(i, clips, sequences, trackItems, bins, effectItems, annotations)
    else:
      # it's not a bin, or an iterable, so check if it's a BinItem
      if hasattr(container, 'activeItem'):
        item = container.activeItem()
        if isinstance(item, hiero.core.Clip):
          clips.append(item)
        elif isinstance(item, hiero.core.Sequence):
          sequences.append(item)

          # Find all the effects on the sequence
          for track in item.videoTracks():
            for subTrackItems in track.subTrackItems():
              for subTrackItem in subTrackItems:
                self._findItems(subTrackItem, clips, sequences, trackItems, bins, effectItems, annotations)

      # check if it has sub items as well
      if hasattr(container, 'items'):
        items = list(container.items())
        for i in items:
          self._findItems(i, clips, sequences, trackItems, bins, effectItems, annotations)

  def _addAction(self, action, menu):
    self._actions.append(action)
    menu.addAction(action)
    #action.setEnabled(isValid)

  def binContextMenuEventHandler(self, event):
    pass


  def timelineContextMenuEventHandler(self, event):
    pass