from hiero.core import (events,
                        findItemByGuid,
                        BinItem,
                        TrackItem)
from . import messages
from . log import logMessage
from . synctool import (SyncTool, localCallback, remoteCallback)


# Version changed message. Note that itemGuid and binItemGuid might be the same
# if the change was on the bin item
messages.defineMessageType('VersionChange', ('itemGuid', str), ('binItemGuid', str), ('versionGuid', str))
messages.defineMessageType('VersionLinkedChange', ('itemGuid', str), ('linked', messages.Bool))


class SyncVersionsTool(SyncTool):
  """ Tool for syncing version changes on bin and track items. """
  def __init__(self, messageDispatcher):
    super(SyncVersionsTool, self).__init__(messageDispatcher)
    self.messageDispatcher._registerCallback(messages.VersionChange, self._onRemoteVersionChanged)
    self.messageDispatcher._registerCallback(messages.VersionLinkedChange, self._onRemoteVersionLinkedChanged)
    self.registerEventCallback(events.EventType.kVersionChanged, self._onLocalVersionChanged)
    self.registerEventCallback(events.EventType.kVersionLinkedChanged, self._onLocalVersionLinkedChanged)

  @localCallback
  def _onLocalVersionChanged(self, event):
    """ Notification that the version is changing on an object. Note that this is
    the object the change was initiated on, linked items will also change as a
    result of that.
    """
    msg = messages.VersionChange(itemGuid=event.item.guid(),
                                 binItemGuid=event.version.parent().guid(),
                                 versionGuid=event.version.guid())
    self.messageDispatcher.sendMessage(msg)

  @localCallback
  def _onLocalVersionLinkedChanged(self, event):
    """ Notification that the linked state has changed on a track item"""
    msg = messages.VersionLinkedChange(itemGuid=event.item.guid(),
                                 linked=int(event.linked))
    self.messageDispatcher.sendMessage(msg)

  @remoteCallback
  def _onRemoteVersionChanged(self, msg):
    """ Callback for when the version of a track or bin item has changed remotely
        and needs to be synced locally """
    binItem = findItemByGuid(msg.binItemGuid, filter=(BinItem,))
    if not binItem:
      logMessage("_onRemoteVersionChanged: bin item {} not found!".format(msg.binItemGuid))
      return

    version = next((item for item in binItem.items() if item.guid() == msg.versionGuid), None)
    if not version:
      logMessage("onRemoteVersion changed: version {} not found!".format(msg.versionGuid))
      return

    # If the itemGuid and binItemGuid are the same the version change was on that
    # object, otherwise it must be a track item
    if msg.itemGuid == msg.binItemGuid:
      binItem.setActiveVersion(version)
    else:
      item = findItemByGuid(msg.itemGuid, filter=(TrackItem,))
      if item:
        item.setCurrentVersion(version)
      else:
        logMessage("onRemoteVersion changed: trackitem {} not found!".format(msg.itemGuid))

  @remoteCallback
  def _onRemoteVersionLinkedChanged(self, msg):
    """ Callback for when the linked state of a track item has changed remotely
        and needs to be synced locally """
    trackItem = findItemByGuid(msg.itemGuid, filter=(TrackItem,))
    trackItem.setVersionLinkedToBin(msg.linked, True)
