# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import time
import hiero.core
import hiero.core.FnExporterBase as FnExporterBase
import itertools

from hiero.core.VersionScanner import VersionScanner
from . FnExportKeywords import kFileBaseKeyword, kFileHeadKeyword, kFilePathKeyword, KeywordTooltips
from . FnEffectHelpers import ensureEffectsNodesCreated


def getShotNameIndex(trackItem):
  """ Get the name index string for a track item.  This counts other items on the sequence
      with the same name and returns a string in the form '_{index}'.
      If this is the first item, or there are no others with the same name, returns an empty string. """
      
  indexStr = ''
  sequence = trackItem.sequence()
  name = trackItem.name()
  index = 1

  # Iterate over all video track items and check if their names match, incrementing the index.
  # When we hit the test track item, break.
  for videoTrack in sequence.videoTracks():
    matchFound = False
    for otherItem in list(videoTrack.items()):
      if otherItem.name() == name:
        if otherItem == trackItem:
          matchFound = True
          break
        else:
          index = index + 1
    if matchFound:
      break
  if index > 1:
    indexStr = '_%s' % index
  return indexStr



def findTrackItemExportTag(preset, item):
  """ Find a tag from a previous export. """
  presetId = hiero.core.taskRegistry.getPresetId(preset)
  foundTag = None
  for tag in item.tags():
    if tag.metadata().hasKey("tag.presetid") and tag.metadata()["tag.presetid"] == presetId:
      foundTag = tag
      break
  return foundTag



def buildTagsData(exportItems):
  # Collect tags from selection
  tags = FnExporterBase.tagsFromSelection(exportItems, includeChildren=True)

  filters = ["Transcode", "Nuke Project File"]
  # Filter Transcode/NukeProjectFile tags out

  def reverse_contains(item, filters):
    for filter in filters:
      if filter in item:
        return False
    return True

  uniquelist = set()
  def uniquetest(tag, type):
    uniquestr = str(tag.name()) + str(type)
    if uniquestr in uniquelist:
      return False
    uniquelist.add(uniquestr)
    return True

  tags = [(tag, objecttype) for tag, objecttype in tags if tag.visible() and reverse_contains(tag.name(), filters) and uniquetest(tag,objecttype)]
  return tags


class ShotProcessor(hiero.core.ProcessorBase):

  # Settings for determining the start frame of an export.  Note that 'Sequence' is currently disabled.
  kStartFrameSource = "Source"
  kStartFrameCustom = "Custom"
  #kStartFrameSequence = "Sequence"

  # Flag to determine if we should auto-increment the version number if the one selected in the
  # export preset already exists for a track item.  This is a class variable because the check is done
  # in a different instance than the one used for the export.
  _versionUpPreviousExports = False

  def __init__(self, preset, submission=None, synchronous=False):
    """Initialize"""
    hiero.core.ProcessorBase.__init__(self, preset, submission, synchronous)

    self._exportTemplate = None

    self._tags = []

    self.setPreset(preset)

  def preset (self):
    return self._preset

  def setPreset ( self, preset ):
    self._preset = preset
    oldTemplate = self._exportTemplate
    self._exportTemplate = hiero.core.ExportStructure2()
    self._exportTemplate.restore(self._preset.properties()["exportTemplate"])
    if self._preset.properties()["exportRoot"] != "None":
      self._exportTemplate.setExportRootPath(self._preset.properties()["exportRoot"])


  def offlineTrackItems(self, track):
    offlineMedia = []
    for trackitem in track:
      if not trackitem.isMediaPresent():
        try:
            sourcepath = trackitem.source().mediaSource().fileinfos()[0].filename()
        except:
            sourcepath = "Unknown Source"
        offlineMedia.append(' : '.join([trackitem.name(), sourcepath]))
    return offlineMedia


  def _trackHasTrackOrSubTrackItems(self, track):
    """ Test if a track has any items or sub-track items. """
    if (
      len(list(track.items())) > 0 or
      (isinstance(track, hiero.core.VideoTrack) and len( [ item for item in itertools.chain(*track.subTrackItems()) ] ) > 0)
      ):
      return True
    else:
      return False



  def _getTrackItemExistingExportVersionIndices(self, item, tag):
    """ Get the indices of all the existing versions which were exported with the
        current preset from the given track item . """
    tagScriptPath = tag.metadata().value("tag.script")
    scanner = VersionScanner()
    versionIndices = scanner.getVersionIndicesForPath(tagScriptPath) # Get all the existing version indices
    return versionIndices


  def _getTrackItemExportVersionIndex(self, item, version, tag):
    """ Get the version index with which the track item should be exported.  The input is the version which is
        selected in the preset.  If the option was selected, we scan for existing versions, and if that version
        already exists, return a new one. """
    newVersion = version
    if ShotProcessor._versionUpPreviousExports and tag:
      versionIndices = self._getTrackItemExistingExportVersionIndices(item, tag)
      if version in versionIndices:
        newVersion = versionIndices[-1] + 1
    return newVersion


  def _checkTrackItemExportExistingVersion(self, item, version, tag):
    """ Check if a track item has already been exported with a given version. """
    versionIndices = self._getTrackItemExistingExportVersionIndices(item, tag)
    if not versionIndices:
      raise RuntimeError("No version indices found")
    if version in versionIndices:
      return True
    else:
      return False


  def startProcessing(self, exportItems, preview=False):
    hiero.core.log.debug( "ShotProcessor::startProcessing(" + str(exportItems) + ")" )

    sequences = []
    selectedTrackItems = set()
    selectedSubTrackItems = set()
    ignoredTrackItems = set()
    excludedTracks = []
    
    # Build Tags data from selection
    self._tags = buildTagsData(exportItems)
    
    # Filter the include/exclude tags incase the previous tag selection is not included in the current selection
    included_tag_names = [ tag.name() for tag, objectType in self._tags if tag.name() in self._preset.properties()["includeTags"] ]
    excluded_tag_names = [ tag.name() for tag, objectType in self._tags if tag.name() in self._preset.properties()["excludeTags"] ]

    # This flag controls whether items which havent been explicitly included in the export, 
    # should be removed from the copied sequence. This primarily affects the collate functionality in nuke script generation.
    exclusiveCopy = False

    # List of track items for different views related to the main track item.
    trackItemsForViews = []

    # Track items were selected
    if exportItems[0].trackItem():
      sequences.append( exportItems[0].trackItem().parent().parent() )
      for item in exportItems:
        trackItem = item.trackItem()
        if isinstance(trackItem, hiero.core.TrackItem):
          selectedTrackItems.add( trackItem )
          if item.ignore():
            ignoredTrackItems.add( trackItem )
          else:
            trackItemsForViews = item.trackItemsForViews()
        elif isinstance(trackItem, hiero.core.SubTrackItem):
          selectedSubTrackItems.add( trackItem )

    else: 
      # Items were selected in the project panel. Build a list of selected sequences
      sequences = [ item.sequence() for item in exportItems if item.sequence() is not None ]
      
    if ignoredTrackItems:
      # A set of track items have been explicitly marked as ignored. 
      # This track items are to be included in the copy, but not exported.
      # Thus any shot which isnt in the selected list, should be excluded from the copy.
      exclusiveCopy = True

    for sequence in sequences:
      excludedTracks.extend( [track for track in sequence if track.guid() in self._preset._excludedTrackIDs] )
      
    localtime = time.localtime(time.time())

    path = self._exportTemplate.exportRootPath()
    versionIndex = self._preset.properties()["versionIndex"]
    versionPadding = self._preset.properties()["versionPadding"]
    retime = self._preset.properties()["includeRetimes"]

    cutHandles = None
    startFrame = None

    if self._preset.properties()["startFrameSource"] == ShotProcessor.kStartFrameCustom:
      startFrame = self._preset.properties()["startFrameIndex"]

    # If we are exporting the shot using the cut length (rather than the (shared) clip length)
    if self._preset.properties()["cutLength"]:
      # Either use the specified number of handles or zero
      if self._preset.properties()["cutUseHandles"]:
        cutHandles = int(self._preset.properties()["cutHandles"])
      else:
        cutHandles = 0


    # Create a resolver from the preset (specific to this type of processor)
    resolver = self._preset.createResolver()

    self._submission.setFormatDescription( self._preset.name() )

    exportTrackItems = []
    copiedTrackItemsForViews = []
    copiedSequences = []

    project = None

    for sequence in sequences:
      sequenceCopy = sequence.copy()
      copiedSequences.append( sequenceCopy )
      self._tagCopiedSequence(sequence, sequenceCopy)

      # Copied effect items create their nodes lazily, but this has to happen on
      # the main thread, force it to be done here.
      ensureEffectsNodesCreated(sequenceCopy)

      # The export items should all come from the same project
      if not project:
        project = sequence.project()

      if not preview:
        presetId = hiero.core.taskRegistry.addPresetToProjectExportHistory(project, self._preset)
      else:
        presetId = None

      # For each video track
      for track, trackCopy in list(zip(sequence.videoTracks(), sequenceCopy.videoTracks())) + list(zip(sequence.audioTracks(), sequenceCopy.audioTracks())):

        # Unlock copied track so that items may be removed
        trackCopy.setLocked(False)

        if track in excludedTracks or not track.isEnabled():
          # remove unselected track from copied sequence
          sequenceCopy.removeTrack(trackCopy)
          continue

        # Used to store the track items to be removed from trackCopy, this is to
        # avoid removing items whilst we are iterating over them.
        trackItemsToRemove = []

        # For each track item on track
        for trackitem, trackitemCopy in zip(list(track.items()), list(trackCopy.items())):

          trackitemCopy.unlinkAll() # Unlink to prevent accidental removal of items we want to keep

          # If the track item is used for extra views, keep track of the copy, and
          # keep it on the copied sequence
          if trackitem in trackItemsForViews:
            copiedTrackItemsForViews.append(trackitemCopy)
            continue

          # If we're processing the whole sequence, or this shot has been selected
          if not selectedTrackItems or trackitem in selectedTrackItems:

            if trackitem in ignoredTrackItems:
              hiero.core.log.debug( "%s marked as ignore, skipping. Selection : %s" % (str(trackitemCopy), str(exportTrackItems)) )
              continue
              
            # Check tags for excluded tags
            excludedTags = [tag for tag in trackitem.tags() if tag.name() in excluded_tag_names]
            includedTags = [tag for tag in trackitem.tags() if tag.name() in included_tag_names]

            if included_tag_names:
              # If not included, or explictly excluded
              if not includedTags or excludedTags:
                hiero.core.log.debug( "%s does not contain include tag %s, skipping." % (str(trackitemCopy), str(included_tag_names)) )
                ignoredTrackItems.add(trackitem)
                continue
              else:
                hiero.core.log.debug( "%s has include tag %s." % (str(trackitemCopy), str(included_tag_names)) )
              
            elif excludedTags:
              hiero.core.log.debug( "%s contains excluded tag %s, skipping." % (str(trackitemCopy), str(excluded_tag_names)) )
              ignoredTrackItems.add(trackitem)
              continue

            if trackitem.isMediaPresent() or not self.skipOffline():

              exportTrackItems.append((trackitem, trackitemCopy))  

            else:
              hiero.core.log.debug( "%s is offline. Removing." % str(trackitem) )
              trackItemsToRemove.append(trackitemCopy)
          else:
            # Either remove the track item entirely, or mark it as ignored, so that no tasks are spawned to export it.
            if exclusiveCopy:
              hiero.core.log.debug( "%s is not selected. Removing." % str(trackitem) )
              trackItemsToRemove.append(trackitemCopy)
            else:
              hiero.core.log.debug( "%s is not selected. Ignoring." % str(trackitem) )
              ignoredTrackItems.add(trackitem)


        for item in trackItemsToRemove:
          trackCopy.removeItem(item)


    allTasks = []

    for trackitem, trackitemCopy in exportTrackItems:
      
      if trackitem in ignoredTrackItems:
       continue

      # Check if a task is already exporting this item and if so, skip it.
      # This is primarily to handle the case of collating shots by name, where we only 
      # want one script containing all the items with that name.
      createTasks = True
      for existingTask in allTasks:

        if existingTask.isExportingItem(trackitemCopy):
          createTasks = False
          break

      if not createTasks:
        continue
      
      taskGroup = hiero.core.TaskGroup()
      taskGroup.setTaskDescription( trackitem.name() )

      # Track items may end up with different versions if they're being re-exported.  Determine
      # the version for each item.
      trackItemVersionIndex = self._getTrackItemExportVersionIndex(trackitem, versionIndex, findTrackItemExportTag(self._preset, trackitem))
      trackItemVersion = "v%s" % format(int(trackItemVersionIndex), "0%id" % int(versionPadding))

      # If processor is flagged as Synchronous, flag tasks too
      if self._synchronous:
        self._submission.setSynchronous()

      # For each entry in the shot template
      for (exportPath, preset) in self._exportTemplate.flatten():

        # Build TaskData seed
        taskData = hiero.core.TaskData( preset,
                                        trackitemCopy,
                                        path,
                                        exportPath,
                                        trackItemVersion,
                                        self._exportTemplate,
                                        project=project,
                                        cutHandles=cutHandles,
                                        retime=retime,
                                        startFrame=startFrame,
                                        startFrameSource = self._preset.properties()["startFrameSource"],
                                        resolver=resolver,
                                        submission=self._submission,
                                        skipOffline=self.skipOffline(),
                                        presetId=presetId,
                                        shotNameIndex = getShotNameIndex(trackitem) )

        # Set the track items for views on TaskData. For the moment, setting this
        # as an attribute directly as it's only used for create comp with 
        # NukeShotExporter
        taskData.trackItemsForViews = copiedTrackItemsForViews

        # Spawn task
        task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)

        # Add task to export queue
        if task and task.hasValidItem():

          # Give the task an opportunity to modify the original (not the copy) track item
          if not task.error() and not preview:
            task.updateItem(trackitem, localtime)

          taskGroup.addChild(task)
          allTasks.append(task)
          hiero.core.log.debug( "Added to Queue " + trackitem.name() )
      
      if preview:
        # If previewing only generate tasks for the first item, otherwise it
        # can slow down the UI
        if allTasks:
          break
      else:
        # Dont add empty groups
        if len(taskGroup.children()) > 0:
          self._submission.addChild( taskGroup )

    if not preview:
      # If processor is flagged as Synchronous, flag tasks too
      if self._synchronous:
        self._submission.setSynchronous()

      if self._submission.children():

        # Detect any duplicates
        self.processTaskPreQueue()

        self._submission.addToQueue()

      ShotProcessor._versionUpPreviousExports = False # Reset this after export
    return allTasks
      
      
class ShotProcessorPreset(hiero.core.ProcessorPreset):
  def __init__(self, name, properties):
    hiero.core.ProcessorPreset.__init__(self, ShotProcessor, name)

    # setup defaults
    self._excludedTrackIDs = [ ]
    self.nonPersistentProperties()["excludedTracks"] = []
    self.properties()["excludeTags"] = []
    self.properties()["includeTags"] = []
    self.properties()["versionIndex"] = 1
    self.properties()["versionPadding"] = 2
    self.properties()["exportTemplate"] = ( )
    self.properties()["exportRoot"] = "{projectroot}"
    self.properties()["cutHandles"] = 12
    self.properties()["cutUseHandles"] = False
    self.properties()["cutLength"] = False
    self.properties()["includeRetimes"] = False
    self.properties()["startFrameIndex"] = 1001
    self.properties()["startFrameSource"] = ShotProcessor.kStartFrameSource

    self.properties().update(properties)

    # This remaps the project root if os path remapping has been set up in the preferences
    self.properties()["exportRoot"] = hiero.core.remapPath (self.properties()["exportRoot"])

  def addCustomResolveEntries(self, resolver):
    """addDefaultResolveEntries(self, resolver)
    Create resolve entries for default resolve tokens shared by all task types.
    @param resolver : ResolveTable object"""

    resolver.addResolver("{filename}", "Filename of the media being processed", lambda keyword, task: task.fileName())
    resolver.addResolver(kFileBaseKeyword, KeywordTooltips[kFileBaseKeyword], lambda keyword, task: task.filebase())
    resolver.addResolver(kFileHeadKeyword, KeywordTooltips[kFileHeadKeyword], lambda keyword, task: task.filehead())
    resolver.addResolver(kFilePathKeyword, KeywordTooltips[kFilePathKeyword], lambda keyword, task: task.filepath())
    resolver.addResolver("{filepadding}", "Source Filename padding for formatting frame indices", lambda keyword, task: task.filepadding())
    resolver.addResolver("{fileext}", "Filename extension part of the media being processed", lambda keyword, task: task.fileext())
    resolver.addResolver("{clip}", "Name of the clip used in the shot being processed", lambda keyword, task: task.clipName())
    resolver.addResolver("{shot}", "Name of the shot being processed", lambda keyword, task: task.shotName())
    resolver.addResolver("{track}", "Name of the track being processed", lambda keyword, task: task.trackName())
    resolver.addResolver("{sequence}", "Name of the sequence being processed", lambda keyword, task: task.sequenceName())
    resolver.addResolver("{event}", "EDL event of the track item being processed", lambda keyword, task: task.editId())
    resolver.addResolver("{_nameindex}", "Index of the shot name in the sequence preceded by an _, for avoiding clashes with shots of the same name", lambda keyword, task: task.shotNameIndex())

  #check that all nuke shot exporters have at least one write node
  def isValid(self):
    allNukeShotsHaveWriteNodes = True
    for itemPath, itemPreset in self.properties()["exportTemplate"]:
      isNukeShot = isinstance(itemPreset, hiero.exporters.FnNukeShotExporter.NukeShotPreset)
      if isNukeShot and not itemPreset.properties()["writePaths"]:
        allNukeShotsHaveWriteNodes = False
        return (False,"Your Export Structure has no Write Nodes defined.")
    return (True,"")

hiero.core.taskRegistry.registerProcessor(ShotProcessorPreset, ShotProcessor)
