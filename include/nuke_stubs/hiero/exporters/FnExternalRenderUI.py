# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import re
from PySide2 import (QtCore, QtGui, QtWidgets)

import hiero.ui
from . import FnExternalRender
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory

class ExternalRenderTaskUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """Initialize"""
    hiero.ui.TaskUIBase.__init__(self, FnExternalRender.ExternalRenderTask, preset, "External Render")

  def populateUI(self, widget, exportTemplate):
    pass
    
hiero.ui.taskUIRegistry.registerTaskUI(FnExternalRender.ExternalRenderPreset, ExternalRenderTaskUI)


class NukeRenderTaskUI(hiero.ui.RenderTaskUIBase):
  def __init__(self, preset, parenttask=FnExternalRender.NukeRenderTask, displayName="Nuke Write Node"):
    """Initialize"""
    hiero.ui.RenderTaskUIBase.__init__(self, parenttask, preset, displayName)

  def populateUI (self, widget, exportTemplate):
    layout = widget.layout()

    formLayout = TaskUIFormLayout()
    layout.addLayout(formLayout)

    self.buildCodecUI(formLayout, itemTaskType = self.taskItemType())

    # Write node name field. The design specifies this should be the second row,
    # after channels, so it needs to be inserted after calling buildCodecUI().
    writeNodeNameToolTip = """The name given to the Write node of the Nuke script.\nThe can be constructed using tokens available within the export Structure.\nThis may be useful for automated rendering of scripts with multiple write nodes."""
    uiProperty = UIPropertyFactory.create(type(""), key="writeNodeName", value="Write_{ext}", dictionary=self._preset.properties(), label="Write Node Name", tooltip=writeNodeNameToolTip)
    self._uiProperties.append(uiProperty)
    formLayout.insertRow(1, uiProperty._label, uiProperty)

    self.createCreateDirsWidget(formLayout)
    self.createBurnInWidgets(formLayout)

  def createCreateDirsWidget(self, formLayout):
    """ Create the widget for the create_dirs knob. """
    createDirsTooltip = "When rendering, create directories if they do not already exist"
    uiProperty = UIPropertyFactory.create(type(True),
                                          key="create_directories",
                                          value=True,
                                          dictionary=self._preset.properties(),
                                          label="Create Directories:",
                                          tooltip=createDirsTooltip)
    # Insert into the layout. TODO Confirm this is the correct place
    formLayout.insertRow(4, uiProperty._label, uiProperty)

  def createBurnInWidgets(self, formLayout):
    formLayout.addDivider("Burn-in")
    burninLayout = QtWidgets.QHBoxLayout()

    burninToolTip = """When enabled, a text burn-in is applied to the media using a Nuke Gizmo.\nClick Edit to define the information applied during burn-in. Burn-in fields accept any combination of dropdown tokens and custom text, for example {clip}_myEdit.\nYou can also include Nuke expression syntax, for example [metadata input/ctime], will add the creation time metadata in the Nuke stream."""

    burninCheckbox = QtWidgets.QCheckBox()
    burninCheckbox.setToolTip(burninToolTip)
    burninCheckbox.stateChanged.connect(self._burninEnableClicked)
    if self._preset.properties()["burninDataEnabled"]:
      burninCheckbox.setCheckState(QtCore.Qt.Checked)

    burninButton = QtWidgets.QPushButton("Edit")
    burninButton.setToolTip(burninToolTip)
    burninButton.clicked.connect(self._burninEditClicked)

    burninLayout.addWidget(burninCheckbox)
    burninLayout.addWidget(burninButton)

    formLayout.addRow("Burn-in Gizmo", burninLayout)

  def keepNukeScriptCheckboxChanged(self, state):
    # Slot to handle change of checkbox state
    self._preset.properties()["keepNukeScript"] = state == QtCore.Qt.Checked
    
  def readAllLinesCheckboxChanged(self, state):
    # Slot to handle change of checkbox state
    self._preset.properties()["readAllLinesForExport"] = state == QtCore.Qt.Checked

    
  def _burninEnableClicked(self, state):
    self._preset.properties()["burninDataEnabled"] = state == QtCore.Qt.Checked
    pass
    
  def _burninEditClicked(self):
    dialog = KnobEditDialog(self._preset.properties()["burninData"], FnExternalRender.NukeRenderTask.burninPropertyData)
    if dialog.exec_():
      self._preset.properties()["burninData"].update(dialog.data())

class BracketValidator(QtGui.QValidator):
  BRACKETS = ( ('{', '}'), ('(', ')'), ('[', ']'), )
  def __init__ (self):
    QtGui.QValidator.__init__(self)

  def validate ( self, input, pos ):
    for open, close in BracketValidator.BRACKETS:
      if input.count(open) != input.count(close):
        return QtGui.QValidator.Intermediate
    return QtGui.QValidator.Acceptable


class KnobEditDialog(QtWidgets.QDialog):
  """A Dialog to reflect a dictionary for the purpose of selecting knob values"""
  
  def __init__(self, data, properties, parent = None):
    QtWidgets.QDialog.__init__(self, parent)
    hiero.core.log.debug( "KnobEditDialog %s", data )
    self._data = dict(data)
    self._properties = properties
    self.initUI()
    
  def reset(self):
    #defaults = dict((datadict["knobName"], None) for datadict in self.properties() if datadict["knobName"] in self._data) 
    #self._data.update(defaults)
    self._data.clear()
    for uiProperty in self._uiProperties:
      uiProperty.update(commit=True)
      
  def data (self):
    return self._data      
  
  def accept (self):
    result = True
    for uiProperty in self._uiProperties:
      if hasattr(uiProperty, "checkValidation"):
        if not uiProperty.checkValidation():
          result = False
          uiProperty._widget.setFocus(QtCore.Qt.OtherFocusReason)
  
    if result:
      QtWidgets.QDialog.accept(self)
    else: 
      QtWidgets.QMessageBox.warning(self, "Validation Error", "Mismatched brackets.")
  
        
    
  def initUI(self):
    self._dialogLayout = QtWidgets.QVBoxLayout()
    self._layout = QtWidgets.QFormLayout()
    self._dialogLayout.addLayout(self._layout)
    self.setLayout(self._dialogLayout)
      
    toolTip = """Define the information applied during burn-in. Burn-in fields accept any combination of dropdown tokens and custom text, for example {clip}_myEdit.\nYou can also include Nuke expression syntax, for example [metadata input/ctime], will add the creation time metadata in the Nuke stream."""
    
    self._uiProperties = []
    for datadict in self._properties:
      uiProperty = UIPropertyFactory.create(type(datadict["value"]), key=datadict["knobName"], value=datadict["value"], dictionary=self._data, label=datadict["label"], tooltip=toolTip)
      self._uiProperties.append(uiProperty)
      if hasattr(uiProperty._widget, "setValidator"):
        uiProperty._widget.setValidator(BracketValidator())
      self._layout.addRow(datadict["label"], uiProperty)
    self._standardButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.RestoreDefaults)
    self._standardButtons.accepted.connect(self.accept)
    self._standardButtons.rejected.connect(self.reject)
    self._standardButtons.button(QtWidgets.QDialogButtonBox.RestoreDefaults).clicked.connect(self.reset)
    self._dialogLayout.addWidget(self._standardButtons)
    
hiero.ui.taskUIRegistry.registerTaskUI(FnExternalRender.NukeRenderPreset, NukeRenderTaskUI)
