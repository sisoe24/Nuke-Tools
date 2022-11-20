import itertools
import json
import traceback
from PySide2.QtCore import QTimer
import hiero.core
import hiero.ui
from hiero.core import (events, Annotation, Clip, Sequence)
from hiero.core.util import (asBytes, asUnicode)
from . import messages
from . log import logMessage
from . synctool import SyncTool


messages.defineMessageType('AnnotationAdd', ('sequenceGuid', str), ('subTrack', int), ('annotation', messages.Compressed))
messages.defineMessageType('AnnotationChange', ('sequenceGuid', str), ('annotationGuid', str), ('annotation', messages.Compressed))
messages.defineMessageType('AnnotationRemove', ('sequenceGuid', str), ('annotationGuid', str))

def _findAnnotation(sequenceGuid, annotationGuid):
  """ Find an annotation on a clip/sequence by guid """
  sequence = hiero.core.findItemByGuid(sequenceGuid, filter=(Clip, Sequence))
  if not sequence:
   logMessage("findAnnotation sequence not found {}".format(sequenceGuid))
   return None

  track = sequence.getAnnotationsTrack()
  annotation =  next((i for i in itertools.chain(*track.subTrackItems()) if i.guid() == annotationGuid), None)
  if not annotation:
    logMessage("findAnnotation annotation not found {}".format(annotationGuid))
  return annotation

class SyncAnnotationsTool(SyncTool):
  """ Tool for syncing annotations in the viewer. This receives callbacks from
  the annotations tool, and syncs them across the session
  """
  def __init__(self, messageDispatcher):
    super(SyncAnnotationsTool, self).__init__(messageDispatcher)

    self.registerEventCallback(events.EventType.kAnnotationChanged, self.onLocalAnnotationChange)

    self.messageDispatcher._registerCallback(messages.AnnotationAdd, self.onRemoteAnnotationAdded)
    self.messageDispatcher._registerCallback(messages.AnnotationChange, self.onRemoteAnnotationChanged)
    self.messageDispatcher._registerCallback(messages.AnnotationRemove, self.onRemoteAnnotationRemoved)

  def onLocalAnnotationChange(self, event):
    """ Callback when a local annotation is added/removed/edited """
    if event.change == 'added':
      self.onLocalAnnotationAdded(event.annotation)
    elif event.change == 'edited':
      self.onLocalAnnotationChanged(event.annotation)
    elif event.change == 'removed':
      self.onLocalAnnotationRemoved(event.annotation)
    else:
      logMessage('Unexpected annotation change {}'.format(event.change))

  def onLocalAnnotationAdded(self, annotation):
    """ Local annotation added, send message to remotes to create it there """
    msg = messages.AnnotationAdd(
                        sequenceGuid=annotation.parentSequence().guid(),
                        subTrack=annotation.subTrackIndex(),
                        annotation=asBytes(annotation.serialize()))
    self.messageDispatcher.sendMessage(msg)

  def onLocalAnnotationChanged(self, annotation):
    """ Local annotation edited, send message to remotes to create it there """
    msg = messages.AnnotationChange(
                        sequenceGuid=annotation.parentSequence().guid(),
                        annotationGuid=annotation.guid(),
                        annotation=asBytes(annotation.serialize()))
    self.messageDispatcher.sendMessage(msg)

  def onLocalAnnotationRemoved(self, annotation):
    """ Local annotation removed, send message to remotes to remove it there """
    msg = messages.AnnotationRemove(
                        sequenceGuid=annotation.parentSequence().guid(),
                        annotationGuid=annotation.guid())
    self.messageDispatcher.sendMessage(msg)


  def onRemoteAnnotationAdded(self, msg):
    """ Handle message to create an annotation """
    sequence = hiero.core.findItemByGuid(msg.sequenceGuid, filter=(Clip, Sequence))
    if not sequence:
      logMessage("onRemoteAnnotationAdded: sequence {} not found!".format(msg.sequenceGuid))
      return
    annotation = Annotation()
    annotation.deserialize(asUnicode(msg.annotation))
    track = sequence.getAnnotationsTrack()
    track.addSubTrackItem(annotation, msg.subTrack)
    hiero.ui.currentViewer().window().update()

  def onRemoteAnnotationChanged(self, msg):
    """ Handle message to change an annotation. Note that right now, the whole
    annotation is being rebuilt. This should be ok, there's not a huge amount
    of data being sent, but if necessary we could just send e.g. individual points
    being added to a stroke
    """
    annotation = _findAnnotation(msg.sequenceGuid, msg.annotationGuid)
    if annotation:
      annotation.deserialize(asUnicode(msg.annotation))
      hiero.ui.currentViewer().window().update()

  def onRemoteAnnotationRemoved(self, msg):
    """ Handle message to remove an annotation """
    annotation = _findAnnotation(msg.sequenceGuid, msg.annotationGuid)
    if annotation:
      track = annotation.parentTrack()
      track.removeSubTrackItem(annotation)
      hiero.ui.currentViewer().window().update()
