from PySide2.QtCore import QObject, QPointF
from PySide2.QtGui import QColor
import hiero.ui
from . import messages
from . synctool import SyncTool

"""
Classes for syncing the viewer cursor state and position between connected clients.
"""

messages.defineMessageType('SyncCursorPosition', ('x', float), ('y', float))
messages.defineMessageType('SyncCursorLeave')


class SyncClientCursor(SyncTool):
  """ Logic for syncing the cursor position within a session. """

  def __init__(self, messageDispatcher, clientDataProvider):
    super(SyncClientCursor, self).__init__(messageDispatcher)
    self.cursorTool = None
    self._cursorData = dict()
    self._dataProvider = clientDataProvider

    # Get the current viewer state.
    currentViewer = hiero.ui.currentViewer()
    if currentViewer:
      # Get the cursor tool and subscribe to its signals.
      self.cursorTool = currentViewer.cursorTool()
      if self.cursorTool:
        self.cursorTool.cursorPositionChanged.connect(self._onCursorPositionChanged)
        self.cursorTool.cursorLeave.connect(self._onCursorLeave)

    # Register for the event emitted when the Viewer changes
    self.registerEventCallback('kCurrentViewerChanged', self._onViewerChanged)

    self.messageDispatcher._registerCallback(messages.SyncCursorPosition, self._onSyncPosition)
    self.messageDispatcher._registerCallback(messages.SyncCursorLeave, self._onSyncLeave)
    self.messageDispatcher._registerCallback(messages.Disconnected, self._onClientDisconnected)

  def _onViewerChanged(self, event):
    self._setViewer(event.viewer)

  def _setViewer(self, viewer):
    if self.cursorTool:
      self.cursorTool.cursorPositionChanged.disconnect(self._onCursorPositionChanged)
      self.cursorTool.cursorLeave.disconnect(self._onCursorLeave)
      self.cursorTool = None

    if viewer:
      # Get the cursor tool and subscribe to its signals.
      self.cursorTool = viewer.cursorTool()
      if self.cursorTool:
        self.cursorTool.cursorPositionChanged.connect(self._onCursorPositionChanged)
        self.cursorTool.cursorLeave.connect(self._onCursorLeave)

  def _onCursorPositionChanged(self, point):
    msg = messages.SyncCursorPosition(x=point.x(), y=point.y())
    self.messageDispatcher.sendMessage(msg)

  def _onCursorLeave(self):
    msg = messages.SyncCursorLeave()
    self.messageDispatcher.sendMessage(msg)

  def _setCursors(self):
    self.cursorTool.setCursors(list(self._cursorData.values()))

  def _onSyncPosition(self, msg):
    senderId = msg.sender
    if senderId not in self._dataProvider.clientData:
      return

    clientId, (colorR, colorG, colorB) = self._dataProvider.clientData[senderId]
    clientColor = QColor(colorR, colorG, colorB)
    cursor = hiero.ui.ViewerCursor(QPointF(msg.x, msg.y), clientColor, clientId)
    self._cursorData[senderId] = cursor
    self._setCursors()

  def _onLeaveOrDisconnected(self, clientId):
    self._cursorData.pop(clientId, None)
    self._setCursors()

  def _onSyncLeave(self, msg):
    self._onLeaveOrDisconnected(msg.sender)

  def _onClientDisconnected(self, msg):
    self._onLeaveOrDisconnected(msg.disconnected)

  def shutdown(self):
    super(SyncClientCursor, self).shutdown()
    self._setViewer(None)
    self._dataProvider = None
