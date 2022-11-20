
"""
********************************************************************************
IMPORTANT: Most of the code in this file is now deprecated, with the replacement
functionality in FnNukeHelpersV2. Some of the functions are still in use (e.g.
for writing Clips, EffectTrackItems, Annotations).

If you make any further improvements to the code in this file, please move it
to FnNukeHelpersV2, clean it up, apply the changes there, and modify any usages
of it to the new version.
********************************************************************************

Punch addToNukeScript() functions into core classes to add equivalent Nuke nodes to a given script.
"""

import hiero.core
from hiero.core import (Clip,
                        Sequence,
                        TrackItem,
                        VideoTrack,
                        Format,
                        Keys,
                        Transition,
                        Annotation,
                        AnnotationText,
                        AnnotationStroke,
                        EffectTrackItem)
from . FnCompSourceInfo import (CompSourceInfo,
                                isNukeScript)

# Note, we have some ambiguity here.  'import nuke' imports the sub-module hiero.core.nuke, so we need to
# use 'import _nuke' to get the actual Nuke package.  Maybe we should rename hiero.core.nuke?
from . import nuke
import _nuke
import math
import os
import copy
import itertools
import re
import hiero.core.nuke


def nukeColourTransformNameFromHiero(colourTransformName, projectsettings):
  """
  Hiero and Nuke can have different names for equivalent colour transforms.
  This function converts from a hiero colour transform to a nuke one.

  TODO Don't think this function is necessary any more, but it's still in use,
  so leaving it alone for now
  """

  # If we're using a non nuke-default OCIO config, we don't want to do any
  # Hiero-Nuke conversions, since we most likely have selected a specific
  # colorspace from the config we are currently using.
  usingOCIO = projectsettings['lutUseOCIOForExport']
  usingNukeDefault = projectsettings["ocioConfigName"].find("nuke-default") != -1

  if usingOCIO and not usingNukeDefault:
    return colourTransformName

  if colourTransformName == 'raw':
    return 'linear'

  return colourTransformName

def isNonZeroStartFrameMovieFile(filename):
  """Returns True if the filename is a from a movie file which Nuke must read from frame 1 or later (e.g. QuickTime/FFmpeg/MXF), False otherwise"""
  (fullFileName, fileExtension) = os.path.splitext(filename)
  fileExtension = fileExtension.lower()
  if not fileExtension.startswith("."):
    fileExtension = "." + fileExtension

  # This is a list of file format extensions which Nuke must read at frame 1 (currently QuickTime+ffmpeg+MXF)
  return fileExtension in hiero.core.NonZeroStartFrameMovieFileExtensions


def getRetimeSourceOut( trackItem ):
  """ Determine the track item source out frame for writing to the OFlow node.
      This is now floored so the final frame matches what you get in the viewer, rather than possibly blending between two frames if the sourceOut() value didn't return an integer.
      The previous version of this is left commented out, this was added for Bug 45704, but caused incorrect behaviour in other cases. """
  return math.floor( trackItem.sourceOut() )
  #return trackItem.mapTimelineToSource( trackItem.timelineOut()+1 )-1


def _guidFromCopyTag(item):
  for tag in item.tags():
    if tag.name() == "Copy":
      return tag.metadata().value("tag.guid")
  return None


def _Clip_addAnnotationsToNukeScript(self, script, firstFrame, trimmed, trimStart=None, trimEnd=None):
  """ Add the annotations inside a clip to a Nuke script.  This is separated from Clip.addToNukeScript()
      so it's easier to control where in the script the annotations are placed.  The parameters are used to determine
      the frame range for the annotations. """

  startFrame = self.sourceIn()
  start, end = _Clip_getStartEndFrames(self, firstFrame, trimmed, trimStart, trimEnd)
  subTrackItemsOffset = firstFrame + startFrame - start
  if trimStart is not None:
    subTrackItemsOffset += trimStart

  # Add clip internal annotations
  annotations = [ item for item in itertools.chain( *itertools.chain(*self.subTrackItems()) ) if isinstance(item, Annotation) ]

  annotationNodes = createAnnotationsGroup(script, annotations, subTrackItemsOffset, inputs=1)

  return annotationNodes


Clip.addAnnotationsToNukeScript = _Clip_addAnnotationsToNukeScript


def _Clip_getStartEndFrames(self, firstFrame, trimmed, trimStart, trimEnd):
  """ Helper function to determine the start and end frames when writing a clip to a Nuke script.

      @param firstFrame: Custom offset to move start frame of clip
      @param trimmed: If True, a TimeClip node will be added to trim the range output by the Read node. The range defaults to the clip's soft trim range. If soft trims are not enabled on the clip, the range defaults to the clip range. The range can be overridden by passing trimStart and/or trimEnd values.
      @param trimStart: Override the trim range start with this value.
      @param trimEnd: Override the trim range end with this value.
  """

  source = self.mediaSource()
  fi = source.fileinfos()[0]

  # Get start frame. First frame of an image sequence. Zero if quicktime/r3d
  startFrame = self.sourceIn()
  hiero.core.log.debug( "startFrame: " + str(startFrame) )

  # Initialise to the source length, starting at the first frame of the media.
  start = startFrame
  end = start + self.duration()-1
  # Trim if soft trims are available and requested or they specified a trim range.
  if trimmed:
    # Everything within Hiero is zero-based so add file start frame to get real frame numbers at end.
    if self.softTrimsEnabled():
      start = self.softTrimsInTime()
      end = self.softTrimsOutTime()

    # Offset the trim range by the source.startTime() since the user sees frame numbers
    # on Sequences (including Clips) in the UI start numbering from 0.
    if trimStart is not None:
      start = trimStart + startFrame
    if trimEnd is not None:
      end = trimEnd + startFrame

  return start, end


#this map is used for mapping enum values from hiero to nuke
localisationMap = {
  Clip.kOnLocalize : "on",
  Clip.kAutoLocalize : "fromAutoLocalizePath",
  Clip.kOnDemandLocalize : "onDemand",
  Clip.kOffLocalize : "off" }

def _Clip_readInfoKey(self, readFilename):
  """ Generate a key for looking up read info for a clip. This is needed because
  you can have multiple clips which read the same source media with different ranges.
  In this case, separate Read nodes should be generated.
  """
  return "%s-%s-%s" % (readFilename, self.sourceIn(), self.duration())

def _Clip_getFilePath(self):
  """ Helper function for getting the file path from a Clip. This tries to use
  the Read node, but there are cases where this gets called for a Clip which was
  generated by the exporter and doesn't have a node, so in this case fall back to
  the old code which uses the clip's MediaSource.
  """
  try:
    path = self.readNode()['file'].getText()

    # For consistency with the behaviour before the path was being taken from the
    # Read node, and because it can cause problems with the frame server, apply path
    # remap settings to the path set in the comp
    path = hiero.core.util.remapPath(path)
    return path
  except:
    return self.mediaSource().fileinfos()[0].filename()


def _Clip_getReadInfo(self, firstFrame=None):
  """
  Get information (filename and start at value) for any Read Node in this clip.

  @param firstFrame: Custom offset to move start frame of clip
  """
  assert isinstance(self, Clip), "This function can only be punched into a Clip object."

  source = self.mediaSource()

  if source is None:
    return {}

  readFileInfo = {}

  readFilename = _Clip_getFilePath(self)

  try:
    compInfo = CompSourceInfo(self)
    if compInfo.isComp():
      # Change the readFilename to point to the nk script render path
      readFilename = compInfo.writePath
  except RuntimeError:
    if isNukeScript(readFilename):
      readFilename = None

  if readFilename is not None:
    readInfoKey = _Clip_readInfoKey(self, readFilename)
    readFileInfo[readInfoKey] = firstFrame

  return readFileInfo

Clip.getReadInfo = _Clip_getReadInfo


# Set of knob names to ignore when adding knobs from a clip's Read node
# to the generated script. These are already being handled by the export
# code
_Clip_readNodeKnobsToIgnore = set(('name',
                                  'file',
                                  'width',
                                  'height',
                                  'pixelAspect',
                                  'first',
                                  'last',
                                  'localizationPolicy'))

def _Clip_addReadNodeKnobs(clip, scriptReadNode):
  """ Add the knobs from a clip's Read node to the generated script. Knobs are
  only written if aren't in the list of knobs which are being handled separately.
  """
  # Get the Read node. This might not exist if the clip was generated by the
  # export process and so does not belong to a project.
  try:
    clipReadNode = clip.readNode()
  except:
    return

  # To get the knob script, tell the node to write it's knobs, then parse the output.
  # You can get the script for individual knobs, but it doesn't always seem to written
  # in the form it would appear in the nk.
  knobsScript = clipReadNode.writeKnobs(_nuke.TO_SCRIPT|_nuke.WRITE_NON_DEFAULT_ONLY).split('\n')
  for knobScript in knobsScript:
    # Each line consists of the knob name, a space, then the value. Find the first
    # space and split the string. Some lines come in empty, in which case an exception
    # will be thrown
    try:
      firstSpace = knobScript.index(' ')
      name = knobScript[:firstSpace]
      if name not in _Clip_readNodeKnobsToIgnore:
        value = knobScript[firstSpace+1:]
        scriptReadNode.setKnob(name, value)
    except ValueError:
      continue


def _Clip_addToNukeScript(self,
                          script,
                          additionalNodes=None,
                          additionalNodesCallback=None,
                          firstFrame=None,
                          trimmed=True,
                          trimStart=None,
                          trimEnd=None,
                          colourTransform=None,
                          metadataNode=None,
                          includeMetadataNode=True,
                          nodeLabel=None,
                          enabled=True,
                          includeEffects=True,
                          beforeBehaviour=None,
                          afterBehaviour=None,
                          project = None,
                          readNodes = {},
                          addEffectsLifetime=True):
  """addToNukeScript(self, script, trimmed=True, trimStart=None, trimEnd=None)

  Add a Read node to the Nuke script for each media sequence/file used in this clip. If there is no media, nothing is added.

  @param script: Nuke script object to add nodes
  @param additionalNodes: List of nodes to be added post read
  @param additionalNodesCallback: callback to allow custom additional node per item function([Clip|TrackItem|Track|Sequence])
  @param firstFrame: Custom offset to move start frame of clip
  @param trimmed: If True, a TimeClip node will be added to trim the range output by the Read node. The range defaults to the clip's soft trim range. If soft trims are not enabled on the clip, the range defaults to the clip range. The range can be overridden by passing trimStart and/or trimEnd values.
  @param trimStart: Override the trim range start with this value.
  @param trimEnd: Override the trim range end with this value.
  @param colourTransform: if specified, is set as the color transform for the clip
  @param metadataNode: node containing metadata to be inserted into the script
  @param includeMetadataNode: specifies whether a metadata node should be added to the script
  @param nodeLabel: optional label for the Read node
  @param enabled: enabled status of the read node. True by default
  @param includeEffects: if True, soft effects in the clip are included
  @param beforeBehaviour: What to do for frames before the first ([hold|loop|bounce|black])
  @param afterBehaviour: What to do for frames after the last ([hold|loop|bounce|black])
  """

  hiero.core.log.debug( "trimmed=%s, trimStart=%s, trimEnd=%s, firstFrame=%s" % (str(trimmed), str(trimStart), str(trimEnd), str(firstFrame)) )
  # Check that we are on the right type of object, just to be safe.
  assert isinstance(self, Clip), "This function can only be punched into a Clip object."

  added_nodes = []

  source = self.mediaSource()

  if source is None:
    # TODO: Add a constant here so that offline media has some representation within the nuke scene.
    # For now just do nothing
    return added_nodes

  # Get start frame. First frame of an image sequence. Zero if quicktime/r3d
  startFrame = self.sourceIn()
  hiero.core.log.debug( "startFrame: " + str(startFrame) )

  start, end = _Clip_getStartEndFrames(self, firstFrame, trimmed, trimStart, trimEnd)

  # Grab clip format
  format = self.format()

  isRead = False
  isPostageStamp = False

  readFilename = _Clip_getFilePath(self)

  hiero.core.log.debug( "- adding Nuke node for:%s %s %s", readFilename, start, end )

  # When writing a clip which points to an nk script, we can't just add a Read
  # node with the nk as path.
  # For an nk clip, try to find the metadata for the write path, and use that
  # in the Read node.  This should be present, it's set by nkReader.  If it's
  # not, CompSourceInfo will throw an exception, fall back to using a Precomp
  # just in case
  try:
    compInfo = CompSourceInfo(self)
    if compInfo.isComp():
      # Change the readFilename to point to the nk script render path
      readFilename = compInfo.unexpandedWritePath
  except RuntimeError:
    if isNukeScript(readFilename):
      # Create a Precomp node and reset readFilename to prevent a Read node
      # being created below
      read_node = nuke.PrecompNode( readFilename )
      readFilename = None

  # If there is a read filename, create a Read node
  if readFilename:
    # First check if we want to create a PostageStamp or Read node
    readInfoKey = _Clip_readInfoKey(self, readFilename)
    if enabled and readInfoKey in readNodes:
      readInfo = readNodes[readInfoKey]

      # Increment the usage
      readInfo.instancesUsed += 1
    else:
      readInfo = None

    # Only create a Read Node if this is the only usage of this filename, or this
    # is the last usage
    isPostageStamp = readInfo is not None and readInfo.instancesUsed < readInfo.totalInstances

    if isPostageStamp:
      # We will need a push command to connect it its Read Node
      pushCommandID = readInfo.readNodeID + "_" + str(readInfo.totalInstances)
      pushCommand = nuke.PushNode(pushCommandID)
      if script is not None:
        script.addNode(pushCommand)
      added_nodes.append(pushCommand)

      read_node = nuke.PostageStampNode()
    else:
      read_node = nuke.ReadNode(readFilename,
                                format.width(),
                                format.height(),
                                format.pixelAspect(),
                                round(start),
                                round(end),)
      read_node.setKnob("localizationPolicy", localisationMap[self.localizationPolicy()] )

      if firstFrame is not None:
        read_node.setKnob("frame_mode", 'start at')
        read_node.setKnob("frame", firstFrame)

      if beforeBehaviour is not None:
        read_node.setKnob("before", beforeBehaviour)
      if afterBehaviour is not None:
        read_node.setKnob("after", afterBehaviour)

      # Add the knobs from the clip's own Read node
      _Clip_addReadNodeKnobs(self, read_node)

      # If the colourTransform was specified, set the 'colorspace' knob to it,
      # overriding any settings from the Read node
      if colourTransform:
        read_node.setKnob('colorspace', colourTransform)

      # Set the color the node appears in the DAG. In Studio this is currently
      # stored on the parent bin item. The script format for the color is in the
      # form 0xrrggbbaa
      binItem = self.binItem()
      if binItem and binItem.displayColor().isValid():
        rgba = binItem.displayColor().getRgb() # Get tuple of rgba components
        colorString = "0x" + "".join("%02x" % i for i in rgba)
        read_node.setKnob("tile_color", colorString)

      isRead = True



  # If a node name has been specified
  if nodeLabel is not None:
    read_node.setKnob("label", nodeLabel)

  if script is not None:
    script.addNode(read_node)
  added_nodes.append(read_node)

  if readInfo:
    if isRead:
      # We'll need a set and a push command, so that the script can be reordered later to put all
      # the Read and associated Set commands to the top. The Push commands will stay
      # where they are so that Nodes will connect up properly afterwards
      if enabled:
        setCommandID = readInfo.readNodeID + "_" + str(readInfo.totalInstances)
      else:
        setCommandID = readInfo.readNodeID + "_disabled"

      setCommand = nuke.SetNode(setCommandID, 0)
      pushCommand = nuke.PushNode(setCommandID)
      if script is not None:
        script.addNode(setCommand)
        script.addNode(pushCommand)
      added_nodes.append(setCommand)
      added_nodes.append(pushCommand)
    elif isPostageStamp:
      # If it's a postage stamp node, we'll also need a time offset to correct the Frame Range
      # relative to the original read
      originalFirstFrame = readInfo.startAt
      if originalFirstFrame is not None:
        # There's a slight difference between how frame ranges are handled by Read Nodes
        # and TimeOffset's in Nuke, and the information we pass.
        # Ideally, the Timeoffset would work entirely in floating point, but it, and its interface,
        # don't. We have added the dtime_offset as a workaround for this, but there's an additional
        # problem that the Read Node's original range (originalFirstFrame here) gets cast to int
        # before getting through to Timeoffset.
        # This means that Timeoffset cannot properly process the range because the fractional part
        # of originalFirstFrame has already been lost. We compensate for that here, by adding the
        # fractional part to the Timeoffset value.
        fractpart, intpart = math.modf(originalFirstFrame)
        if fractpart is None:
          fractpart = 0
        timeOffset = nuke.TimeOffsetNode(firstFrame - originalFirstFrame + fractpart)
        if script is not None:
          script.addNode(timeOffset)
        added_nodes.append(timeOffset)

  if not isRead and not isPostageStamp and firstFrame is not None:

    timeClip = nuke.TimeClipNode( round(start), round(end), start, end, round(firstFrame) )
    added_nodes.append( timeClip )

  if not enabled:
    read_node.setKnob("disable", True)

  if includeMetadataNode:
    if metadataNode is None:
      metadataNode = nuke.MetadataNode()
      if script is not None:
        script.addNode(metadataNode)
      added_nodes.append(metadataNode)
      metadataNode.setInputNode(0, read_node)

    metadataNode.addMetadata([("hiero/clip", self.name())])
    # Also set the reel name (if any) on the metadata key the dpx writer expects for this.
    clipMetadata = self.metadata()
    if Keys.kSourceReelId in clipMetadata:
      reel = clipMetadata[Keys.kSourceReelId]
      if len(reel):
        metadataNode.addMetadata( [ ("hiero/reel", reel), ('dpx/input_device', reel), ('quicktime/reel', reel) ] )

    # Add Tags to metadata
    metadataNode.addMetadataFromTags( self.tags() )

  if includeEffects:
    # Add clip internal soft effects
    # We need to offset the frame range of the effects from clip time into the output time.
    if firstFrame is not None:
      effectOffset = firstFrame + startFrame - start
    else:
      effectOffset = startFrame

    effects = [ item for item in itertools.chain( *itertools.chain(*self.subTrackItems()) ) if isinstance(item, EffectTrackItem) ]
    hiero.core.log.info("Clip.addToNukeScript effects %s %s" % (effects, self.subTrackItems()))
    for effect in effects:
      added_nodes.extend( effect.addToNukeScript(script, effectOffset, addLifetime=addEffectsLifetime) )

  postReadNodes = []
  if callable(additionalNodesCallback):
    postReadNodes.extend(additionalNodesCallback(self))

  if additionalNodes is not None:
    postReadNodes.extend(additionalNodes)

  if includeMetadataNode:
    prevNode = metadataNode
  else:
    prevNode = read_node

  for node in postReadNodes:
    # Add additional nodes
    if node is not None:
      node = copy.deepcopy(node)
      node.setInputNode(0, prevNode)
      prevNode = node

      # Disable additional nodes too
      if not enabled:
        node.setKnob("disable", "true")

      added_nodes.append(node)
      if script is not None:
        script.addNode(node)

  return added_nodes


Clip.addToNukeScript = _Clip_addToNukeScript


def _TrackItem_getTransitions(trackItem):
  """ Get a track item's transitions if they exist and are enabled. """
  inTransition = trackItem.inTransition() if trackItem.inTransition() and trackItem.inTransition().isEnabled() else None
  outTransition = trackItem.outTransition() if trackItem.outTransition() and trackItem.outTransition().isEnabled() else None

  return inTransition, outTransition


def _TrackItem_addToNukeScript(self,
                              script=nuke.ScriptWriter(),
                              firstFrame=None,
                              additionalNodes=[],
                              additionalNodesCallback=None,
                              includeRetimes=False,
                              retimeMethod=None,
                              startHandle=None,
                              endHandle=None,
                              colourTransform=None,
                              offset=0,
                              nodeLabel=None,
                              includeAnnotations=False,
                              includeEffects=True,
                              outputToSequenceFormat=False):
  """This is a variation on the Clip.addToNukeScript() method that remaps the
  Read frame range to the range of the this TrackItem rather than the Clip's
  range. TrackItem retimes and reverses are applied via Retime and OFlow nodes
  if needed. The additionalNodes parameter takes a list of nodes to add before
  the source material is shifted to the TrackItem timeline time and trimmed to
  black outside of the cut. This means timing can be set in the original
  source range and adding channels, etc won't affect frames outside the cut
  length.

  @param retimeMethod: "Motion", "Blend", "Frame" - Knob setting for OFlow retime method
  @param offset: Optional, Global frame offset applied across whole script
  """

  # Check that we are on the right type of object, just to be safe.
  assert isinstance(self, TrackItem), "This function can only be punched into a TrackItem object."

  hiero.core.log.debug( "Add TrackItem (%s) to script, startHandle = %s, endHandle = %s, firstFrame=%s" % (self.name(), str(startHandle), str(endHandle), str(firstFrame)) )

  added_nodes = []

  retimeRate = 1.0
  if includeRetimes:
    retimeRate = self.playbackSpeed()

  # Compensate for retime in HandleLength!!
  if startHandle is None:
    startHandle = 0
  if endHandle is None:
    endHandle = 0

  # Check for transitions
  inTransition, outTransition = _TrackItem_getTransitions(self)
  inTransitionHandle, outTransitionHandle = 0, 0

  # Adjust the clips to cover dissolve transition
  if outTransition is not None:
    if outTransition.alignment() == Transition.kDissolve:
      # Calculate the delta required to move the end of the clip to cover the dissolve transition
      outTransitionHandle = (outTransition.timelineOut() - self.timelineOut())
  if inTransition is not None:
    if inTransition.alignment() == Transition.kDissolve:
      # Calculate the delta required to move the beginning of the clip to cover the dissolve transition
      inTransitionHandle = (self.timelineIn() - inTransition.timelineIn())


  # If the clip is reversed, we need to swap the start and end times
  start = min(self.sourceIn(), self.sourceOut())
  end = max(self.sourceIn(), self.sourceOut())

  # Extend handles to incorporate transitions
  # If clip is reversed, handles are swapped
  if retimeRate >= 0.0:
    inHandle = startHandle + inTransitionHandle
    outHandle = endHandle + outTransitionHandle
  else:
    inHandle = startHandle + outTransitionHandle
    outHandle = endHandle + inTransitionHandle

  clip = self.source()
  # Recalculate handles clamping to available media range
  readStartHandle = min(start,  math.ceil(inHandle * abs(retimeRate) ))
  readEndHandle = min((clip.duration() - 1) - end ,  math.ceil(outHandle * abs(retimeRate) ))

  hiero.core.log.debug ( "readStartHandle", readStartHandle, "readEndHandle", readEndHandle )

  # Add handles to source range
  start -= readStartHandle
  end += readEndHandle

  # Read node frame range
  readStart, readEnd = start, end
  # First frame identifies the starting frame of the output. Defaults to timeline in time
  readNodeFirstFrame = firstFrame
  if readNodeFirstFrame is None:
    readNodeFirstFrame = self.timelineIn() -  min( min(self.sourceIn(), self.sourceOut()), inHandle)
  else:
    # If we have trimmed the handles, bump the start frame up by the difference
    readNodeFirstFrame += round(inHandle * abs(retimeRate)) - readStartHandle

  # Apply global offset
  readNodeFirstFrame+=offset

  # Calculate the frame range, != read range as read range may be clamped to available media range
  first_frame=start
  last_frame=end
  if firstFrame is not None:
    # if firstFrame is specified
    last_frame =  firstFrame + (startHandle + inTransitionHandle) + (self.duration() -1) + (endHandle + outTransitionHandle)
    hiero.core.log.debug( "last_frame(%i) =  firstFrame(%i) + startHandle(%i) + (self.duration() -1)(%i) + endHandle(%i)" % (last_frame, firstFrame, startHandle + inTransitionHandle, (self.duration() -1), endHandle + outTransitionHandle) )
    first_frame = firstFrame
  else:
    # if firstFrame not specified, use timeline time
    last_frame =  self.timelineIn() + (self.duration() -1) + (endHandle + outTransitionHandle)
    first_frame = (self.timelineIn() - (startHandle + inTransitionHandle))
    hiero.core.log.debug( "first_frame(%i) =  self.timelineIn(%i) - (startHandle(%i) + inTransitionHandle(%i)" % (first_frame, self.timelineIn(), startHandle, inTransitionHandle) )

  # Create a metadata node
  metadataNode = nuke.MetadataNode()
  reformatNode = None

  # Add TrackItem metadata to node
  metadataNode.addMetadata([("hiero/shot", self.name()), ("hiero/shot_guid", _guidFromCopyTag(self))])

  # sequence level metadata
  seq = self.parentSequence()
  if seq:
    seqTimecodeStart = seq.timecodeStart()
    seqTimecodeFrame = seqTimecodeStart + self.timelineIn() - inHandle
    seqTimecode = hiero.core.Timecode.timeToString(seqTimecodeFrame, seq.framerate(), hiero.core.Timecode.kDisplayTimecode)

    metadataNode.addMetadata( [ ("hiero/project", clip.project().name() ),
                                ("hiero/sequence/frame_rate", seq.framerate() ),
                                ("hiero/sequence/timecode", "[make_timecode %s %s %d]" % (seqTimecode, str(seq.framerate()), first_frame) )
                                ] )

  # Add Tags to metadata
  metadataNode.addMetadataFromTags( self.tags() )

  # Add Track and Sequence here as these metadata nodes are going to be added per clip/track item. Not per sequence or track.
  if self.parent():
    metadataNode.addMetadata([("hiero/track", self.parent().name()), ("hiero/track_guid", _guidFromCopyTag(self.parent()))])
    if self.parentSequence():
      metadataNode.addMetadata([("hiero/sequence", self.parentSequence().name()), ("hiero/sequence_guid", _guidFromCopyTag(self.parentSequence()))])

      # If we have clip and we're in a sequence then we output the reformat settings as another reformat node.
      reformat = self.reformatState()
      if reformat.type() != nuke.ReformatNode.kDisabled:
        formatString = str(seq.format())
        reformatNode = nuke.ReformatNode( resize=reformat.resizeType(),
                                          center=reformat.resizeCenter(),
                                          flip=reformat.resizeFlip(),
                                          flop=reformat.resizeFlop(),
                                          turn=reformat.resizeTurn(),
                                          to_type=reformat.type(),
                                          format=formatString,
                                          scale=reformat.scale(),
                                          pbb=True)

  # To support the TimeWarp effect, we now set the full clip's frame range in the Read node, with the desired.
  # frames selected by the TimeClip node.  This shifts the Read nodes 'start at' frame to compensate.
  readNodeFirstFrame -= readStart

  # Capture the clip nodes without adding to the script, so that we can group them as necessary
  clip_nodes = clip.addToNukeScript(None,
                                    firstFrame=readNodeFirstFrame,
                                    colourTransform=colourTransform,
                                    metadataNode=metadataNode,
                                    nodeLabel=nodeLabel,
                                    enabled=self.isEnabled(),
                                    includeEffects=includeEffects)

  # Add the read node to the script
  # This assumes the read node will be the first node
  read_node = clip_nodes[0]
  if script:
    script.addNode(read_node)
  added_nodes.append(read_node)

  if includeAnnotations:
    # Add the clip annotations.  This goes immediately after the Read, so it is affected by the Reformat if there is one
    clipAnnotations = clip.addAnnotationsToNukeScript(script, firstFrame=readNodeFirstFrame, trimmed=True, trimStart=readStart, trimEnd=readEnd)
    added_nodes.extend(clipAnnotations)

  added_nodes.extend( clip_nodes[1:] )
  # Add all other clip nodes to the group
  for node in clip_nodes[1:]:
    script.addNode(node)

  # Add reformat node
  if reformatNode is not None:
    added_nodes.append(reformatNode)
    script.addNode(reformatNode)

  # Add metadata node
  added_nodes.append(metadataNode)
  script.addNode(metadataNode)

  # This parameter allow the whole nuke script to be shifted by a number of frames
  first_frame += offset
  last_frame += offset

  # Frame range is used to correct the range from OFlow
  timeClipNode = nuke.TimeClipNode( first_frame, last_frame, clip.sourceIn(), clip.sourceOut(), first_frame)
  timeClipNode.setKnob('label', 'Set frame range to [knob first] - [knob last]')
  added_nodes.append(timeClipNode)
  script.addNode(timeClipNode)

  # Add Additional nodes.
  postReadNodes = []
  if callable(additionalNodesCallback):
    postReadNodes.extend(additionalNodesCallback(self))
  if additionalNodes is not None:
    postReadNodes.extend(additionalNodes)

  # Add any additional nodes.
  for node in postReadNodes:
    if node is not None:
      node = copy.deepcopy(node)
      # Disable additional nodes too
      if not self.isEnabled():
        node.setKnob("disable", True)

      added_nodes.append(node)
      script.addNode(node)

  assert (not includeRetimes) or (retimeMethod is not None), "includeRetimes is true and retimeMethod is None"

  # If this clip is a freeze frame add a frame hold node
  isFreezeFrame = (retimeRate == 0.0)
  if isFreezeFrame:
    # first_frame is max of first_frame and readNodeFirstFrame because when
    # using a dissolve with a still clip first_frame is the first frame of 2
    # clips, which is lower than readNodeFirstFrame.
    frameHoldNode = nuke.Node("FrameHold", first_frame=max(first_frame, readNodeFirstFrame))
    added_nodes.append(frameHoldNode)
    script.addNode(frameHoldNode)

  # If the clip is retimed we need to also add an OFlow node.
  elif includeRetimes and retimeRate != 1 and retimeMethod != 'None' and retimeMethod is not None:

    # Obtain keyFrames
    tIn, tOut = self.timelineIn(), self.timelineOut()
    sIn, sOut = self.sourceIn(), getRetimeSourceOut(self)

    hiero.core.log.debug("sIn %f sOut %f tIn %i tOut %i" % (sIn, sOut, tIn, tOut))
    # Offset keyFrames, so that they match the input range (source times) and produce expected output range (timeline times)
    # timeline values must start at first_frame
    tOffset = (first_frame + startHandle + inTransitionHandle) - self.timelineIn()
    tIn += tOffset
    tOut += tOffset
    sOffset = readNodeFirstFrame
    sIn += sOffset
    sOut += sOffset

    hiero.core.log.debug("Creating OFlow:", tIn, sIn, tOut, sOut)
    # Create OFlow node for computed keyFrames
    keyFrames = "{{curve l x%d %f x%d %f}}" % (tIn, sIn, tOut, sOut)
    oflow = nuke.Node("OFlow2",
      interpolation=retimeMethod,
      timing="Source Frame",
      timingFrame=keyFrames)
    oflow.setKnob('label', 'retime ' + str(retimeRate))
    added_nodes.append(oflow)
    script.addNode(oflow)

  # Find linked effects if includeEffects is specified
  linkedEffects = []
  if includeEffects:
    effectOffset = first_frame - self.timelineIn() + inHandle
    linkedEffects = [ item for item in self.linkedItems() if isinstance(item, hiero.core.EffectTrackItem) ]

    # If includeRetimes is False, do not include retime effects in the export.  Note that clip-level Timewarps will still be included.
    # That's a lot trickier to deal with (how do we copy those when doing Build Track?), so leaving that for now.
    if not includeRetimes:
      linkedEffects = [ effect for effect in linkedEffects if not effect.isRetimeEffect() ]

    # Make sure the effects are in the correct order.  They should be written from lowest sub-track to highest
    linkedEffects.sort(key = lambda effect: effect.subTrackIndex())

  # If outputting to sequence format, or there are any linked effects, need to make sure the format matches the sequence.
  # If the track item reformat state is not set to 'to format', we need to:
  # - Add a Reformat node to sequence
  # - Then write out any linked effects
  # - Then, if not outputting to sequence format, add further reformat nodes to get back to whatever the format was before that

  # TODO Some of this code is duplicated in NukeShotExporter.writeTrackItem(), it needs to be cleaned up

  reformatState = self.reformatState()
  itemSetToSequenceFormat = (reformatState.type() == nuke.ReformatNode.kToFormat)
  needAdditionalReformatNodes = (not itemSetToSequenceFormat) and (outputToSequenceFormat or linkedEffects)

  if needAdditionalReformatNodes:
    # Reformat to sequence
    toSequenceFormatNode = nuke.ReformatNode( resize=nuke.ReformatNode.kResizeNone,
                                              format=str(seq.format()),
                                              center=reformatState.resizeCenter(),
                                              black_outside=False,
                                              pbb=True)
    script.addNode(toSequenceFormatNode)
    added_nodes.append( toSequenceFormatNode )

  # Write out the linked effects, setting the cliptype knob to 'bbox' if necessary
  effectClipType = "bbox" if not itemSetToSequenceFormat else None
  for effect in linkedEffects:
    added_nodes.extend( effect.addToNukeScript( script,
                                                effectOffset,
                                                startHandle=inHandle,
                                                endHandle=outHandle,
                                                cliptype=effectClipType,
                                                addLifetime = False
                                                ) )

  # If not outputting to sequence format, add Reformats to get back to the previous format state
  if needAdditionalReformatNodes and not outputToSequenceFormat:
    clipFormatNode = nuke.ReformatNode( resize=nuke.ReformatNode.kResizeNone,
                                        format=str(self.source().format()),
                                        center=reformatState.resizeCenter(),
                                        black_outside=False,
                                        pbb=True)
    script.addNode(clipFormatNode)
    added_nodes.append(clipFormatNode)

    # If the item reformat is set to 'Scale' we need to add two Reformat nodes to restore the format, one to put it back to the clip format,
    # and here another to re-apply the scaling.  The image has already been scaled, so resize knob should be 'none'
    if reformatState.type() == nuke.ReformatNode.kToScale:
      scaleReformatNode = nuke.ReformatNode(resize=nuke.ReformatNode.kResizeNone,
                                            to_type=reformatState.type(),
                                            scale=reformatState.scale(),
                                            pbb=True,
                                            black_outside=False)
      script.addNode(scaleReformatNode)
      added_nodes.append(scaleReformatNode)

  return added_nodes

TrackItem.addToNukeScript = _TrackItem_addToNukeScript


def createAnnotationsGroup(script, annotations, offset, inputs, cliptype=None):
  """ Add a list of annotations to a script and place them inside a group. """

  # Don't do anything if there are no annotations
  if len(annotations) == 0:
    return []

  # Create the group with its disable knob linked to the annotations_show knob which we add to
  # the root node.
  annotationsGroup = nuke.GroupNode("Annotations", disable="{{!annotations_show }}", inputs=inputs)

  # If there are inputs, create an Input node for the group
  if inputs:
    annotationsGroup.addNode( nuke.Node("Input", inputs=0) )

  # Add the annotations to the group
  for annotation in annotations:
    annotation.addToNukeScript(annotationsGroup, offset=offset, inputs=inputs, cliptype=cliptype)
    inputs = 1 # Once we've added a node, any following should take their input from it

  # Add an Output node to the group
  annotationsGroup.addNode( nuke.Node("Output") )

  if script:
    script.addNode( annotationsGroup )

  # For consistency with all the other functions in this file, return a list of nodes
  return [ annotationsGroup ]


def _addTrackSubTrackItems(itemFilter, track, script, offset, inputs, cliptype):
  """ Write out the sub-track items of type itemType for a track. """

  # Build a list of effects across all the sub-tracks
  items = [ item for item in itertools.chain(*track.subTrackItems()) if itemFilter(item) ]

  # Write them to the script.  If the track has no clips on it and the sequence is being written disconnected,
  # there might not be any inputs, after the first item is added set inputs to 1.
  added_nodes = []
  for item in items:
    itemNodes = item.addToNukeScript(script, offset, inputs, cliptype)
    added_nodes.extend(itemNodes)
    inputs=1

  return added_nodes


def _addEffectsAnnotationsForTrack(track, includeEffects, includeAnnotations, script, offset, inputs=1, cliptype=None):
  """ Write the soft effects and annotations for a given track. """

  added_nodes = []

  if includeAnnotations:
    annotationNodes = _addTrackSubTrackItems( lambda x: isinstance(x, Annotation), track, script, offset, inputs, cliptype )
    if annotationNodes:
      added_nodes.extend( annotationNodes )
      inputs = 1

  if includeEffects:

    ## first add metadata node so the sequence time is correct in case of retimes on the clips

    sequence = track.parent()
    timecodeStart = sequence.timecodeStart()
    try:
     firstFrame = sequence.inTime()
    except:
     firstFrame = 0
    timecodeFrame = timecodeStart + firstFrame - offset
    scriptFrame = firstFrame

    timecodeStr = hiero.core.Timecode.timeToString(timecodeFrame, sequence.framerate(), hiero.core.Timecode.kDisplayTimecode)

    metadataNode = nuke.MetadataNode(inputs=inputs)
    metadataNode.addMetadata( [   ("hiero/sequence/timecode", "[make_timecode %s %s %d]" % (timecodeStr, str(sequence.framerate()), scriptFrame) ) ] )
    script.addNode( metadataNode )
    added_nodes.append(metadataNode)
    inputs = 1 # Next Node has metadata as input

    # Add track level effects, not including ones linked to a track item.  Those are added in TrackItem.addToNukeScript
    added_nodes.extend( _addTrackSubTrackItems( lambda x: isinstance(x, EffectTrackItem) and not x.linkedItems(), track, script, offset, inputs, cliptype ) )

  return added_nodes


def _VideoTrack_addToNukeScript(self,
                                script = nuke.ScriptWriter(),
                                additionalNodes=[],
                                additionalNodesCallback=None,
                                includeRetimes=False,
                                retimeMethod=None,
                                offset=0,
                                skipOffline=True,
                                mediaToSkip=[],
                                disconnected=False,
                                includeAnnotations=False,
                                includeEffects=True):
  """Add a Read node for each track item to the script with Merge or Dissolve nodes
  to join them in a sequence. TimeClip nodes are added to pad any gaps between clips.

  @param script: Nuke script object to add nodes to.
  @param additionalNodes: List of nodes to be added post read, passed on to track items
  @param additionalNodesCallback: callback to allow custom additional node per item function([Clip|TrackItem|Track|Sequence])
  @param includeRetimes: True/False include retimes
  @param retimeMethod: "Motion", "Blend", "Frame" - Knob setting for OFlow retime method
  @param offset: Optional, Global frame offset applied across whole script
  @param skipOffline: If True, offline clips are not included in the export
  @param mediaToSkip: List of MediaSources which should be excluded from the export
  @param disconnected: If True, items on the track are not connected and no constant nodes are added to fill gaps
  @param includeAnnotations: If True, clip-level annotations will be included in the output
  @param includeEffects: If True, clip-level soft effects will be included in the output
  """

  # Check that we are on the right type of object, just to be safe.
  assert isinstance(self, VideoTrack), "This function can only be punched into a VideoTrack object."

  added_nodes = []

  merge_nodes = []

  sequence = self.parent()

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

  # Work backwards so that the Merge nodes hook up the right way around.
  for trackItem in reversed(list(self.items())):
    source = trackItem.source().mediaSource()

    # Check if the source is in the mediaToSkip list
    if source in mediaToSkip:
      continue

    if not source.isMediaPresent() and skipOffline:
      continue

    hiero.core.log.debug( "  - " + str(trackItem) )

    # Check for transitions
    inTransition, outTransition = _TrackItem_getTransitions(trackItem)

    script.pushLayoutContext("clip", trackItem.name() + str(trackItem.eventNumber()), label=trackItem.name())

    # In case additional nodes is a Tuple, we need to be able to append.
    tiAdditionalNodes = list(additionalNodes)

    trackitem_nodes = trackItem.addToNukeScript(script,
                                                additionalNodes=tiAdditionalNodes,
                                                additionalNodesCallback=additionalNodesCallback,
                                                includeRetimes=includeRetimes,
                                                retimeMethod=retimeMethod,
                                                offset=offset,
                                                includeAnnotations=includeAnnotations,
                                                includeEffects=includeEffects,
                                                outputToSequenceFormat=True)
    added_nodes = added_nodes + trackitem_nodes

    # Check if we're going to join this to another track item. If so we'll need a Dot node
    dot = None
    if trackItem != list(self.items())[0] and len(list(self.items())) > 1:
      dot = nuke.DotNode()
      dot.setInputNode(0, added_nodes[-1])
      script.addNode(dot)
      added_nodes.append(dot)

    # Don't add any merges if the track is disconnected
    if not disconnected and lastTrackItem is not None:

      # For dissolves create a Dissolve node rather than Merge
      if outTransition and outTransition.alignment() == Transition.kDissolve:
        merge = nuke.DissolveNode()
        merge.setWhichKeys( (outTransition.timelineIn()+offset, 0), (outTransition.timelineOut()+offset, 1) )

      else:
        merge = nuke.MergeNode()

      # Connect this to the Dot created on the last track processed (if any)
      if lastDot is not None:
        merge.setInputNode(0, lastDot)

      merge_nodes.append((merge, lastTrackItem or trackItem))

    lastDot = dot

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

  perTrackNodes = []
  if callable(additionalNodesCallback):
    perTrackNodes.extend(additionalNodesCallback(self))

  # Add any additional nodes.
  for node in perTrackNodes:
    if node is not None:
      added_nodes.append(node)
      script.addNode(node)

  return added_nodes


VideoTrack.addToNukeScript = _VideoTrack_addToNukeScript


def getConnectedDisconnectedTracks(sequence,
                                   masterTracks,
                                   disconnected,
                                   includeEffects,
                                   includeAnnotations,
                                   view=None):
  """ Helper function to determine the connected and disconnected tracks for the
  given sequence, master tracks (possibly one per view) and disconnected setting.
  This can also filter the tracks for a particular view """

  if isinstance(masterTracks, VideoTrack):
    masterTracks = [masterTracks]

  connectedTracks = []
  disconnectedTracks = []
  tracks = []
  for track in sequence.videoTracks():
    # If a view was specified, check if the track should output to it
    if view:
      trackView = track.view()
      if trackView and trackView != view:
        continue

    # If the track has no TrackItems, check if it should be included based on the includeEffects and includeAnnotations settings.
    if not list(track.items()):
      hasEffects, hasAnnotations = False, False
      for item in itertools.chain(*track.subTrackItems()):
        if isinstance(item, Annotation):
          hasAnnotations = True
        elif isinstance(item, EffectTrackItem):
          hasEffects = True

      if (not includeAnnotations and hasAnnotations and not hasEffects) or (not includeEffects and hasEffects and not hasAnnotations):
        continue

    tracks.append(track)

  # If the disconnected parameter is not True, or no masterTrackItem was given, all tracks are connected.
  if disconnected:
    # A track is connected if:
    # a) it's in the list of master tracks, or
    # b) it only has effects/annotations, and it is above the master track
    # c) blending is enabled

    for track in tracks:
      isMaster = (track in masterTracks)
      isEffectsOnly = (not list(track.items()) and len(connectedTracks) > 0)
      isBlended = track.isBlendEnabled()

      if isMaster or isEffectsOnly or isBlended:
        connectedTracks.append(track)
      else:
        disconnectedTracks.append(track)

  else:
    connectedTracks = tracks

  return connectedTracks, disconnectedTracks


def _Sequence_addToNukeScript(self,
                              script = nuke.ScriptWriter(),
                              additionalNodes=[],
                              additionalNodesCallback=None,
                              includeRetimes=False,
                              retimeMethod=None,
                              offset=0,
                              skipOffline=True,
                              mediaToSkip=[],
                              disconnected=False,
                              masterTrackItem=None,
                              includeAnnotations=False,
                              includeEffects=True,
                              outputToFormat=None):
  """addToNukeScript(self, script)
  @param script: Nuke script object to add nodes to.
  @param includeRetimes: True/False include retimes
  @param retimeMethod: "Motion", "Blend", "Frame" - Knob setting for OFlow retime method
  @param additionalNodesCallback: callback to allow custom additional node per item function([Clip|TrackItem|Track|Sequence])
  @param offset: Optional, Global frame offset applied across whole script
  @param skipOffline: If True, offline clips are not included in the export
  @param mediaToSkip: List of MediaSources which should be excluded from the export
  @param disconnected: If True, tracks other than that containing the masterTrackItem are not connected to any inputs
  @param masterTrackItem: Used for controlling the script output if disconnected is specified
  @param includeAnnotations: If True, annotations are included in the exported script
  @param includeEffects: If True, soft effects are included in the exported script
  @param outputToFormat: Format to use for output.  If not specified, the sequence's own format is used.
  @return: None

  Add nodes representing this Sequence to the specified script.
  If there are no clips in the Sequence, nothing is added."""

  # Check that we are on the right type of object, just to be safe.
  assert isinstance(self, Sequence), "This function can only be punched into a Sequence object."

  added_nodes = []

  hiero.core.log.debug( '<'*10 + "Sequence.addToNukeScript()" + '>'*10 )
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
  effectsClipType = "bbox" if outputToFormat else None

  tracksWithVideo = set()

  # If layout is disconnected, only the 'master' track is connected to the Write node, any others
  # will be placed in the script but with clips disconnected.  To make this work, connected tracks
  # needs to be written last, so re-order the list. Effects/annotations which apply to the master track
  # also need to be connected

  connectedTracks, disconnectedTracks = getConnectedDisconnectedTracks(self, masterTrackItem.parent(), disconnected, includeEffects, includeAnnotations)
  tracks = connectedTracks + disconnectedTracks

  # Keep a record of the last Node in each track, since this will be used later to set the
  # correct connections to Merge nodes
  lastTrackNodeDict = {}

  # First write out the tracks and their annotations in reverse order, as described above
  for track in reversed(tracks):
    trackDisconnected = track in disconnectedTracks

    # Add the track and whether it is disconnected as data to the layout context
    script.pushLayoutContext("track", track.name(), track=track, disconnected=trackDisconnected)

    # If the track has any clips, write them and the effects out.
    trackItems = list(track.items())
    if len(trackItems) > 0:
      track_nodes = track.addToNukeScript(script,
                                         additionalNodes=additionalNodes,
                                         additionalNodesCallback=additionalNodesCallback,
                                         includeRetimes=includeRetimes,
                                         retimeMethod=retimeMethod,
                                         offset=offset,
                                         skipOffline=skipOffline,
                                         mediaToSkip=mediaToSkip,
                                         disconnected=trackDisconnected,
                                         includeAnnotations=includeAnnotations,
                                         includeEffects=includeEffects)
      added_nodes = added_nodes + track_nodes

      added_nodes.extend( _addEffectsAnnotationsForTrack(track, includeEffects, includeAnnotations, script, offset, cliptype=effectsClipType) )

      tracksWithVideo.add(track)

      # Check if we will be adding a merge node here later. If so, this would be the A input and
      # we will need a dot node to connect between this and the Merge
      if track != tracks[0] and not trackDisconnected and track.isBlendEnabled():
        dot = nuke.DotNode()
        # Set the dot node's input so we can properly align it after laying out the associated Merge node
        dot.setInputNode(0, added_nodes[-1])
        script.addNode(dot)
        added_nodes.append(dot)

    elif trackDisconnected:
      added_nodes.extend( _addEffectsAnnotationsForTrack(track, includeEffects, includeAnnotations, script, offset, inputs=0, cliptype=effectsClipType) )

    # Store the last node added to this track
    if added_nodes:
      lastTrackNodeDict[track] = added_nodes[-1]

    script.popLayoutContext()

  # Now iterate over the tracks in order, writing merges and their soft effects
  previousTrack = None
  for track in tracks:
    if previousTrack:
      # If we have a previous track, we will be creating a Merge node. In this case we don't want to
      # use the Track's Layout context, since Merges representing track blends should be on their own.
      script.pushLayoutContext("merge", "Merge " + previousTrack.name() + " " + track.name(), track=previousTrack)
    else:
      script.pushLayoutContext("track", track.name(), track=track)

    trackDisconnected = track in disconnectedTracks

    if not trackDisconnected and previousTrack:
      # We need a merge if this track contains any clips, if it's the first track it will go over
      # the background Constant node added above
      #
      # If blending is enabled, a Merge node is created, otherwise Copy.
      if track in tracksWithVideo:
        if track.isBlendEnabled():
          merge = nuke.MergeNode()
          blendMode = track.blendMode()
          merge.setKnob('operation', blendMode )
          if track.isBlendMaskEnabled() :
            # set the mask input to use the "A" channel instead of the "B" default
            inputAId = 1 + 1 # input 'A' is has 0-based index '1' (2nd input) plus the offset for the 'none' entry
            merge.setKnob('maskProviderInput', inputAId) # set by ID instead of string because the enum knob requires fromScript() to parse strings
            merge.setKnob("maskChannelInput", "alpha" ) # set the mask to use the upstream alpha channel - use string as the ChannelKnob supports it
        else:
          merge = nuke.CopyNode()
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

        script.addNode(merge)
        added_nodes.append(merge)

      # If there were no clips on the track, write the effects and annotations after the merge so they get applied to the tracks below
      else:
        added_nodes.extend( _addEffectsAnnotationsForTrack(track, includeEffects, includeAnnotations, script, offset, cliptype=effectsClipType) )

    script.popLayoutContext()

    previousTrack = track

  # If an output format is specified, add a reformat node at the end.  Put this in the layout of the last connected track
  if outputToFormat:
    script.pushLayoutContext("track", connectedTracks[-1].name())
    added_nodes.append( outputToFormat.addToNukeScript(script, resize=nuke.ReformatNode.kResizeNone, black_outside=False) )
    script.popLayoutContext()

  perSequenceNodes = []
  if callable(additionalNodesCallback):
    perSequenceNodes.extend(additionalNodesCallback(self))

  # Add any additional nodes.
  for node in perSequenceNodes:
    if node is not None:
      added_nodes.append(node)
      script.addNode(node)

  # Add crop node with Sequence Format parameters
#  format = self.format()
#  crop = nuke.Node("Crop", box=('{0 0 %i %i}' % (format.width(), format.height())),  reformat='true' )
#  script.addNode(crop)
#  added_nodes.append(crop)

  return added_nodes

Sequence.addToNukeScript = _Sequence_addToNukeScript


def  _Format_addToNukeScript(self, script=None, resize=nuke.ReformatNode.kResizeWidth, black_outside=True):
  """self.addToNukeScript(self, script, to_type) -> adds a Reformat node matching this Format to the specified script and returns the nuke node object. \
  \
  @param script: Nuke script object to add nodes to, or None to just generate and return the node. \
  @param resize: Type of resize (use constants from nuke.ReformatNode, default is kResizeWidth). \
  @parm black_outside: Value for the black_outside knob. \
  @return: hiero.core.nuke.ReformatNode object
  """
  #Build the string representing the reformat
  formatstring = str(self)
  #Add Reformat node to script
  reformatNode = nuke.ReformatNode(resize=resize, to_type=nuke.ReformatNode.kToFormat, format=formatstring, pbb=True, black_outside=black_outside)
  if script is not None:
    script.addNode(reformatNode)

  return reformatNode

Format.addToNukeScript = _Format_addToNukeScript


def _Annotation_addToNukeScript(self, script, offset=0, inputs=0, cliptype=None):
  added_nodes = []

  # Add all the elements
  # Stroke elements can all be added in one RotoPaint node.
  # Each text element must use a separate Text node.
  # TODO Do we need to consider the ordering?

  # Use the start/end frames as the lifetime for the node
  startFrame = self.timelineIn() + offset
  endFrame = self.timelineOut() + offset

  knobSettings = {}
  knobSettings['inputs'] = inputs
  knobSettings['lifetimeStart'] = startFrame
  knobSettings['lifetimeEnd'] = endFrame
  knobSettings['useLifetime'] = "true"

  # Set the cliptype knob if specified
  if cliptype:
    knobSettings['cliptype'] = cliptype

  # Set the disabled knob if the annotation is disabled on the timeline
  if not self.isEnabled():
    knobSettings["disable"] = "true"

  strokes = []
  for element in self.elements():
    if isinstance(element, AnnotationText):
      added_nodes.extend( _AnnotationText_addToNukeScript(element, script, **knobSettings) )
      inputs = 1 # Once we've added a node, any following should take their input from it
    elif isinstance(element, AnnotationStroke):
      strokes.append( element )
    else:
      assert False

  if strokes:
    added_nodes.extend( _AnnotationStrokes_addToNukeScript(strokes, script, **knobSettings) )

  return added_nodes

Annotation.addToNukeScript = _Annotation_addToNukeScript


# Map from the text justify enum values to the strings used on the xjustify and yjustify knobs
_hJustifyTable = { AnnotationText.eHLeft : "left", AnnotationText.eHCenter : "center", AnnotationText.eHRight : "right", AnnotationText.eHJustify : "justify" }
_vJustifyTable = { AnnotationText.eVBaseline : "baseline", AnnotationText.eVTop : "top", AnnotationText.eVCenter : "center", AnnotationText.eVBottom : "bottom" }

# Annotations use a fixed font which is bundled with the application.  In the Text node, use a Python expression to determine the correct path.
# This works because the font file should always be in the same location relative to the executable.
_defaultFontExpression = "\\[python \\{os.path.split( nuke.env.get('ExecutablePath') )\\[0] + '/plugins/fonts/UtopiaRegular.pfa'\\}]"

def _AnnotationText_addToNukeScript(self, script, **knobs):
  added_nodes = []

  box = self.box()
  center = (box[0] + (box[2]/2), box[1] + (box[3]/2))

  r, g, b, a = self.color()

  textNode = nuke.Node("Text",
    message = self.text(),
    box = "{%s %s %s %s}" % (box[0], box[1], box[0]+box[2], box[1]+box[3]),
    font = _defaultFontExpression,
    color = "{%s %s %s 1}" % (r, g, b), # Alpha value is set on the opacity knob rather than color
    opacity = a,
    xjustify = _hJustifyTable[self.horizontalJustification()],
    yjustify = _vJustifyTable[self.verticalJustification()],
    size = self.fontSize(),
    rotate = self.rotation(),
    center = "{%s %s}" % (center), # Need to set the center point for rotation
    **knobs
    )

  added_nodes.append( textNode )

  if script:
    script.addNode( textNode )

  return added_nodes


def _AnnotationStroke_writeCurveStr(stroke, curve_id):
  """ Write out a stroke as a curve in the form expected by the RotoPaint node.
  Receives a stroke and the curve id (should be an integer)"""
  color  = stroke.color()
  # defines the curve's name.
  curve_name = "Brush" + str(curve_id)
  curveStr = (
      "{cubiccurve \"" + curve_name + "\" 512 catmullrom"
     "\n{cc"
      "\n{f 2080}"

      # Stringify each point and join them into the curve string.
      "\n{p\n" + "\n".join( ["{%s %s 1}" % (x, y) for x, y in stroke.points()] ) + "}}"

     "\n{t 0}"

     # Write the line width and color.  Note that the alpha is written as opc (opacity)
     "\n{ a bs %s h 0.9 r %s g %s b %s a 1 opc %s }}" % (stroke.lineWidth(), color[0], color[1], color[2], color[3])
     )
  return curveStr


def _AnnotationStrokes_addToNukeScript(strokes, script, **knobs):
  # Write all the strokes as curves in a RotoPaint node
  rotoNode = nuke.Node("RotoPaint", **knobs)

  # The start of a curves knob.  I don't know what all these values are for, but it's what Nuke
  # writes out.
  curvesKnob = ("{{{v x3f99999a}"
   "\n{f 0}"
   "\n{n"
   "\n{layer Root"
   "\n{a}\n"
   )

  # Use a list comprehension to write out each stroke as a curve and join them together into a single string
  # Use the list index to name each curve with a different name 'Brush1, Brush2, ...'
  curvesKnob = curvesKnob + "\n".join( [ _AnnotationStroke_writeCurveStr(stroke, index + 1) for index,stroke in enumerate(strokes) ] ) + "}}}}"
  rotoNode.setKnob("curves", curvesKnob)
  if script:
    script.addNode(rotoNode)
  return [rotoNode]


def offsetNodeAnimationFrames(node, offset):
  """ Iterate over all the knobs in a Nuke node, offsetting the key frame numbers. """

  if offset == 0:
    return

  isTimeWarp = node.Class() == "TimeWarp"
  for knob in list(node.knobs().values()):

    # Some knobs can have isAnimated True, but not actually have an animations() method.
    # This happens if the user chooses if for example 'Set key on all knobs'.
    # Swallow any exceptions that occur due to these issues.
    try:
      # If this is a link knob, need to modify the knob being linked to
      if isinstance(knob, _nuke.Link_Knob):
        knob = knob.getLinkedKnob()

      if knob.isAnimated():
        for curve in knob.animations():
          for key in list(curve.keys()):
            key.x = key.x + offset
            if isTimeWarp and knob.name() == "lookup":
              # time warp maps input frames to output so we need to adjust both the x and y curves
              key.y = key.y + offset
    except:
      pass


def _EffectTrackItem_addToNukeScript(self, script, offset=0, inputs=1, cliptype=None, startHandle=0, endHandle=0, addLifetime=True):
  # Write an EffectTrackItem to the script.  We can access the Nuke node, so we just need
  # to write that out, plus any additional knobs that need to be added.

  node = self.node()

  # Apply the offset to all the Node's animations
  offsetNodeAnimationFrames(node, offset)

  # Any additional knobs we want in the script.  These are added as raw lines of text
  additionalKnobs = []

  # Set the lifetime knobs to disable the node outside the desired frame range.  Handles should be included
  startFrame = self.timelineIn() + offset - startHandle
  endFrame = self.timelineOut() + offset + endHandle

  if addLifetime:
    additionalKnobs.append( "lifetimeStart %s" % startFrame )
    additionalKnobs.append( "lifetimeEnd %s" % endFrame )
    additionalKnobs.append( "useLifetime true" )

  # Set the inputs knob
  additionalKnobs.append( "inputs %s" % inputs )

  # Set disabled knob if the effect is disabled on the timeline
  if not self.isEnabled():
    additionalKnobs.append( "disable true" )

  # If cliptype is specified and the node has a cliptype knob, set its value
  cliptypeKnob = node.knob("cliptype")
  if cliptype and cliptypeKnob:
    cliptypeKnob.setValue(cliptype)

  nodeStr = node.Class() + " {\n" + node.writeKnobs(_nuke.TO_SCRIPT) + "\n" + "\n".join(additionalKnobs) + "\n}"

  scriptNode = nuke.UserDefinedNode(nodeStr)

  added_nodes = []
  added_nodes.append( scriptNode )
  if script:
    script.addNode(added_nodes)

  # Reverse the offset, since the effect might be included in the export for multiple shots
  offsetNodeAnimationFrames(node, -offset)

  return added_nodes


EffectTrackItem.addToNukeScript = _EffectTrackItem_addToNukeScript


def _EffectTrackItem_isRetimeEffect(self):
  """ Check if an EffectTrackItem applies a retime.  Currently this only applies to TimeWarp effects. """
  return self.node().Class() == "TimeWarp"

EffectTrackItem.isRetimeEffect = _EffectTrackItem_isRetimeEffect

