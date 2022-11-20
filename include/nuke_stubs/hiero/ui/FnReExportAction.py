import itertools
import traceback
import hiero.core
import hiero.ui
from hiero.core import ItemWrapper
from hiero.core.VersionScanner import VersionScanner
from PySide2.QtWidgets import QAction, QMessageBox, QMenu


def findTrackItemByUID(sequence, uid):
  """ Try to find an item with the given uid on the sequence. """
  for track in sequence.videoTracks():
    for item in list(track.items()):
      if item.guid() == uid:
        return item
  return None


def findItemReExportTag(item):
  """ Helper function to find the export tag to be used for re-export.  Returns the most recent tag
      if there is more than one. """
  foundTag = None
  for tag in reversed(item.tags()):
    if tag.metadata().hasKey("tag.presetid"):
      foundTag = tag
      break
  return foundTag


def findOriginalTrackItemAndTag(trackItem):
  """ Given a track item which has been created using 'Build Track', find the tag
      which links back to the original item, and return both the original item and its export tag. """

  for tag in reversed(trackItem.tags()):
    if tag.metadata().hasKey("tag.originaltrackitem"):
      originalTrackItem = findTrackItemByUID(trackItem.sequence(), tag.metadata().value("tag.originaltrackitem"))
      if originalTrackItem:
        originalTag = findItemReExportTag(originalTrackItem)
        if originalTag:
          return originalTrackItem, originalTag
  return None, None


def findNewVersionIndex(path):
  """ Scan for versioned files in the given path and return the first unused version index.  If the path
      contains no versioning, the user is asked if they wish to overwrite the existing files. """
  try:
    # Get the new version from the scanner.  Raises an exception if no versioned files were found, i.e. there was no versioning in the path
    versionScanner = VersionScanner()
    newVersionIndex = versionScanner.getNewVersionIndexForPath(path)
  except:
    response = QMessageBox.question(hiero.ui.mainWindow(), "Re-Export", "No versions in export path.  Do you want to overwrite?", QMessageBox.Yes | QMessageBox.No)
    if response == QMessageBox.Yes:
      newVersionIndex = 1 # Version doesn't matter since it's not being used, but we need to return something
    else:
      raise
  return newVersionIndex


def setEnabledTasks(preset, enableShots, enableAnnotations):
  """ Set tasks in the preset enabled or disabled depending on whether shots or annotations
      are being exported. """

  # Do this import here, otherwise we have problems with circular imports
  import hiero.exporters

  for path, taskPreset in preset.properties()["exportTemplate"]:
    if isinstance(taskPreset, hiero.exporters.FnNukeAnnotationsExporter.NukeAnnotationsPreset):
      taskPreset.properties()["enable"] = enableAnnotations
    elif isinstance(taskPreset, hiero.exporters.FnNukeShotExporter.NukeShotPreset):
      taskPreset.properties()["enable"] = enableShots


def setPresetTasksProperty(preset, name, value):
  """ Iterate over the task presets and if they have the given property, set its value. """
  for path, taskPreset in preset.properties()["exportTemplate"]:
    if name in taskPreset.properties():
      taskPreset.properties()[name] = value



def findTrackItemsIntersecting(intersectTrackItem, excludeTracks=[]):
  """ Find items intersecting the given track item. """
  intersectingItems = []

  inTime = intersectTrackItem.timelineIn()
  outTime = inTime + intersectTrackItem.duration()
  sequence = intersectTrackItem.sequence()

  for track in sequence.videoTracks():
    if track in excludeTracks:
      continue

    for trackItem in track:
      if trackItem == intersectTrackItem:
        continue

      trackItemIn = trackItem.timelineIn()
      trackItemOut = trackItemIn + trackItem.duration()
      if trackItemIn >= outTime:
        break
      elif inTime < trackItemOut:
        intersectingItems.append(trackItem)

  return intersectingItems


class ReExportAction(QAction):
  """ Action for re-exporting track items. """

  def __init__(self, reExportItemsTags, text="Re-Export", parent=None):
    QAction.__init__(self, text, parent)
    self.triggered.connect(self.onTriggered)

    self.reExportItemsTags = reExportItemsTags


  def onTriggered(self):
    try:
      # Determine the tags and versions for all our items.  If this fails then exit without doing anything
      excludeTracks = set()
      trackItems = []
      tags = []
      versions = []

      for (builtItem, item, tag) in self.reExportItemsTags:
        excludeTracks.add( builtItem.parentTrack() )
        trackItems.append(item)
        tags.append(tag)
        newVersion = findNewVersionIndex(tag.metadata()["tag.script"])
        versions.append(newVersion)

      # Re-export all the tagged track items we were given.
      for item, tag, version in zip(trackItems, tags, versions):
        intersectingItems = findTrackItemsIntersecting(item, excludeTracks)

        self.reExportItem(item, tag, version, trackItems + intersectingItems)

    except:
      hiero.core.log.exception("ReExportAction error")


  def reExportItem(self, item, tag, newVersionIndex, allTrackItems):
    project = item.project()

    # Send all the items we were given to the exporter.  Every item other than the one we're currently exporting is set to ignore=True.
    exportItems = [ ItemWrapper(i, ignore=(i != item)) for i in allTrackItems ]

    # Find the preset in the project export history, set the version and do a new export with it.
    preset = hiero.core.taskRegistry.findPresetInProjectExportHistory(project, tag.metadata()["tag.presetid"])
    preset = hiero.core.taskRegistry.copyPreset(preset)
    preset.properties()["versionIndex"] = newVersionIndex

    # Disable annotation tasks
    setEnabledTasks(preset, enableShots=True, enableAnnotations=False)

    hiero.core.taskRegistry.createAndExecuteProcessor(preset, exportItems, synchronous=True)



class ReExportAnnotationsAction(QAction):
  """ Action for re-exporting annotations.  This works a bit differently, as it re-exports from
      the track item created with 'Build Track' rather than the original item.  Any track items under the
      main one are also included and collated into the script. """

  def __init__(self, reExportItemsTags, text="Re-Export Annotations", parent=None):
    QAction.__init__(self, text, parent)
    self.triggered.connect(self.onTriggered)

    self.reExportItemsTags = reExportItemsTags

  # This commented out code writes out the annotations script as a sequence which collates all the other shots which intersect the
  # annotated one.
  #
  # After discussions with Jon and Jack, this is disabled as it can leads to the scripts having different timings, and that makes it awkward
  # for viewing the annotations in Nuke.  Leaving the code in for the time being in case we want to switch back to it working that way.

  #def onTriggered(self):
    #try:
      ## Determine the tags and versions for all our items.  If this fails then exit without doing anything
      #trackItems = []
      #tags = []
      #versions = []
      #for (builtItem, item, tag) in self.reExportItemsTags:
        #trackItems.append(builtItem)
        #tags.append(tag)
        #newVersion = findNewVersionIndex(tag.metadata()["tag.scriptannotations"])
        #versions.append(newVersion)

      ## Re-export all the tagged track items we were given.
      #for item, tag, version in zip(trackItems, tags, versions):
        #intersectingItems = findTrackItemsIntersecting(item)
        #self.reExportAnnotations(item, tag, version, intersectingItems)
    #except:
      #hiero.core.log.exception("ReExportAnnotationsAction error")


  #def reExportAnnotations(self, item, tag, newVersionIndex, allTrackItems):
    #project = item.project()

    ## Send all the items we were given to the exporter.  Every item other than the one we're currently exporting is set to ignore=True.
    #exportItems = []
    #exportItems.append( ItemWrapper(item) )
    #exportItems.extend( [ ItemWrapper(i, ignore=True) for i in allTrackItems ] )

    ## Find the preset in the project export history, set the version and do a new export with it.
    #preset = hiero.core.taskRegistry.findPresetInProjectExportHistory(project, tag.metadata()["tag.presetid"])
    #preset = hiero.core.taskRegistry.copyPreset(preset)
    #preset.properties()["versionIndex"] = newVersionIndex

    ## Disable the main shot task in the export preset
    #setEnabledTasks(preset, enableShots=False, enableAnnotations=True)

    ## Annotations re-export should behave similarly to 'Create Comp'.  We want to create a sequence with all intersecting items,
    ## but have it 'disconnected'.
    #setPresetTasksProperty(preset, "collateSequence", True)

    #hiero.core.taskRegistry.createAndExecuteProcessor(preset, exportItems, synchronous=True)
    #return True


  def onTriggered(self):
    try:
      # Determine the tags and versions for all our items.  If this fails then exit without doing anything
      trackItems = []
      tags = []
      versions = []
      for (builtItem, item, tag) in self.reExportItemsTags:
        trackItems.append(builtItem)
        tags.append(tag)
        newVersion = findNewVersionIndex(tag.metadata()["tag.scriptannotations"])
        versions.append(newVersion)

      # Re-export all the tagged track items we were given.
      for item, tag, version in zip(trackItems, tags, versions):
        self.reExportAnnotations(item, tag, version)
    except:
      hiero.core.log.exception("ReExportAnnotationsAction error")


  def reExportAnnotations(self, item, tag, newVersionIndex):
    project = item.project()

    # Send the item to the exporter
    exportItems = [ ItemWrapper(item) ]

    # Find the preset in the project export history, set the version and do a new export with it.
    preset = hiero.core.taskRegistry.findPresetInProjectExportHistory(project, tag.metadata()["tag.presetid"])
    preset = hiero.core.taskRegistry.copyPreset(preset)
    preset.properties()["versionIndex"] = newVersionIndex

    # Make sure the collate options are disabled on the NukeShotExporter.  The original export may have been collating multiple items, but this one only uses a single track 
    # item and having the collate options enabled can lead to problems.
    setPresetTasksProperty(preset, "collateSequence", False)
    setPresetTasksProperty(preset, "collateTracks", False)
    setPresetTasksProperty(preset, "collateShotNames", False)

    # Disable the main shot task in the export preset
    setEnabledTasks(preset, enableShots=False, enableAnnotations=True)

    hiero.core.taskRegistry.createAndExecuteProcessor(preset, exportItems, synchronous=True)
    return True



class ReExportEventListener(object):
  """ Listen for context menu events in the timeline, and add ReExportActions to it if appropriate depending on the selection. """

  def __init__(self):
    hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kTimeline), self.onContextMenuEvent)


  def onContextMenuEvent(self, event):
    """ Context menu event handler.  Check for items which are valid for re-export and if any are found,
        add entries to the menu. """
    timelineEditor = event.sender
    selection = timelineEditor.selection()
    reExportTrackItems = []
    reExportAnnotationTrackItems = []


    def checkItem(item):
      """ Helper function to recursively check for track items which are valid for re-export. """

      if isinstance(item, hiero.core.VideoTrack):
        for trackItem in item:
          checkItem(trackItem)
      elif isinstance(item, hiero.core.TrackItem):
        originalTrackItem, originalTag = findOriginalTrackItemAndTag(item)
        if originalTrackItem and originalTag:
          reExportTrackItems.append( (item, originalTrackItem, originalTag) )

          # If the original export had annotations, add the re-export annotations option
          if originalTag.metadata().hasKey("tag.scriptannotations"):
            reExportAnnotationTrackItems.append( (item, originalTrackItem, originalTag) )


    # Iterate over the selection, and determine if there are any track items which are suitable for
    # re-export.  We keep a list of invalid items, which will be passed to the exporter so they can be included
    # if they're effects or used for collation.
    for item in selection:
      checkItem(item)

    # If there is anything to re-export, add the appropriate actions.
    # This creates an 'Export' sub-menu, moves the 'Export..' action into it, and
    # adds the re-export actions.
    if (len(reExportAnnotationTrackItems) > 0) or (len(reExportTrackItems) > 0):

      menu = event.menu

      exportAction = hiero.ui.findMenuAction("foundry.project.export")

      exportMenu = QMenu("Export", parent=None)
      menu.insertMenu(exportAction, exportMenu)

      menu.removeAction(exportAction)
      exportMenu.insertAction(None, exportAction)

      # Create Re-Export action
      if len(reExportTrackItems) > 0:
        reExportAction = ReExportAction(reExportTrackItems)
        exportMenu.insertAction(None, reExportAction)

      # Create Re-Export Annotations action
      if len(reExportAnnotationTrackItems) > 0:
        reExportAnnotationsAction = ReExportAnnotationsAction(reExportAnnotationTrackItems)
        exportMenu.insertAction(None, reExportAnnotationsAction)


if not hiero.core.isHieroPlayer():
  eventListener = ReExportEventListener()

