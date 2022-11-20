from PySide2.QtCore import (QObject, QTimer)
from . socket import (ServerSocket)
from . import messages
from . import config
from . log import (logDebug, logMessage)
from . connectionstate import ConnectionState

class ClientConnection(object):
  """ 
  Per-client state for the server 
  """
  def __init__(self, socketId):
    self.socketId = socketId
    self.heartbeatTimer = QTimer()
    self.heartbeatTimer.setSingleShot(True)
    self.heartbeatTimer.setInterval(config.HEARTBEAT_TIMEOUT)

  def disconnected(self):
    self.heartbeatTimer.stop()

  def resetHeartbeatTimer(self):
    self.heartbeatTimer.start()


class Server(QObject):
  """ 
  A server listening on connections from clients and routing messages.
  """
  def __init__(self):
    super(Server, self).__init__()
    self._socket = ServerSocket()
    self._socket.dataReceived.connect(self._onDataReceived)
    self._clients = {}

  def bind(self, port):
    self._socket.bind("tcp://*:{}".format(port))
    logDebug("Server: listening on port {}".format(port))

  def shutdown(self):
    logMessage("Server.shutdown: messaging clients")
    for connection in self._clients.values():
      self._sendMessageToClient(connection.socketId, messages.Disconnect())
      connection.disconnected()
    self._clients = {}
    self._socket.close()

  def _onDataReceived(self, clientSocketId, data):
    msg = messages.deserializeMessage(data)

    clientId = msg.sender

    if clientId in self._clients:
      self._clients[clientId].resetHeartbeatTimer()

    if isinstance(msg, messages.Connect):
      self._handleConnectRequest(clientSocketId, msg)
    elif clientId in self._clients:
      if isinstance(msg, messages.Disconnect):
        logMessage("Server._onDataReceived: client disconnected '{}'".format(clientId))
        self._clientDisconnected(clientId)
        self._broadcastNumberOfClients()
      elif isinstance(msg, messages.Ping):
        self._sendMessageToClient(clientSocketId, messages.Pong())
      else:
        self._processInterClientMessage(clientId, msg)
    else:
      logMessage("Server._onDataReceived: Error unexpected message from client '{}' '{}'".format(clientId, msg))

  def _handleConnectRequest(self, clientSocketId, msg):
    # Check if the client is using a compatible version. For now, only allow exactly
    # matching Nuke versions to connect
    logMessage("Server._handleConnectRequest: clientSocket: {} message: {}".format(clientSocketId, msg))
    versionsMatch = (msg.applicationVersion == config.APPLICATION_VERSION)
    if not versionsMatch:
      errorText = 'Connection Failed: Incompatible version with the host which is running {}'.format(config.APPLICATION_VERSION)
      responseMsg = messages.ConnectResponse(result=ConnectionState.ERROR_CONNECT_INCOMPATIBLE_VERSION,
                                          responseText=errorText)
      logMessage("Server._handleConnectRequest: Failed connection {}".format(responseMsg))
      self._sendMessageToClient(clientSocketId, responseMsg)
      return

    logMessage("Server._handleConnectRequest: client connected")
    self._addClientConnection(clientSocketId, msg.sender)
    responseMsg = messages.ConnectResponse(result=ConnectionState.ERROR_NONE,
                                        responseText='Connected')
    self._sendMessageToClient(clientSocketId, responseMsg)
    self._broadcastNumberOfClients()

    # Notify existing clients of the new connection
    self.sendMessageToAllClients(msg, exclude=msg.sender)

  def _addClientConnection(self, clientSocketId, clientId):
    """ Set up a newly connected client """
    assert(clientId not in self._clients)

    connection = ClientConnection(clientSocketId)
    self._clients[clientId] = connection
    connection.heartbeatTimer.timeout.connect(lambda: self._onClientTimeout(clientId))
    connection.resetHeartbeatTimer()

  def _processInterClientMessage(self, clientId, msg):
    """ Handle a non-connection related message from a client and forward it on
    to other clients
    """
    if msg.target == messages.Message.TARGET_BROADCAST:
      self.sendMessageToAllClients(msg, exclude=clientId)
    else:
      self._sendMessageToClient(self._clients[msg.target].socketId, msg)

  def sendMessageToAllClients(self, msg, exclude=None):
    """ Send a message to connected clients, optionally excluding one
    """
    for clientId, connection in self._clients.items():
      if clientId == exclude:
        continue
      self._sendMessageToClient(connection.socketId, msg)

  def _sendMessageToClient(self, clientSocketId, msg):
    """ Send a message to a single client """
    self._socket.send(clientSocketId, msg.serialize())

  def _onClientTimeout(self, clientId):
    logMessage("Client timed out '{}'".format(clientId))
    self._clientDisconnected(clientId)
    self._broadcastNumberOfClients()

  def _clientDisconnected(self, clientId):
    self._clients[clientId].disconnected()
    del self._clients[clientId]
    msg = messages.Disconnected(disconnected=clientId)
    self.sendMessageToAllClients(msg)

  def _getNumberOfConnectedClients(self):
    """ Return the number of connected clients excluding the host client """
    return len(self._clients)-1

  def _broadcastNumberOfClients(self):
    numberOfConnectedClients = self._getNumberOfConnectedClients()
    msg = messages.NumberOfPeers(content=numberOfConnectedClients)
    self.sendMessageToAllClients(msg)

