from PySide2.QtCore import (QObject, Signal)


class ConnectionState(QObject):
  """ Class representing the sync connection state. Defines the possible states
  and emits signals when it changes
  """

  # Connection states
  DISCONNECTED = 0
  SERVER_RUNNING = 1
  CLIENT_CONNECTING = 2
  CLIENT_CONNECTED = 3

  # Error states
  ERROR_NONE = 100
  ERROR_UNKNOWN = 101
  ERROR_CONNECT_TIMEOUT = 102
  ERROR_CONNECT_INVALID_HOST = 103
  ERROR_CONNECT_INCOMPATIBLE_VERSION = 104

  # Used when an established connection is lost. This is useful as a distinct error
  # from a timeout when creating a connection
  ERROR_CONNECTION_LOST = 105

  ERROR_BIND_FAILURE = 106

  # Signal emitted when the state changes, the parameters are (newState, oldState)
  changed = Signal(int, int)

  error = Signal(int, str)

  def __init__(self):
    QObject.__init__(self)
    self._state = ConnectionState.DISCONNECTED
    self._error = ConnectionState.ERROR_NONE
    self._errorText = ''

  def setState(self, state):
    """ Set the connection state. Clears any error that was set """
    oldState = self._state
    if state == oldState:
      return
    self._state = state
    self._error = ConnectionState.ERROR_NONE # Reset the error state
    self._errorText = ''
    self.changed.emit(state, oldState)

  def setError(self, error, errorText=''):
    """ Set the error flag, and reset the main state to DISCONNECTED """
    self.setState(ConnectionState.DISCONNECTED)
    self._error = error
    self._errorText = errorText
    self.error.emit(error, errorText)

  def state(self):
    return self._state

  def __eq__(self, state):
    """ Convenience implementation for comparing the object to the state values """
    return self._state == state

  def __ne__(self, state):
    return not self.__eq__(state)

  def errorState(self):
    return self._error

  def errorText(self):
    return self._errorText
