from . connectionmanager import (ConnectionManager,
                               ConnectionState)
import hiero.ui
import hiero.core
import operator
from PySide2.QtCore import (QAbstractItemModel,
                            QAbstractTableModel,
                            QModelIndex,
                            QPoint,
                            QSize,
                            QSortFilterProxyModel,
                            Qt, )
from PySide2.QtGui import (QColor,
                           QFont,
                           QFontMetrics,
                           QIcon, )
from PySide2.QtWidgets import (QAbstractItemView,
                               QApplication,
                               QHBoxLayout,
                               QHeaderView,
                               QPushButton,
                               QSizePolicy,
                               QTableView,
                               QToolTip,
                               QVBoxLayout,
                               QWidget, )

from . import config


class _Columns:
  """ Columns present in the table model. """

  color = 0
  """ Participant's color. """

  participant = 1
  """ Participant's name. """

  status = 2
  """ Participant's connection status. """

  size = 3
  """ Number of columns in the table. """


_participantsHeaderFormat = 'Participants ({})'


class _Participant:
  """ Holds the data of a participant in the table model. """

  def __init__(self, clientId, name, color, status):
    self.clientId = clientId
    self.name = name
    self.color = QColor(color[0], color[1], color[2], 255)
    self.status = status


class _SyncReviewStatusModel(QAbstractTableModel):
  """ Data model for the data of the participants in the current sync review session. """

  def __init__(self, view):
    QAbstractTableModel.__init__(self)
    self._view = view
    # List of _Participant instances.
    self._data = list()
    self._clientDataProvider = None

  def _updateClientData(self, clientData):
    self.beginResetModel()

    # Keep known participants that are no longer connected as offline.
    self._data = [_Participant(p.clientId, p.name, (p.color.red(), p.color.green(), p.color.blue()), False) for p in self._data if
                  p.clientId not in clientData]

    # Add new clients as connected participants. Update existing participant data.
    for clientId, clientData in clientData.items():
      name, color = clientData
      self._data.append(_Participant(clientId, name, color, True))

    self.endResetModel()

  def _clientDataChanged(self):
    self._updateClientData(self._clientDataProvider.clientData)

  def _clearClientData(self):
    self._data = list()
    self._updateClientData(dict())

  def rowCount(self, parent):
    if parent.isValid():
      return 0
    return len(self._data)

  def columnCount(self, parent):
    if parent.isValid():
      return 0
    return _Columns.size

  def headerData(self, section, orientation, role):
    global _participantsHeaderFormat
    data = None

    if orientation != Qt.Orientation.Horizontal:
      return data

    if role == Qt.DisplayRole:
      if section == _Columns.participant:
        data = _participantsHeaderFormat.format(len(self._data))
      elif section == _Columns.status:
        data = 'Status'
    elif role == Qt.DecorationRole:
      if section == _Columns.color:
        return QIcon("icons:SyncParticipants.png")

    return data

  def data(self, index, role):
    if not index.isValid():
      return None

    data = None
    participant = self._data[index.row()]
    column = index.column()
    if role == Qt.DisplayRole:
      if column == _Columns.participant:
        data = participant.name
      elif column == _Columns.status:
        if (participant.clientId == config.HOST_ID):
          data = 'Host'
        else:
          data = 'Connected' if participant.status else 'Offline'
    elif role == Qt.DecorationRole:
      if column == _Columns.color:
        # ToDo Use a colorized icon instead of a color square.
        data = participant.color

    return data

  def enterSession(self, clientDataProvider):
    self._clientDataProvider = clientDataProvider
    self._clientDataProvider.clientDataChanged.connect(self._clientDataChanged)
    self._clientDataProvider.clientDataCleared.connect(self._clearClientData)
    self._clientDataChanged()

  def leaveSession(self):
    if self._clientDataProvider is not None:
      self._clientDataProvider.clientDataChanged.disconnect(self._clientDataChanged)
      self._clientDataProvider.clientDataCleared.disconnect(self._clearClientData)
      self._clientDataProvider = None


def _colorHeaderMinWidth():
  # ToDo use the width of the icon.
  return 32


def _participantsHeaderMinWidth():
  # Size of the selected header showing a 3-digit number of participants plus an estimated size for the sort indicator.
  return QFontMetrics(QFont()).width(_participantsHeaderFormat.format(888)) + 32


class SyncStatusPanel(QWidget):
  """ Shows the current status of the participants of a sync review session. """

  def __init__(self, connectionManager):
    QWidget.__init__(self)
    self._connectionManager = connectionManager

    self.setObjectName('uk.co.thefoundry.syncreviewstatus.1')
    self.setWindowTitle('Sync Session')
    self.setWindowIcon(QIcon("icons:SyncTab.png"))

    # Last column used for sorting the table. Used for disabling clicking on the color header for sorting.
    self._lastSortedColumn = -1
    # Last sort order used. Used for disabling clicking on the color header for sorting.
    self._lastSortedOrder = None

    # Models used by the window.
    self._model = _SyncReviewStatusModel(self)

    # Toolbar widgets.
    # The buttons' labels and actions and icons are set up by _updateConnectionState.
    self._hostButton = QPushButton('')
    self._hostAction = None
    self._connectButton = QPushButton('')
    self._connectButton.setToolTip(config.CONNECT_BUTTON_TOOL_TIP)
    self._connectAction = None

    # Create the push session button.
    pushIcon = QIcon("icons:SyncPush.png")
    pushIcon.addFile("icons:SyncPush_disabled.png", QSize(), QIcon.Disabled)
    self._pushSessionButton = QPushButton(pushIcon, '')
    self._pushSessionButton.setMaximumHeight(24)
    self._pushSessionButton.setToolTip(config.PUSH_SESSION_TOOL_TIP)
    self._pushSessionButton.clicked.connect(connectionManager.pushSession)
    self._pushSessionButton.setFocusPolicy(Qt.NoFocus)

    # Create the push session button.
    connectInfoIcon = QIcon("icons:SyncCopyInfo.png")
    connectInfoIcon.addFile("icons:SyncCopyInfo_disabled.png", QSize(), QIcon.Disabled)
    self._copyConnectionInfoButton = QPushButton(connectInfoIcon, '')
    self._copyConnectionInfoButton.setMaximumHeight(24)
    self._copyConnectionInfoButton.setToolTip(config.COPY_INFO_TOOL_TIP)
    self._copyConnectionInfoButton.clicked.connect(self._copyConnectionInfo)
    self._copyConnectionInfoButton.setFocusPolicy(Qt.NoFocus)

    # Toolbar setup.
    toolbarLayout = QHBoxLayout()
    toolbarLayout.setAlignment(Qt.AlignLeft)
    toolbarLayout.setContentsMargins(5, 5, 5, 0)
    toolbarLayout.addWidget(self._hostButton)
    toolbarLayout.addWidget(self._connectButton)
    toolbarLayout.addWidget(self._copyConnectionInfoButton)
    toolbarLayout.addWidget(self._pushSessionButton)

    # Main view.
    self._tableView = QTableView()
    self._sortModel = QSortFilterProxyModel()
    self._sortModel.setSourceModel(self._model)
    self._tableView.setModel(self._sortModel)
    # Disable the vertical header.
    self._tableView.verticalHeader().setVisible(False)
    # Set the sizes of each column on the horizontal header.
    self._tableView.setColumnWidth(_Columns.color, _colorHeaderMinWidth())
    self._tableView.setColumnWidth(_Columns.participant, _participantsHeaderMinWidth())
    self._tableView.horizontalHeader().setStretchLastSection(True)
    # Table style.
    self._tableView.setGridStyle(Qt.NoPen)
    self._tableView.setAlternatingRowColors(True)
    # Disable selection.
    self._tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self._tableView.setFocusPolicy(Qt.NoFocus)
    self._tableView.setSelectionMode(QAbstractItemView.NoSelection)
    # Table sorting.
    self._tableView.setSortingEnabled(True)
    # Do not show a sort indicator on launch.
    self._setUnsorted()

    # Disable clicking on the color header for sorting.
    self._tableView.horizontalHeader().sortIndicatorChanged.connect(self._ignoreClicksOnColorHeader)

    # Main layout configuration.
    mainLayout = QVBoxLayout()
    mainLayout.addLayout(toolbarLayout)
    mainLayout.addWidget(self._tableView)
    self.setLayout(mainLayout)

    # Connection state
    self._updateConnectionState(ConnectionState.DISCONNECTED)
    connectionManager.connectionState.changed.connect(self._updateConnectionState)

  def getSortedColumn(self):
    """ Column that is currently being sorted. Holds a negative value if the table is currently not sorted. """
    return self._lastSortedColumn

  def getSortedOrder(self):
    """ Current sort order. If getSortedColumn is negative, it will return None. """
    return self._lastSortedOrder

  def _setUnsorted(self):
    # After calling this method no sort indicator will be shown and the model will return to its natural, unsorted
    # order.
    self._lastSortedColumn = -1
    self._tableView.horizontalHeader().setSortIndicator(self._lastSortedColumn, Qt.SortOrder.AscendingOrder)

  def _ignoreClicksOnColorHeader(self, newSortedColumn, _):
    if newSortedColumn == _Columns.color:
      # If the user clicked on the color header, restore the sort indicator status from before the click.
      if self._lastSortedColumn in (_Columns.participant, _Columns.status):
        self._tableView.horizontalHeader().setSortIndicator(self._lastSortedColumn, self._lastSortedOrder)
      else:
        self._setUnsorted()
    else:
      # Store the sort indicator status for the next click.
      self._lastSortedColumn = newSortedColumn
      if newSortedColumn != -1:
        self._lastSortedOrder = self._tableView.horizontalHeader().sortIndicatorOrder()

  def _updateHostButton(self, state):
    self._hostButton.setText('Host' if state != ConnectionState.SERVER_RUNNING else 'End Session')
    self._hostButton.setToolTip( config.HOST_BUTTON_TOOL_TIP if state != ConnectionState.SERVER_RUNNING else config.END_SESSION_BUTTON_TOOL_TIP)
    self._hostButton.setEnabled(state in (ConnectionState.DISCONNECTED, ConnectionState.SERVER_RUNNING))
    if self._hostAction is not None:
      self._hostButton.pressed.disconnect(self._hostAction)

    hostActionName = 'foundry.application.{}'.format(
      'hostSession' if state != ConnectionState.SERVER_RUNNING else 'endSession')
    self._hostAction = hiero.ui.findMenuAction(hostActionName).trigger
    self._hostButton.pressed.connect(self._hostAction)

  def _updateConnectButton(self, state):
    self._connectButton.setText('Connect' if state != ConnectionState.CLIENT_CONNECTED else 'Disconnect')
    self._connectButton.setEnabled(state in (ConnectionState.DISCONNECTED, ConnectionState.CLIENT_CONNECTED))
    if self._connectAction is not None:
      self._connectButton.pressed.disconnect(self._connectAction)

    connectActionName = 'foundry.application.{}'.format(
      'connectSession' if state != ConnectionState.CLIENT_CONNECTED else 'disconnectSession')
    self._connectAction = hiero.ui.findMenuAction(connectActionName).trigger
    self._connectButton.pressed.connect(self._connectAction)

  def _updateConnectionState(self, state):
    self._updateHostButton(state)
    self._updateConnectButton(state)
    self._copyConnectionInfoButton.setEnabled(state == ConnectionState.SERVER_RUNNING)
    self._pushSessionButton.setEnabled(state in (ConnectionState.SERVER_RUNNING, ConnectionState.CLIENT_CONNECTED))
    if state == ConnectionState.DISCONNECTED:
      self._model.leaveSession()
    elif state in (ConnectionState.SERVER_RUNNING, ConnectionState.CLIENT_CONNECTED):
      self._model.enterSession(self._connectionManager.session.clientDataProvider())

  def _copyConnectionInfo(self):
    """ Copies the connection info of the server into the clipboard. """
    connectionInfo = self._connectionManager.getConnectionInfo()
    if connectionInfo:
      QApplication.clipboard().setText(connectionInfo)
      toolTipPosition = self.mapToGlobal(self._copyConnectionInfoButton.pos())
      toolTipPosition += QPoint(0, 10) # Adjust tooltip position so it doesn't cover the button
      QToolTip.showText(toolTipPosition,
                        "Connection info successfully copied to clipboard",
                        self._copyConnectionInfoButton,
                        self._copyConnectionInfoButton.rect(),
                        3000)


# Global instance of the sync review status panel.
_statusPanelInstance = None


def initialise(connectionManager):
  """ Initialize the global instance of the sync review status panel. """
  global _statusPanelInstance
  try:
    _statusPanelInstance = SyncStatusPanel(connectionManager)
    hiero.ui.windowManager().addWindow(_statusPanelInstance)
  except Exception as ex:
    print('Initialization of the sync review status panel failed: {}'.format(ex))

def openStatusPanelIfClosed():
  """ Opens the status panel in a floating window if it's closed and the user preference is to open
  it on session startup"""
  if (not _statusPanelInstance):
    return

  settings = hiero.core.ApplicationSettings()
  if ( not _statusPanelInstance.isVisible() and settings.boolValue(config.OPEN_PANEL_ON_STARTUP_KEY)):
    hiero.ui.windowManager().popupWindow(_statusPanelInstance)


