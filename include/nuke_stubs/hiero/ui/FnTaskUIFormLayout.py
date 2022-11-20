# Copyright (c) 2016 The Foundry Visionmongers Ltd.  All Rights Reserved.

import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

class TaskUILayoutDivider(QtWidgets.QWidget):
  """ Widget for showing a divider in TaskUIFormLayout. """
  def __init__(self, text):
    QtWidgets.QWidget.__init__(self)

    hLayout = QtWidgets.QHBoxLayout()
    hLayout.setContentsMargins(0, 2, 0, 2)
    self._label = QtWidgets.QLabel(text)
    hLayout.addWidget(self._label)
    divider = QtWidgets.QFrame()
    divider.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Sunken)
    divider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    hLayout.addWidget(divider)
    self.setLayout(hLayout)

  def setText(self, text):
    """ Set the text shown in the divider. """
    self._label.setText(text)


class TaskUIFormLayout(QtWidgets.QFormLayout):
  """ Specialised form layout for constructing task UIs. This includes helpers
  for adding dividers, multiple widgets on a row, and enabling/disabling widgets.
  """
  def __init__(self, parent=None):
    QtWidgets.QFormLayout.__init__(self, parent)
    self.setContentsMargins(0, 0, 0, 0)
    self._widgetsLabelsMap = {}

  def addDivider(self, text):
    """ Add a divider showing the given text, and return it. """
    divider = TaskUILayoutDivider(text)
    self.addRow(divider)
    return divider

  def addMultiWidgetRow(self, labels, widgets):
    """ Add multiple widgets, each with a label, to a single row. """
    hLayout = QtWidgets.QHBoxLayout()
    hLayout.setContentsMargins(0, 0, 0, 0)
    hLayout.addWidget(widgets[0])
    for label, widget in zip(labels[1:], widgets[1:]):
      labelWidget = QtWidgets.QLabel(label)
      hLayout.addWidget(labelWidget)
      hLayout.addWidget(widget)
      self._widgetsLabelsMap[widget] = labelWidget
    self.addRow(labels[0], hLayout)
    # The QLabel for the first widget is the row's label
    self._widgetsLabelsMap[widgets[0]] = self.labelForField(hLayout)

  def setWidgetEnabled(self, widget, enabled):
    """ Set the enabled state of a widget in the layout. This will also set the
    state of its label.
    """
    widget.setEnabled(enabled)
    try:
      label = self._widgetsLabelsMap[widget]
    except KeyError:
      label = self.labelForField(widget)
    if label:
      label.setEnabled(enabled)

  def setWidgetVisible(self, widget, visible):
    """ Set the visible state of a widget in the layout. This will also set the
    state of its label.
    """
    #TODO: get rid of the padding on the row when hiding the widget
    widget.setVisible(visible)
    try:
      label = self._widgetsLabelsMap[widget]
    except KeyError:
      label = self.labelForField(widget)
    if label:
      label.setVisible(visible)
