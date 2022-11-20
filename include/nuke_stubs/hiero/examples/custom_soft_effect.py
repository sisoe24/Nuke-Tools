# custom_soft_effect.py - Example of registering a custom Soft Effect 
from hiero.ui import registerAction
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction

# This creates an action with an icon and effect named 'Awesome OCIO'
action = QAction(QIcon("icons:LUT.png"), "Awesome OCIO", None)

# Soft effect actions can be found by prefixing the QAction's objectName with: 'foundry.timeline.effect'
action.setObjectName("foundry.timeline.effect.addAwesomeEffect")

# You can optionally set a tooltip for this action
action.setToolTip("Will apply an AwesomeOCIO soft effect")

# Setting of Data here will point to the Nuke node class name.
# Here, we assume there is a plugin with a Class name 'AwesomeOCIO'
# Note: for soft effects to work, the Nuke node must use a gpuEngine implementation.
action.setData("AwesomeOCIO")

# This registers your custom action with the Effects Menu
registerAction(action)
