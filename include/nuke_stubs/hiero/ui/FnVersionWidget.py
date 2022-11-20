# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.


import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets


class VersionWidget(QtWidgets.QSpinBox):
  """ Widget for editing version indices and padding. This extends QSpinbox to
  allow the user to add leading zeroes to specify padding.
  """

  paddingChanged = QtCore.Signal(int)

  def __init__ (self):
    QtWidgets.QSpinBox.__init__(self)
    self._padding = 2
    self.setRange(0, 99999)
    self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

  def setPadding(self, padding):
    if padding == self._padding:
      return
    self._padding = padding
    value = self.value()
    # Toggle value to update padding
    self.setValue(99999)
    self.setValue(value)  
    self.adjustSize()
    self.updateGeometry()
    self.paddingChanged.emit(self._padding)

  def padding(self):
    return self._padding

  def sizeHint (self):
    count = len(self.textFromValue(self.value()))
    return QtCore.QSize(max(count * 15, 80), 20)

  def textFromValue(self, value):
    text = format(value, "0%id" % self._padding)
    return text

  def valueFromText(self, text):
    try:
      value = int(text)
      self._padding = len(text)
      self.paddingChanged.emit(self._padding)
      return value
    except:
      return self.value()
