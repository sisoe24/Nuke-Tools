from PySide2.QtCore import (QObject, Signal)
import hiero.core
from . server import Server
from . client import Client
from . clientsync import ClientSyncHost, ClientSyncGuest
from . connectionstate import ConnectionState
from . cursorsync import SyncClientCursor
from . inoutsync import SyncInOutTool
from . itemstatussync import SyncItemStatusTool
from . import log
from . messagedispatcher import MessageDispatcher
from . import messages
from . projectsync import ProjectPushTool, ProjectSyncProgressTool, HostProjectSyncTool
from . viewsync import SyncViewerTool
from . annotationsync import SyncAnnotationsTool
from . binitemsync import SyncBinItemTool
from . editorialsync import SyncSequenceEditsTool
from . versionsync import SyncVersionsTool
from . effectitemsync import SyncEffectItemKnobsTool
from . import config


class Session(QObject):
  def __init__(self):
    super(Session, self).__init__()
    self._clientDataProvider = None

  def clientDataProvider(self):
    """ Holds data about the current participants of a sync review session. """
    return self._clientDataProvider

  def stop(self):
    """ Clean up all session data. """
    pass


class ServerSession(Session):
  """ Class representing a session running with a server. This creates a Server
  and a Client object which connects to the server and is used for sending and
  receiving messages.
  """

  def __init__(self, port, clientData, project):
    super(ServerSession, self).__init__()

    # Create the server object and bind to the port
    self.server = Server()
    self.server.bind(port)

    # Create the internal client object with a special id
    self.client = Client(ConnectionState(), config.HOST_ID)
    self.messageDispatcher = MessageDispatcher(self.client)

    # ClientSyncHost needs to receive the messages.Connect that will be sent when
    # self.client.connectToHost is called.
    self._clientDataProvider = ClientSyncHost(self.messageDispatcher)

    viewerSyncTool = SyncViewerTool(self.messageDispatcher)

    # Create the project push tool and add the projects to sync
    self.projectPushTool = ProjectPushTool(self.messageDispatcher, viewerSyncTool, clientData)
    self.projectPushTool.addProjects(project)

    # Connect the client object to the local server.
    self.client.connectToHost("localhost", port, clientData)

    self._clientDataProvider.addGuest(config.HOST_ID, clientData)

    self.syncTools = [
      self._clientDataProvider,
      self.projectPushTool,
      HostProjectSyncTool(self.messageDispatcher, self.projectPushTool),
      ProjectSyncProgressTool(self.messageDispatcher),
      viewerSyncTool,
      SyncClientCursor(self.messageDispatcher, self._clientDataProvider),
      SyncAnnotationsTool(self.messageDispatcher),
      SyncVersionsTool(self.messageDispatcher),
      SyncInOutTool(self.messageDispatcher),
      SyncItemStatusTool(self.messageDispatcher),
      SyncEffectItemKnobsTool(self.messageDispatcher),
      SyncSequenceEditsTool(self.messageDispatcher, viewerSyncTool),
      SyncBinItemTool(self.messageDispatcher),
    ]

  def stop(self):
    for tool in self.syncTools:
      tool.shutdown()
    self.messageDispatcher.shutdown()
    self.client.disconnectFromHost()
    self.server.shutdown()


class ClientSession(Session):
  """ Class representing a session running with a client connected to an external
  server.
  """
  def __init__(self, hostname, port, connectionState, clientData):
    super(ClientSession, self).__init__()

    self.client = Client(connectionState, config.MACHINE_ID)

    self.client.connectToHost(hostname, port, clientData)

    self.messageDispatcher = MessageDispatcher(self.client)

    viewerSyncTool = SyncViewerTool(self.messageDispatcher)

    self.projectPushTool = ProjectPushTool(self.messageDispatcher, viewerSyncTool, clientData)
    self._clientDataProvider = ClientSyncGuest(self.messageDispatcher)

    self.syncTools = [
      self.projectPushTool,
      ProjectSyncProgressTool(self.messageDispatcher),
      viewerSyncTool,
      self._clientDataProvider,
      SyncClientCursor(self.messageDispatcher, self._clientDataProvider),
      SyncAnnotationsTool(self.messageDispatcher),
      SyncVersionsTool(self.messageDispatcher),
      SyncInOutTool(self.messageDispatcher),
      SyncItemStatusTool(self.messageDispatcher),
      SyncEffectItemKnobsTool(self.messageDispatcher),
      SyncSequenceEditsTool(self.messageDispatcher, viewerSyncTool),
      SyncBinItemTool(self.messageDispatcher),
    ]

  def stop(self):
    for tool in self.syncTools:
      tool.shutdown()
    self.messageDispatcher.shutdown()
    self.client.disconnectFromHost()



class ConnectionManager(QObject):
  """ Class for managing the connection state of the sync review functionality.
  This can be used to either start a listening server, or to connect a client to
  a running server.

  When running a session object will be created which sets up all the logic for
  the sync functionality and message dispatch.

  Note that in either case, a Client object is created. When running in server
  mode, this will connect locally and be used for the sending and receiving of
  messages.
  """

  # Notification of a change in the number of clients
  numberOfClientsChanged = Signal(int)

  def __init__(self):
    super(ConnectionManager, self).__init__()
    self.connectionState = ConnectionState()
    self.connectionState.changed.connect(self.onConnectionStateChanged)
    self.session = None
    self._connectionInfo = None

  def startServer(self, port, clientData, project):
    """ Start the server and listen on the given port """
    if self.connectionState != ConnectionState.DISCONNECTED:
      raise RuntimeError("Cannot start server")

    # If there was an error initialising the socket (e.g. unable to bind on the
    # specified port) an exception will be raised, stop this falling through
    try:
      log.initLogger('syncsessionhost')
      self.session = ServerSession(port, clientData, project)
      self.connectionState.setState(ConnectionState.SERVER_RUNNING)
      self.session.client.numberOfClientsChanged.connect(self._onNumberOfClientsChanged)
    except:
      self.connectionState.setError(ConnectionState.ERROR_BIND_FAILURE)

  def stopServer(self):
    """ Stop the server """
    if self.connectionState.state() != ConnectionState.SERVER_RUNNING:
      raise RuntimeError("Cannot stop server, it's not running")

    self.shutdown()
    self.connectionState.setState(ConnectionState.DISCONNECTED)

  def connectClient(self, hostname, port, clientData):
    """ Connect as a client to the given hostname and port """
    if self.connectionState != ConnectionState.DISCONNECTED:
      raise RuntimeError("Cannot connect client")

    # Pass the ConnectionState object to the client, it will update it as the
    # connection is started. If there was an error initiating the socket connection
    # (e.g. invalid hostname) an exception will be raised, stop this falling through
    try:
      log.initLogger('syncsessionclient')
      self.session = ClientSession(hostname, port, self.connectionState, clientData)
      self.session.client.numberOfClientsChanged.connect(self._onNumberOfClientsChanged)
    except:
      pass

  def disconnectClient(self):
    """ Disconnect the client """
    if self.connectionState not in (ConnectionState.CLIENT_CONNECTED, ConnectionState.CLIENT_CONNECTING):
      raise RuntimeError("Cannot disconnect, client not connected")
    self.shutdown()

  def shutdown(self):
    """ Shut down the connection if there was one """
    if self.session:
      # Unset self.session first to avoid recursion.
      # TODO It would be good to do some refactoring to avoid this
      session = self.session
      self.session = None
      self._connectionInfo = None
      session.stop()
      log.closeLogger()

  def sessionMessageHandler(self):
    """ Get the object used for sending and receiving messages in the current session. """
    return self.session.client

  def pushSession(self):
    """ Pushes the project to all other clients. """
    self.session.projectPushTool.pushAllProjects(messages.Message.TARGET_BROADCAST)

  def getProjects(self):
    """ Get the project used for the sync session """
    return self.session.projectPushTool.projects()

  def onConnectionStateChanged(self, state):
    """ Callback when the connection state changes. Resets the session when
    disconnected for any reason
    """
    if state == ConnectionState.DISCONNECTED:
      self.shutdown()

  def setConnectionInfo(self, connectionInfo):
    """ Set the current connection info """
    self._connectionInfo = connectionInfo

  def getConnectionInfo(self):
    """ Get the current connection info """
    return self._connectionInfo

  def _onNumberOfClientsChanged(self, numberOfClients):
    """Callback when the number of clients changed"""
    self.numberOfClientsChanged.emit(numberOfClients)


