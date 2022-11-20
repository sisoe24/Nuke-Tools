# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import tempfile
import re
import sys
import math
import traceback
import copy
from PySide2.QtGui import QColor

import hiero.core
import hiero.core.log as log
import hiero.core.nuke as nuke

from . import FnAudioConstants
from . import FnAudioHelper
from . import FnShotExporter
from . import FnExternalRender
from . import FnEffectHelpers
from . import FnScriptLayout
import hiero.core.FnNukeHelpersV2 as FnNukeHelpersV2
from .FnSubmission import Submission
from .FnReformatHelpers import reformatNodeFromPreset
from . FnExportUtil import (trackItemTimeCodeNodeStartFrame,
                            TrackItemExportScriptWriter,
                            writeSequenceAudioWithHandles,
                            createViewerNode)


def _findMultiViewTrackItems(views, mainTrackItem):
  """ For multi-view projects, if the given track item is on a track which
  outputs to a single view, try to find the corresponding items on other tracks
  so they can be included in the exported script. Returns a list of found views,
  and the found TrackItems, including the original
  """
  mainTrack = mainTrackItem.parent()
  sequence = mainTrack.parent()

  # Helper for finding a matching track item for a particular view
  def _findItemForView(view):
    for track in sequence.videoTracks():
      if track.view() == view:
        for trackItem in track:
          # For the moment, match only if using the same clip and the timing is
          # the same. This may become more sophisticated
          matches = (trackItem.timelineIn() == mainTrackItem.timelineIn()
                      and trackItem.source() == mainTrackItem.source())
          if matches:
            return trackItem

  foundViews = []
  foundItems = []
  for view in views:
    trackItem = _findItemForView(view)
    if trackItem:
      foundViews.append(view)
      foundItems.append(trackItem)
  return foundViews, foundItems


class TranscodeExporter(FnExternalRender.NukeRenderTask):
  def __init__(self, initDict):
    """Initialize"""
    FnExternalRender.NukeRenderTask.__init__(self, initDict )

    self._audioFile  = None

    # When transcoding shots with %v in paths, there may be items on different
    # tracks for each view. _detemineSourceViews() builds the list if necessary
    self._multiViewTrackItems = []
    self._determineSourceViews()

    # Figure out the script location
    path = self.resolvedExportPath()
    dirname, filename = os.path.split(path)
    root, ext = os.path.splitext(filename)

    # Remove any trailing .#### or %0?d characters.  This should only be done to the filename part of the path,
    # otherwise the directory can end up being different to where the transcodes are placed.
    #
    # We might want to disallow these characters from dir names at some other time, but if we do that would be handled
    # in resolvedExportPath().
    percentmatch = re.search("%\d+d", root)
    if percentmatch:
      percentpad = percentmatch.group()
      root = root.replace(percentpad, '')

    # Join the dir and root.  Note that os.path.join is not used here because it introduces backslashes on Windows,
    # which is bad if they get written into a Nuke script
    self._root = dirname + "/" + root.rstrip('#').rstrip('.')

    # If the path contains view placeholders, use the first view as the directory
    # for the script
    if hiero.core.util.isMultiViewPath(self._root):
      self._root = hiero.core.util.formatMultiViewPath(self._root, self.views()[0])

    if hiero.core.isNC():
      scriptExtension = ".nknc"
    elif hiero.core.isIndie():
      scriptExtension = ".nkind"
    else:
      scriptExtension = ".nk"
    self._scriptfile = self._root + scriptExtension

    log.debug( "TranscodeExporter writing script to %s", self._scriptfile )

    self._renderTask = None
    if self._submission is not None:

      # Pass the frame range through to the submission.  This is useful for rendering through the frame
      # server, otherwise it would have to evaluate the script to determine it.
      start, end = self.outputRange()
      submissionDict = copy.copy(initDict)
      submissionDict["startFrame"] = start
      submissionDict["endFrame"] = end

      # Create a job on our submission to do the actual rendering.
      self._renderTask = self._submission.addJob( Submission.kNukeRender, submissionDict, self._scriptfile )

  def updateItem (self, originalItem, localtime):
    """updateItem - This is called by the processor prior to taskStart, crucially on the main thread.\n
      This gives the task an opportunity to modify the original item on the main thread, rather than the clone."""

    timestamp = self.timeStampString(localtime)
    tagName = str("Transcode {0} {1}").format(self._preset.properties()["file_type"], timestamp)
    tag = hiero.core.Tag(tagName, "icons:Nuke.png", False)

    tag.metadata().setValue("tag.pathtemplate", self._exportPath)
    tag.metadata().setValue("tag.description", "Transcode " + self._preset.properties()["file_type"])

    tag.metadata().setValue("tag.path", self.resolvedExportPath())
    tag.metadata().setValue("tag.localtime", str(localtime))

    # No point in adding script path if we're not planning on keeping the script
    if self._preset.properties()["keepNukeScript"]:
      tag.metadata().setValue("tag.script", self._scriptfile)

    start, end = self.outputRange()
    tag.metadata().setValue("tag.startframe", str(start))
    tag.metadata().setValue("tag.duration", str(end-start+1))
    
    frameoffset = self._startFrame if self._startFrame else 0
    if hiero.core.isVideoFileExtension(os.path.splitext(self.resolvedExportPath())[1].lower()):
      frameoffset = 0
    tag.metadata().setValue("tag.frameoffset", str(frameoffset))

    # Note: if exporting without cut handles, i.e. the whole clip, we do not try to determine  the handle values,
    # just writing zeroes.  The build track classes need to treat this as a special case.
    # There is an interesting 'feature' of how tags work which means that if you create a Tag with a certain name,
    # the code tries to find a previously created instance with that name, which has any metadata keys that were set before.
    # This means that when multiple shots are being exported, they inherit the tag from the previous one.  To avoid problems
    # always set these keys.
    startHandle, endHandle = 0, 0
    if self._cutHandles:
      startHandle, endHandle = self.outputHandles()

    tag.metadata().setValue("tag.starthandle", str(startHandle))
    tag.metadata().setValue("tag.endhandle", str(endHandle))

    # Store if retimes were applied in the export.  Note that if self._cutHandles
    # is None, we are exporting the full clip and retimes are never applied whatever the
    # value of self._retime
    applyingRetime = (self._retime and self._cutHandles is not None)
    appliedRetimesStr = "1" if applyingRetime else "0"
    tag.metadata().setValue("tag.appliedretimes", appliedRetimesStr)

    originalItem.addTag(tag)


  def validate(self):
    super(TranscodeExporter, self).validate()

    # Check that any clips in use for this task can be transcoded. If any are in
    # error state, will throw an exception
    clips = set()
    if isinstance(self._item, hiero.core.Clip):
      clips.add(self._item)
    elif isinstance(self._item, hiero.core.TrackItem):
      clips.add(self._item.source())
    elif isinstance(self._item, hiero.core.Sequence):
      for track in self._item.videoTracks():
        for trackItem in track:
          clips.add(trackItem.source())
    # Find clips which have an error. If they have no media, don't treat that as 
    # an error, as it can be handled.
    errorClips = [clip.name() for clip in clips if clip.mediaSource().isMediaPresent() and clip.hasError()]
    if errorClips:
      raise RuntimeError("Unable to transcode, some clips being transcoded are in "
        "error state (perhaps colorspace is invalid):\n" + "\n".join(errorClips))


  def writeAudio(self):
    if isinstance(self._item, (hiero.core.Sequence, hiero.core.TrackItem)):
      if self._sequenceHasAudio(self._sequence):

        self.setAudioExportSettings()

        if isinstance(self._item, hiero.core.Sequence):
          start, end = self.outputRange()
          self._item.writeAudioToFile(self._audioFile, 
                                      start, 
                                      end, 
                                      self._outputChannels,
                                      self._sampleRate,
                                      self._bitDepth,
                                      self._bitRate)

        elif isinstance(self._item, hiero.core.TrackItem):
          # Write out the audio covering the range of the track item,
          # including handles
          startHandle, endHandle = self.outputHandles()
          writeSequenceAudioWithHandles(self._audioFile,
                                        self._sequence,
                                        self._item.timelineIn(),
                                        self._item.timelineOut(),
                                        startHandle,
                                        endHandle,
                                        self._outputChannels,
                                        self._sampleRate,
                                        self._bitDepth,
                                        self._bitRate)

    if isinstance(self._item, hiero.core.Clip):
      if self._item.mediaSource().hasAudio():

        self.setAudioExportSettings()

        # If clip, write out full length
        self._item.writeAudioToFile(self._audioFile,
                                    self._outputChannels,
                                    self._sampleRate,
                                    self._bitDepth,
                                    self._bitRate)

  def startTask(self):
    try:
      # Call base start task.
      FnExternalRender.NukeRenderTask.startTask(self)

      # Write out the audio bounce down
      if self._preset.includeAudio():
        self.writeAudio()

      # Write our Nuke script
      self.buildScript()
      self.writeScript()

      # Start the render task if we have one
      if self._renderTask:
        self._renderTask.startTask()
        if self._renderTask.error():
          self.setError( self._renderTask.error() )
    except Exception as e:
      if self._renderTask and self._renderTask.error():
        self.setError( self._renderTask.error() )
      else:
        self.setError( "Error starting transcode\n\n%s" % str(e) )
        exc_type, exc_value, exc_traceback = sys.exc_info()
        hiero.core.log.exception("TranscodeExporter.startTask")

  def cleanupAudio(self):
    # Delete generated audio file if it was being written into a MOV
    if self._audioFile and self._preset.deleteAudioOnFinished():
      self.deleteTemporaryFile( self._audioFile )

  def finishTask(self):
    # Finish the render task if we have one
    if self._renderTask:
      self._renderTask.finishTask()
    FnExternalRender.NukeRenderTask.finishTask(self)
    self.cleanupAudio()

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


  def createPresetReformatNode(self):
    """ If reformat options are selected on the preset, create a ReformatNode.  Otherwise returns None. """
    try:
      seqFormat = self._sequence.format() if self._sequence else None
      trackItem = self._item if isinstance(self._item, hiero.core.TrackItem) else None
      return reformatNodeFromPreset(self._preset, seqFormat, trackItem=trackItem)
    except Exception as e:
      self.setError(str(e))

  def makeRootNode(self, start, end, fps):
    rootNode = nuke.RootNode(start, end, fps,
                             showAnnotations=self.includeAnnotations())
    rootNode.setKnob("project_directory", os.path.split(self.resolvedExportPath())[0])
    rootNode.addProjectSettings(self._projectSettings)

    # Set the views knobs. Colors don't matter in this context
    viewsAndColors = [(view, QColor('#000000')) for view in self.views()]
    rootNode.setViewsConfiguration(viewsAndColors)

    return rootNode

  def writeSequenceToScript(self, script):
    """ When exporting a Sequence, write it to a script.
    """

    # Get the range to set on the Root node. This is the range the nuke script will render by default.
    start, end = self.outputRange()
    log.debug( "TranscodeExporter: rootNode range is %s %s", start, end )

    framerate = self._sequence.framerate()
    dropFrames = self._sequence.dropFrame()
    fps = framerate.toFloat()
    rootNode = self.makeRootNode(start, end, fps)
    script.addNode(rootNode)

    # Add Unconnected additional nodes
    if self._preset.properties()["additionalNodesEnabled"]:
      script.addNode(FnExternalRender.createAdditionalNodes(FnExternalRender.kUnconnected, self._preset.properties()["additionalNodesData"], self._item))

    # Force track items to be reformatted to fit the sequence in this case
    reformatMethod = { "to_type" : nuke.ReformatNode.kCompReformatToSequence,
    "filter": self._preset.properties()["reformat"].get("filter")}

    # Build out the sequence.
    scriptParams = FnNukeHelpersV2.ScriptWriteParameters(includeAnnotations=self.includeAnnotations(),
                                                         includeEffects=self.includeEffects(),
                                                         retimeMethod=self._preset.properties()["method"],
                                                         reformatMethod=reformatMethod,
                                                         additionalNodesCallback=self._buildAdditionalNodes,
                                                         views=self.views())

    script.pushLayoutContext("sequence", self._sequence.name(), disconnected=False)
    sequenceWriter = FnNukeHelpersV2.SequenceScriptWriter(self._sequence, scriptParams)
    sequenceWriter.writeToScript(script,
                                 offset=0,
                                 skipOffline=self._skipOffline,
                                 mediaToSkip=self._mediaToSkip,
                                 disconnected=False,
                                 masterTracks=None,
                                 projectSettings=self._projectSettings)
    script.popLayoutContext()
    script.pushLayoutContext("write", "%s_Render" % self._item.name())

    # Create metadata node
    metadataNode = nuke.MetadataNode(metadatavalues=[("hiero/project", self._projectName), ("hiero/project_guid", self._project.guid())] )

    # Add sequence Tags to metadata
    metadataNode.addMetadataFromTags( self._sequence.tags() )

    # Apply timeline offset to nuke output
    script.addNode(nuke.AddTimeCodeNode(timecodeStart=self._sequence.timecodeStart(), fps=framerate, dropFrames=dropFrames, frame= 0 if self._startFrame is None else self._startFrame))

    # The AddTimeCode field will insert an integer framerate into the metadata, if the framerate is floating point, we need to correct this
    metadataNode.addMetadata([("input/frame_rate", framerate.toFloat())])

    # And next the Write.
    script.addNode(metadataNode)

    # Add Burnin group (if enabled)
    self.addBurninNodes(script)

    # Get the output format, either from the sequence or the preset,  and set it as the root format.
    # If a reformat is specified in the preset, add it immediately before the Write node.
    outputReformatNode = self._sequence.format().addToNukeScript(resize=nuke.ReformatNode.kResizeNone, black_outside=False)
    self._addReformatNode(script,rootNode,outputReformatNode)

    self.addWriteNodeToScript(script, rootNode, framerate)
    script.addNode(createViewerNode(self._projectSettings))
    script.popLayoutContext()

  def addWriteNodeToScript(self, script, rootNode, framerate):
    """ Build Write node from transcode settings and add it to the script. """
    try:
      writeNode = self.nukeWriteNode(framerate, project=self._project)
    except RuntimeError as e:
      # Failed to generate write node, set task error in export queue
      # Most likely because could not map default colourspace for format settings.
      self.setError(str(e))
      return

    # The 'read_all_lines' knob controls whether input frames are read line by line or in one go,
    # so needs to be set to match the readAllLinesForExport property.
    readAllLines = self._preset.properties()["readAllLinesForExport"]
    writeNode.setKnob("read_all_lines", readAllLines)

    if self._audioFile:
      # If the transcode format supports audio (e.g. QuickTime), add the path to
      # the audio file knob
      if self._preset.fileTypeSupportsAudio():
        writeNode.setKnob("audiofile", self._audioFile)
        presetproperties = self._preset.properties()
        filetype = presetproperties["file_type"]

    # Add Write node to the script
    script.addNode(writeNode)

    # Set the knob so the Root node has the name of the Write node for viewing
    # on the timeline.  This allows for reading the script as a comp clip
    rootNode.setKnob(nuke.RootNode.kTimelineWriteNodeKnobName, writeNode.knob("name"))


  def writeClipOrTrackItemToScript(self, script):
    """ When exporting a Clip or TrackItem, write it to a script.
    """
    isMovieContainerFormat = self._preset.properties()["file_type"] in ("mov", "mov64", "ffmpeg")

    start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)
    unclampedStart = start
    log.debug( "rootNode range is %s %s", start, end )

    firstFrame, lastFrame = start, end
    if self._startFrame is not None:
      firstFrame = self._startFrame

    # if startFrame is negative we can only assume this is intentional
    if start < 0 and (self._startFrame is None or self._startFrame >= 0) and not isMovieContainerFormat:
      # We dont want to export an image sequence with a negative frame numbers
      self.setWarning("%i Frames of handles will result in a negative frame index.\nFirst frame clamped to 0." % self._cutHandles)
      start = 0

    # The clip framerate may be invalid, if so, use parent sequence framerate
    fps, framerate, dropFrames = None, None, False
    if self._sequence:
      framerate = self._sequence.framerate()
      dropFrames = self._sequence.dropFrame()
    if self._clip.framerate().isValid():
      framerate = self._clip.framerate()
      dropFrames = self._clip.dropFrame()
    if framerate:
      fps = framerate.toFloat()

    # Create root node, this defines global frame range and framerate
    rootNode = self.makeRootNode(start, end, fps)
    script.addNode(rootNode)

    # Add Unconnected additional nodes
    if self._preset.properties()["additionalNodesEnabled"]:
      script.addNode(FnExternalRender.createAdditionalNodes(FnExternalRender.kUnconnected, self._preset.properties()["additionalNodesData"], self._item))

    # Stores nodes that must be applied after the reformat node.
    pendingNodesScript = nuke.ScriptWriter()

    # Now add the Read node.
    writingClip = isinstance(self._item, hiero.core.Clip)
    if writingClip:
      script.pushLayoutContext("clip", self._item.name())
      self._clip.addToNukeScript(script,
                                 additionalNodesCallback=self._buildAdditionalNodes,
                                 firstFrame=firstFrame,
                                 trimmed=True,
                                 includeEffects= self.includeEffects(),
                                 project = self._project) # _clip has no project set, but one is needed by addToNukeScript to do colorpsace conversions
      if self.includeAnnotations():
        self._clip.addAnnotationsToNukeScript(script, firstFrame=firstFrame, trimmed=True)
      script.popLayoutContext()
    else:
      # If there are separate track items for each view, write them out (in reverse
      # order so the inputs are correct) then add a JoinViews
      items = self._multiViewTrackItems if self._multiViewTrackItems else [self._item]
      for item in reversed(items):
        script.pushLayoutContext("clip", item.name())
        # Construct a TrackItemExportScriptWriter and write the track item
        trackItemWriter = TrackItemExportScriptWriter(item)
        trackItemWriter.setAdditionalNodesCallback(self._buildAdditionalNodes)
        # Find sequence level effects/annotations which apply to the track item.
        # Annotations are not currently included by the transcode exporter
        effects, annotations = FnEffectHelpers.findEffectsAnnotationsForTrackItems( [item] )
        trackItemWriter.setEffects(self.includeEffects(), effects)
        trackItemWriter.setAnnotations(self.includeAnnotations(), annotations)

        # TODO This is being done in both the NukeShotExporter and TranscodeExporter.
        # There should be fully shared code for doing the handles calculations.
        fullClipLength = (self._cutHandles is None)
        if fullClipLength:
          trackItemWriter.setOutputClipLength()
        else:
          trackItemWriter.setOutputHandles(*self.outputHandles())

        trackItemWriter.setIncludeRetimes(self._retime, self._preset.properties()["method"])
        trackItemWriter.setFirstFrame(firstFrame)
        trackItemWriter.writeToScript(script, pendingNodesScript)
        script.popLayoutContext()

      if self._multiViewTrackItems:
        joinViewsNode = nuke.Node("JoinViews", inputs=len(self.views()))
        script.addNode(joinViewsNode)

    script.pushLayoutContext("write", "%s_Render" % self._item.name())

    metadataNode = nuke.MetadataNode(metadatavalues=[("hiero/project", self._projectName), ("hiero/project_guid", self._project.guid())] )

    # Add sequence Tags to metadata
    metadataNode.addMetadataFromTags( self._clip.tags() )

    # Need a framerate inorder to create a timecode
    if framerate:
      # Apply timeline offset to nuke output
      if self._cutHandles is None:
        timeCodeNodeStartFrame = unclampedStart
      else:
        startHandle, endHandle = self.outputHandles()
        timeCodeNodeStartFrame = trackItemTimeCodeNodeStartFrame(unclampedStart, self._item, startHandle, endHandle)

      script.addNode(nuke.AddTimeCodeNode(timecodeStart=self._clip.timecodeStart(), fps=framerate, dropFrames=dropFrames, frame=timeCodeNodeStartFrame))

      # The AddTimeCode field will insert an integer framerate into the metadata, if the framerate is floating point, we need to correct this
      metadataNode.addMetadata([("input/frame_rate",framerate.toFloat())])

    script.addNode(metadataNode)

    # Add Burnin group (if enabled)
    self.addBurninNodes(script)

    # Get the output format, either from the clip or the preset,  and set it as the root format.
    # If a reformat is specified in the preset, add it immediately before the Write node.
    reformatNode = self._clip.format().addToNukeScript(None)
    self._addReformatNode(script,rootNode,reformatNode)

    # Apply pending nodes to the final script right after the reformat node.
    for pendingNode in pendingNodesScript.getNodes():
      script.addNode(pendingNode)

    self.addWriteNodeToScript(script, rootNode, framerate)
    script.addNode(createViewerNode(self._projectSettings))
    script.popLayoutContext()


  def buildScript (self):
    # Generate a nuke script to render.
    script = nuke.ScriptWriter()
    self._script = script

    writingTrackItem = isinstance(self._item, hiero.core.TrackItem)
    writingClip = isinstance(self._item, hiero.core.Clip)
    writingSequence = isinstance(self._item, hiero.core.Sequence)

    assert (writingTrackItem or writingClip or writingSequence)

    # Export an individual clip or track item
    if writingClip or writingTrackItem:
      self.writeClipOrTrackItemToScript(script)

    # Export an entire sequence
    elif writingSequence:
      self.writeSequenceToScript(script)

    # Layout the script
    FnScriptLayout.scriptLayout(script)

  # And finally, write out the script (next to the output files).
  def writeScript (self):
    self._script.writeToDisk(self._scriptfile)


  def includeEffects(self):
      """ Check if soft effects should be included in the export. """
      return self._preset.properties()["includeEffects"]

  def includeAnnotations(self):
      """ Check if annotations should be included in the export. """
      return self._preset.properties()["includeAnnotations"]

  def taskStep(self):
    # Call taskStep on our render task
    if self._renderTask:
      result = self._renderTask.taskStep()
      if self._renderTask.error():
        self.setError(self._renderTask.error())
      return result
    else:
      return False

  def forcedAbort(self):
    if self._renderTask:
      self._renderTask.forcedAbort()
    self.cleanupAudio()

  def progress(self):
    if self._renderTask:
      progress = self._renderTask.progress()
      if self._renderTask.error():
        self.setError(self._renderTask.error())
      return progress
    elif self._finished:
      return 1.0
    else:
      return 0.0

  def outputHandles ( self, ignoreRetimes = True):
    """ Override which does nothing except changing the default value of
    ignoreRetimes from False to True.  This is not good, but the code calling
    this method is currently depending on it.
    """
    return super(TranscodeExporter, self).outputHandles(ignoreRetimes)


  def outputRange(self, ignoreHandles=False, ignoreRetimes=True, clampToSource=True):
    """outputRange(self)
    Returns the output file range (as tuple) for this task, if applicable"""
    start = 0
    end  = 0
    if isinstance(self._item, (hiero.core.TrackItem, hiero.core.Clip)):
      # Get input frame range
      
      ignoreRetimes = self._preset.properties()["method"] != "None"
      start, end = self.inputRange(ignoreHandles=ignoreHandles, ignoreRetimes=ignoreRetimes, clampToSource=clampToSource)

      if self._retime and isinstance(self._item, hiero.core.TrackItem) and ignoreRetimes:
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


      # If the item is a TrackItem, and the task is configured to output to sequence time,
      # map the start and end into sequence time.
      if self.outputSequenceTime() and isinstance(self._item, hiero.core.TrackItem):
        offset = self._item.timelineIn() - int(self._item.sourceIn() + self._item.source().sourceIn())
        start = max(0, start + offset)
        end = end + offset

      # Offset by custom start time
      elif self._startFrame is not None:
        end = self._startFrame + (end - start)
        start = self._startFrame

    elif isinstance(self._item, hiero.core.Sequence):
      start, end = 0, self._item.duration() - 1

      try:
        start = self._item.inTime()
      except RuntimeError:
        # This is fine, no in time set
        pass

      try:
        end = self._item.outTime()
      except RuntimeError:
        # This is fine, no out time set
        pass

    return (start, end)

  def _addReformatNode(self, script=None, rootNode=None, reformatNode=None):
    """If the preset has a reformat node, and the knob "format" is set set the root as that knob.
    otherwise default to the clip/sequence format."""
    rootFormat = reformatNode.knob("format")
    presetReformatNode = self.createPresetReformatNode()
    if presetReformatNode:
      reformatNode = presetReformatNode
      script.addNode(reformatNode)
      if "format" in presetReformatNode.knobs():
        rootFormat = presetReformatNode.knob("format")

    rootNode.setKnob("format", rootFormat)

  def viewsFromSource(self):
    return self._sourceViews

  def _determineSourceViews(self):
    """ Figure out which views should be rendered based on the source
    sequence/clip/trackitem.
    """
    views = []
    if isinstance(self._item, hiero.core.TrackItem):
      track = self._item.parentTrack()
      views = self._project.views()
      # Note: Transcode tasks can be created for audio track items. They won't
      # actually get executed, but need to make sure this code is safe for them
      if isinstance(track, hiero.core.VideoTrack) and track.view():
        views, items = _findMultiViewTrackItems(views, self._item)
        self._multiViewTrackItems = items
    elif isinstance(self._item, hiero.core.Clip):
      views = self._item.views()
      if not views:
        views = ['main']
    else: #Sequence
      views = self._project.views()
    self._sourceViews = views

  def isExportingItem(self, item):
    """ Prevent duplicates when multiple multi-view track items have been included in a render """
    return item == self._item or item in self._multiViewTrackItems

  def setAudioExportSettings(self):
      extension = FnAudioConstants.kCodecs[self._preset.properties()[FnAudioConstants.kCodecKey]]
      self._audioFile = self._root + extension

      FnAudioHelper.setAudioExportSettings(self)

class TranscodePreset(hiero.core.RenderTaskPreset):
  def __init__(self, name, properties):
    hiero.core.RenderTaskPreset.__init__(self, TranscodeExporter, name, properties)

    # Set any preset defaults here
    self.properties()["keepNukeScript"] = False
    self.properties()["readAllLinesForExport"] = self._defaultReadAllLinesForCodec()
    self.properties()["useSingleSocket"] = False
    self.properties()["burninDataEnabled"] = False
    self.properties()["burninData"] = dict((datadict["knobName"], None) for datadict in FnExternalRender.NukeRenderTask.burninPropertyData)
    self.properties()["additionalNodesEnabled"] = False
    self.properties()["additionalNodesData"] = []
    self.properties()["method"] = "Blend"
    self.properties()["includeEffects"] = True
    self.properties()["includeAudio"] = False
    self.properties()["deleteAudio"] = True
    self.properties()["includeAnnotations"] = False

    FnAudioHelper.defineExportPresetProperties(self)

    # Give the Write node a name, so it can be referenced elsewhere
    if "writeNodeName" not in self.properties():
      self.properties()["writeNodeName"] = "Write_{ext}"

    self.properties().update(properties)

  def _defaultReadAllLinesForCodec(self):
    '''
    Return the default value for the read all lines property based on the current file type and codec.
    This will only return True for ProRes 4444 or ProRes 422 formats as read all lines might slow down other
    exports.
    '''
    readAllLines = False

    movDetails = self.properties()["mov"] if self.properties()["file_type"] == "mov" else None
    if movDetails:
      codecProfile = movDetails.get("mov_prores_codec_profile")
      if codecProfile:
        isProRes4444 = "4:4:4:4" in codecProfile
        isProRes422 = "4:2:2" in codecProfile
        readAllLines = isProRes4444 or isProRes422

    return readAllLines

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kAllItems

  def includeAudio(self):
    """ Check whether an audio file should be generated for the export. """
    return self.properties()["includeAudio"]

  def deleteAudioOnFinished(self):
    """ Check whether audio should be deleted when finished. """
    if self.deleteAudioValid():
      return self.properties()["deleteAudio"]
    else:
      return False

  def deleteAudioValid(self):
    """ Check if the delete audio option is valid for the current configuration. """
    return (self.includeAudio() and self.fileTypeSupportsAudio())

  def fileTypeSupportsAudio(self):
    """ Check if the selected file type supports audio tracks. This currently
    only works for files being written with the the mov writer.
    """
    return self.properties()["file_type"] in ("mov", "mov64", "ffmpeg")

hiero.core.taskRegistry.registerTask(TranscodePreset, TranscodeExporter)
