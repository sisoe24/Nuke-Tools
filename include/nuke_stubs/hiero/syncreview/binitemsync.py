from hiero.core import (events, findItemByGuid, findProjectTags, Bin, BinItem, Version)
from . import messages
from . log import logMessage
from . synctool import (SyncTool, localCallback, remoteCallback)

messages.defineMessageType('BinItemAdded', ('parentGuid', str), ('index', int), ('data', messages.Compressed))
messages.defineMessageType('BinItemRemoved', ('guid', str))
messages.defineMessageType('BinItemRenamed', ('guid', str), ('name', str))
messages.defineMessageType('BinItemMoved', ('guid', str), ('parentGuid', str), ('index', int))


def _getItemParent(item):
  """ Obtain the parent of a bin item. """
  if isinstance(item, Version):
    parent = item.parent()
  else:
    parent = item.parentBin()
  return parent


def _findBinItemByGuid(guid):
  """ Searches for BinItems and Bins first, and if they are not found it also searches for Tags. """
  item = findItemByGuid(guid, filter=(BinItem, Bin, ))
  if not item:
    # Assume that item is a tag.
    for tag in findProjectTags():
      if tag.guid() == guid:
        item = tag
        break
  return item


class SyncBinItemTool(SyncTool):
  """
  Tool for syncing generic bin item operations such as adding empty items.
  Type-specific operations should be handled by other tools.
  """

  def __init__(self, messageDispatcher):
    super(SyncBinItemTool, self).__init__(messageDispatcher)
    self.registerEventCallback(events.EventType.kBinItemAdded, self.onLocalBinItemAdded)
    self.registerEventCallback(events.EventType.kBinItemRemoved, self.onLocalBinItemRemoved)
    self.registerEventCallback(events.EventType.kBinItemRenamed, self.onLocalBinItemRenamed)
    self.registerEventCallback(events.EventType.kBinItemMoved, self.onLocalBinItemMoved)
    self.messageDispatcher._registerCallback(messages.BinItemAdded, self.onRemoteBinItemAdded)
    self.messageDispatcher._registerCallback(messages.BinItemRemoved, self.onRemoteBinItemRemoved)
    self.messageDispatcher._registerCallback(messages.BinItemRenamed, self.onRemoteBinItemRenamed)
    self.messageDispatcher._registerCallback(messages.BinItemMoved, self.onRemoteBinItemMoved)

  @localCallback
  def onLocalBinItemAdded(self, event):
    """ Handle addition of new bin items. """
    item = event.item
    parent = _getItemParent(item)
    index = parent.items().index(item)

    msg = messages.BinItemAdded(parentGuid=parent.guid(),
                                index=index,
                                data=item.serialize())
    self.messageDispatcher.sendMessage(msg)

  @localCallback
  def onLocalBinItemRemoved(self, event):
    """ Handle removal of bin items. """
    msg = messages.BinItemRemoved(guid=event.item.guid(),)
    self.messageDispatcher.sendMessage(msg)

  @remoteCallback
  def onRemoteBinItemAdded(self, msg):
    """ Receive new bin items from a remote participant. """
    parentItem = findItemByGuid(msg.parentGuid, filter=(Bin, BinItem))
    if not parentItem:
      logMessage("onRemoteBinItemAdded: parent item {} not found!".format(msg.parentGuid))
      return

    parentItem.deserializeChildItem(msg.data, msg.index)

  @remoteCallback
  def onRemoteBinItemRemoved(self, msg):
    """ Receive removed bin items from a remote participant. """
    item = _findBinItemByGuid(msg.guid)

    if not item:
      logMessage("onRemoteBinItemRemoved: item {} not found!".format(msg.guid))
      return

    parent = _getItemParent(item)
    parent.removeItem(item)

  @localCallback
  def onLocalBinItemRenamed(self, event):
    """ Handle renaming of new bin items. """
    msg = messages.BinItemRenamed(guid=event.item.guid(),
                                  name=event.name)
    self.messageDispatcher.sendMessage(msg)

  @remoteCallback
  def onRemoteBinItemRenamed(self, msg):
    """ Receive new bin item names from a remote participant. """
    item = _findBinItemByGuid(msg.guid)

    if not item:
      logMessage("onRemoteBinItemRenamed: item {} not found!".format(msg.guid))
      return

    item.syncName(msg.name)

  @localCallback
  def onLocalBinItemMoved(self, event):
    """ Handle bin items being moved. """
    msg = messages.BinItemMoved(guid=event.item.guid(),
                                parentGuid=event.parent.guid(),
                                index=event.index)
    self.messageDispatcher.sendMessage(msg)


  @remoteCallback
  def onRemoteBinItemMoved(self, msg):
    """ Receive bin item movements from a remote participant. """
    item = _findBinItemByGuid(msg.guid)

    if not item:
      logMessage("onRemoteBinItemMoved: item {} not found!".format(msg.guid))
      return

    parent = findItemByGuid(msg.parentGuid, filter=(Bin, ))
    if not parent:
      logMessage("onRemoteBinItemMoved: parent {} not found!".format(msg.parentGuid))
      return

    parent.moveItem(item, msg.index)
