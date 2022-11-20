from PySide2.QtCore import QObject
import inspect
from hiero.core import events

def localCallback(func):
  """ Decorator for a local callback function (handling events/signals from local
  changes). Stops the function from being called if a remote message was being handled
  """
  # Connections to Qt signals may take fewer parameters than the signal has,
  # check how many args the function takes and only forward that many
  numArgs = len(inspect.getargspec(func)[0]) - 1
  def inner(self, *args, **kwargs):
    if self._handlingRemoteChange:
      return
    return func(self, *args[:numArgs], **kwargs)
  return inner

def remoteCallback(func):
  """ Decorator for a callback for handling remote messages. Sets the
  _handlingRemoteChange flag
  """
  def inner(self, *args, **kwargs):
    try:
      self._handlingRemoteChange = True
      return func(self, *args, **kwargs)
    finally:
      self._handlingRemoteChange = False
  return inner


class SyncTool(QObject):
  """ Base class for 'tools' which handle the syncing logic. """
  def __init__(self, messageDispatcher):
    super(SyncTool, self).__init__()
    self.messageDispatcher = messageDispatcher
    # Flag set when handling a remote message, many tools need to check this to avoid recursion
    self._handlingRemoteChange = False
    self._eventCallbacks = []

  def registerEventCallback(self, eventType, callback):
    """ Register a callback with hiero.core.events. Will be cleaned up in shutdown() """
    self._eventCallbacks.append((eventType, callback))
    events.registerInterest(eventType, callback)

  def shutdown(self):
    """ Clean up the tool, the default implementation unregisters any event callbacks """
    for eventType, callback in self._eventCallbacks:
      events.unregisterInterest(eventType, callback)
    self._eventCallbacks = []
