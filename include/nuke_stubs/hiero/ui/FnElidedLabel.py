# -*- coding: utf-8 -*-

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

class ElidedLabel(QtWidgets.QFrame):
  """ Class for showing text which is elided if it exceeds the widget's width.
  Note that this can currently only handle showing a single line of text.
  """
  def __init__(self, parent=None):
    QtWidgets.QFrame.__init__(self, parent)
    self._elideMode = QtCore.Qt.ElideMiddle
    self._text = ""
    self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

  def text(self):
    """ Get the text being displayed. """
    return self._text

  def setText(self, text):
    """ Set the text to display. """
    self._text = text
    self.update()

  def elideMode(self):
    """ Get the elide mode. """
    return self._elideMode

  def setElideMode(self, mode):
    """ Set the elide mode. """
    self._elideMode = mode

  def minimumSizeHint(self):
    return QtCore.QSize(1, self.fontMetrics().height())

  def paintEvent(self, event):
    QtWidgets.QFrame.paintEvent(self, event)

    if not self._text:
      return
    painter = QtGui.QPainter(self)
    fontMetrics = painter.fontMetrics()
    elidedText = fontMetrics.elidedText(self._text, self._elideMode, self.width())
    painter.drawText(QtCore.QPoint(0, fontMetrics.ascent()), elidedText)
