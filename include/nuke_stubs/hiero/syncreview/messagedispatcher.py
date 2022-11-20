from PySide2.QtCore import (QObject, Qt, Signal)
import traceback
from .log import (logException, logMessage)


class MessageDispatcher(QObject):
  """ Receives messages from a connected session and forwards them to registered
  callbacks. Also allows for sending messages back.
  """
  def __init__(self, messageClient):
    super(MessageDispatcher, self).__init__()
    self._messageClient = messageClient
    self._messageClient.messageReceived.connect(self._onMessageReceived, Qt.QueuedConnection)
    self._incomingMessages = []
    self._handlingIncomingMessages = False
    self._messageCallbacks = {}

  def _registerCallback(self, msgType, callback):
    """ Register a callback for a particular message type """
    if msgType not in self._messageCallbacks:
      self._messageCallbacks[msgType] = list()
    self._messageCallbacks[msgType].append(callback)

  def _onMessageReceived(self, msg):
    """ Slot called when a message is received. Forwards to callbacks if one
    was registered
    """
    # In certain situations (e.g. when loading a project) more messages can be
    # received while the current one is still being processed. This recursion makes
    # the sync logic more complex, so avoid this and keep a queue of messages
    logMessage("MessageDispatcher._onMessageReceived: {}".format(msg))
    self._incomingMessages.append(msg)
    if self._handlingIncomingMessages:
      return
    self._handlingIncomingMessages = True
    while self._incomingMessages:
      msg = self._incomingMessages.pop(0)
      try:
        callbacks = self._messageCallbacks.get(type(msg), [])
        for callback in callbacks:
          callback(msg)
      except:
        logException("MessageDispatcher._onMessageReceived: Error handling message {}".format(msg))
    self._handlingIncomingMessages = False

  def sendMessage(self, msg):
    """ Send a message back to the connected session """
    logMessage("MessageDispatcher.sendMessage: {}".format(msg))
    self._messageClient.sendMessage(msg)

  def shutdown(self):
    self._messageCallbacks.clear()
    self._messageClient.messageReceived.disconnect(self._onMessageReceived)
    self._messageClient = None
