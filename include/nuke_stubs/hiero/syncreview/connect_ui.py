from PySide2.QtCore import (QObject, Qt, Signal)
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import (QAction,
                               QCheckBox,
                               QDialog,
                               QDialogButtonBox,
                               QFormLayout,
                               QInputDialog,
                               QLineEdit,
                               QMessageBox,
                               QPushButton,
                               QShortcut,
                               QSpinBox,
                               )

import hiero.core
import hiero.ui
import nuke

from . import config
from . import syncreviewstatuspanel
from . connectdialog import ConnectDialog
from . connectionmanager import ConnectionManager
from . connectionstate import ConnectionState
from . messages import Notification
from . sessionsetupdialog import SessionSetupDialog

_UNSAVED_WORK_MSGBOX_TITLE = "Warning"
_UNSAVED_WORK_MSGBOX_TEXT = ("By connecting to a remote Sync Session, all current projects will be closed.\n"
                             "Would you like to continue?")
_UNSAVED_WORK_MSGBOX_DONT_SHOW = "Don't show this warning again"
_UNSAVED_WORK_MSGBOX_CONTINUE = "Continue"


def _keepUnsavedWork():
  # Returns True if the user prefers to keep their unsaved work. In this case the connect dialog should not be shown.
  settings = hiero.core.ApplicationSettings()
  if not settings.boolValue(config.SHOW_UNSAVED_WORK_WARNING, True):
    return False

  hasUnsavedWork = False
  for project in hiero.core.projects():
    if project.modifiedSinceLastSave():
      hasUnsavedWork = True
      break

  if hasUnsavedWork:
    msgBox = QMessageBox(QMessageBox.Warning,
                         _UNSAVED_WORK_MSGBOX_TITLE,
                         _UNSAVED_WORK_MSGBOX_TEXT)
    continueButton = msgBox.addButton(_UNSAVED_WORK_MSGBOX_CONTINUE, QMessageBox.AcceptRole)
    msgBox.addButton(QMessageBox.Cancel)
    msgBox.setDefaultButton(QMessageBox.Cancel)
    dontShowCheckBox = QCheckBox(_UNSAVED_WORK_MSGBOX_DONT_SHOW)
    dontShowCheckBox.blockSignals(True)
    msgBox.addButton(dontShowCheckBox, QMessageBox.ResetRole)
    msgBox.exec_()

    continueClicked = msgBox.clickedButton() == continueButton
    if dontShowCheckBox.isChecked() and continueClicked:
      settings.setBoolValue(config.SHOW_UNSAVED_WORK_WARNING, False)

    return not continueClicked

  return False


class ClientConnectUI(QObject):
  """ Class for handling showing dialogs and error messages when connecting as a
  client to a sync session.
  """

  DISCONNECTED_MSGBOX_TITLE = "Warning"
  DISCONNECTED_MSGBOX_TEXT = ("It looks like you lost connection to the chosen Nuke sync session. "
                              "Would you like to reconnect?")

  def __init__(self, connectionManager):
    super(ClientConnectUI, self).__init__()
    self._connectionManager = connectionManager
    connectionState = self._connectionManager.connectionState
    connectionState.error.connect(self.onConnectionError)
    connectionState.changed.connect(self.onConnectStateChanged)

    # Find the actions to disable when connected as a client. Not all of these
    # might be present, e.g. save as player project is only available when running
    # HieroPlayer
    # If it's the action for a sub-menu (recent projects) all the actions in the
    # sub-menu also need to be disabled for this to work properly on Mac
    clientDisabledActionNames = ["foundry.application.newProject",
                                 "foundry.project.save",
                                 "foundry.project.saveas",
                                 "foundry.project.saveAsPlayerProject",
                                 "foundry.application.openProject",
                                 "foundry.project.recentprojects",
                                 "foundry.project.close"]
    self._clientsDisabledActions = []
    for actionName in clientDisabledActionNames:
      action = hiero.ui.findMenuAction(actionName)
      if action:
        self._clientsDisabledActions.append(action)
        actionMenu = action.menu()
        if actionMenu:
          self._clientsDisabledActions.extend(actionMenu.actions())

  def connectClient(self, autoConnect=False):
    """ Connect as a client to a running server, showing UI to get the host and port
    to connect on. If autoConnect is True, will show the dialog and try to connect
    automatically with the previous settings
    """
    if _keepUnsavedWork():
      return

    dlg = ConnectDialog(self._connectionManager)
    if autoConnect:
      dlg.connect()
    if (dlg.exec_()):
      syncreviewstatuspanel.openStatusPanelIfClosed()

  def disconnectClient(self):
    """ Disconnect the client """
    self._connectionManager.disconnectClient()

  def onConnectionError(self, error, errorText):
    """ Handle connection errors. If a connection is lost, gives the user the option
    to reconnect.
    """
    if error == ConnectionState.ERROR_CONNECTION_LOST:
      msgBox = QMessageBox(QMessageBox.Warning,
                           ClientConnectUI.DISCONNECTED_MSGBOX_TITLE,
                           ClientConnectUI.DISCONNECTED_MSGBOX_TEXT)
      reconnectButton = msgBox.addButton("Reconnect", QMessageBox.AcceptRole)
      msgBox.addButton(QMessageBox.Cancel)
      msgBox.exec_()
      if msgBox.clickedButton() == reconnectButton:
        self.connectClient(autoConnect=True)

  def onConnectStateChanged(self, newState, oldState):
    clientDisconnected = (newState == ConnectionState.DISCONNECTED) and (oldState == ConnectionState.CLIENT_CONNECTED)
    if clientDisconnected:
      # When a client is disconnected, close all projects (currently they must all
      # be synced). Note that a new empty project is automatically created once
      # they're all closed
      projects = hiero.core.projects()
      for proj in projects:
        proj.close()

    # Update the state of the actions which should be disabled while connected as a client
    # The disallowEnabled dynamic property is used to prevent UI logic in the application
    # code from enabling the actions. Store the previous enabled state as a property so it
    # can be set back to that on disconnect
    if (newState == ConnectionState.CLIENT_CONNECTED):
      for action in self._clientsDisabledActions:
        action.setProperty("disallowEnabled", True)
        action.setProperty("lastEnabledState", action.isEnabled())
        action.setEnabled(False)
    elif clientDisconnected:
      for action in self._clientsDisabledActions:
        action.setEnabled(action.property("lastEnabledState"))
        action.setProperty("lastEnabledState", None)
        action.setProperty("disallowEnabled", None)


class HostUI(QObject):
  """ Class for handling showing dialogs and error messages when acting as host
  in a sync session.
  """

  SAVE_PROJECT_MSGBOX_TITLE = "Sync Session"
  SAVE_PROJECT_MSGBOX_TEXT = "Session ended. Do you want to save your project(s)?"

  def __init__(self, connectionManager):
    super(HostUI, self).__init__()
    self._connectionManager = connectionManager

  def startServer(self):
    """ Start the server, getting the port from the user """
    # Get the projects to share, which at the moment is all of them
    projects = hiero.core.projects()

    dialog = SessionSetupDialog(self._connectionManager, projects)
    if (dialog.exec_()):
      syncreviewstatuspanel.openStatusPanelIfClosed()

  def stopServer(self):
    """ Stop the server if it was running """
    projects = self._connectionManager.getProjects()

    self._connectionManager.stopServer()

    # Create an autosave file for all the synced projects
    for proj in projects:
      proj.autosave()


class MenuBuilder(QObject):
  """ Class which handles the menu logic for the sync functionality """

  def __init__(self, connectionManager):
    super(MenuBuilder, self).__init__()
    self.connectionManager = connectionManager
    self.connectionManager.connectionState.changed.connect(self.updateMenuEnabledStates)
    self.hostSessionAction = None
    self.endSessionAction = None
    self.connectSessionAction = None
    self.disconnectSessionAction = None
    self._clientUI = ClientConnectUI(connectionManager)
    self._hostUI = HostUI(connectionManager)

  def createMenus(self):
    """ Add entries to the file menu for managing the connection """
    fileMenu = hiero.ui.findMenuAction("foundry.menu.file")

    self.hostSessionAction = hiero.ui.createMenuAction('Host Sync Session...', self._hostUI.startServer, path="foundry.application.hostSession")
    self.endSessionAction = hiero.ui.createMenuAction('End Sync Session', self._hostUI.stopServer, path="foundry.application.endSession")
    self.connectSessionAction = hiero.ui.createMenuAction('Connect to Sync Session...', self._clientUI.connectClient, path="foundry.application.connectSession")
    self.disconnectSessionAction = hiero.ui.createMenuAction('Disconnect from Sync Session', self._clientUI.disconnectClient, path="foundry.application.disconnectSession")

    syncSessionActions = [
      self.disconnectSessionAction,
      self.connectSessionAction,
      self.endSessionAction,
      self.hostSessionAction,
    ]

    # Add the sync review actions to the file menu and set their context property. Menus are organised differently in Hiero,
    # so we need to account for this when adding the sync review actions
    for action in syncSessionActions:
      action.setProperty(hiero.ui.kContextProperty, hiero.ui.kContextTimeline)
    if (not nuke.env.get('hiero')):
      for action in syncSessionActions:
        hiero.ui.insertMenuAction(action, fileMenu.menu(), after="foundry.project.importSequence")
      fileMenu.menu().insertSeparator(self.hostSessionAction)
    else:
      hiero.ui.insertMenuAction(self.hostSessionAction, fileMenu.menu(), before="foundry.application.quit")
      hiero.ui.insertMenuAction(self.endSessionAction, fileMenu.menu(), before="foundry.application.quit")
      hiero.ui.insertMenuAction(self.connectSessionAction, fileMenu.menu(), before="foundry.application.quit")
      hiero.ui.insertMenuAction(self.disconnectSessionAction, fileMenu.menu(), before="foundry.application.quit")
      fileMenu.menu().insertSeparator(hiero.ui.findMenuAction("foundry.application.quit"))


    # Create a shortcut for pushing the session state, it doesn't appear in the menu
    # but should be enabled globally whenever connected to a session
    self.pushSessionShortcut = QShortcut(QKeySequence("Ctrl+P"), hiero.ui.mainWindow())
    self.pushSessionShortcut.setContext(Qt.ApplicationShortcut)
    self.pushSessionShortcut.activated.connect(self.connectionManager.pushSession)

    self.updateMenuEnabledStates()

  def updateMenuEnabledStates(self):
    """ Set the enabled states of sync menu actions """
    connectState = self.connectionManager.connectionState
    self.hostSessionAction.setEnabled(connectState == ConnectionState.DISCONNECTED)
    self.endSessionAction.setEnabled(connectState == ConnectionState.SERVER_RUNNING)
    self.connectSessionAction.setEnabled(connectState == ConnectionState.DISCONNECTED)
    self.disconnectSessionAction.setEnabled(connectState == ConnectionState.CLIENT_CONNECTED)
    self.pushSessionShortcut.setEnabled(connectState in (ConnectionState.SERVER_RUNNING, ConnectionState.CLIENT_CONNECTED))

