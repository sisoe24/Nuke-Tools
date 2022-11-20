# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import time
import hiero.core
from . FnCompRenderTask import createCompRenderTasks
from hiero.core.FnNukeHelpers import offsetNodeAnimationFrames
from . FnEffectHelpers import ensureEffectsNodesCreated


class TimelineProcessor(hiero.core.ProcessorBase):

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


  def sequenceRange (self, sequence):
    # Calculate the actual range of a sequence
    min, max = sequence.duration() - 1, 0
    for track in sequence.videoTracks() + sequence.audioTracks():
      if len(track) > 0:
        if track[0].timelineIn() < min:
          min = track[0].timelineIn()
        if track[-1].timelineOut() > max:
          max = track[-1].timelineOut()
    return min, max


  def startFrameOffset(self):
    """ If the export start frame is set to 'Custom', return the custom value.
    Otherwise returns 0.
    """
    offset = 0
    if self._preset.properties()["startFrameSource"] == "Custom":
      offset = self._preset.properties()["startFrameIndex"]
    return offset


  def createSequenceCopy(self, sequence, excludedTracks, itemFilter=None):
    """ Create a copy of a sequence, not including any tracks which are in the
    excluded list, and filtering track items with the itemFilter function if
    given.
    """
    sequenceCopy = sequence.copy()

    # Copied effect items create their nodes lazily, but this has to happen on
    # the main thread, force it to be done here.
    ensureEffectsNodesCreated(sequenceCopy)

    # If startframe source is custom, transpose the trackitems on the timeline
    offset = self.startFrameOffset()

    # Add tags to the copied sequence
    self._tagCopiedSequence(sequence, sequenceCopy)

    trackCopyPairs = list(zip(sequence.videoTracks(), sequenceCopy.videoTracks())) + list(zip(sequence.audioTracks(), sequenceCopy.audioTracks()))
    for track, trackCopy in trackCopyPairs:
      # Filter excluded tracks
      if track in excludedTracks:
        sequenceCopy.removeTrack(trackCopy)
        continue
      else:
        # Unlock copied track so that items may be removed
        trackCopy.setLocked(False)

      # walk the track items in the track, in reverse order
      for trackItem, trackItemCopy in reversed(list(zip(track, trackCopy))):
        #if we dont unlink, the deletion of linked items may delete selected items
        trackItemCopy.unlinkAll()

        # Apply the filter function if given
        itemFiltered = itemFilter(trackItem) if itemFilter else False
        if itemFiltered:
          trackCopy.removeItem(trackItemCopy, hiero.core.TrackBase.eDontRemoveLinkedItems)
        elif offset:
          # Transpose clip according to start frame offset
          trackItemCopy.move(offset)

      # Handle the track's subtracks, iterating over the items in reverse order
      if isinstance(track, hiero.core.VideoTrack):
        for subTrackItems, subTrackItemsCopy in zip(track.subTrackItems(), trackCopy.subTrackItems()):
          for subTrackItem, subTrackItemCopy in reversed(list(zip(subTrackItems, subTrackItemsCopy))):
            # Apply the filter function if given
            itemFiltered = itemFilter(subTrackItem) if itemFilter else False

            # Filter out items which are not valid. At the moment, this means
            # effects which are not aligned with track items as they should be.
            isEffectItem = isinstance(subTrackItemCopy, hiero.core.EffectTrackItem)
            itemValid = subTrackItem.isValid() if isEffectItem else True

            removeItem = itemFiltered or (not itemValid)

            if removeItem:
              # Generally, subtrack items only have links if they're effects attached to a track item.  It's also not
              # possible to unlink these.  In the current selection logic, shouldn't be possible to have a track item
              # selected and its linked effects not, but who knows, this might change.  To ensure correctness, remove
              # effects independently from their linked items.
              trackCopy.removeSubTrackItem(subTrackItemCopy, hiero.core.TrackBase.eDontRemoveLinkedItems)
            elif offset:
              # Transpose clip according to start frame offset
              subTrackItemCopy.move(offset)

            # An additional call to isValid() to make sure all the effect items
            # are linked correctly.. Could really do with a better/more reliable
            # mechanism for this.
            if isEffectItem:
              subTrackItemCopy.isValid()

      # Filter out any tracks which didn't have any selected items on them
      removeTrack = True
      if trackCopy.numItems() > 0 or (isinstance(trackCopy, hiero.core.VideoTrack) and len(trackCopy.subTrackItems()) > 0):
        removeTrack = False

      if removeTrack:
        sequenceCopy.removeTrack(trackCopy)

      if offset:
        # Offset transitions by startFrameOffset
        for transition, transitionCopy in reversed(list(zip(track.transitions(), trackCopy.transitions()))):
          transitionCopy.move(offset)

    return sequenceCopy


  def exportSequenceForTrackItem(self, trackItem, exportItems, excludedTracks):
    """ Create a copy of the track item's sequence, removing any excluded
    tracks or unselected items from it.
    Return a tuple of the sequence, the copy, and the project
    """

    sequence = trackItem.parent().parent()

    # Function for filtering unselected items. Return True if the item wasn't
    # in the selected list
    # Here it is assumed that if we encounter a track item in the selected
    # export items all of the items are trackitems. Right now this is a
    # safe assumption because the selection of track items comes from the
    # timeline viewer which only has context of one timeline at a time.
    def selectedFilter(item):
      for i in exportItems:
        if i.trackItem() == item:
          return False
      return True

    sequenceCopy = self.createSequenceCopy(sequence, excludedTracks, itemFilter=selectedFilter)
        
    # Calculate the actual range of the sequence now that items have been trimmed
    offset = self.startFrameOffset()
    inTime, outTime = self.sequenceRange(sequenceCopy)
    if self._preset.properties()["inOutTrim"]:

      # If in/out points have been set, copy to clone
      try:
        # Adjust in/out points by any start frame offset and copy to cloneSequence  
        inTime = sequence.inTime() + offset
      except RuntimeError:
        # In point not set
        pass

      try:
        # Adjust in/out points by any start frame offset and copy to cloneSequence
        outTime = sequence.outTime() + offset
      except RuntimeError:
        # Out point not set
        pass

    sequenceCopy.setInTime(inTime)
    sequenceCopy.setOutTime(outTime)

    return sequence, sequenceCopy, sequence.project()


  def exportSequenceForSequence(self, sequence, excludedTracks):
    """ Create a copy of the sequence and remove any excluded tracks from it
    Return a tuple of the sequence, the copy, and the project name
    """

    sequenceCopy = self.createSequenceCopy(sequence, excludedTracks)

    # Make sure the sequence actually has anything on it, otherwise setting the
    # in/out times will cause an exception.
    if sequence.duration() > 0:
      # Always use the full range of the sequence
      offset = self.startFrameOffset()
      inTime, outTime = offset, sequenceCopy.duration() - 1
      if self._preset.properties()["inOutTrim"]:
        try:
          # If in/out points have been set, copy to clone
          # Adjust in/out points by any start frame offset and copy to cloneSequence
          inTime = sequence.inTime() + offset
        except RuntimeError:
          # In point not set
          pass
        try:
          # Adjust in/out points by any start frame offset and copy to cloneSequence
          outTime = sequence.outTime() + offset
        except RuntimeError:
          # Out point not set
          pass

      sequenceCopy.setInTime(inTime)
      sequenceCopy.setOutTime(outTime)

    return sequence, sequenceCopy, sequence.project()

  def _processTrackItems(self, exportItems, preview):
    firstTrackItem = exportItems[0].trackItem()
    sequence = firstTrackItem.sequence()
    excludedTracks = [track for track in sequence if track.guid() in self._preset._excludedTrackIDs]
    sequenceData = []
    s = self.exportSequenceForTrackItem(firstTrackItem, exportItems, excludedTracks)
    if not s[1]:
      raise Exception("TimelineProcessor.startProcessing no sequence given!")
    sequenceData.append( s )
    return self._createTasks( sequenceData, preview )

  def _processSequences(self, exportItems, preview):
    sequenceData = []
    for item in exportItems:
      # Non-sequences may be included in the export items, skip them
      if not item.sequence():
        continue

      excludedTracks = [track for track in item.sequence() if track.guid() in self._preset._excludedTrackIDs]
      s = self.exportSequenceForSequence(item.sequence(), excludedTracks)
      if not s[1]:
        raise Exception("TimelineProcessor.startProcessing no sequence given!")
      sequenceData.append( s )
    return self._createTasks( sequenceData, preview )

  def _createTasks(self, sequences, preview):
    """ Create export tasks. sequences is a list of tuples with
    (sequence, sequenceClone, project).
    """

    tasks = []

    # Create the queue structure
    self._submission.setFormatDescription( self._preset.name() )

    localtime = time.localtime(time.time())
    path = self._exportTemplate.exportRootPath()
    versionIndex = self._preset.properties()["versionIndex"]
    versionPadding = self._preset.properties()["versionPadding"]

    startFrame = None
    if self._preset.properties()["startFrameSource"] == "Custom":
      startFrame = self._preset.properties()["startFrameIndex"]

    version = "v%s" % format(versionIndex, "0%id" % int(versionPadding))

    # Keep a list of resolved export paths, so we can detect duplicates
    exportPaths = []

    # Create a resolver from the preset (specific to this type of processor)
    resolver = self._preset.createResolver()

    # Generate tasks for any comps that need to be rendered before the main export.
    # sequences is a list of tuples in the form sequence, sequenceCopy, project, get
    # the project from the first tuple in the list
    if not preview:
      createCompRenderTasks(self, sequences[0][2] )

    for sequence, sequenceCopy, project in sequences:
      group = hiero.core.TaskGroup()
      group.setTaskDescription( sequence.name() )
      self._submission.addChild( group )

      for (exportPath, preset) in self._exportTemplate.flatten():
        # Create export task seed
        taskData = hiero.core.TaskData(preset,
                                       sequenceCopy,
                                       path,
                                       exportPath,
                                       version,
                                       self._exportTemplate,
                                       project=project,
                                       startFrame=startFrame,
                                       retime=True, resolver=resolver,
                                       submission=self._submission,
                                       skipOffline=self.skipOffline(),
                                       mediaToSkip=self._preset._compsToSkip)

        # Create task
        task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)

        # Add task to export queue
        if task:
          # Give the task an oppertunity to modify the original (not the copy) sequence
          if not task.error() and not preview:
            task.updateItem(sequence, localtime)

          tasks.append(task)
          group.addChild(task)
          hiero.core.log.debug( "Added to Queue " + task.name() )

    if not preview:
      # If processor is flagged as Synchronous, flag tasks too
      if self._synchronous:
        self._submission.setSynchronous()

      if self._submission.children():

        # Detect any duplicates
        self.processTaskPreQueue()

        self._submission.addToQueue()

    return tasks

  def startProcessing(self, exportItems, preview=False):

    hiero.core.log.debug( "TimelineProcessor::startProcessing(" + str(exportItems) + ")" )

    # exportItems should either be a list of TrackItems or a list of Sequences, check the first
    # item to determine which
    processingTrackItems = exportItems[0].trackItem() is not None
    if processingTrackItems:
      return self._processTrackItems(exportItems, preview)
    else:
      return self._processSequences(exportItems, preview)

class TimelineProcessorPreset(hiero.core.ProcessorPreset):
  def __init__(self, name, properties):
    hiero.core.ProcessorPreset.__init__(self, TimelineProcessor, name)

    # setup defaults
    self._excludedTrackIDs = [ ]
    self.nonPersistentProperties()["excludedTracks"] = [ ]
    self.properties()["versionIndex"] = 1
    self.properties()["versionPadding"] = 2
    self.properties()["exportTemplate"] = ( )
    self.properties()["exportRoot"] = "{projectroot}"
    self.properties()["inOutTrim"] = False
    self.properties()["startFrameIndex"] = 1
    self.properties()["startFrameSource"] = "Sequence"
    self.properties().update(properties)

    # This remaps the project root if os path remapping has been set up in the preferences
    self.properties()["exportRoot"] = hiero.core.remapPath (self.properties()["exportRoot"])

  def addCustomResolveEntries(self, resolver):
    """addDefaultResolveEntries(self, resolver)
    Create resolve entries for default resolve tokens shared by all task types.
    @param resolver : ResolveTable object"""

    resolver.addResolver("{sequence}", "Name of the sequence being processed", lambda keyword, task: task.sequenceName())


hiero.core.taskRegistry.registerProcessor(TimelineProcessorPreset, TimelineProcessor)
