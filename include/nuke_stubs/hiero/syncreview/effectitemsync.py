from hiero.core import (events, findItemByGuid, EffectTrackItem)
from . synctool import (SyncTool, localCallback, remoteCallback)
from . import messages
from . log import logMessage

messages.defineMessageType('EffectItemKnobChange', ('itemGuid', str), ('knobName', str), ('knobScript', str))

# Register a filter so that when receiving messages, all but the most recent to
# a knob gets ignored. Otherwise when the user is e.g. moving a slider there can
# be a lot of unnecessary knob changes
messages.addMessageFilter(messages.RemoveDuplicateMessagesFilter(messages.EffectItemKnobChange, matchAttributes=('itemGuid', 'knobName')))


class SyncEffectItemKnobsTool(SyncTool):
  """ Handle syncing of knob changes on soft effects """
  def __init__(self, messageDispatcher):
    super(SyncEffectItemKnobsTool, self).__init__(messageDispatcher)
    messageDispatcher._registerCallback(messages.EffectItemKnobChange, self._onRemoteKnobChanged)
    self.registerEventCallback(events.EventType.kEffectItemKnobChanged, self._onLocalKnobChanged)

  @remoteCallback
  def _onRemoteKnobChanged(self, msg):
    """ Process a remote knob changed message """
    item = findItemByGuid(msg.itemGuid, filter=[EffectTrackItem])
    if not item:
      logMessage("SyncEffectItemKnobsTool._onRemoteKnobChanged effect item {} not found!".format(msg.itemGuid))
      return
    knob = item.node().knob(msg.knobName)
    if not knob:
      logMessage("SyncEffectItemKnobsTool._onRemoteKnobChanged knob {} not found!".format(msg.knobName))
      return
    knob.fromScript(msg.knobScript)

  @localCallback
  def _onLocalKnobChanged(self, event):
    """ Process a knob changed callback """
    # The event has the knob name, not the object, look it up on the node
    knob = event.item.node().knob(event.knobName)

    # It is valid for there not to be a knob here, there are some special callbacks
    # with knobs which do not actually belong to the node. These don't need to be synced
    if not knob:
      return
    value = knob.toScript()
    msg = messages.EffectItemKnobChange(itemGuid=event.item.guid(),
                                        knobName=event.knobName,
                                        knobScript=knob.toScript())
    self.messageDispatcher.sendMessage(msg)
