from hiero.core import (AudioTrack,
                        events,
                        findItemByGuid,
                        EffectTrackItem,
                        TrackItem,
                        VideoTrack)
from . import messages
from .synctool import (SyncTool, localCallback, remoteCallback)
from . log import logMessage

messages.defineMessageType('ItemStatusChange', ('itemGuids', messages.Json), ('enabled', messages.Bool))


class SyncItemStatusTool(SyncTool):
  """ Tool for syncing enabled/disabled status changes of items. """

  def __init__(self, messageDispatcher):
    super(SyncItemStatusTool, self).__init__(messageDispatcher)
    self.messageDispatcher._registerCallback(messages.ItemStatusChange, self._onRemoteItemStatusChanged)
    self.registerEventCallback(events.EventType.kTrackEnabledChanged, self._onLocalTrackStatusChanged)

  @localCallback
  def _onLocalTrackStatusChanged(self, event):
    msg = messages.ItemStatusChange(itemGuids=[event.track.guid()], enabled=event.enable)
    self.messageDispatcher.sendMessage(msg)

  @remoteCallback
  def _onRemoteItemStatusChanged(self, msg):
    itemTypes = (AudioTrack, TrackItem, VideoTrack, EffectTrackItem)
    for itemGuid in msg.itemGuids:
      item = findItemByGuid(itemGuid, filter=itemTypes)
      if not item:
        logMessage("onRemoteItemStatusChanged finding item failed {}".format(itemGuid))
        continue
      item.setEnabled(msg.enabled)
