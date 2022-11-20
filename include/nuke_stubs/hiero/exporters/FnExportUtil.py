#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A file for helper functions related to exporting which may be shared between
tasks.
"""

import hiero.core
import hiero.core.nuke as nuke
import hiero.core.FnNukeHelpers as FnNukeHelpers
import hiero.core.FnNukeHelpersV2 as FnNukeHelpersV2


def trackItemTimeCodeNodeStartFrame(scriptStartFrame, trackItem, startHandle, endHandle):
  """
  Calculate the frame for an AddTimeCode node when exporting a single track item to a Nuke script, adjusting
  for the trim and handles.

  If playback speed is positive, this should be offset by the track item's source in and the start handle.
  Otherwise the offset should use the source out and end handle.
  """

  if trackItem.playbackSpeed() >= 0.0:
    timeCodeNodeStartFrame = scriptStartFrame - trackItem.sourceIn() + startHandle
  else:
    timeCodeNodeStartFrame = scriptStartFrame - trackItem.sourceOut() + endHandle
  return timeCodeNodeStartFrame


def _toNukeViewerLutFormat(hieroViewerLut):
  """ Return the specified hiero viewer lut in the nuke format.
  Since hiero formats are specified by 'family/colourspace' while
  nuke formats are expected to be 'colourspace (family)'.
  """
  lutParts = hieroViewerLut.split("/")
  assert(0 < len(lutParts) <= 2)
  hasFamilyName = len(lutParts) == 2
  if hasFamilyName:
    viewerLut = "%s (%s)" % (lutParts[1], lutParts[0])
  else:
    viewerLut = lutParts[0]

  return viewerLut


def createViewerNode(projectSettings):
  """ Create a Viewer node, with the viewerProcess configured based on the
  projectSettings.
  """
  # add a viewer
  viewerNode = nuke.Node("Viewer")

  # Bug 45914: If the user has for some reason selected a custom OCIO config, but then set the 'Use OCIO nodes when export' option to False,
  # don't set the 'viewerProcess' knob, it's referencing a LUT in the OCIO config which Nuke doesn't know about
  setViewerProcess = True
  if not projectSettings['lutUseOCIOForExport'] and projectSettings['ocioConfigPath']:
    setViewerProcess = False

  if setViewerProcess:
    # Bug 45845 - default viewer lut should be set in the comp
    viewerLut = _toNukeViewerLutFormat(projectSettings['lutSettingViewer'])
    viewerNode.setKnob("viewerProcess", viewerLut)
  return viewerNode


class TrackItemExportScriptWriter(object):
  """ Helper class for writing TrackItems to a Nuke script. This provides a
  higher-level wrapper around the code in FnNukeHelpers/FnNukeHelpersV2.
  TODO Could probably be got rid of with some refactoring.
  """

  def __init__(self, trackItem):
    self._trackItem = trackItem
    self._additionalNodesCallback = None
    self._writeEffects = True
    self._sequenceEffects = []
    self._writeAnnotations = False
    self._sequenceAnnotations = []
    self._startHandle = 0
    self._endHandle = 0
    self._includeRetimes = False
    self._retimeMethod = None
    self._reformatProperties = None
    self._firstFrame = 0

  def setAdditionalNodesCallback(self, callback):
    self._additionalNodesCallback = callback

  def setEffects(self, shouldWrite, sequenceEffects=[]):
    """ Set whether effects should be written and add any Sequence-level
    effects that should be included.
    """
    self._writeEffects = shouldWrite
    self._sequenceEffects = sequenceEffects


  def setAnnotations(self, shouldWrite, sequenceAnnotations=[]):
    """ Set whether annotations should be written and add any Sequence-level
    effects that should be included.
    """
    self._writeAnnotations = shouldWrite
    self._sequenceAnnotations = sequenceAnnotations


  def setOutputHandles(self, startHandle, endHandle):
    """ Set the handles to be included around the TrackItem cut times in
    the exported script.
    """
    self._startHandle = startHandle
    self._endHandle = endHandle


  def setOutputClipLength(self):
    """ Set to output the full clip length.  Calculates the handle values
    accordingly.
    """
    self._startHandle = self._trackItem.sourceIn()
    self._endHandle = (self._trackItem.source().duration() - self._trackItem.sourceOut()) - 1


  def setIncludeRetimes(self, includeRetimes, retimeMethod):
    """ Set whether retime nodes should be written and the retime method knob
    value.
    """
    self._includeRetimes = includeRetimes
    self._retimeMethod = retimeMethod


  def setReformat(self, reformatProperties):
    """ Sets information for reformatting in the Nuke script"""
    self._reformatProperties = reformatProperties

  def setFirstFrame(self, firstFrame):
    """ Set the first frame of the script.  This is used to apply appropriate
    offsets to the written nodes.
    """
    self._firstFrame = firstFrame


  def writeToScript(self, script, pendingNodesScript=None):
    # For the moment, if annotations are being written, fall back to the old
    # code path
    if self._writeAnnotations:
      self.writeToScript_old(script)
      return

    retimeMethod = self._retimeMethod if self._includeRetimes else None
    scriptParameters = FnNukeHelpersV2.ScriptWriteParameters( includeAnnotations=self._writeAnnotations,
                                                              includeEffects=self._writeEffects,
                                                              retimeMethod=retimeMethod,
                                                              reformatMethod=self._reformatProperties,
                                                              additionalNodesCallback=self._additionalNodesCallback)
    additionalEffects = self._sequenceEffects if self._writeEffects else []
    writer = FnNukeHelpersV2.TrackItemScriptWriter(self._trackItem, 
                                                   scriptParameters,                           
                                                   firstFrame=self._firstFrame,
                                                   startHandle=self._startHandle,
                                                   endHandle=self._endHandle)
    writer.writeToScript( script,
                          nodeLabel=self._trackItem.parent().name(),
                          additionalEffects=additionalEffects,
                          addTimeClip = False,
                          pendingNodesScript=pendingNodesScript)


  def writeToScript_old(self, script):
    """ Add the nodes for the TrackItem to a script writer.
    """

    # Some care is needed when dealing with soft effects and annotations.  If
    # there are sequence-level effects, then the format which is input to them
    # must be sequence format.  If the track item reformat state is set to
    # 'Disabled' or 'Scale', this means we need to reformat to sequence, add the
    # effects with the 'cliptype' knob set to 'bbox', then modify the format
    # back to what the user asked for.

    # This is further complicated because TrackItem.addToNukeScript adds any
    # linked effects, and does this reformatting itself.
    # So: if there are any non-linked effects/annotations, ask the TrackItem to
    # output to Sequence format, which it will do by adding a Reformat if
    # necessary, then add the extra reformat back to clip format.

    # TODO Some of this code is duplicated in TrackItem.addToNukeScript(), it
    # needs to be cleaned up

    clip = self._trackItem.source()
    itemReformatState = self._trackItem.reformatState()
    keepSourceFormat = (itemReformatState.type() in (nuke.ReformatNode.kDisabled, nuke.ReformatNode.kToScale))
    writeSequenceEffects = (self._writeEffects and self._sequenceEffects)
    writeSequenceAnnotations = (self._writeAnnotations and self._sequenceAnnotations)
    formatForSequenceEffects = (keepSourceFormat and (writeSequenceEffects or writeSequenceAnnotations))

    self._trackItem.addToNukeScript(script,
                                    firstFrame=self._firstFrame,
                                    includeRetimes=self._includeRetimes,
                                    retimeMethod=self._retimeMethod,
                                    startHandle=self._startHandle,
                                    endHandle=self._endHandle,
                                    nodeLabel=self._trackItem.parent().name(),
                                    includeAnnotations=self._writeAnnotations,
                                    outputToSequenceFormat=formatForSequenceEffects,
                                    includeEffects=self._writeEffects,
                                    additionalNodesCallback=self._additionalNodesCallback
                                    )

    # Calculate the offset for effect key frames and lifetimes
    effectOffset = self._firstFrame - self._trackItem.timelineIn() + self._startHandle

    cliptype = "bbox" if formatForSequenceEffects else None

    # Write out any sequence level effects
    if writeSequenceEffects:
      # first add metadata node so the sequence time is correct in case of retimes on the clips
      self._writeSequenceTimecodeMetadata(script, effectOffset)

      # Add all the effects
      for effect in self._sequenceEffects:
        effect.addToNukeScript(script, offset=effectOffset, cliptype=cliptype)

    if writeSequenceAnnotations:
      hiero.core.FnNukeHelpers.createAnnotationsGroup( script,
                                                       self._sequenceAnnotations,
                                                       offset=effectOffset,
                                                       inputs=1,
                                                       cliptype=cliptype
                                                       )

    if formatForSequenceEffects:
      clipFormatNode = nuke.ReformatNode(resize=nuke.ReformatNode.kResizeNone,
                                         format=str(clip.format()),
                                         center=itemReformatState.resizeCenter(),
                                         black_outside=False,
                                         pbb=True
                                         )
      script.addNode(clipFormatNode)

      # If the item reformat is set to 'Scale' we need to add two Reformat nodes
      # to restore the format, one to put it back to the clip format, and here
      # another to re-apply the scaling.  The image has already been scaled, so
      # resize knob should be 'none'
      if itemReformatState.type() == nuke.ReformatNode.kToScale:
        scaleReformatNode = nuke.ReformatNode(resize=nuke.ReformatNode.kResizeNone,
                                              to_type=itemReformatState.type(),
                                              scale=itemReformatState.scale(),
                                              center=itemReformatState.resizeCenter(),
                                              pbb=True,
                                              black_outside=False
                                              )
        script.addNode(scaleReformatNode)


  def _writeSequenceTimecodeMetadata(self, script, effectOffset):
    sequence = self._trackItem.parentSequence()
    timecodeStart = sequence.timecodeStart()
    try:
     firstFrame = sequence.inTime()
    except:
     firstFrame = 0
    timecodeFrame = timecodeStart + firstFrame - effectOffset
    scriptFrame = firstFrame

    timecodeStr = hiero.core.Timecode.timeToString(timecodeFrame, sequence.framerate(), hiero.core.Timecode.kDisplayTimecode)

    metadataNode = nuke.MetadataNode()
    metadata = { "hiero/sequence/timecode" : "[make_timecode %s %s %d]" % (timecodeStr, str(sequence.framerate()), scriptFrame) }
    metadataNode.addMetadata(metadata)
    script.addNode( metadataNode )



def writeSequenceAudioWithHandles(filePath,
                                  sequence,
                                  inTime,
                                  outTime,
                                  inHandle,
                                  outHandle,
                                  numChannels,
                                  sampleRate,
                                  bitDepth,
                                  bitRate):
  """ Helper function for writing audio on a sequence with handles. This will:
  - find audio items which intersect the original time range
  - if they intersect the start or end times, extend those items by the in/out
    handles specified
  - write out the audio file with the given time range, plus handles
  """

  assert inHandle >= 0, "Negative in handle not allowed!"
  assert outHandle >= 0, "Negative out handle not allowed!"

  # in/out times including the handles
  inTimeHandle = inTime - inHandle
  outTimeHandle = outTime + outHandle

  # Copy the sequence. Note this has to be done on the main thread
  sequenceCopy = hiero.core.executeInMainThreadWithResult(sequence.copy)

  # Iterate over all the audio tracks, then over their items in reverse order
  # because we need to shift them to higher times
  for track in sequenceCopy.audioTracks():
    itemsToRemove = []
    for item in reversed(track):
      item.unlinkAll() # Unlink items so we can move/delete them independently
      # Check the item is in the specified range. If not, it will be removed
      itemInTime = item.timelineIn()
      itemOutTime = item.timelineOut()
      inRange = itemInTime <= outTime and itemOutTime >= inTime
      if inRange:
        # If the item times intersect the range being exported, extend them to
        # include the handles if needed. The source in/out times also need to
        # be adjusted for the setTimes() call below
        newItemInTime = itemInTime
        itemSrcIn = item.sourceIn()
        newItemSrcIn = itemSrcIn
        if itemInTime <= inTime and itemInTime > inTimeHandle:
          newItemInTime = max(inTimeHandle, itemInTime - item.handleInLength())
          newItemSrcIn = itemSrcIn - (itemInTime - newItemInTime)

        newItemOutTime = itemOutTime
        itemSrcOut = item.sourceOut()
        newItemSrcOut = itemSrcOut
        if itemOutTime >= outTime and itemOutTime < outTimeHandle:
          newItemOutTime = min(outTimeHandle, itemOutTime + item.handleOutLength())
          newItemSrcOut = itemSrcOut + (newItemOutTime - itemOutTime)

        # Offset all the times by the inHandle. This is to ensure we can add
        # handles to items which are at the beginning of the timeline
        newItemInTime += inHandle
        newItemOutTime += inHandle
        item.setTimes(newItemInTime, newItemOutTime, newItemSrcIn, newItemSrcOut)
      else:
        itemsToRemove.append(item)

    # Remove all the items outside the exported range
    for item in itemsToRemove:
      track.removeItem(item)

  # Write the audio including handles. All the items have been shifted, so start
  # at the in time, and put the extra frames for the in handle at the end
  sequenceCopy.writeAudioToFile(filePath, inTime, outTime+inHandle+outHandle, numChannels, sampleRate, bitDepth, bitRate)
