# -*- coding: utf-8 -*-

""" Code for writing hiero objects to Nuke scripts. This is an attempt to
replace the code in FnNukeHelpers.py, done in parallel so we can change things
on a case-by-case basis and avoid breaking everything. Hopefully the old code
can be removed before too long..
"""

import os
import math
import copy
import re
import hiero.core.nuke as nuke
import hiero.core
from hiero.core import (FnNukeHelpers,
                        Transition)
from hiero.core.FnEffectHelpers import (transformNodeToFormatChange,
                                        FormatChange)
from .nuke import ReformatNode

gJumpCount = 0

def makeJumpNameForTrack(track):
  """Makes a jump name for the track. This is the name which shall be used to identify the
  'set' and the 'push' nodes which corrispond to each track. This name consists of the Track
  Name (with any non-alphanumeric characters replaced by _) and also a global counter which
  is to make sure we don't get duplicate names.
  """
  global gJumpCount
  countSuffix = str(gJumpCount)
  gJumpCount += 1
  ret = re.sub('[^0-9a-zA-Z_]+', "_", track.name()) + countSuffix
  return ret

class ScriptWriteParameters(object):
  """ Class for specifying parameters when writing to Nuke scripts. """
  def __init__(self,
               includeAnnotations=False,
               includeEffects=True,
               retimeMethod=None,
               reformatMethod=None,
               additionalNodesCallback=None,
               views=None):
    """
    @param includeAnnotations: whether annotations should be written to the script
    @param includeEffects: whether effects should be written to the script
    @param retimeMethod: method for retimes, if None retimes will not be included
    in the script
    @additionalNodesCallback: callback function for injecting additional nodes
    into the script, should return a list of the nodes
    """
    self._includeAnnotations = includeAnnotations
    self._includeEffects = includeEffects
    self._retimeMethod = retimeMethod
    self._reformatMethod = reformatMethod
    self._additionalNodesCallback = additionalNodesCallback
    self._views = views or []

  def includeAnnotations(self):
    """ Get whether annotations should be included in the script. """
    return self._includeAnnotations

  def includeEffects(self):
    """ Get whether effects should be included in the script. """
    return self._includeEffects

  def includeRetimes(self):
    """ Get whether retimes should be included in the script. """
    return self._retimeMethod is not None

  def retimeMethod(self):
    """ Get the method used for retiming in the created OFlow node. """
    return self._retimeMethod

  def views(self):
    return self._views

  def doAdditionalNodesCallback(self, *args):
    """ If a callback for additional nodes has been set, call it, otherwise
    returns an empty list.
    """
    if self._additionalNodesCallback:
      # Filter out None entries. Not sure if this is needed, but existing code was
      # checking for it
      return [n for n in self._additionalNodesCallback(*args) if n is not None]
    else:
      return []


class TrackItemScriptWriter(object):
  """ Class for writing TrackItems to a Nuke script. """
  def __init__(self, 
               trackItem, 
               params,                     
               firstFrame=None,
               startHandle=0,
               endHandle=0,
               offset=0):
    """
    @param firstFrame: optional frame for the Read node to start at
    @param startHandle: the number of frames of handles to include at the start
    @param endHandle: the number of frames of handles to include at the end
    @param offset: global frame offset applied across whole script
    """
    self._trackItem = trackItem
    self._params = params

    self._startHandle = startHandle
    self._offset = offset

    self._retimeRate = 1.0
    if self._params.includeRetimes():
      self._retimeRate = self._trackItem.playbackSpeed()

    # Check for transitions
    inTransition, outTransition = FnNukeHelpers._TrackItem_getTransitions(self._trackItem)
    self._inTransitionHandle, self._outTransitionHandle = 0, 0

    # Adjust the clips to cover dissolve transition
    if outTransition is not None:
      if outTransition.alignment() == Transition.kDissolve:
        # Calculate the delta required to move the end of the clip to cover the dissolve transition
        self._outTransitionHandle = (outTransition.timelineOut() - self._trackItem.timelineOut())
    if inTransition is not None:
      if inTransition.alignment() == Transition.kDissolve:
        # Calculate the delta required to move the beginning of the clip to cover the dissolve transition
        self._inTransitionHandle = (self._trackItem.timelineIn() - inTransition.timelineIn())


    # If the clip is reversed, we need to swap the start and end times
    start = min(self._trackItem.sourceIn(), self._trackItem.sourceOut())
    end = max(self._trackItem.sourceIn(), self._trackItem.sourceOut())

    self._outputStartHandle = startHandle + self._inTransitionHandle
    self._outputEndHandle = endHandle + self._outTransitionHandle

    # Extend handles to incorporate transitions
    # If clip is reversed, handles are swapped
    if self._retimeRate >= 0.0:
      readStartHandle = startHandle + self._inTransitionHandle
      readEndHandle = endHandle + self._outTransitionHandle
    else:
      readStartHandle = startHandle + self._outTransitionHandle
      readEndHandle = endHandle + self._inTransitionHandle

    clip = self._trackItem.source()
    # Recalculate handles clamping to available media range
    readStartHandle = min(start, math.ceil(readStartHandle * abs(self._retimeRate) ))
    readEndHandle = min((clip.duration() - 1) - end, math.ceil(readEndHandle * abs(self._retimeRate)))

    # Add handles to source range
    start -= readStartHandle
    end += readEndHandle

    # Read node frame range
    self._readStart, self._readEnd = start, end
    # First frame identifies the starting frame of the output. Defaults to timeline in time
    self._readNodeFirstFrame = firstFrame
    if self._readNodeFirstFrame is None:
      self._readNodeFirstFrame = self._trackItem.timelineIn() -  min(min(self._trackItem.sourceIn(), self._trackItem.sourceOut()), readStartHandle)
    else:
      # If we have trimmed the handles, bump the start frame up by the difference
      self._readNodeFirstFrame += round(readStartHandle * abs(self._retimeRate)) - readStartHandle

    # Apply global offset
    self._readNodeFirstFrame += offset

    # To support the TimeWarp effect, we now set the full clip's frame range in the Read node, with the desired.
    # frames selected by the FrameRange node.  This shifts the Read nodes 'start at' frame to compensate.
    self._readNodeFirstFrame -= self._readStart

    # Calculate the frame range, != read range as read range may be clamped to available media range
    self._first_frame = start
    self._last_frame = end
    if firstFrame is not None:
      # if firstFrame is specified
      self._last_frame = firstFrame + (startHandle + self._inTransitionHandle) + (self._trackItem.duration() -1) + (endHandle + self._outTransitionHandle)
      self._first_frame = firstFrame
    else:
      # if firstFrame not specified, use timeline time
      self._last_frame = self._trackItem.timelineIn() + (self._trackItem.duration() -1) + (endHandle + self._outTransitionHandle)
      self._first_frame = (self._trackItem.timelineIn() - (startHandle + self._inTransitionHandle))

  def getReadNodeInfo(self):
    """
    Helper function to get usage information about Read Nodes for this track item
    """
    clip = self._trackItem.source()
    return clip.getReadInfo(firstFrame=self._readNodeFirstFrame)

  def addChannelNodeToScript(self, script, added_nodes):
    """ We need an AddChannels node to add full alpha to the track.
    We want this put into a custom channel, so that it doesn't affect 
    other parts of the comp - The Merge node will just be told to use
    this channel for its A alpha.
    First we need to create the layer which will contain the custom channel
    """
    addLayerCommand = nuke.AddLayerCommand()
    addLayerCommand.setKnob('Track_Alpha', 'Track_Alpha.a')
    added_nodes.append(addLayerCommand)
    script.addNode(addLayerCommand)

    # Now create the AddChannels Node itself, which will write 1 into this channel.
    addChannelsNode = nuke.AddChannelsNode()
    addChannelsNode.setKnob('channels', 'Track_Alpha')
    addChannelsNode.setKnob('color', '{0 0 0 1}')
    # We want the alpha applied across the entire image format.
    addChannelsNode.setKnob('format_size', 'true')  

    if not self._trackItem.isEnabled():
      # Also disable the addChannelsNode node, otherwise it will still 
      # overwrite with black
      addChannelsNode.setKnob("disable", "true")

    added_nodes.append(addChannelsNode)
    script.addNode(addChannelsNode)

  def getColorspaceFromProperty(self, lutValue):
    """Get just the colorspace name (in parentheses if the LUT value is a role)."""
    if lutValue.endswith(")"):
      return lutValue[lutValue.find('(')+1 : -1]
    else:
      return lutValue

  def getClipColorTransform(self, projectSettings, clip):
    colourspaceKnob = clip.readNode()['colorspace']
    if projectSettings and not projectSettings['lutUseOCIOForExport'] and colourspaceKnob.notDefault():
      colorspaceDisplayStr = colourspaceKnob.getDisplayStrFromID(colourspaceKnob.value())
      colourTransform = self.getColorspaceFromProperty(colorspaceDisplayStr)
      return FnNukeHelpers.nukeColourTransformNameFromHiero(colourTransform, projectSettings)
    return None

  def writeToScript(self,
                    script=nuke.ScriptWriter(),
                    nodeLabel=None,
                    additionalEffects=(),
                    addChannelNode = False,
                    readNodes = {},
                    addTimeClip = True,
                    projectSettings = None,
                    pendingNodesScript=None):
    """ Writes the TrackItem to a script. Returns the added nodes.
    @param script: the script writer to add nodes to
    @param nodeLabel: label for the Read node
    @param additionalEffects: unlinked effects on the sequence which should be
                              included
    @param addChannelNode: add an AddChannels Node to the TrackItem, which will
                           inject a full alpha channel to Node tree
    @param pendingNodesScript Certain nodes must not be added to the script immediately. They are stored here.
    """
    added_nodes = []

    clip = self._trackItem.source()

    # Create a metadata node
    metadataNode = nuke.MetadataNode()

    # Add TrackItem metadata to node
    metadataNode.addMetadata([("hiero/shot", self._trackItem.name()), ("hiero/shot_guid", FnNukeHelpers._guidFromCopyTag(self._trackItem))])

    # sequence level metadata
    seq = self._trackItem.parentSequence()
    if seq:
      seqTimecodeStart = seq.timecodeStart()
      seqTimecodeFrame = seqTimecodeStart + self._trackItem.timelineIn() - self._outputStartHandle
      seqTimecode = hiero.core.Timecode.timeToString(seqTimecodeFrame, seq.framerate(), hiero.core.Timecode.kDisplayTimecode)

      metadataNode.addMetadata( [ ("hiero/project", clip.project().name() ),
                                  ("hiero/sequence/frame_rate", seq.framerate() ),
                                  ("hiero/sequence/timecode", "[make_timecode %s %s %d]" % (seqTimecode, str(seq.framerate()), self._first_frame) )
                                  ] )

    # Add Tags to metadata
    metadataNode.addMetadataFromTags( self._trackItem.tags() )

    # Add Track and Sequence here as these metadata nodes are going to be added per clip/track item. Not per sequence or track.
    if self._trackItem.parent():
      metadataNode.addMetadata([("hiero/track", self._trackItem.parent().name()), ("hiero/track_guid", FnNukeHelpers._guidFromCopyTag(self._trackItem.parent()))])
      if self._trackItem.parentSequence():
        metadataNode.addMetadata([("hiero/sequence", self._trackItem.parentSequence().name()), ("hiero/sequence_guid", FnNukeHelpers._guidFromCopyTag(self._trackItem.parentSequence()))])

    colourTransform = self.getClipColorTransform(projectSettings, clip)

    # Capture the clip nodes without adding to the script, so that we can group them as necessary
    clip_nodes = clip.addToNukeScript(None,
                                      firstFrame=self._readNodeFirstFrame,
                                      metadataNode=metadataNode,
                                      nodeLabel=nodeLabel,
                                      enabled=self._trackItem.isEnabled(),
                                      includeEffects=self._params.includeEffects(),
                                      readNodes = readNodes,
                                      colourTransform = colourTransform)

    # Add the read node to the script
    # This assumes the read node will be the first node
    lastReadAssociatedNode = 0
    read_node = clip_nodes[0]

    if isinstance(read_node, nuke.PushNode):
      # Push nodes come before PostageStamps, to connect the PostageStamp to its original Read.
      # Need to add the Push command first
      if script:
        script.addNode(read_node)
      added_nodes.append(read_node)

      # Get the actual PostageStamp
      read_node = clip_nodes[1]
      lastReadAssociatedNode += 1

    # Add the read or postage stamp node
    if script:
      script.addNode(read_node)
    added_nodes.append(read_node)

    # If it's a Read, Add the next 2 nodes also, which represent set and push nodes
    if readNodes is not None and len(readNodes) > 0 and isinstance(read_node, nuke.ReadNode):
      if lastReadAssociatedNode < len(clip_nodes) - 2:
        setNode = clip_nodes[lastReadAssociatedNode + 1]
        pushNode = clip_nodes[lastReadAssociatedNode + 2]

        if isinstance(setNode, nuke.SetNode) and isinstance(pushNode, nuke.PushNode):
          if script:
            script.addNode(setNode)
            script.addNode(pushNode)
          added_nodes.append(setNode)
          added_nodes.append(pushNode)
          lastReadAssociatedNode += 2
    elif isinstance(read_node, nuke.PostageStampNode):
      # For PostageStamps, the TimeOffset should immediately follow the Node itself
      timeOffsetNode = clip_nodes[lastReadAssociatedNode + 1]

      if script:
        script.addNode(timeOffsetNode)
      added_nodes.append(timeOffsetNode)
      lastReadAssociatedNode += 1

    if self._params.includeAnnotations():
      # Add the clip annotations.  This goes immediately after the Read, so it is affected by the Reformat if there is one
      clipAnnotations = clip.addAnnotationsToNukeScript(script, firstFrame=self._readNodeFirstFrame, trimmed=True, trimStart=self._readStart, trimEnd=self._readEnd)
      added_nodes.extend(clipAnnotations)

    added_nodes.extend( clip_nodes[lastReadAssociatedNode + 1:] )
    # Add all other clip nodes to the group
    for node in clip_nodes[lastReadAssociatedNode + 1:]:
      script.addNode(node)

    # Add metadata node
    added_nodes.append(metadataNode)
    script.addNode(metadataNode)

    # This parameter allow the whole nuke script to be shifted by a number of frames
    self._first_frame += self._offset
    self._last_frame += self._offset

    # Add Additional nodes.
    postReadNodes = self._params.doAdditionalNodesCallback(self._trackItem)

    # Add any additional nodes.
    for node in postReadNodes:
      if node is not None:
        node = copy.deepcopy(node)
        # Disable additional nodes too
        if not self._trackItem.isEnabled():
          node.setKnob("disable", True)

        added_nodes.append(node)
        script.addNode(node)

    # If this clip is a freeze frame add a frame hold node
    isFreezeFrame = (self._retimeRate == 0.0)
    if isFreezeFrame:
      # first_frame is max of first_frame and readNodeFirstFrame because when
      # using a dissolve with a still clip first_frame is the first frame of 2
      # clips, which is lower than readNodeFirstFrame.
      holdFirstFrame = max(self._first_frame, self._readNodeFirstFrame)
      frameHoldNode = nuke.Node("FrameHold", first_frame=holdFirstFrame)
      added_nodes.append(frameHoldNode)
      script.addNode(frameHoldNode)

    # If the clip is retimed we need to also add an OFlow node.
    elif self._params.includeRetimes() and self._retimeRate != 1 and self._params.retimeMethod() != 'None':

      # Obtain keyFrames
      tIn, tOut = self._trackItem.timelineIn(), self._trackItem.timelineOut()
      sIn, sOut = self._trackItem.sourceIn(), FnNukeHelpers.getRetimeSourceOut(self._trackItem)

      # Offset keyFrames, so that they match the input range (source times) and produce expected output range (timeline times)
      # timeline values must start at first_frame
      tOffset = (self._first_frame + self._startHandle + self._inTransitionHandle) - self._trackItem.timelineIn()
      tIn += tOffset
      tOut += tOffset
      sOffset = self._readNodeFirstFrame
      sIn += sOffset
      sOut += sOffset

      # Create OFlow node for computed keyFrames
      keyFrames = "{{curve l x%d %f x%d %f}}" % (tIn, sIn, tOut, sOut)
      oflow = nuke.Node("OFlow2",
                        interpolation=self._params.retimeMethod(),
                        timing="Source Frame",
                        timingFrame=keyFrames)
      oflow.setKnob('label', 'retime ' + str(self._retimeRate))
      added_nodes.append(oflow)
      script.addNode(oflow)

    added_nodes.extend( self.writeReformatAndEffects(script, additionalEffects, pendingNodesScript) )

    # TimeClip is used to correct the range from OFlow. This isn't necessary
    # when exporting a single shot, and was causing problems with retimes, so only
    # add it if requested
    if addTimeClip:
      timeClipNode = nuke.TimeClipNode( self._first_frame, self._last_frame, clip.sourceIn(), clip.sourceOut(), self._first_frame)
      timeClipNode.setKnob('label', 'Set frame range to [knob first] - [knob last]')
      added_nodes.append(timeClipNode)
      script.addNode(timeClipNode)

    # Add any AddChannels nodes and Layers commands
    if addChannelNode:
      self.addChannelNodeToScript(script, added_nodes)

    # Disable all clip nodes if Track Item is disabled
    if not self._trackItem.isEnabled():
      for node in added_nodes:
        node.setKnob("disable", "true")

    return added_nodes

  def writeReformatAndEffects(self, script, additionalEffects, pendingNodesScript):
    """ Write the nodes for reformat and effects, if needed. When outputting to
    sequence format, the reformat goes first. In other cases, the effects are
    modified to fit the input clip's format, and the reformat node is added after.
    """
    reformatMethod = self._params._reformatMethod
    outputToSequenceFormat = ((reformatMethod["to_type"] == nuke.ReformatNode.kCompReformatToSequence)
                                if reformatMethod else False)

    reformatNode = self.makeOutputReformatNode()

    added_nodes = []

    # If outputting sequence format, add the reformat first
    if reformatNode and outputToSequenceFormat:
      added_nodes.append(reformatNode)
      script.addNode(reformatNode)

    # Add effects
    effectNodes = []
    if self._params.includeEffects():
      effectOffset = self._first_frame - self._trackItem.timelineIn() + self._outputStartHandle
      transformToClipFormat = not outputToSequenceFormat
      effectNodes = self.writeEffects(script, effectOffset, additionalEffects, transformToClipFormat, pendingNodesScript)
      added_nodes.extend(effectNodes)

    # If not outputting to sequence format, add the reformat after the effects
    if reformatNode and not outputToSequenceFormat:
      added_nodes.append(reformatNode)
      script.addNode(reformatNode)
    return added_nodes

  def findLinkedEffects(self):
    """ Find effects linked to the track item being written. """
    linkedEffects = [ item for item in self._trackItem.linkedItems() if isinstance(item, hiero.core.EffectTrackItem) ]

    # If includeRetimes is False, do not include retime effects in the export.  Note that clip-level Timewarps will still be included.
    # That's a lot trickier to deal with (how do we copy those when doing Build Track?), so leaving that for now.
    if not self._params.includeRetimes():
      linkedEffects = [ effect for effect in linkedEffects if not effect.isRetimeEffect() ]

    # Make sure the effects are in the correct order.  They should be written from lowest sub-track to highest
    linkedEffects.sort(key = lambda effect: effect.subTrackIndex())
    return linkedEffects

  def writeEffects(self, script, effectOffset, additionalEffects, transformToClipFormat, pendingNodesScript):
    """ Write the track item's linked effects plus any additional sequence-level
    ones.
    """
    added_nodes = []
    linkedEffects = self.findLinkedEffects()
    seqFormat = self._trackItem.parentSequence().format()
    clipFormat = self._trackItem.source().format()
    reformatState = self._trackItem.reformatState()
    effectClipType = "format"
    formatChange = FormatChange(clipFormat, seqFormat, clipFormat, reformatState)
    invertFormatChange = FormatChange(seqFormat, clipFormat, clipFormat, reformatState)
    # Write the linked effects
    for effect in linkedEffects:
      # Burn-in nodes should be applied after the reformat node. They need to be postponed
      # and they also should not be transformed to the clip format.
      addLater = pendingNodesScript is not None and effect.node().Class() == 'BurnIn'
      if not addLater and transformToClipFormat:
        transformNodeToFormatChange(effect.node(), formatChange, lambda x: None)
      effectScript = pendingNodesScript if addLater else script
      effectNodes = effect.addToNukeScript(effectScript,
                                           effectOffset,
                                           cliptype=effectClipType,
                                           addLifetime=False)
      #apply the invert soft effect transformation or else, the soft effect
      #transformation will be carried over to the following track items
      if not addLater and transformToClipFormat:
        transformNodeToFormatChange(effect.node(), invertFormatChange, lambda x: None)
      added_nodes.extend(effectNodes)
    # Write sequence-level effects. Because the timeline in/out for these don't
    # match the track item, the node lifetime needs to be set.
    for effect in additionalEffects:
      if transformToClipFormat:
        transformNodeToFormatChange(effect.node(), formatChange, lambda x: None)
      effectNodes = effect.addToNukeScript(script,
                                           effectOffset,
                                           cliptype=effectClipType,
                                           addLifetime=True)
      if transformToClipFormat:
        transformNodeToFormatChange(effect.node(), invertFormatChange, lambda x: None)
      added_nodes.extend(effectNodes)
    return added_nodes

  def makeOutputReformatNode(self):
    """ If outputting to a different format from the clip (e.g. to the sequence
    format), create a ReformatNode to do this. If no output format is set, or
    it's the same as that of the clip, returns None.
    """
    reformatMethod = self._params._reformatMethod
    if not reformatMethod:
      return None

    # Default to no reformat, i.e. maintain plate format
    reformatNode = None

    clipFormatString = str(self._trackItem.source().format())

    if reformatMethod["to_type"] == nuke.ReformatNode.kCompReformatToSequence:
      # Reformat to sequence
      formatString = str(self._trackItem.parentSequence().format())
      if clipFormatString != formatString:
        reformatState = self._trackItem.reformatState()
        if reformatState.type() == nuke.ReformatNode.kDisabled:
          reformatNode = nuke.ReformatNode(resize=nuke.ReformatNode.kResizeNone,
                                           center=True,
                                           to_type=nuke.ReformatNode.kToFormat,
                                           format=formatString,
                                           filter=reformatMethod.get("filter"),
                                           pbb=True)
        else:
          reformatNode = nuke.ReformatNode( resize=reformatState.resizeType(),
                                            center=reformatState.resizeCenter(),
                                            flip=reformatState.resizeFlip(),
                                            flop=reformatState.resizeFlop(),
                                            turn=reformatState.resizeTurn(),
                                            to_type=reformatState.type(),
                                            format=formatString,
                                            scale=reformatState.scale(),
                                            filter=reformatMethod.get("filter"),
                                            pbb=True)
    elif reformatMethod["to_type"] == nuke.ReformatNode.kToFormat:
      # Reformat to specific format
      format = hiero.core.Format(reformatMethod["width"], reformatMethod["height"],
                                 reformatMethod["pixelAspect"], reformatMethod["name"])
      formatString = str(format)
      if clipFormatString != formatString:
        resizeType = reformatMethod["resize"]
        center = reformatMethod["center"]
        filter = reformatMethod.get("filter")
        reformatNode = nuke.ReformatNode( resize=resizeType,
                                          center=center,
                                          flip=False,
                                          flop=False,
                                          turn=False,
                                          to_type=ReformatNode.kToFormat,
                                          format=formatString,
                                          scale=1.0,
                                          filter=filter,
                                          pbb=True)
    return reformatNode


class VideoTrackScriptWriter(object):
  """ Class for writing VideoTracks to a Nuke script. """
  def __init__(self, track, params):
    self._track = track
    self._params = params
    # Jump to get to the end of the track
    self._jumpName = makeJumpNameForTrack(track)
    # Jump to get to the end of the merge
    self._maskJumpName = self._jumpName + "Mask"

  def getJumpName(self):
    return self._jumpName

  def setJumpName(self, name):
    self._jumpName = name

  def getMaskJumpName(self):
    return self._maskJumpName

  def allTrackItemsDisabled(self):
    for trackItem in list(self._track.items()):
      if trackItem.isEnabled():
        return False

    # No items are enabled 
    return True

  def writeToScript(self,
                    script=nuke.ScriptWriter(),
                    offset=0,
                    skipOffline=True,
                    mediaToSkip=(),
                    disconnected=False,
                    needToAddChannelNode = False,
                    readNodes = {},
                    projectSettings = None):

    added_nodes = []

    merge_nodes = []

    sequence = self._track.parent()

    # Get the sequence format for setting on Constant nodes
    sequenceFormatStr = str(sequence.format())

    # Build the track by generating script for each TrackItem and using TimeClip nodes to set the active
    # frame ranges for the TrackItems.
    # Gaps in the track are handled by using black outside in the TimeClips.
    lastInTime = sequence.duration()
    lastTrackItem = None

    # For tracks with multiple track items, we will be creating either Merge nodes or Dissolves to 
    # join the items together. However the Merge will be created on the next track item processed
    # after the Dot is created, ie. we will need to create the Dot node on the current track item,
    # but then connect it to a Node that is created on the next. We use lastDot to facilitate this.
    lastDot = None

    # Keep track of when we have AddChannels nodes in the previous track.
    # These will be added after the TimeClips to avoid the TimeClip applying
    # fades to the added channel. However, we only want them to be active when 
    # the timeclip is. We will use the Merge node's Lifetime knobs to achieve this,
    # so we need to store the associated TimeClip node so that we can get its 
    # frame range knobs
    lastTimeclip = None

    lastTrackItemDisabled = False

    # Check environment variable to enable the currently experimental switch node code
    useSwitch = "NUKE_EXPORT_SWITCH_NODES" in os.environ

    # Work backwards so that the Merge nodes hook up the right way around.    
    for trackItem in reversed(list(self._track.items())):
      source = trackItem.source().mediaSource()

      # Check if the source is in the mediaToSkip list
      if source in mediaToSkip:
        continue

      if not source.isMediaPresent() and skipOffline:
        continue

      hiero.core.log.debug( "  - " + str(trackItem) )

      # Check for transitions
      inTransition, outTransition = FnNukeHelpers._TrackItem_getTransitions(trackItem)

      script.pushLayoutContext("clip", trackItem.name() + str(trackItem.eventNumber()), label=trackItem.name())

      trackItemWriter = TrackItemScriptWriter(trackItem, self._params, offset=offset)

      trackitem_nodes = trackItemWriter.writeToScript(script, addChannelNode = needToAddChannelNode, readNodes = readNodes, projectSettings = projectSettings)

      added_nodes = added_nodes + trackitem_nodes

      # Check if we're going to join this to another track item. If so we'll need a Dot node
      dot = None
      if trackItem != list(self._track.items())[0] and len(list(self._track.items())) > 1 and not disconnected:
        dot = nuke.DotNode()
        dot.setInputNode(0, added_nodes[-1])
        script.addNode(dot)
        added_nodes.append(dot)

      # Don't add any Merges if the track is disconnected
      if not disconnected and lastTrackItem is not None:

        # For dissolves create a Dissolve node rather than Merge
        if outTransition and outTransition.alignment() == Transition.kDissolve:
          merge = nuke.DissolveNode()
          merge.setWhichKeys( (outTransition.timelineIn()+offset, 0), (outTransition.timelineOut()+offset, 1) )

        else:
          if useSwitch:
            # Experimental code to connect up clips along the track with a switch
            # node. We're not really merging because the track items have
            # non-intersecting frame ranges, and the switch should be more efficient
            # because it only generates upstream ops for the active input
            whichExpression = "{{curve K x%d 0 x%d 1}}" % (trackItem.timelineIn() + offset,
                                                           lastTrackItem.timelineIn()+offset)
            merge = nuke.Node("Switch", inputs=2, which=whichExpression)
          else:
            merge = nuke.MergeNode()

        # Connect this to the Dot created on the last track processed (if any)
        if lastDot is not None:
          merge.setInputNode(0, lastDot)        

        if lastTrackItemDisabled:
          merge.setKnob("disable", "true")
        
        # Store the associated TimeClip with the merge node for setting it's lifetime range.  
        merge_nodes.append((merge, lastTimeClip))

      # Check if we have an AddChannels node on this track item. If so, we need to
      # store the associated TimeClip so we can set the Merge node's lifetime
      # range later
      hasAddChannels = False
      lastTimeClip = None
      for node in reversed(trackitem_nodes):
        # Note that we will always reach the AddChannels node before the TimeClip
        if isinstance(node, nuke.AddChannelsNode):
          hasAddChannels = True
        elif isinstance(node, nuke.TimeClipNode) and hasAddChannels:
          lastTimeClip = node
          break

      lastDot = dot
      lastTrackItemDisabled = not trackItem.isEnabled()

      # Handle fade in and out.  Use the TimeClip node's fade controls for this.
      fadeIn = inTransition and inTransition.alignment() == Transition.kFadeIn
      fadeOut = outTransition and outTransition.alignment() == Transition.kFadeOut

      if fadeIn or fadeOut:

        # Find the TimeClip node created by the track item so we can set the fades
        trackItemTimeClipNode = next(n for n in trackitem_nodes if isinstance(n, nuke.TimeClipNode))

        if fadeIn:
          fadeInValue = inTransition.timelineOut() - inTransition.timelineIn()
          trackItemTimeClipNode.setKnob("fadeIn", fadeInValue)
          trackItemTimeClipNode.setKnob("fadeInType", "linear")

        if fadeOut:
          fadeOutValue = outTransition.timelineOut() - outTransition.timelineIn()
          trackItemTimeClipNode.setKnob("fadeOut", fadeOutValue)
          trackItemTimeClipNode.setKnob("fadeOutType", "linear")

      lastTrackItem = trackItem
      lastInTime = lastTrackItem.timelineIn()

      script.popLayoutContext()

    # Have to apply the Merge nodes in reverse order
    for node, trackItem in reversed(merge_nodes):
      added_nodes.append(node)
      script.addNode(node)

      # AddChannels Nodes are added after TimeClips, so need to be masked
      # out outside the TimeClip's range. Use the Merge Node's lifetime
      # knobs for this
      if isinstance(trackItem, nuke.TimeClipNode): 
        startTime = trackItem.knob("first")
        endTime = trackItem.knob("last")
        node.setKnob("lifetimeStart", startTime)
        node.setKnob("lifetimeEnd", endTime)
        node.setKnob("useLifetime", "true")

    perTrackNodes = self._params.doAdditionalNodesCallback(self._track)
    added_nodes.extend(perTrackNodes)
    script.addNode(perTrackNodes)

    return added_nodes

class ReadNodeInstanceInfo:
  """
  Simple class to hold the 3 parameters that will allow us to instance ReadNodes.
  """
  def __init__(self, startAt, totalInstances, instancesUsed, readNodeID):
    self.startAt = startAt
    self.totalInstances = totalInstances
    self.instancesUsed = instancesUsed
    self.readNodeID = readNodeID        # Unique ID for this ReadNode (Read0, Read1 etc)

class ReadNodeUsageCollator:
  """ Class used to keep track of all instances of Read Nodes throughout
  a project. This enables us to replace multiple instances of the same Read
  Node with PostageStamps.
  """
  def __init__(self):
    # Dict to map Read file name to a class containing the number of instances,
    # the number instanced so far, and also stores the "start at" value for the 
    # first Read - any postage stamps will need a TimeOffset Node which corrects
    # their start at value relative to this
    self._readNodes = {}
    self._readNodeIDCounter = 0

  def getReadNodes(self):
    return self._readNodes

  def collateReadNodes(self, tracks, params, offset, view=None):
    for track in tracks:
      for trackItem in list(track.items()):
        # Need to get all ReadNode information for this track item
        if trackItem.isEnabled():
          trackItemWriter = TrackItemScriptWriter(trackItem, params, offset=offset)
          readNodeInfo = trackItemWriter.getReadNodeInfo()
        
          for read in readNodeInfo:
            if read in self._readNodes:
              # We already have a reference for this Read. Increment its usage parameter
              self._readNodes[read].totalInstances += 1
            else:
              # Create a new object
              self._readNodes[read] = ReadNodeInstanceInfo(readNodeInfo[read], 1, 0, "Read" + str(self._readNodeIDCounter))
              self._readNodeIDCounter += 1


class EffectsTrackJump(object):
  "Object which stores the jumpname for an effects track"
  def __init__(self, track):
    self._jumpName = makeJumpNameForTrack(track)
    self._track = track

  def getJumpName(self):
    return self._jumpName

  def setJumpName(self, name):
    self._jumpName = name


class SequenceScriptWriter(object):
  """ Class for writing Sequences to a Nuke script. """
  def __init__(self, sequence, params):
    self._sequence = sequence
    self._params = params
    self._trackWriters = []
    self._readNodeUsageCollator = ReadNodeUsageCollator()

  def writeTracks(self,
                  connectedTracks,
                  disconnectedTracks,
                  script,
                  offset,
                  skipOffline,
                  mediaToSkip,
                  projectSettings = None):
    """ Write a set of tracks, some of which may not be connected to any output.
    If there are multiple connected these are connected to a Merge node.
    Returns a jump name for the final output node.
    """
    added_nodes = [] # Note: this used to be returned but isn't needed any more, could be eliminated
    previousTrack = None

    # First write the tracks in reverse order.  When it comes to detemining the inputs for the merges below,
    # Nuke uses a stack.  We also need to add each track's annotations and soft effects in the right place.
    # Effects/annotations on a track which also has clips should only apply to that track, so are added before the
    # track is merged.  Otherwise they should apply to all the tracks below, so are added after.
    # So for example if there are 4 tracks (Video 1, Video 2, Effects 1, Video 3) then the order is as follows:
    #   Video 3
    #   Video 3 annotations
    #   Video 3 effects
    #   Video 2
    #   Video 2 annotations
    #   Video 2 effects
    #   Video 1
    #   Video 1 annotations
    #   Video 1 effects
    #   Merge track 2 over track 1
    #   Effects 1
    #   Merge track 3 over track 2
    #   Write

    # If there is an output format specified, to make sure effects and annotations appear in the right place,
    # they should have their 'cliptype' knob set to 'bbox'.
    effectsClipType = "bbox"

    # Keep track of the jump set for whatever node the track's output should be. This
    # is returned and used for joining views
    outputJumpName = None

    tracksWithVideo = set()
    tracks = connectedTracks + disconnectedTracks

    readNodes = self._readNodeUsageCollator.getReadNodes()

    # Keep a record of the last Node in each track, since this will be used later to set the
    # correct connections to Merge nodes
    lastTrackNodeDict = {}

    # Keep a list of all LifeTime ranges of each track. This is the range Specified by the
    # TimeClip nodes first and last knobs.
    # We will also need to know the overall comp's start frame, so that we can disable
    # the Merge node over it's entire range initially
    lastLifetimeRange = {}
    firstCompFrame = None

    # Also keep track of Dot nodes created for tidying up the layout of A and
    # mask inputs, since we will be positioning these after the Merge node gets
    # its final aplacement
    maskInputDict = {}
    AInputDict = {}

    # Keep track of whether all TrackItems are disabled for a track
    trackDisabled = {}

    # Check all tracks for soft effect tracks
    hasSoftEffectTracks = False
    for track in tracks:
      trackItems = list(track.items())
      subTrackItems = track.subTrackItems()
      if len(trackItems) is 0 and len(subTrackItems) > 0:
        # Soft effect tracks if track only contains sub track items
        hasSoftEffectTracks = True

    # First write out the tracks and their annotations in reverse order, as described above
    for track in reversed(tracks):
      trackDisconnected = track in disconnectedTracks
      # If the track has any clips, write them and the effects out.
      trackItems = list(track.items())
      if len(trackItems) > 0:
        # Add the track and whether it is disconnected as data to the layout context
        script.pushLayoutContext("track", track.name(), track=track, disconnected=trackDisconnected)

        # Check if we'll need to add an AddChannels node to each track item in this track
        addChannelNode = not (track == tracks[0]) and not trackDisconnected and not track.isBlendEnabled()
        trackWriter = VideoTrackScriptWriter(track, self._params)

        self._trackWriters.append(trackWriter)

        track_nodes = trackWriter.writeToScript(script,
                                                offset=offset,
                                                skipOffline=skipOffline,
                                                mediaToSkip=mediaToSkip,
                                                disconnected=trackDisconnected,
                                                needToAddChannelNode=addChannelNode,
                                                readNodes = readNodes,
                                                projectSettings = projectSettings)

        # Traverse the track nodes to find all Timeclip nodes.
        # When we find one, use it to define that TrackItem's lifetime.
        # This will later be written to the Merge.
        for node in track_nodes:
          if isinstance(node, nuke.TimeClipNode):
            if not track in lastLifetimeRange:
              lastLifetimeRange[track] = []
            startFrame = node.knob("first")
            endFrame = node.knob("last")

            if firstCompFrame is None or startFrame < firstCompFrame:
              firstCompFrame = startFrame

            #check if the clip is disabled
            shouldAddLifetime = True
            if str("disable") in node.knobs():
              shouldAddLifetime =  not node.knob("disable")

            if shouldAddLifetime:
              lastLifetimeRange[track].append((startFrame, endFrame))

        added_nodes = added_nodes + track_nodes

        effectsAnnotationsNodes = FnNukeHelpers._addEffectsAnnotationsForTrack(track,
                                                                         self._params.includeEffects(),
                                                                         self._params.includeAnnotations(),
                                                                         script,
                                                                         offset,
                                                                         cliptype=effectsClipType)
        added_nodes.extend( effectsAnnotationsNodes )

        # Check whether every track item is disabled on this track
        trackDisabled[track] = trackWriter.allTrackItemsDisabled()

        # If all track items are disabled, we should also disable all effects
        # and annotations nodes
        if trackDisabled[track]:
          for node in effectsAnnotationsNodes:
            node.setKnob("disable", "true")


          # Add a constant node to ensure we're always passing channels through.
          # It's range should be the super-range of all contained clips.
          firstFrame, lastFrame = 0, 0
          if track in lastLifetimeRange and len(lastLifetimeRange[track]) > 0:
            firstFrame, lastFrame = lastLifetimeRange[track][0]
            for start, end in lastLifetimeRange[track]:
              if start < firstFrame:
                firstFrame = start
              if end > lastFrame:
                lastFrame = end

          constant = nuke.ConstantNode(firstFrame, lastFrame, channels="rgb")
          added_nodes.append(constant)
          script.addNode(constant)

        shouldAddBlackOutside = hasSoftEffectTracks and track.isBlendEnabled() and not trackDisconnected
        if shouldAddBlackOutside:
          # We will be merging this track later and we need to make sure we have black outside so that
          # subsequent transform effects work correctly.
          blackOutside = nuke.Node("BlackOutside")
          script.addNode(blackOutside)
          added_nodes.append(blackOutside)

        tracksWithVideo.add(track)

        # Check if we will be adding a merge node here later. If so, this would be the A input and
        # we will need a dot node to connect between this and the Merge
        if track != tracks[0] and not trackDisconnected:
          dot = nuke.DotNode()
          # Set the dot node's input so we can properly align it after laying out the associated Merge node
          dot.setInputNode(0, added_nodes[-1])
          script.addNode(dot)
          added_nodes.append(dot)

          # If the next item will be a Merge node, and blendMask is enabled,
          # we'll need a set and push here, as well as additional Dot nodes
          # to join everything up nicely.
          if track.isBlendMaskEnabled():
            # Add a dot for the mask input
            dotA = nuke.DotNode()
            script.addNode(dotA)
            added_nodes.append(dotA)

            AInputDict[track] = dotA

            # Construct a unique label for the set/push.
            commandLabel = "Mask_" + str(tracks.index(track))

            # Add the set command
            setCommand = nuke.SetNode(commandLabel, 0)
            script.addNode(setCommand)
            added_nodes.append(setCommand)

            # Add a dot command to bring together the A and mask inputs
            dotMask = nuke.DotNode()
            script.addNode(dotMask)
            added_nodes.append(dotMask)

            #Add a set command so that we can back to this dot for the merge mask input
            dotMaskSetNode = nuke.SetNode(trackWriter.getMaskJumpName(), 0)
            script.addNode(dotMaskSetNode)
            added_nodes.append(dotMaskSetNode)

            maskInputDict[track] = dotMask

            # Add the push command
            pushCommand = nuke.PushNode(commandLabel)
            script.addNode(pushCommand)
            added_nodes.append(pushCommand)

            lastTrackNodeDict[track] = dot

        # Add a set node to the end of the track
        setNode = nuke.SetNode(trackWriter.getJumpName(), 0)
        outputJumpName = trackWriter.getJumpName()
        added_nodes.append(setNode)
        script.addNode(setNode)

        script.popLayoutContext()

      elif trackDisconnected:
        script.pushLayoutContext("track", track.name(), track=track, disconnected=trackDisconnected)

        added_nodes.extend( FnNukeHelpers._addEffectsAnnotationsForTrack(track,
                                                                         self._params.includeEffects(),
                                                                         self._params.includeAnnotations(),
                                                                         script,
                                                                         offset,
                                                                         inputs=0,
                                                                         cliptype=effectsClipType) )
        script.popLayoutContext()


      # Store the last node added to this track
      if not track in lastTrackNodeDict and len(added_nodes) > 0:
        # Get the last non-tcl command Node added
        for node in reversed(added_nodes):
          lastTrackNodeDict[track] = node
          if node.isNode():
            break

    # Now iterate over the tracks in order, writing merges and their soft effects
    previousTrack = None
    for track in tracks:
      trackDisconnected = track in disconnectedTracks

      if not trackDisconnected and previousTrack:
        # We need a merge if this track contains any clips
        if track in tracksWithVideo:
          merge = nuke.MergeNode()
          if track.isBlendEnabled():
            blendMode = track.blendMode()
            merge.setKnob('operation', blendMode )

            # For a blend track, use 'All' for metadata which means the B input
            # is copied over A
            merge.setKnob('metainput', 'All')

            # For blend track, we want to output the bbox to be the union of A and B
            merge.setKnob('bbox', 'union')

            # will this node need to connect to its mask input to its A input?
            if track.isBlendMaskEnabled():
              # The correct command in the nuke script should be:
              #    inputs 2+1
              # However we need to use quotes here to stop the 2nd parameter being
              # evaluated as 3. This will be special cased in the Script contruction
              # later.
              merge.setKnob("inputs", "2+1")
              merge.setDotInputs(AInputDict[track], maskInputDict[track])

          else:
            # For non-blend track, we want to output the metadata from the A input
            merge.setKnob('metainput', 'A')

            # For non-blend track, we want to output the bbox from the A input
            merge.setKnob('bbox', 'A')

            # This Merge node should use the custom alpha channel created on the A input track
            merge.setKnob('Achannels', '{rgba.red rgba.green rgba.blue Track_Alpha.a}')
          if previousTrack:
            merge.setKnob( 'label', track.name()+' over '+previousTrack.name() )


            # Set the Merge's inputs, so we can use them to properly position the Merge later.
            if track in lastTrackNodeDict:
              merge.setInputNode(0, lastTrackNodeDict[track])
            if previousTrack in lastTrackNodeDict:
              merge.setInputNode(1, lastTrackNodeDict[previousTrack])

            # Any subsequent Merges will be connected to this one, so update the last Node in the track.
            lastTrackNodeDict[track] = merge
          else:
            merge.setKnob( 'label', track.name() )

          # If all items from the track are disabled, also fully disable the Merge Node
          if track in trackDisabled and trackDisabled[track] == True:
            merge.setKnob("disable", "true")
          elif track in lastLifetimeRange:
            # Animate the Merge node's disable knob over each lifetime on the track
            for start, end in lastLifetimeRange[track]:
              merge.addEnabledRange(start, end, firstCompFrame)

          script.pushLayoutContext("merge", "Merge " + previousTrack.name() + " " + track.name(), track=previousTrack, inputA=track, inputB=previousTrack)

          inputAWriter = None
          inputBWriter = None
          for writer in self._trackWriters:
            if writer._track == track:
              inputAWriter = writer
            if writer._track == previousTrack:
              inputBWriter = writer

          #Add pushes for inputs
          if track.isBlendMaskEnabled():
            # Push for the mask input
            pushMaskNode = nuke.PushNode(inputAWriter.getMaskJumpName())
            added_nodes.append(pushMaskNode)
            script.addNode(pushMaskNode)

          pushANode = nuke.PushNode(inputAWriter.getJumpName())
          added_nodes.append(pushANode)
          script.addNode(pushANode)

          pushBNode = nuke.PushNode(inputBWriter.getJumpName())
          added_nodes.append(pushBNode)
          script.addNode(pushBNode)

          script.addNode(merge)
          added_nodes.append(merge)

          #Add a set for the merge because this merge should replace the track
          mergeJumpName = inputAWriter.getJumpName() + "Merge"
          mergeSetNode = nuke.SetNode(mergeJumpName, 0)
          added_nodes.append(mergeSetNode)
          script.addNode(mergeSetNode)
          inputAWriter.setJumpName(mergeJumpName)
          outputJumpName = mergeJumpName

          script.popLayoutContext()
        # If there were no clips on the track, write the effects and annotations after the merge so they get applied to the tracks below
        else:
          script.pushLayoutContext("effectsTrack", track.name(), track=track, disconnected=trackDisconnected)

          effectInputs = 1
          if trackDisconnected:
            effectInputs = 0

          extendedNodes = FnNukeHelpers._addEffectsAnnotationsForTrack(track,
                                                                           self._params.includeEffects(),
                                                                           self._params.includeAnnotations(),
                                                                           script,
                                                                           offset,
                                                                           inputs=effectInputs,
                                                                           cliptype=effectsClipType)

          if extendedNodes:
            added_nodes.extend( extendedNodes )

            # We need to make sure that effects and annotations are aligned under the main comp branch
            if previousTrack and previousTrack in lastTrackNodeDict:
              previousNode = None
              for node in extendedNodes:
                if previousNode is None:
                  inputNode = lastTrackNodeDict[previousTrack]
                else:
                  inputNode = previousNode
                  lastTrackNodeDict[track] = node

                node.setInputNode(0, inputNode)
                previousNode = node

          # Add the effects jump
          effectsJump = EffectsTrackJump(track)
          effectsSetNode = nuke.SetNode(effectsJump.getJumpName(), 0)
          added_nodes.append(effectsSetNode)
          script.addNode(effectsSetNode)
          self._trackWriters.append(effectsJump)
          outputJumpName = effectsJump.getJumpName()

          script.popLayoutContext() # effectsTrack

      previousTrack = track
    return outputJumpName

  def needJoinViews(self):
    """ Test if the views need to be written separately and connected to a JoinViews
    node. This is the case if any of the tracks are set to output to a single view """
    if len(self._params.views()) > 1:
      for track in self._sequence.videoTracks():
        if track.view():
          return True
    return False

  def writeTracksWithJoinViews(self, script, offset, skipOffline, mediaToSkip, disconnected, masterTracks):
    """ Write the tracks for each view separately and then add a JoinViews node """
    jumpNames = {}
    tracks = {}
    # Need multiple passes over the views:
    # a) to build all the Read nodes info. Because the same track may be written
    #    once per view these need to  be included in the collateReadNodes
    #    for the number of times used
    # b) to actually write the tracks for each view
    # c) to push the jump names for the outputs from each track before adding the JoinViews
    for view in reversed(self._params.views()):
      connectedTracks, disconnectedTracks = FnNukeHelpers.getConnectedDisconnectedTracks(self._sequence,
                                                                                         masterTracks,
                                                                                         disconnected,
                                                                                         self._params.includeEffects(),
                                                                                         self._params.includeAnnotations(),
                                                                                         view)
      tracks[view] = connectedTracks, disconnectedTracks
      self._readNodeUsageCollator.collateReadNodes(connectedTracks + disconnectedTracks, self._params, offset)

    for view in reversed(self._params.views()):
      connectedTracks, disconnectedTracks = tracks[view]
      if connectedTracks or disconnectedTracks:
        script.pushLayoutContext("view", view)
        outputJumpName = self.writeTracks(connectedTracks, disconnectedTracks, script, offset, skipOffline, mediaToSkip)
        if connectedTracks:
          jumpNames[view] = outputJumpName
        script.popLayoutContext()

    for view in reversed(self._params.views()):
      try:
        script.addNode( nuke.PushNode(jumpNames[view]) )
      except:
        # If there were no tracks for this view add 'push 0' for a disconnected input
        script.addNode( nuke.PushNode('0') )
    joinViewsNode = nuke.Node("JoinViews", inputs=len(self._params.views()))
    script.addNode(joinViewsNode)

  def writeToScript(self,
                    script,
                    offset=0,
                    skipOffline=True,
                    mediaToSkip=(),
                    disconnected=False,
                    masterTracks=None,
                    projectSettings = None):
    hiero.core.log.debug( '<'*10 + "Sequence.addToNukeScript()" + '>'*10 )

    masterTracks = masterTracks or []

    if self.needJoinViews():
      self.writeTracksWithJoinViews(script, offset, skipOffline, mediaToSkip, disconnected, masterTracks)
    else:
      script.pushLayoutContext("view", "main")
      # If layout is disconnected, only the 'master' track is connected to the Write node, any others
      # will be placed in the script but with clips disconnected.  To make this work, connected tracks
      # needs to be written last, so re-order the list. Effects/annotations which apply to the master track
      # also need to be connected

      self._readNodeUsageCollator.collateReadNodes(self._sequence.videoTracks(), self._params, offset)

      connectedTracks, disconnectedTracks = FnNukeHelpers.getConnectedDisconnectedTracks(self._sequence,
                                                                                         masterTracks,
                                                                                         disconnected,
                                                                                         self._params.includeEffects(),
                                                                                         self._params.includeAnnotations())

      self.writeTracks(connectedTracks, disconnectedTracks, script, offset, skipOffline, mediaToSkip, projectSettings)
      script.popLayoutContext()

    # Add any additional nodes.
    perSequenceNodes = self._params.doAdditionalNodesCallback(self._sequence)
    for node in perSequenceNodes:
      if node is not None:
        script.addNode(node)
