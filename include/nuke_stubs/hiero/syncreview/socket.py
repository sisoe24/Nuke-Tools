from datetime import datetime
import foundry.zmq as zmq
from PySide2.QtCore import (QObject, Signal, QSocketNotifier, QTimer)
import random
from hiero.core.util import (asBytes,)
from . import config
from . log import logDebug


class Socket(QObject):
  """
  Class which wraps around a zmq socket and allows for integration into a 
  Qt event loop with QSocketNotifier.
  """
    
  def __init__(self, parent=None):
    super(Socket, self).__init__(parent)
    self._socket = None
    self._readNotifier = None
    self._pollTimer = None

  def close(self):
    """ Close the socket and reset its state """
    if not self._socket:
      return
    self._pollTimer.stop()
    self._pollTimer.timeout.disconnect(self._pollSocket)
    self._pollTimer = None
    self._readNotifier.activated.disconnect(self._onReadActivated)
    self._readNotifier = None
    self._socket.close()
    self._socket = None

  def socketId(self):
    """ Get the zmq socket id. If the socket was not yet created returns an
    empty string
    """
    return self._socket.getsockopt(zmq.IDENTITY) if self._socket is not None else ''

  def _createSocket(self, type_):
    """ Create socket with specified type.
    Creates a QSocketNotifier which emits signals when there is data ready to read.
    Unfortunately this is not entirely reliable. When a lot of user interaction
    is happening and lots of messages are being sent (such as when moving a
    slider on a soft effect knob), the notifier can get into a state where the
    activated() signal stops being emitted, which leads to lost messages and timeouts.
    Polling the socket for read data on a timer seems to fix this.
    """
    self._socket = zmq.Context.instance().socket(type_)
    # The last part of the ID is the time elapsed since the day started in UTC.
    # For the unlikely case of clients connecting at the same millisecond, a random prefix is added.
    strId = '{:x}-{}'.format(random.randint(0x0, 0x100), datetime.utcnow().strftime('%H:%M:%S.%f')[:-3])
    self._socket.setsockopt_string(zmq.IDENTITY, strId)

    # Create the socket notifier
    fd = self._socket.getsockopt(zmq.FD)
    self._readNotifier = QSocketNotifier(fd, QSocketNotifier.Read)
    self._readNotifier.activated.connect(self._onReadActivated)

    # Create a timer for polling the socket
    self._pollTimer = QTimer()
    self._pollTimer.setObjectName("SyncSocket.{}".format(type_))
    self._pollTimer.setInterval(config.SOCKET_POLL_INTERVAL)
    self._pollTimer.timeout.connect(self._pollSocket)
    self._pollTimer.start()


  def _onReadActivated(self):
    """ Callback from socket notifier. """
    self._pollSocket()

  def _pollSocket(self):
    """ Polls the socket, and calls self._onDataReceived() with all the data read
    (which will be a list of a list of frames). This should be implemented by sub-classes.
    """
    if not self._socket:
      return

    logDebug("{}._pollSocket {}".format(type(self), self.socketId()))

    # Disable the notifier while reading data to avoid recursion
    self._readNotifier.setEnabled(False)

    # Read all available data into a list, then send it to _onDataReceived
    data = []
    while self._isReadAvailable():
      data.append(self._socket.recv_multipart())
    if data:
      self._onDataReceived(data)

    # Receiving the data can result in the socket being closed, check the notifier
    # still exists.
    if self._readNotifier:
      self._readNotifier.setEnabled(True)
      
  def _isReadAvailable(self):
    """ Check if there's a message ready to read on the socket. 
    """
    return self._socket and (self._socket.getsockopt(zmq.EVENTS) & zmq.POLLIN)

  def _send(self, data):
    """ Send a list of data frames to the ZMQ socket.
    """
    self._socket.send_multipart(data)


class ServerSocket(Socket):
  """
  Socket which binds on a port and uses a ROUTER socket which can route messages 
  to multiple clients.
  """

  # Signal emitted when a message is available, containing (sender_id, data)
  dataReceived = Signal(object, object)

  def __init__(self, parent=None):
    super(ServerSocket, self).__init__(parent)

  def bind(self, url):
    """ Create the socket and bind on the specified url.
    """
    self._createSocket(zmq.ROUTER)
    self._socket.bind(url)

  def _onDataReceived(self, data):
    # Emit the dataReceived signal for each message received
    for msgData in data:
      sender = msgData[0]
      payload = msgData[2:] # Strip the sender and empty frame
      self.dataReceived.emit(sender, payload)

  def send(self, receiver, frames):
    """ Send message frames to a given receiver. """
    logDebug("{}.send {}".format(type(self), frames[0]))
    frames = [asBytes(receiver), b''] + frames
    self._send(frames)


class ClientSocket(Socket):
  """ 
  Socket which connects to a port and uses a DEALER socket for communications 
  with a server.
  """

  # Signal emitted when a message is available, containing the message data
  dataReceived = Signal(object)

  def __init__(self, parent=None):
    super(ClientSocket, self).__init__(parent)

  def connectToHost(self, url):
    self._createSocket(zmq.DEALER)
    self._socket.connect(url)

  def _onDataReceived(self, data):
    # Emit all the received data, which may contain multiple messages
    # Our messages follow the zmq REQ/REP pattern of each address being followed by an empty frame.
    # DEALER sockets (unlike REQ) don't remove this when you receive, so we need to do it here.
    data = [d[1:] for d in data]
    self.dataReceived.emit(data)

  def send(self, frames):
    logDebug("{}.send {}".format(type(self), frames[0]))
    frames = [b''] + frames
    self._send(frames)

