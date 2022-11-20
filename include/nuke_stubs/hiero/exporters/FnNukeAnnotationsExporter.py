import hiero.core
import hiero.core.nuke as nuke
import itertools

from .FnNukeShotExporter import NukeShotPreset, NukeShotExporter
from hiero.core.FnNukeHelpers import getConnectedDisconnectedTracks

"""
Exporter for supporting export of annotations in a separate script.

This is mostly a wrapper around the regular NukeShotExporter with a bit of specialised behaviour.
"""

class NukeAnnotationsExporter(NukeShotExporter):
  def __init__(self, initDict):

    # To simplify determining where the annotation keyframes should be placed, don't add cut handles for annotations exports
    if initDict[hiero.core.TaskData.kCutHandles]:
      initDict[hiero.core.TaskData.kCutHandles] = 0

    NukeShotExporter.__init__(self, initDict)


  def updateItem(self, originalItem, localtime):

    # The tag should be added by the main export task.  We don't want to add two of them, so
    # look it up and add the path to the annotations script to the tag's metadata.
    existingTag = None
    for tag in originalItem.tags():
      if tag.metadata().hasKey("tag.presetid") and tag.metadata()["tag.presetid"] == self._presetId:
        existingTag = tag
        break

    if existingTag:
      existingTag.metadata().setValue("tag.scriptannotations", self.resolvedExportPath())


  def getAnnotationKeyFramesForTrackItem(self, trackItem, offset, toSequenceTime):
    """ Get the annotation key frames for the track item's clip.  This is modified by offset and
        mapped to sequence time if required. """
    keyFrames = set()

    clip = trackItem.source()

    # Get the list of annotations from the clip, only including ones which are in the track item's source range
    annotations = [ item for item in itertools.chain( *itertools.chain(*clip.subTrackItems()) ) if isinstance(item, hiero.core.Annotation)
                                                                                                and item.timelineOut() >= trackItem.sourceIn()
                                                                                                and item.timelineIn() < trackItem.sourceOut() ]

    for annotation in annotations:
      time = annotation.timelineIn()

      # Map to sequence time.  If the mapped annotation start time is before the track item timeline in, use the track item's timeline in
      if toSequenceTime:
        time = max(int(trackItem.mapSourceToTimeline(time)), trackItem.timelineIn())

      keyFrames.add( time + offset )

    return keyFrames


  def getSequenceAnnotationsKeyFrames(self):
    """ If a sequence is being exported, returns keyframes for annotations on tracks which will be connected. """
    keyFrames = set()

    # When building a collated sequence, everything is offset by 1000
    # This gives head room for shots which may go negative when transposed to a
    # custom start frame. This offset is negated during script generation.
    offset = -NukeShotExporter.kCollatedSequenceFrameOffset if self._collate else 0

    # Get the list of connected tracks for the sequence
    connectedTracks, disconnectedTracks = getConnectedDisconnectedTracks(self._sequence, self._masterTrackItemCopy.parent(),
                                                                          self.writingSequenceDisconnected(), True, True)

    for track in connectedTracks:
      # Add clip-level annotations for each item on the track
      for item in list(track.items()):
        keyFrames.update( self.getAnnotationKeyFramesForTrackItem(item, offset, True) )

      # Add sequence-level annotations
      trackAnnotations = [ item for item in itertools.chain(*track.subTrackItems()) if isinstance(item, hiero.core.Annotation) ]
      for annotation in trackAnnotations:
        keyFrames.add( annotation.timelineIn() + offset )

    return keyFrames


  def getTrackItemAnnotationsKeyFrames(self):
    """ If a single track item is being exported, returns keyframes for the annotations on the item's clip,
        plus any above it on the sequence which are being included. """
    keyFrames = set()

    # Determine the start frame, the frame numbers need to be offset by this
    start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)

    # Get the keyframes from the track item's clip
    trackItem = self._item

    fullClipLength = self._cutHandles is None

    toSequenceTime = self.outputSequenceTime()
    if toSequenceTime:
      clipAnnotationsOffset = 0
    elif self._startFrame:
      if fullClipLength:
        clipAnnotationsOffset = self._startFrame
      else:
        clipAnnotationsOffset = self._startFrame - trackItem.sourceIn()
    else:
      clipAnnotationsOffset = trackItem.source().sourceIn()

    keyFrames.update( self.getAnnotationKeyFramesForTrackItem(trackItem, clipAnnotationsOffset, toSequenceTime) )

    # Add sequence-level annotations.  The times are offset to the start of the track item plus the first frame offset
    sequenceToTrackItemOffset = start - trackItem.timelineIn()

    if fullClipLength:
      sequenceToTrackItemOffset += trackItem.sourceIn()

    for annotation in self._annotations:
      # The annotation might start before the track item timeline in, in which case the key frame should be the track item timeline in
      time = max(annotation.timelineIn(), trackItem.timelineIn())

      keyFrames.add( time + sequenceToTrackItemOffset )

    return keyFrames


  def getAnnotationsKeyFrames(self):
    """ Get the list of annotations keyframes for the current export. """

    keyFrames = set()

    if self.writingSequence():
      keyFrames = self.getSequenceAnnotationsKeyFrames()
    else:
      keyFrames = self.getTrackItemAnnotationsKeyFrames()

    return sorted(keyFrames)


  def _beforeNukeScriptWrite(self, script):
    """ Add a node containing keyframes for the location of the exported annotations.  These are linked from the annotations Precomp in the main script. """

    annotationsNoOp = nuke.Node("NoOp", name="AnnotationsKeys")

    # Set up the user knobs
    annotationsNoOp.addTabKnob("Annotations")
    annotationsNoOp.addRawKnob('addUserKnob {3 annotation_key l annotation -STARTLINE}')
    annotationsNoOp.addRawKnob('addUserKnob {3 annotation_count l of -STARTLINE}')
    annotationsNoOp.addRawKnob('addUserKnob {22 prev l @KeyLeft -STARTLINE T "k = nuke.thisNode()\[\'annotation_key\']\\ncurFrame = nuke.frame()  \\nnewFrame = curFrame\\ncurve = k.animation(0)\\nfor key in reversed(curve.keys()):\\n  if key.x < curFrame:\\n    newFrame = key.x\\n    break\\nnuke.frame( newFrame )\\n"}')
    annotationsNoOp.addRawKnob('addUserKnob {22 next l @KeyRight -STARTLINE T "k = nuke.thisNode()\[\'annotation_key\']\\ncurFrame = nuke.frame()  \\nnewFrame = curFrame\\ncurve = k.animation(0)\\nfor key in curve.keys():\\n  if key.x > curFrame:\\n    newFrame = key.x\\n    break\\nnuke.frame( newFrame )\\n"}')

    # Get all the key frame locations, and add them as keys to the annotation_key knob.
    annotationKeyFrames = self.getAnnotationsKeyFrames()
    if annotationKeyFrames:
      annotationKeysStr = ''.join( [ " x%s %s" % (frame, index + 1) for index, frame in enumerate(annotationKeyFrames) ] )
      annotationsNoOp.addRawKnob('annotation_key {{curve %s}}' % annotationKeysStr)
      annotationsNoOp.addRawKnob('annotation_count %s' % len(annotationKeyFrames))

    script.addNode(annotationsNoOp)


class NukeAnnotationsPreset(NukeShotPreset):

  def __init__(self, name, properties):
    NukeShotPreset.__init__(self, name, properties, task=NukeAnnotationsExporter)

    properties = self.properties()

    # Force these properties to True
    properties["includeAnnotations"] = True
    properties["showAnnotations"] = True



hiero.core.taskRegistry.registerTask(NukeAnnotationsPreset, NukeAnnotationsExporter)
