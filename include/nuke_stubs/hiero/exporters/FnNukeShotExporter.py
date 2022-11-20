# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import sys, math
import itertools
import traceback
import re
import copy
import hiero.core
import hiero.core.util
import hiero.core.nuke as nuke
import hiero.ui
from . import FnShotExporter
from . import FnExternalRender
from . import FnEffectHelpers
from . import FnScriptLayout
from hiero.core.FnNukeHelpers import offsetNodeAnimationFrames
from .FnReformatHelpers import reformatNodeFromPreset
from hiero.core import (EffectTrackItem,
                        FnNukeHelpersV2)
import _nuke # import _nuke so it does not conflict with hiero.core.nuke
from . FnExportUtil import (trackItemTimeCodeNodeStartFrame,
                            TrackItemExportScriptWriter,
                            createViewerNode
                            )
from hiero.core.FnEffectHelpers import (FormatChange, transformNodeToFormatChange)
from .FnReformatHelpers import reformatSettingsFromPreset

from hiero.ui.nuke_bridge import FnNsFrameServer as postProcessor

def _subTrackIndex(subTrackItem):
  """ Helper function to get the subtrack index for a subtrack item.
      TODO Should this go in the API? """
  track = subTrackItem.parentTrack()
  for index, subTrackItems in enumerate(track.subTrackItems()):
    if subTrackItem in subTrackItems:
      return index


class NukeShotExporter(FnShotExporter.ShotTask):

  # When building a collated sequence, everything is offset by 1000
  # This gives head room for shots which may go negative when transposed to a
  # custom start frame. This offset is negated during script generation.
  kCollatedSequenceFrameOffset = 1000

  def __init__( self, initDict ):
    """Initialize"""
    FnShotExporter.ShotTask.__init__( self, initDict )

    # Initialise attributes

    # self._sequence may be set to the newly created sequence when collating, keep
    # a reference to the original
    self._parentSequence = self._sequence
    self._collate = False
    self._effects = []
    self._annotations = []
    self._collatedItems = []
    self._collatedSequenceOutputFormat = None

    # Handles from the collated sequence.  This is set as a tuple if a collated sequence is created
    self._collatedSequenceHandles = None

    # Need to keep track of the master track item for disconnected sequence export
    self._masterTrackItemCopy = None

    # Default this to True.  If the following tests fail and return early, we want it in that state.
    # Maybe it would be better to raise an exception or something?
    self._nothingToDo = True
    
    # If skip offline is True and the input track item is offline, return
    if isinstance(self._item, hiero.core.TrackItem):
      if not self._source.isMediaPresent() and self._skipOffline:
        return

    # Check if this task is enabled.  Some tasks in a preset might be selectively disabled
    # when re-exporting
    if not self._preset.properties()["enable"]:
      return

    # All clear.
    self._nothingToDo = False

    # Try to get the track items corresponding to the main one for other views.
    # This isn't always set, so handle the AttributeError exception
    try:
      self._trackItemsForViews = initDict.trackItemsForViews
    except AttributeError:
      self._trackItemsForViews = []

    if isinstance(self._item, hiero.core.TrackItem):
      
      # Build list of collated shots
      self._collatedItems = self._findCollatedItems()

      # Only build sequence if there are multiple shots
      if  len(self._collatedItems) > 1:
        self._collate = True

        # Find all the effects which apply to collated items
        self._effects, self._annotations = FnEffectHelpers.findEffectsAnnotationsForTrackItems(self._collatedItems)

        # Build the sequence of collated shots
        self._buildCollatedSequence()
      else:
        # Find the effects which apply to this item.  Note this function expects a list.
        self._effects, self._annotations = FnEffectHelpers.findEffectsAnnotationsForTrackItems( [self._item] )

    # When creating a comp a bin item and a new track are created with the
    # preset script. The created script is sent to the frameserver to be
    # rewritten with the correct header.
    # In NC, if the script name ends with .nk a new one will be saved by the
    # frameserver with .nknc and the new bin/track items will be created for
    # the .nk script and not for of the one ending with .nknc.
    # _fixExtensionForNukeScriptsPath will change the extensions from .nk to
    # .nknc for the _exportPath and any annotationsPreCompPaths existing in
    # the preset.
    self._fixExtensionForNukeScriptsPath()

    # Generate tasks for the read/write nodes to go in the script. This needs to be
    # done on the main thread, from where this constructor should always be called.
    self._writeTaskData = self._generateTasksForPaths("writePaths")
    self._readTaskData = self._generateTasksForPaths("readPaths")


  def _changeExtension(self, filepath):
    """ Returns the filepath with new extension."""
    if _nuke.env['nc']:
      return re.sub('\.nk$', '.nknc', filepath)

    return re.sub('\.nk$', '.nkind', filepath)


  def _fixExtensionForNukeScriptsPath(self):
    """ Checks if the nuke script extensions in the preset are correct according
    to the application mode"""
    if _nuke.env['nc'] or _nuke.env['indie']:
      if self._exportPath.endswith('.nk'):
        self._exportPath = self._changeExtension( self._exportPath )

      annotationsPreCompPaths = self._preset.properties().get("annotationsPreCompPaths", [])
      for index in range(len(annotationsPreCompPaths)):
        if annotationsPreCompPaths[index].endswith('.nk'):
          annotationsPreCompPaths[index] = self._changeExtension( annotationsPreCompPaths[index] )


  def _findCollatedItems(self):
    """ Build and return list of collated shots, the CollateTracks option includes 
    overlapping and identically named shots. CollateSequence Option includes all 
    shots in parent sequence. This also collates any additional track items for 
    other views"""
    collatedItems = []
    
    collateTime = self._preset.properties()["collateTracks"]
    collateName = self._preset.properties()["collateShotNames"]
    
    # If 'collateSequence' is set, include all the items on the parent sequence 
    # in the exported script
    if self._preset.properties()["collateSequence"]:
      
      # Add all trackitems to collate list
      for track in self._sequence.videoTracks():
        for trackitem in track:
          collatedItems.append(trackitem)

    elif collateName or collateTime or self._trackItemsForViews:
      
      nameMatches = [self._item]
      orderedMatches = []
      
      # First if the collate name option is set, find any items which have 
      # matching names
      if collateName:
        for track in self._sequence.videoTracks():
          for trackitem in track:
            
            if trackitem is not self._item:
              
              # Collate if shot name matches.
              if trackitem.name() == self._item.name():
                nameMatches.append(trackitem)
                continue

      # Second pass, finding any track items which 
      # a) are in the _trackItemsForViews list
      # b) were found in the names list
      # c) have timings which overlap with the main track item, or any of the
      #    ones with matching names
      for track in self._sequence.videoTracks():
        for trackitem in track:
          if trackitem in self._trackItemsForViews:
            orderedMatches.append(trackitem)
            continue

          for nameMatchTrackItem in nameMatches:
            
            if collateTime:
              
              # Starts before or at same time
              if trackitem.timelineIn() <= nameMatchTrackItem.timelineIn():
                # finishes after start
                if trackitem.timelineOut() >= nameMatchTrackItem.timelineIn():
                  orderedMatches.append(trackitem)
                  break
            
              # Starts after
              elif trackitem.timelineIn() > nameMatchTrackItem.timelineIn():
                # Starts before end
                if trackitem.timelineIn() < nameMatchTrackItem.timelineOut():
                  orderedMatches.append(trackitem)
                  break
          
            elif trackitem == nameMatchTrackItem:
              orderedMatches.append(trackitem)
              break
      collatedItems = orderedMatches
    return collatedItems


  def _buildCollatedSequence(self):
    """From the list of collated Items build a sequence, extend edge shots for handles, offset relative to custom start or master shot source frame"""
    if self._collate:
      # When building a collated sequence, everything is offset by 1000
      # This gives head room for shots which may go negative when transposed to a
      # custom start frame. This offset is negated during script generation.
      headRoomOffset = NukeShotExporter.kCollatedSequenceFrameOffset
      
      # Build a new sequence from the collated items
      newSequence = hiero.core.Sequence(self._sequence.name())
      
      # Copy tags from sequence to copy
      for tag in self._sequence.tags():
        newSequence.addTag(hiero.core.Tag(tag))

      # If outputting sequence time, we want the items to remain where they are on the sequence, offset should be 0
      if self.outputSequenceTime():
        offset = 0
      else:
        offset = self._item.sourceIn() - self._item.timelineIn()
        if self._startFrame is not None and self._cutHandles is not None:
          # This flag indicates that an explicit start frame has been specified
          # To make sure that when the shot is expanded to include handles this is still the first
          # frame, here we offset the start frame by the in-handle size
          if  self._preset.properties()["collateCustomStart"]:
            self._startFrame += self._cutHandles

          # The offset required to shift the timeline position to the custom start frame.
          offset = self._startFrame - self._item.timelineIn()

      # Copy the sequence properties.  Timecode start is offset so that track items have
      # the same timecode at their shifted timeline in.
      newSequence.setFormat(self._sequence.format())
      newSequence.setFramerate(self._sequence.framerate())
      newSequence.setDropFrame(self._sequence.dropFrame())
      newSequence.setTimecodeStart(self._sequence.timecodeStart() - (headRoomOffset + offset))
      
      sequenceIn, sequenceOut = sys.maxsize, 0
      for trackitem in self._collatedItems:
        if trackitem.timelineIn() <= sequenceIn:
          sequenceIn = trackitem.timelineIn()
        if trackitem.timelineOut() >= sequenceOut:
          sequenceOut = trackitem.timelineOut()

      # Track the handles added
      sequenceInHandle = 0
      sequenceOutHandle = 0

      # Start with a sequence format as a default
      self._collatedSequenceOutputFormatUpdated = False
      self._collatedSequenceOutputFormat = self._sequence.format()

      # The track items for additional views also need to be copied, build a 
      # list of the copies which will be assigned back to self._trackItemsForViews
      copiedTrackItemsForViews = []

      # Add tracks to the new sequence with tracks that match the original.  These will then be populated
      # with the items that should be exported.  They are stored in newTracks with the original guid as key, so
      # copied track items are added to the correct one.  There is also a list of unusedNewTracks, so any which
      # are not used can be removed at the end.
      unusedNewTracks = set()
      newTracks = {}
      for originalTrack in self._sequence.videoTracks():
        # Create new track
        newTrack = hiero.core.VideoTrack(originalTrack.name())
        newTracks[originalTrack.guid()] = newTrack
        unusedNewTracks.add(newTrack)
        newSequence.addTrack(newTrack)

        # Copy tags from track to copy
        for tag in originalTrack.tags():
          newTrack.addTag(hiero.core.Tag(tag))

        # Copy blending enabled flag
        newTrack.setBlendEnabled(originalTrack.isBlendEnabled())
        newTrack.setBlendMode(originalTrack.blendMode())
        newTrack.setBlendMaskEnabled(originalTrack.isBlendMaskEnabled())

        # Set the view name on the new track
        newTrack.setView(originalTrack.view())

      transitions = set()
      handleInAdjustments = {}
      handleOutAdjustments = {}

      linkedEffects = []

      for trackitem in self._collatedItems:
        parentTrack = trackitem.parentTrack()
        newTrack = newTracks[parentTrack.guid()]
        unusedNewTracks.discard(newTrack)

        # Build a list of transitions to be copied to the new sequence
        if trackitem.inTransition():
          transitions.add(trackitem.inTransition())
        if trackitem.outTransition():
          transitions.add(trackitem.outTransition())

        # Get the item's linked effects to be copied
        linkedEffects.extend( [ item for item in trackitem.linkedItems() if isinstance(item, hiero.core.EffectTrackItem) ] )

        trackItemCopy = trackitem.copy()

        # Need to keep track of the master track item for disconnected sequence exports
        if trackitem == self._item:
          self._masterTrackItemCopy = trackItemCopy
        elif trackitem in self._trackItemsForViews:
          copiedTrackItemsForViews.append(trackItemCopy)

        # When writing a collated sequence, if any track items have their reformat state set to disabled,
        # use the largest source media format as the output format for the sequence.
        if trackitem.reformatState().type() == nuke.ReformatNode.kDisabled:
          sourceFormat = trackitem.source().format()
          if (sourceFormat.width() > self._collatedSequenceOutputFormat.width() and
              sourceFormat.height() > self._collatedSequenceOutputFormat.height()):
            self._collatedSequenceOutputFormatUpdated = True
            self._collatedSequenceOutputFormat = sourceFormat

        # extend any shots
        if self._cutHandles is not None:
          # Maximum available handle size
          handleInLength, handleOutLength = trackitem.handleInLength(), trackitem.handleOutLength()
          # Clamp to desired handle size
          handleIn, handleOut = min(self._cutHandles, handleInLength), min(self._cutHandles, handleOutLength)

          # Prevent in handle going negative. Calculating timelineIn + offset tells us where the item will sit on the
          # sequence, and thus how many frames of handles there are available before it would become negative (since
          # the start of the sequence is always frame 0)
          offsetTimelineIn = trackItemCopy.timelineIn() + offset
          if offsetTimelineIn < handleIn:
            handleIn = max(0, offsetTimelineIn)

          if trackItemCopy.timelineIn() <= sequenceIn and handleIn:
            sequenceInHandle = max(sequenceInHandle, handleIn)
            trackItemCopy.trimIn(-handleIn)
            # Store the handle adjustment so that the linked item can be resized
            # to match the track item it's linked to. Otherwise the item copy
            # will not get relinked to trackItemCopy when it is added to
            # the video track.
            for linkedItem in trackitem.linkedItems():
              handleInAdjustments[linkedItem] = -handleIn
            hiero.core.log.debug("Expanding %s in by %i frames" % (trackItemCopy.name(), handleIn))
          if trackItemCopy.timelineOut() >= sequenceOut and handleOut:
            sequenceOutHandle = max(sequenceOutHandle, handleOut)
            trackItemCopy.trimOut(-handleOut)
            # Store the handle adjustment so that the linked item can be resized
            # to match the track item it's linked to. Otherwise the item copy
            # will not get relinked to trackItemCopy when it is added to
            # the video track.
            for linkedItem in trackitem.linkedItems():
              handleOutAdjustments[linkedItem] = handleOut
            hiero.core.log.debug("Expanding %s out by %i frames" % (trackItemCopy.name(), handleOut))

        trackItemCopy.setTimes(trackItemCopy.timelineIn() + headRoomOffset + offset, trackItemCopy.timelineOut() + headRoomOffset + offset,
                               trackItemCopy.sourceIn(), trackItemCopy.sourceOut())

        # Add copied track item to copied track
        try:
          newTrack.addItem(trackItemCopy)
        except Exception as e:
          clash = list(newTracks[parentTrack.guid()].items())[0]
          error = "Failed to add shot %s (%i - %i) due to clash with collated shots, This is likely due to the expansion of the master shot to include handles. (%s %i - %i)\n" % (trackItemCopy.name(), trackItemCopy.timelineIn(), trackItemCopy.timelineOut(), clash.name(), clash.timelineIn(), clash.timelineOut())
          self.setError(error)
          hiero.core.log.error(error)
          hiero.core.log.error(str(e))

      # If the sequence format wasn't updated this will prevent from attaching
      # additional reformat node
      if not self._collatedSequenceOutputFormatUpdated :
        self._collatedSequenceOutputFormat = None

      # Copy transitions to the new sequence
      for transition in transitions:
        parentTrack = transition.parentTrack()
        newTrack = newTracks[parentTrack.guid()]
        transitionCopy = transition.copy()
        transitionCopy.setTimelineOut(transitionCopy.timelineOut() + headRoomOffset + offset)
        transitionCopy.setTimelineIn(transitionCopy.timelineIn() + headRoomOffset + offset)
        newTrack.addTransition(transitionCopy)

      def copySubTrackItems(subTrackItems):
        """ Helper function to copy sub-track items and add them to the new
        sequence. Returns the copied items """
        copiedItems = []
        for subTrackItem in subTrackItems:
          parentTrack = subTrackItem.parentTrack()
          newTrack = newTracks[parentTrack.guid()]
          unusedNewTracks.discard(newTrack)

          subTrackIndex = _subTrackIndex(subTrackItem)

          subTrackItemCopy = subTrackItem.copy()
          inAdjustment = handleInAdjustments.get(subTrackItem, 0)
          outAdjustment = handleOutAdjustments.get(subTrackItem, 0)
          subTrackItemCopy.setTimelineOut(subTrackItemCopy.timelineOut() + headRoomOffset + offset + outAdjustment)
          subTrackItemCopy.setTimelineIn(subTrackItemCopy.timelineIn() + headRoomOffset + offset + inAdjustment)

          # Offset the soft effects key frames by 1000
          if isinstance( subTrackItemCopy , EffectTrackItem ):
            effectTrackNode = subTrackItemCopy.node()
            offsetNodeAnimationFrames( effectTrackNode , headRoomOffset + offset);
          try:
            newTrack.addSubTrackItem(subTrackItemCopy, subTrackIndex)
            copiedItems.append(subTrackItemCopy)
          except:
            hiero.core.log.exception("NukeShotExporter._buildCollatedSequence failed to add effect")
        return copiedItems

      # Copy linked effects and annotations. This happens before modifying
      # the sequence output format so linked effects get transformed correctly
      copySubTrackItems(itertools.chain(linkedEffects, self._annotations))

      # If reformat type is set to use plate format, set the sequence output
      # format to match the master track item. This will also transform any
      # effects which have been added.
      reformatType = self._preset.properties()["reformat"]["to_type"]
      usingPlateFormat = (reformatType == nuke.ReformatNode.kCompFormatAsPlate)
      usingCustomFormat = (reformatType == nuke.ReformatNode.kToFormat)
      if usingPlateFormat or usingCustomFormat:
        masterItemFormat = self._item.source().format()
        newSequence.setFormat(masterItemFormat)

      # Now add the unlinked effects, and if not outputting to sequence format,
      # transform them.
      copiedEffects = copySubTrackItems(self._effects)

      if copiedEffects and (usingPlateFormat or usingCustomFormat):
        # First transform effects to the master clip's format
        effectsFormatChange = FormatChange(masterItemFormat, self._sequence.format(), masterItemFormat, self._item.reformatState())
        for effect in copiedEffects:
          transformNodeToFormatChange(effect.node(), effectsFormatChange, None)

        # Then, if outputting to a custom format, transform the effects to fit
        # that format. The reason for this is that currently when doing this,
        # the Reformat nodes are added for each clip, and then the unlinked
        # effects on other tracks are added. So they need to be at the custom
        # format selection
        if usingCustomFormat:
          reformatType, format, scale, resize, center, filter = reformatSettingsFromPreset(self._preset)
          reformatState = {"type":reformatType, "resizeType":resize, "resizeCenter":center}
          customFormatChange = FormatChange(format, masterItemFormat, masterItemFormat, reformatState)
          for effect in copiedEffects:
            transformNodeToFormatChange(effect.node(), customFormatChange, None)

      # Use in/out point to constrain output framerange to track item range
      newSequence.setInTime(max(0, (sequenceIn + offset) - sequenceInHandle))
      newSequence.setOutTime((sequenceOut + offset) + sequenceOutHandle)

      # Remove any empty tracks from the new sequence
      for track in unusedNewTracks:
        newSequence.removeTrack(track)

      self._collatedSequenceHandles = (sequenceInHandle, sequenceOutHandle)

      self._trackItemsForViews = copiedTrackItemsForViews
      
      # Useful for debugging, add copied collated sequence to Project
      #newSequence.setName("Collated Sequence")
      #hiero.core.projects()[-1].clipsBin().addItem(hiero.core.BinItem(newSequence))

      # Use this newly built sequence instead
      self._sequence = newSequence


  def updateItem(self, originalItem, localtime):
    """updateItem - This is called by the processor prior to taskStart, crucially on the main thread.\n
      This gives the task an opportunity to modify the original item on the main thread, rather than the copy."""

    # Don't add the tag if this task isn't going to do anything
    if self._nothingToDo:
      return

    import time

    existingTag = None
    for tag in originalItem.tags():
      if tag.metadata().hasKey("tag.presetid") and tag.metadata()["tag.presetid"] == self._presetId:
        existingTag = tag
        break

    if existingTag:
      # Update the script name to the one we just wrote.  This makes it easier
      # for the caller to do any post-export processing (e.g. for Create Comp)
      existingTag.metadata().setValue("tag.script", self.resolvedExportPath())

      # Ensure the startframe/duration tags are updated
      start, end = self.outputRange(clampToSource=False)
      existingTag.metadata().setValue("tag.startframe", str(start))
      existingTag.metadata().setValue("tag.duration", str(end-start+1))

      # Move the tag to the end of the list.
      originalItem.removeTag(existingTag)
      originalItem.addTag(existingTag)
      return

    timestamp = self.timeStampString(localtime)
    tag = hiero.core.Tag("Nuke Project File " + timestamp,
                         "icons:Nuke.png",
                         False)

    tag.metadata().setValue("tag.pathtemplate", self._exportPath)
    tag.metadata().setValue("tag.description", "Nuke Project File")

    writePaths = []
    writeFormats = []

    timelineWriteNode = self._preset.properties().get("timelineWriteNode","")
    # Iterate over write tasks and resolve the paths
    for task, writePath, writePreset in self._writeTaskData:
      resolvedPath = task.resolvedExportPath()

      # Ensure enough padding for output range
      output_start, output_end = task.outputRange(ignoreRetimes=False, clampToSource=False)
      count = len(str(max(output_start, output_end)))
      resolvedPath = hiero.core.util.ResizePadding(resolvedPath, count)

      writePaths.append(resolvedPath)

      writeReformat = reformatNodeFromPreset(writePreset, self._sequence.format())
      # If there is a reformat specified in the preset and it is 'to format', store that, otherwise use
      # the root format.
      if writeReformat and "format" in writeReformat.knobs():
        writeFormats.append(writeReformat.knob("format"))
      else:
        writeFormats.append(self.rootFormat())

    tag.metadata().setValue("tag.path", ";".join(writePaths))
    tag.metadata().setValue("tag.format", ";".join(writeFormats))

    # Right now don't add the time to the metadata
    # We would rather store the integer time than the stringified time stamp
    # tag.setValue("time", timestamp)
    tag.metadata().setValue("tag.script", self.resolvedExportPath())
    tag.metadata().setValue("tag.localtime", str(localtime))
    if self._presetId:
      tag.metadata().setValue("tag.presetid", self._presetId)

    start, end = self.outputRange(clampToSource=False)
    tag.metadata().setValue("tag.startframe", str(start))
    tag.metadata().setValue("tag.duration", str(end-start+1))
    
    if isinstance(self._item, hiero.core.TrackItem):
      tag.metadata().setValue("tag.sourceretime", str(self._item.playbackSpeed()))

    # Store if retimes were applied in the export.  If exporting a collated sequence, retimes are always applied
    # If self._cutHandles is None,  we are exporting the full clip and retimes are never applied whatever the
    # value of self._retime
    applyingRetime = (self._retime and self._cutHandles is not None) or self._collate
    appliedRetimesStr = "1" if applyingRetime else "0"
    tag.metadata().setValue("tag.appliedretimes", appliedRetimesStr)
    
    frameoffset = self._startFrame if self._startFrame else 0
    
    # Only if write paths have been set
    if len(writePaths) > 0:
      # Video file formats are not offset, so set frameoffset to zero
      if hiero.core.isVideoFileExtension(os.path.splitext(timelineWriteNode)[1].lower()):
        frameoffset = 0
        
    tag.metadata().setValue("tag.frameoffset", str(frameoffset))
      
    # Handles aren't included if the item is a freeze frame
    isFreezeFrame = isinstance(self._item, hiero.core.TrackItem) and self._item.playbackSpeed() == 0.0

    # Note: if exporting without cut handles, i.e. the whole clip, we do not try to determine  the handle values,
    # just writing zeroes.  The build track classes need to treat this as a special case.
    # There is an interesting 'feature' of how tags work which means that if you create a Tag with a certain name,
    # the code tries to find a previously created instance with that name, which has any metadata keys that were set before.
    # This means that when multiple shots are being exported, they inherit the tag from the previous one.  To avoid problems
    # always set these keys.
    startHandle, endHandle = 0, 0
    if self._cutHandles and not isFreezeFrame:
      startHandle, endHandle = self.outputHandles()


    tag.metadata().setValue("tag.starthandle", str(startHandle))
    tag.metadata().setValue("tag.endhandle", str(endHandle))

    originalItem.addTag(tag)

  def _buildAdditionalNodes(self, item):
    # Callback from script generation to add additional nodes
    nodes = []
    data = self._preset.properties()["additionalNodesData"]
    if self._preset.properties()["additionalNodesEnabled"]:
      if isinstance(item, hiero.core.Clip):
        # Use AdditionalNodes data to populate based on clip tags
        nodes.extend(FnExternalRender.createAdditionalNodes(FnExternalRender.kPerShot, data, item))
      elif isinstance(item, hiero.core.TrackItem):
        # Use AdditionalNodes data to populate based on TrackItem tags
        nodes.extend(FnExternalRender.createAdditionalNodes(FnExternalRender.kPerShot, data, item))
      elif isinstance(item, (hiero.core.VideoTrack, hiero.core.AudioTrack)):
        # Use AdditionalNodes data to populate based on sequence tags
        nodes.extend(FnExternalRender.createAdditionalNodes(FnExternalRender.kPerTrack, data, item))
      elif isinstance(item, hiero.core.Sequence):
        # Use AdditionalNodes data to populate based on sequence tags
        nodes.extend(FnExternalRender.createAdditionalNodes(FnExternalRender.kPerSequence, data, item))
    return nodes


  def _generateTasksForPaths(self, propertyKey):
    """ Lookup paths in the preset properties and generate tasks from them for
    generating Read/Write nodes. Returns a list of tuples of (task, path, preset).
    """
    tasks = []
    paths = self._preset.properties()[propertyKey]
    for (itemPath, itemPreset) in self._exportTemplate.flatten():
      for path in paths:
        if path == itemPath:
          # Generate a task on same items as this one but swap in the shot path that goes with this preset.
          taskData = hiero.core.TaskData(itemPreset,
                                         self._item,
                                         self._exportRoot,
                                         itemPath,
                                         self._version,
                                         self._exportTemplate,
                                         project=self._project,
                                         cutHandles=self._cutHandles,
                                         retime=self._retime,
                                         startFrame=self._startFrame,
                                         resolver=self._resolver,
                                         skipOffline=self._skipOffline,
                                         shotNameIndex=self._shotNameIndex)
          task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)
          tasks.append( (task, itemPath, itemPreset) )
    return tasks


  def _createWriteNodes(self, firstFrame, start, end, framerate, rootNode):

    class WriteNodeGroup():
      #helper class to allow grouping of nodes around a write node
      def __init__(self):
        self._list = []
        self._name = ""

      def append(self, node):
        self._list.append(node)

      def remove(self, node):
        self._list.remove(node)

      def setWriteNodeName(self, name):
        self._name = name

      def getWriteNodeName(self):
        return self._name

      def nodes(self):
        return self._list

    # To add Write nodes, we get a task for the paths with the preset
    # (default is the "Nuke Write Node" preset) and ask it to generate the Write node for
    # us, since it knows all about codecs and extensions and can do the token
    # substitution properly for that particular item.
    # And doing it here rather than in taskStep out of threading paranoia.
    writeNodes = []
    # Create a stack to prevent multiple write nodes inputting into each other
    StackIdBase = "WriteBranch_"
    branchCount = 0
    stackId = StackIdBase + str(branchCount)

    mainStackId = stackId

    mainStackEndId = "MainStackEnd"

    writeNodes.append( nuke.SetNode(stackId, 0) )
    writeNodeGroups = []

    timelineWriteNode = self._preset.properties()["timelineWriteNode"]
    timelineWriteNodeName = ""
    mainWriteStack = None

    for task, writePath, writePreset in self._writeTaskData:
      if hasattr(task, "nukeWriteNode"):
        localWriteNodeGroup = WriteNodeGroup()
        # Push to the stack before adding the write node

        # If the write path matches the timeline write path and we don't already have a timeline
        # write group, then set this group as the timeline write group.
        setAsMainWrite = ((writePath == timelineWriteNode) and not mainWriteStack)

        if setAsMainWrite:
          # Timeline Write goes on the main branch
          localWriteNodeGroup.append( nuke.PushNode(mainStackId) )
        else:
          # Add dot nodes for non timeline writes.
          # Add a push so that these branch from the Set for the last branch.
          localWriteNodeGroup.append( nuke.PushNode(stackId) )

          # Add the dot
          dotNode = nuke.DotNode()
          localWriteNodeGroup.append(dotNode)

          # Add a set so that the next branch connects to the dot for the last branch
          branchCount += 1
          stackId = StackIdBase + str(branchCount)
          localWriteNodeGroup.append( nuke.SetNode(stackId, 0) )

        try:
          trackItem = self._item if isinstance(self._item, hiero.core.TrackItem) else None
          reformatNode = reformatNodeFromPreset(writePreset, self._parentSequence.format(), trackItem=trackItem)
          if reformatNode:
            localWriteNodeGroup.append(reformatNode)
        except Exception as e:
          self.setError(str(e))

        # Add Burnin group (if enabled)
        burninGroup = task.addBurninNodes(script=None)
        if burninGroup is not None:
          localWriteNodeGroup.append(burninGroup)

        try:
          writeNode = task.nukeWriteNode(framerate, project=self._project)
          writeNode.setKnob("first", start)
          writeNode.setKnob("last", end)
          localWriteNodeGroup.append(writeNode)

          # Set the groups write node name
          localWriteNodeGroup.setWriteNodeName(writeNode.knob("name"))

          if setAsMainWrite:
            mainWriteStack = localWriteNodeGroup
            localWriteNodeGroup.append( nuke.SetNode(mainStackEndId, 0) )

          writeNodeGroups.append(localWriteNodeGroup)

        except RuntimeError as e:
          # Failed to generate write node, set task error in export queue
          # Most likely because could not map default colourspace for format settings.
          self.setError(str(e))

    # Find duplicate write node names
    nameSet = set()
    for nodeStack in writeNodeGroups:
      nodeName = nodeStack.getWriteNodeName()
      if nodeName in nameSet:
        self.setWarning("Duplicate write node name:\'%s\'"%nodeName)
      else:
        nameSet.add(nodeName)

    # If no timelineWriteNode was set, just pick the first one
    if not mainWriteStack and writeNodeGroups:
      mainWriteStack = writeNodeGroups[0]
      # Get rid of the dot node as we're going to add this group to the main branch
      for node in mainWriteStack.nodes():
        if isinstance(node, nuke.DotNode):
          mainWriteStack.remove(node)
      mainWriteStack.append( nuke.SetNode(mainStackEndId, 0) )

    # Set the write node name to the root
    if mainWriteStack:
      timelineWriteNodeName = mainWriteStack.getWriteNodeName()
      rootNode.setKnob(nuke.RootNode.kTimelineWriteNodeKnobName, timelineWriteNodeName)

    # Flatten the groups as a list
    for nodeStack in writeNodeGroups:
      writeNodes.extend(nodeStack.nodes())

    # Add push to connect the next node (probably the viewer) to the timeline write node 
    if mainWriteStack:
      writeNodes.append( nuke.PushNode(mainStackEndId) )

    return writeNodes


  def _createAnnotationsPreComps(self):
    """ Create a pre-comp node for any external annotation scripts. """
    nodes = []
    for path in self._preset.properties()["annotationsPreCompPaths"]:
      path = self.resolvePath( os.path.join(self._exportRoot, path) )
      precomp = nuke.PrecompNode(path, label="Annotations")

      precomp.addTabKnob("Annotations")
      precomp.addRawKnob('addUserKnob {41 annotation_key l annotation T AnnotationsKeys.annotation_key}')
      precomp.addRawKnob('addUserKnob {41 annotation_count l of -STARTLINE T AnnotationsKeys.annotation_count}')
      precomp.addRawKnob('addUserKnob {22 prev l @KeyLeft -STARTLINE T "k = nuke.thisNode()\[\'annotation_key\']\\ncurFrame = nuke.frame()  \\nnewFrame = curFrame\\ncurve = k.animation(0)\\nfor key in reversed(curve.keys()):\\n  if key.x < curFrame:\\n    newFrame = key.x\\n    break\\nnuke.frame( newFrame )\\n"}')
      precomp.addRawKnob('addUserKnob {22 next l @KeyRight -STARTLINE T "k = nuke.thisNode()\[\'annotation_key\']\\ncurFrame = nuke.frame()  \\nnewFrame = curFrame\\ncurve = k.animation(0)\\nfor key in curve.keys():\\n  if key.x > curFrame:\\n    newFrame = key.x\\n    break\\nnuke.frame( newFrame )\\n"}')

      nodes.append( precomp )
    return nodes

  def validate(self):
    # Check that the output Write node has valid views set on it
    timelineWritePath = self._preset.properties()['timelineWriteNode']
    for task, writePath, _ in self._writeTaskData:
      if writePath == timelineWritePath:
        task.validate()

  def views(self):
    # At the moment, all the project's views are set in the script
    return self._project.views()

  def includeAnnotations(self):
    """ Check if annotations are included. """
    return self._preset.properties()["includeAnnotations"]


  def writingSequence(self):
    """ Check if we're writing a single clip or a sequence.  This is the case if the object was initialised with a sequence, or if the collate option is set. """
    return isinstance(self._item, hiero.core.Sequence) or self._collate


  def writingSequenceDisconnected(self):
    """ Check if a sequence being written should be 'disconnected', with only the master track connected to the Write node. """
    return not self._preset.properties()["connectTracks"]


  def rootFormat(self):
    """ Get the string representation of the format that should be set on the
    Root node.
    """
    reformatMethod = self._preset.properties()["reformat"]
    reformatType = reformatMethod["to_type"]

    # A particular format was specified in the preset
    if reformatType == nuke.ReformatNode.kToFormat:
      return reformatMethod["name"]
    # Exporting a sequence or the preset is set to export to the sequence format
    elif (isinstance(self._item, hiero.core.Sequence)
          or self._collate
          or reformatType == nuke.ReformatNode.kCompReformatToSequence):
      return str(self._sequence.format())
    elif isinstance(self._item, hiero.core.TrackItem):
      return str(self._item.source().format())
    else:
      raise RuntimeError("Unable to determine the root format for the Nuke shot")

  def taskStep(self):
    try:
      return self._taskStep()
    except:
      hiero.core.log.exception("NukeShotExporter.taskStep")


  def writeSequence(self, script):
    """ Write the collated sequence to the script. """
    sequenceDisconnected = self.writingSequenceDisconnected()

    script.pushLayoutContext("sequence", self._sequence.name(), disconnected=sequenceDisconnected)
    # When building a collated sequence, everything is offset by 1000
    # This gives head room for shots which may go negative when transposed to a
    # custom start frame. This offset is negated during script generation.
    offset = -NukeShotExporter.kCollatedSequenceFrameOffset if self._collate else 0

    # Get a set of master tracks from the master track item and the ones for
    # other views on different tracks
    masterTracks = set()
    if self._masterTrackItemCopy:
      masterTracks.add(self._masterTrackItemCopy.parent())
      for trackItem in self._trackItemsForViews:
        masterTracks.add(trackItem.parent())

    # When exporting a sequence, everything must output to the same format,
    # if it's set to plate format, use the sequence format. When collating,
    # the sequence will have the same format as the master track item.
    reformatMethod = copy.copy(self._preset.properties()["reformat"])
    if reformatMethod['to_type'] == nuke.ReformatNode.kCompFormatAsPlate:
      reformatMethod['to_type'] = nuke.ReformatNode.kCompReformatToSequence

    scriptParams = FnNukeHelpersV2.ScriptWriteParameters(includeAnnotations=self.includeAnnotations(),
                                                         includeEffects=self.includeEffects(),
                                                         retimeMethod=self._preset.properties()["method"],
                                                         reformatMethod=reformatMethod,
                                                         additionalNodesCallback=self._buildAdditionalNodes,
                                                         views=self.views())
    sequenceWriter = FnNukeHelpersV2.SequenceScriptWriter(self._sequence,
                                                          scriptParams)
    sequenceWriter.writeToScript(script,
                                 offset=offset,
                                 skipOffline=self._skipOffline,
                                 disconnected=sequenceDisconnected,
                                 masterTracks=masterTracks)

    script.popLayoutContext()


  def writeTrackItemCustomReadPaths(self, script, firstFrame):
    """ If other export items are selected as Read nodes, add those to the
    script.  This allows for e.g. using the output of the copy exporter as
    the path for the read node.

    Returns True if any read paths were set.
    """

    # Note: Due to the way this is currently implemented, the script will be a
    # bit different using custom read nodes:
    # - No effects or annotations are included
    # - The output format will always be that of the source clip

    if not self._readTaskData:
      return False

    for task, _, _ in self._readTaskData:
      readNodePath = task.resolvedExportPath()
      itemStart, itemEnd = task.outputRange()
      itemFirstFrame = firstFrame
      if self._startFrame:
        itemFirstFrame = self._startFrame

      if hiero.core.isVideoFileExtension(os.path.splitext(readNodePath)[1].lower()):
        # Don't specify frame range when media is single file
        newSource = hiero.core.MediaSource(readNodePath)
        itemEnd = itemEnd - itemStart
        itemStart = 0
      else:
        # File is image sequence, so specify frame range
        newSource = hiero.core.MediaSource(readNodePath + (" %i-%i" % task.outputRange()))

      # Try to determine the colorspace setting. If the task is a transcode, it
      # will have a 'colourspace' property on the preset and we can use that.
      # Otherwise it's probably a copy or symlink export so can use the same setting
      # as the original clip
      preset = task._preset
      colourspace = None
      if 'colourspace' in preset.properties():
        colourspace = preset.properties()['colourspace']
      else:
        colourspaceKnob = self._clip.readNode()['colorspace']
        if colourspaceKnob.notDefault():
          colourspace = colourspaceKnob.toScript()

      newClip = hiero.core.Clip(newSource, itemStart, itemEnd)

      if self._cutHandles is None:
        newClip.addToNukeScript(script,
                                firstFrame=itemFirstFrame,
                                trimmed=True,
                                nodeLabel=self._item.parent().name(),
                                additionalNodesCallback=self._buildAdditionalNodes,
                                includeEffects=self.includeEffects(),
                                colourTransform=colourspace)
      else:
        # Copy track item and replace source with new clip (which may be offline)
        newTrackItem = hiero.core.TrackItem(self._item.name(), self._item.mediaType())

        for tag in self._item.tags():
          newTrackItem.addTag(tag)

        # Handles may not be exactly what the user specified. They may be clamped to media range
        inHandle, outHandle = 0, 0
        if self._cutHandles:
          # Get the output range without handles
          inHandle, outHandle = task.outputHandles()
          hiero.core.log.debug( "in/outHandle %s %s", inHandle, outHandle )


        newTrackItem.setSource(newClip)

        # Set the new track item's timeline range
        newTrackItem.setTimelineIn(self._item.timelineIn())
        newTrackItem.setTimelineOut(self._item.timelineOut())

        # Set the new track item's source range.  This is the clip range less the handles.
        # So if the export is being done with, say, 10 frames of handles, the source in should be 10
        # (first frame of clip is always 0), and the source out should be (duration - 1 - 10) (there's
        # a 1 frame offset since the source out is the start of the last frame that should be read).
        newTrackItem.setSourceIn(inHandle)
        newTrackItem.setSourceOut((newClip.duration() -1 )- outHandle)

        # Add track item to nuke script
        newTrackItem.addToNukeScript(script,
                                      firstFrame=itemFirstFrame,
                                      includeRetimes=self._retime,
                                      retimeMethod=self._preset.properties()["method"],
                                      startHandle=self._cutHandles,
                                      endHandle=self._cutHandles,
                                      nodeLabel=self._item.parent().name(),
                                      additionalNodesCallback=self._buildAdditionalNodes,
                                      includeEffects=self.includeEffects(),
                                      colourTransform=colourspace)

    return True


  def writeTrackItemOriginalReadPath(self, script, firstFrame):
    """ Write the source track item to the script. """

    # Construct a TrackItemExportScriptWriter and write the track item
    writer = TrackItemExportScriptWriter(self._item)
    writer.setAdditionalNodesCallback(self._buildAdditionalNodes)
    writer.setEffects(self.includeEffects(), self._effects)
    writer.setAnnotations(self.includeAnnotations(), self._annotations)

    # TODO This is being done in both the NukeShotExporter and TranscodeExporter.
    # There should be fully shared code for doing the handles calculations.
    fullClipLength = (self._cutHandles is None)
    if fullClipLength:
      writer.setOutputClipLength()
    else:
      writer.setOutputHandles(*self.outputHandles())

    writer.setIncludeRetimes(self._retime, self._preset.properties()["method"])
    writer.setReformat(self._preset.properties()["reformat"])
    writer.setFirstFrame(firstFrame)
    writer.writeToScript(script)


  def writeTrackItem(self, script, firstFrame):
    """ Write the track item to the script. """

    script.pushLayoutContext("clip", self._item.name())

    # First add any custom read paths if the user selected them. If any were
    # added it will return True
    addedCustomReads = self.writeTrackItemCustomReadPaths(script,
                                                          firstFrame)

    # If no custom reads were added, write the original
    if not addedCustomReads:
      self.writeTrackItemOriginalReadPath(script,
                                          firstFrame)

    script.popLayoutContext()


  def includeEffects(self):
    """ Check if soft effects should be included in the export. """
    return self._preset.properties()["includeEffects"]


  def _taskStep(self):
    FnShotExporter.ShotTask.taskStep(self)
    if self._nothingToDo:
      return False
    
    script = nuke.ScriptWriter()
    
    start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)
    unclampedStart = start
    hiero.core.log.debug( "rootNode range is %s %s %s", start, end, self._startFrame )
    
    firstFrame = start
    if self._startFrame is not None:
      firstFrame = self._startFrame

    # if startFrame is negative we can only assume this is intentional
    if start < 0 and (self._startFrame is None or self._startFrame >= 0):
      # We dont want to export an image sequence with negative frame numbers
      self.setWarning("%i Frames of handles will result in a negative frame index.\nFirst frame clamped to 0." % self._cutHandles)
      start = 0
      firstFrame = 0

    # Clip framerate may be invalid, then use parent sequence framerate
    framerate = self._sequence.framerate()
    dropFrames = self._sequence.dropFrame()
    if self._clip and self._clip.framerate().isValid():
      framerate = self._clip.framerate()
      dropFrames = self._clip.dropFrame()
    fps = framerate.toFloat()
    showAnnotations = self._preset.properties()["showAnnotations"]

    # Create the root node, this specifies the global frame range and frame rate
    rootNode = nuke.RootNode(start, end, fps, showAnnotations)
    rootNode.addProjectSettings(self._projectSettings)

    # Set the views knobs to match the project being exported from
    rootNode.setViewsConfiguration(self._project.viewsAndColors(),
                                   self._project.heroView(),
                                   self._project.showViewColors())

    script.addNode(rootNode)

    if isinstance(self._item, hiero.core.TrackItem):
      rootNode.addInputTextKnob("shot_guid", value=hiero.core.FnNukeHelpers._guidFromCopyTag(self._item),
                                tooltip="This is used to identify the master track item within the script",
                                visible=False)
      inHandle, outHandle = self.outputHandles(self._retime != True)
      rootNode.addInputTextKnob("in_handle", value=int(inHandle), visible=False)
      rootNode.addInputTextKnob("out_handle", value=int(outHandle), visible=False)

    # Set the format knob of the root node
    rootNode.setKnob("format", self.rootFormat())

    # BUG 40367 - proxy_type should be set to 'scale' by default to reflect
    # the custom default set in Nuke. Sadly this value can't be queried,
    # as it's set by nuke.knobDefault, hence the hard coding.
    rootNode.setKnob("proxy_type","scale")

    # Add Unconnected additional nodes
    if self._preset.properties()["additionalNodesEnabled"]:
      script.addNode(FnExternalRender.createAdditionalNodes(FnExternalRender.kUnconnected, self._preset.properties()["additionalNodesData"], self._item))

    writeNodes = self._createWriteNodes(firstFrame, start, end, framerate, rootNode)

    # MPLEC TODO should enforce in UI that you can't pick things that won't work.
    if not writeNodes:
      # Blank preset is valid, if preset has been set and doesn't exist, report as error
      self.setWarning(str("NukeShotExporter: No write node destination selected"))

    if self.writingSequence():
      self.writeSequence(script)

    # Write out the single track item
    else:
      self.writeTrackItem(script, firstFrame)


    script.pushLayoutContext("write", "%s_Render" % self._item.name())
    
    metadataNode = nuke.MetadataNode(metadatavalues=[("hiero/project", self._projectName), ("hiero/project_guid", self._project.guid())] )
    
    # Add sequence Tags to metadata
    metadataNode.addMetadataFromTags( self._sequence.tags() )
    
    # Apply timeline offset to nuke output
    if isinstance(self._item, hiero.core.TrackItem):
      if self._cutHandles is None:
        # Whole clip, so timecode start frame is first frame of clip
        timeCodeNodeStartFrame = unclampedStart
      else:
        startHandle, endHandle = self.outputHandles()
        timeCodeNodeStartFrame = trackItemTimeCodeNodeStartFrame(unclampedStart, self._item, startHandle, endHandle)
      timecodeStart = self._clip.timecodeStart()
    else:
      # Exporting whole sequence/clip
      timeCodeNodeStartFrame = unclampedStart
      timecodeStart = self._item.timecodeStart()

    script.addNode(nuke.AddTimeCodeNode(timecodeStart=timecodeStart, fps=framerate, dropFrames=dropFrames, frame=timeCodeNodeStartFrame))
    # The AddTimeCode field will insert an integer framerate into the metadata, if the framerate is floating point, we need to correct this
    metadataNode.addMetadata([("input/frame_rate",framerate.toFloat())])

    script.addNode(metadataNode)

    # Generate Write nodes for nuke renders.

    for node in writeNodes:
      script.addNode(node)

    # add a viewer
    viewerNode = createViewerNode(self._projectSettings)
    script.addNode( viewerNode )

    # Create pre-comp nodes for external annotation scripts
    annotationsNodes = self._createAnnotationsPreComps()
    if annotationsNodes:
      script.addNode(annotationsNodes)

    scriptFilename = self.resolvedExportPath()
    hiero.core.log.debug( "Writing Script to: %s", scriptFilename )

    # Call callback before writing script to disk (see _beforeNukeScriptWrite definition below)
    self._beforeNukeScriptWrite(script)

    script.popLayoutContext()

    # Layout the script
    FnScriptLayout.scriptLayout(script)

    script.writeToDisk(scriptFilename)
    #if postProcessScript has been set to false, don't post process
    #it will be done on a background thread by create comp
    #needs to be done as part of export task so that information
    #is added in hiero workflow
    if self._preset.properties().get("postProcessScript", True):
      error = postProcessor.postProcessScript(scriptFilename)
      if error:
        hiero.core.log.error( "Script Post Processor: An error has occurred while preparing script:\n%s", scriptFilename )
    # Nothing left to do, return False.
    return False


  def finishTask(self):
    FnShotExporter.ShotTask.finishTask(self)
    self._parentSequence = None



  def _outputHandles(self, ignoreRetimes):
    """ Override from TaskBase.  This deals with handles in collated sequence export
        as well as individual items. """
    startH, endH = self.outputRange(ignoreHandles = False, ignoreRetimes=ignoreRetimes, clampToSource=False)
    start, end = self.outputRange(ignoreHandles = True, ignoreRetimes=ignoreRetimes)
    return int(round(start - startH)), int(round(endH - end))


  def outputRangeForCollatedSequence(self, ignoreHandles):
    """ Get the output range for the collated sequence, with or without handles. """
    start = 0
    end = 0

    if self._startFrame: # Custom start frame specified
      start = self._startFrame
      end = start + self._sequence.duration() - 1

    try:
      start = self._sequence.inTime()
    except RuntimeError:
      # This is fine, no in time set
      pass

    try:
      end = self._sequence.outTime()
    except RuntimeError:
      # This is fine, no out time set
      pass

    # If handles are being ignored, offset the start and end by the handles
    if ignoreHandles and self._collatedSequenceHandles:
      start += self._collatedSequenceHandles[0]
      end -= self._collatedSequenceHandles[1]

    return start, end


  def outputRangeForTrackItem(self, ignoreHandles=False, ignoreRetimes=True, clampToSource=True):
    """ Get the output range for the single track item case. """
    
    # Get input frame range
    ignoreRetimes = self._preset.properties()["method"] != "None"
    start, end = self.inputRange(ignoreHandles=ignoreHandles, ignoreRetimes=ignoreRetimes, clampToSource=clampToSource)

    if self._retime and isinstance(self._item, hiero.core.TrackItem) and ignoreRetimes:
      # end should always be > start.  abs these values to ensure we don't report a -ve duration.
      srcDuration = abs(self._item.sourceDuration())
      playbackSpeed = abs(self._item.playbackSpeed())

      # If the clip is a freeze frame, then playbackSpeed will be 0.  Handle the resulting divide-by-zero error and set output range to duration
      # of the clip.
      try:
        end = (end - srcDuration) + (srcDuration / playbackSpeed) + (playbackSpeed - 1.0)
      except:
        end = start + self._item.duration() - 1

    start = int(math.floor(start))
    end = int(math.ceil(end))

    # If the task is configured to output to sequence time, map the start and end into sequence time.
    if self.outputSequenceTime():
      offset = self._item.timelineIn() - int(self._item.sourceIn() + self._item.source().sourceIn())

      start = max(0, start + offset) # Prevent start going negative
      end = end + offset

    # Offset by custom start time
    elif self._startFrame is not None:
      startFrame = self._startFrame

      # If a custom start time is specified, this includes the handles.  To get the range without handles, we need to offset this
      if ignoreHandles and self._cutHandles:
        inputRangeWithHandles = self.inputRange(ignoreHandles=False, ignoreRetimes=ignoreRetimes, clampToSource=clampToSource)
        startFrame = startFrame + start - inputRangeWithHandles[0]

      end = startFrame + (end - start)
      start = startFrame

    return start, end



  def outputRange(self, ignoreHandles=False, ignoreRetimes=True, clampToSource=True):
    """outputRange(self)
      Returns the output file range (as tuple) for this task, if applicable"""
    start = 0
    end  = 0

    if isinstance(self._item, hiero.core.Sequence) or self._collate:
      start, end = self.outputRangeForCollatedSequence(ignoreHandles)
    elif isinstance(self._item, hiero.core.TrackItem):
      start, end = self.outputRangeForTrackItem(ignoreHandles, ignoreRetimes, clampToSource)

    return (start, end)


  def isExportingItem(self, item):
    """ Check if this task is already including an item in its export.
        Used for preventing duplicates when collating shots into a single script. """

    # Return true if this is the main item for this task, or it's in the list of collated items. """
    if item == self._item or item in self._collatedItems:
      return True
    else:
      return False


  def _beforeNukeScriptWrite(self, script):
    """ Call-back method introduced to allow modifications of the script object before it is written to disk. 
    Note that this is a bit of a hack, please speak to the AssetMgrAPI team before improving it. """
    pass




class NukeShotPresetBase(hiero.core.TaskPresetBase):
  """ Base class for Nuke Project File exports. This only exists because we need
  slightly different behaviour when exporting as shots or sequences, and the way
  exporters are registered requires different types to make that work.
  """
  def __init__(self, name, properties, task):
    """Initialise presets to default values"""
    hiero.core.TaskPresetBase.__init__(self, task, name)
    self.initDefaultProperties()

    # Update preset with loaded data
    self.properties().update(properties)

  def initDefaultProperties(self):
    # Set any preset defaults here
    self.properties()["enable"] = True
    self.properties()["readPaths"] = []
    self.properties()["writePaths"] = []
    self.properties()["timelineWriteNode"] = ""
    self.properties()["collateTracks"] = False
    self.properties()["collateShotNames"] = False
    self.properties()["annotationsPreCompPaths"] = []
    self.properties()["includeAnnotations"] = False
    self.properties()["showAnnotations"] = True
    self.properties()["includeEffects"] = True

    # If True, tracks other than the master one will not be connected to the write node
    self.properties()["connectTracks"] = False

    # Not exposed in UI
    self.properties()["collateSequence"] = False    # Collate all trackitems within sequence
    self.properties()["collateCustomStart"] = True  # Start frame is inclusive of handles

    self.properties()["additionalNodesEnabled"] = False
    self.properties()["additionalNodesData"] = []
    self.properties()["method"] = "Blend"
    self.properties()["reformat"] = {}

    # Add property to control whether the exporter does a postProcessScript call.
    # This is not in the UI, and is only changed by create_comp.  See where this is accessed
    # in _taskStep() for more details.
    self.properties()["postProcessScript"] = True

  def addCustomResolveEntries(self, resolver):
    if _nuke.env['nc']:
      resolver.addResolver("{ext}", "Extension of the file to be output", "nknc")
    elif _nuke.env['indie']:
      resolver.addResolver("{ext}", "Extension of the file to be output", "nkind")
    else:
      resolver.addResolver("{ext}", "Extension of the file to be output", "nk")
  

  def propertiesForPathCallbacks(self):
    """ Get a list of properties used for path callbacks """
    return ( self.properties()["readPaths"],
             self.properties()["writePaths"],
             self.properties()["annotationsPreCompPaths"] )


  def initialiseCallbacks(self, exportStructure):
    """ Reimplemented.  This preset contains paths which reference other
    elements in the export structure.  Registers callbacks which update
    those paths when they change in the UI.
    """

    # TODO This whole mechanism is unreliable and confusing for users.  It could
    # do with a redesign.
    for path in itertools.chain( *self.propertiesForPathCallbacks() ):
      elements = exportStructure.findElementsByPath(path)
      for element in elements:
        element.addPathChangedCallback(self.onElementPathChanged)

  
  def onElementPathChanged(self, oldPath, newPath):
    """ Callback when the path for an element changes.  This updates the paths
    referencing other tasks for read/write/annotations.
    """
    for pathlist in self.propertiesForPathCallbacks():
      for path in pathlist:
        if path == oldPath:
          pathlist.remove(oldPath)
          pathlist.append(newPath)

    if oldPath == self.properties()["timelineWriteNode"]:
      self.properties()["timelineWriteNode"] = newPath


class NukeShotPreset(NukeShotPresetBase):
  """ Preset for 'Process as Shots' script export. """
  def __init__(self, name, properties, task=NukeShotExporter):
    super(NukeShotPreset, self).__init__(name, properties, task)

  def initDefaultProperties(self):
    super(NukeShotPreset, self).initDefaultProperties()
    self._properties["reformat"] = {"to_type":nuke.ReformatNode.kCompFormatAsPlate,
                                    "resize":"width",
                                    "center":True,
                                    "filter":"Cubic"}

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kTrackItem

hiero.core.taskRegistry.registerTask(NukeShotPreset, NukeShotExporter)


class NukeSequenceExporter(NukeShotExporter):
  """ Exporter for 'Process as Sequence' script export. This only exists because
  we need a distinct type to be used for this. It doesn't yet do anything.
  """
  def __init__( self, initDict ):
    super(NukeSequenceExporter, self).__init__(initDict)


class NukeSequencePreset(NukeShotPresetBase):
  """ Preset for 'Process as Sequence' script export. """
  def __init__(self, name, properties, task=NukeSequenceExporter):
    super(NukeSequencePreset, self).__init__(name, properties, task)

  def initDefaultProperties(self):
    super(NukeSequencePreset, self).initDefaultProperties()
    self._properties["reformat"] = {"to_type":nuke.ReformatNode.kCompReformatToSequence,
                                    "resize":"width",
                                    "center":True,
                                    "filter":"Cubic"}

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kSequence

hiero.core.taskRegistry.registerTask(NukeSequencePreset, NukeSequenceExporter)
