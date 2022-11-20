# -*- coding: utf-8 -*-

from PySide2 import QtCore, QtGui, QtWidgets


class DisclosureButton(QtWidgets.QCheckBox):
  """
  Button used for showing/hiding widgets in a layout.  This is a Python reimplementation of the class of the same name in the Core/UI library.
  """

  def __init__(self, contentsVisible=True, parent=None):
    """ Initialise the button with the given parent and contents visible flag. """
    QtWidgets.QCheckBox.__init__(self, parent)
    self._contentsVisible = contentsVisible
    self.setCheckable(True)
    self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self._widgets = []
    self.clicked.connect(self.showOrHideWidgets)


  def addWidget(self, widget):
    """ Add a new widget to the set of those controlled by this
        disclosure button (the widget is not a layout and so the
        new widget should be added to the hierarchy of displayed widgets
        in some other way).  If this checkbox is ticked and it's marked
        "contents visible" than the widget will be shown, otherwise
        it will be hidden. """
    self._widgets.append(widget)
    widget.setVisible(self.widgetsVisible())


  def removeWidget(self, widget):
    """ Remove a widget from the button's control. """
    self._widgets.remove(widget)


  def setVisible(self, newVisible):
    """ Set the visibility of the widget.  Will also change the visibility of any controlled widgets. """
    QtWidgets.QCheckBox.setVisible(self, newVisible)
    self.showOrHideWidgets()


  def widgetsVisible(self):
    """ Get if controlled widgets should be visible. """
    return self.isChecked() and self.isVisible()


  def showOrHideWidgets(self):
    """ Update the visibility of controlled widgets. """
    visible = self.widgetsVisible()
    for widget in self._widgets:
      widget.setVisible(visible)


  def paintEvent(self, event):
    """ Paint the widget. """
    style = self.style()
    styleOption = QtWidgets.QStyleOptionButton()
    subStyleOption = QtWidgets.QStyleOptionButton()
    self.initStyleOption(styleOption)
    self.initStyleOption(subStyleOption)

    painter = QtGui.QPainter(self)
    subStyleOption.rect = style.subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator, styleOption, self)
    brush = QtCore.Qt.black if self.isEnabled() else self.palette().color(QtGui.QPalette.Disabled, QtGui.QPalette.Light)
    painter.setBrush(brush)
    painter.setPen(QtCore.Qt.NoPen)

    path = QtGui.QPainterPath()
    if self.isChecked():
      path.moveTo(4, 3)
      path.lineTo(13, 3)
      path.lineTo(8, 11)
    else:
      path.moveTo(4, 3)
      path.lineTo(12, 7)
      path.lineTo(4, 12)
    path.moveTo(subStyleOption.rect.left(), subStyleOption.rect.top())
    painter.drawPath(path)

    subStyleOption.rect = style.subElementRect(QtWidgets.QStyle.SE_CheckBoxContents, styleOption, self)
    style.drawControl(QtWidgets.QStyle.CE_PushButtonLabel, subStyleOption, painter, self)

