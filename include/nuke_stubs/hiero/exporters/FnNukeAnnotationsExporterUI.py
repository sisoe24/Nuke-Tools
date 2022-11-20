from PySide2 import(QtCore, QtGui, QtWidgets)

import hiero.ui
from . import FnNukeAnnotationsExporter
from .FnNukeExporterWidgets import NukeProjectNodeSelectionWidget,TimelineWriteNodeWidget
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory


class NukeAnnotationsExporterUI(hiero.ui.TaskUIBase):
  """ UI for NukeAnnotationsExporter.  This is largely the same as the NukeShotExporterUI, with some options hidden. """

  def __init__(self, preset):
    super(NukeAnnotationsExporterUI, self).__init__(FnNukeAnnotationsExporter.NukeAnnotationsExporter, preset, "Nuke Annotations File")

    self._uiProperties = []
    self._tags = []

  def updatePreset( self,presetValue, model, topLeft, bottomRight):
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
        presetValue.append(item.text())
    # Update the path changed callbacks
    self._preset.initialiseCallbacks(self._exportTemplate)
    
  def readPresetChanged (self, topLeft, bottomRight):
    presetValue = self._preset.properties()["readPaths"] = []
    model = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kReadNode)
    self.updatePreset(presetValue, model, topLeft, bottomRight)


  def writePresetChanged (self, topLeft, bottomRight):
    presetValue = self._preset.properties()["writePaths"] = []
    model = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kWriteNode)
    self.updatePreset(presetValue, model, topLeft, bottomRight)


  def timelineWriteNodeChanged(self, text):
    hiero.core.log.debug( "setting timelineWriteNode property to:\'%s\'"%text)
    self._preset.properties()["timelineWriteNode"] = text


  def populateUI (self, widget, exportTemplate):
    if exportTemplate:
      self._exportTemplate = exportTemplate
      layout = widget.layout()
      
      ###Node selection widget
      self._nodeSelectionWidget = NukeProjectNodeSelectionWidget(exportTemplate,self._preset)
      self._nodeSelectionWidget.addNodeSelector(
        NukeProjectNodeSelectionWidget.kReadNode, "Read Nodes", "readPaths",
        "Select multiple entries within the shot template to be used as inputs "
        "for the read nodes (i.e. symlink, transcode.. etc).\n No selection will "
        "mean that read nodes are created in the nuke script pointing directly "
        "at the source media.\n")
      self._nodeSelectionWidget.addNodeSelector(
        NukeProjectNodeSelectionWidget.kWriteNode, "Write Nodes", "writePaths",
        "Add one or more \"Nuke Write Node\" tasks to your export structure "
        "to define the path and codec settings for the nuke script.\nIf no "
        "write paths are selected, no write node will be added to the nuke script.",
        True)
      layout.addWidget(self._nodeSelectionWidget)
      self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kReadNode).dataChanged.connect(self.readPresetChanged)
      writeModel = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kWriteNode)
      self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kWriteNode).dataChanged.connect(self.writePresetChanged)


      formLayout = TaskUIFormLayout()
      layout.addLayout(formLayout)

      self._timelineWriteNode = TimelineWriteNodeWidget(writeModel, self._preset)
      formLayout.addRow("Timeline Write Node:",self._timelineWriteNode)
      self._timelineWriteNode.timelineWriteNodeChanged.connect(self.timelineWriteNodeChanged)

      ###Retime
      formLayout.addDivider("Retiming")
      
      retimeToolTip = """Sets the retime method used if retimes are enabled.\n-Motion - Motion Estimation.\n-Blend - Frame Blending.\n-Frame - Nearest Frame"""
      key, value = "method", ("None", "Motion", "Frame", "Blend")
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label="Retime Method", tooltip=retimeToolTip)
      self._uiProperties.append(uiProperty)
      formLayout.addRow(uiProperty._label + ":", uiProperty)

      self.readPresetChanged(None, None)

      #Effects
      formLayout.addDivider("Effects")
      includeEffectsToolTip = """Enable this to include soft effects in the exported script."""
      key, value, label = "includeEffects", True, "Include Effects"
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=includeEffectsToolTip)
      formLayout.addRow(label+":", uiProperty)
      self._uiProperties.append(uiProperty)

      ###Additional Nodes
      formLayout.addDivider("AdditionalNodes")
      additionalNodesToolTip = """When enabled, allows custom Nuke nodes to be added into Nuke Scripts.\n Click Edit to add nodes on a per Shot, Track or Sequence basis.\n Additional Nodes can also optionally be filtered by Tag."""

      additionalNodesLayout = QtWidgets.QHBoxLayout()
      additionalNodesCheckbox = QtWidgets.QCheckBox()
      additionalNodesCheckbox.setToolTip(additionalNodesToolTip)
      additionalNodesCheckbox.stateChanged.connect(self._additionalNodesEnableClicked)
      if self._preset.properties()["additionalNodesEnabled"]:
        additionalNodesCheckbox.setCheckState(QtCore.Qt.Checked)
      additionalNodesButton = QtWidgets.QPushButton("Edit")
      additionalNodesButton.setToolTip(additionalNodesToolTip)
      additionalNodesButton.clicked.connect(self._additionalNodesEditClicked)
      additionalNodesLayout.addWidget(additionalNodesCheckbox)
      additionalNodesLayout.addWidget(additionalNodesButton)
      formLayout.addRow("Additional Nodes:", additionalNodesLayout)


  def _additionalNodesEnableClicked(self, state):
    self._preset.properties()["additionalNodesEnabled"] = state == QtCore.Qt.Checked


  def _additionalNodesEditClicked(self):
    dialog = FnAdditionalNodesDialog.AdditionalNodesDialog(self._preset.properties()["additionalNodesData"], self._tags)
    if dialog.exec_():
      self._preset.properties()["additionalNodesData"] = dialog.data()


  def setTags ( self, tags ):
    """setTags passes the subset of tags associated with the selection for export"""
    self._tags = tags


hiero.ui.taskUIRegistry.registerTaskUI(FnNukeAnnotationsExporter.NukeAnnotationsPreset, NukeAnnotationsExporterUI)
