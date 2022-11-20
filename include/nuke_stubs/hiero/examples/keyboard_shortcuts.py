# This example shows how you can add custom keyboard shortcuts to Hiero.
# If you wish for this code to be run on startup, copy it to your ~/.nuke/Python/Startup directory.

from hiero.ui import findMenuAction
from PySide2 import QtGui

# ADD YOUR CUSTOM SHORTCUTS BELOW

# Examples of adding keyboard shortcuts for 'Metadata View', the 'Spreadsheet View' and the 'Focus Next Tab' action.
# See also:
# https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QAction.html#PySide2.QtWidgets.PySide2.QtWidgets.QAction.setShortcut

myMenuItem = findMenuAction('Metadata View')
myMenuItem.setShortcut(QtGui.QKeySequence('Alt+M'))

# This sets a keyboard shortcut for opening the Spreadsheet View
myMenuItem = findMenuAction('foundry.project.openInSpreadsheet')
myMenuItem.setShortcut(QtGui.QKeySequence('S'))

# This allows you to override the Focus Next Tab (Ctrl+Shift+]) keyboard shortcut
for a in hiero.ui.registeredActions():
  if a.objectName() == 'foundry.application.focusNextTab':
    a.setShortcut("Ctrl+Space")
    break

playButton = hiero.ui.findMenuAction('Play/Pause')
playButton.setShortcut("")
