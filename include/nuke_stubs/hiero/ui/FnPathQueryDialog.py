# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.


import os

from PySide2 import (QtCore, QtWidgets)
from hiero.core import util
import foundry.ui


#We need the dialog to be destroyed after being closed, otherwise it will cause crash as on bug 45216
#FnPathQueryDialog can't inherit from QDialog because given the requirement to be destroyed after
#the exec returns, we wouldn't be able to get the path entered by the user
class PathQueryDialog(object):
  def __init__(self, message, title, isDirectory, path = None, parent = None):
    self._path = path
    self._dialog = QtWidgets.QDialog(parent=parent)
    self._dialog.setWindowTitle(title)
    self._dialog.setAttribute( QtCore.Qt.WA_DeleteOnClose, True)
    self._dialog._dialogLayout = QtWidgets.QVBoxLayout()
    self._dialog.setLayout(self._dialog._dialogLayout)
    self._dialog.setModal(True)
    self._dialog._dialogLayout.addWidget(QtWidgets.QLabel(message))
    self._dialog._pathWidget = foundry.ui.FnFilenameField(isDirectory, caption=title)
    self._dialog._dialogLayout.addWidget(self._dialog._pathWidget)
    if path:
      self._dialog._pathWidget.setFilename(path)
    
    self._dialog._standardButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    okButton = self._dialog._standardButtons.button(QtWidgets.QDialogButtonBox.Ok)

    self._dialog._standardButtons.accepted.connect(self._dialog.accept)
    self._dialog._standardButtons.rejected.connect(self._dialog.reject)
    self._dialog._dialogLayout.addWidget(self._dialog._standardButtons)

    self._dialog._pathWidget.filenameChanged.connect(self._filenameChanged)
    self._filenameChanged()

  def path (self):
    return self._path

  #since PathQueryDialog doesn't inherit from QDialog, added exec_ method to avoid changing the interface with PathQueryDialog
  def exec_(self):
    return self._dialog.exec_()

  def _filenameChanged(self):
    self._path = self._dialog._pathWidget.filename()
    # Don't enable the Ok button unless we have a valid path
    okButton = self._dialog._standardButtons.button(QtWidgets.QDialogButtonBox.Ok)
    okButton.setEnabled( util.filesystem.exists(self.path()) )

