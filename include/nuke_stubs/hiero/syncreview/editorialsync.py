from hiero.core import (events, findItemByGuid, Sequence)
from . import messages
from . log import logMessage
from . synctool import (SyncTool, remoteCallback, localCallback)


messages.defineMessageType('SequenceEdit', ('sequenceGuid', str),
                                           ('data', messages.Compressed),
                                           ('rangeMin', int),
                                           ('rangeMax', int))


class SyncSequenceEditsTool(SyncTool):
  """ Tool for syncing sequence edits. """

  def __init__(self, messageDispatcher, viewerSyncTool):
    super(SyncSequenceEditsTool, self).__init__(messageDispatcher)
    self.registerEventCallback(events.EventType.kSequenceEdited, self.onLocalSequenceEdited)
    self.messageDispatcher._registerCallback(messages.SequenceEdit, self.onRemoteSequenceEdited)
    self._viewerSyncTool = viewerSyncTool

  @localCallback
  def onLocalSequenceEdited(self, event):
    """ Handle event when sequence is edited and send the sequence state to remotes.
    Note the event will also be sent for clips, but that's not being handled here
    """
    seq = event.sequence
    if isinstance(seq, Sequence):
      msg = messages.SequenceEdit(sequenceGuid=seq.guid(),
                                  data=seq.serialize(),
                                  rangeMin=event.rangeMin,
                                  rangeMax=event.rangeMax)
      self.messageDispatcher.sendMessage(msg)

      # Have to re-push the tracks mask otherwise it breaks because it keeps pointers
      # to the old tracks which get removed
      self._viewerSyncTool.pushViewerState()

  @remoteCallback
  def onRemoteSequenceEdited(self, msg):
    """ Receive sequence edit data from a remote """
    sequence = findItemByGuid(msg.sequenceGuid, filter=(Sequence,))
    if not sequence:
      logMessage("onRemoteSequenceEdited: sequence {} not found!".format(msg.sequenceGuid))
      return
    sequence.deserialize(msg.data, msg.rangeMin, msg.rangeMax)
