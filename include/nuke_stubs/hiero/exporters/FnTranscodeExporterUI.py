# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import hiero.ui

from PySide2 import(QtCore, QtGui, QtWidgets)
from . import FnTranscodeExporter
from . import FnExternalRenderUI
from . import FnAdditionalNodesDialog
from . import FnAudioConstants
from . import FnAudioHelper
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import *

class TranscodeExporterUI(FnExternalRenderUI.NukeRenderTaskUI):
  def __init__(self, preset):
    """Initialize"""
    FnExternalRenderUI.NukeRenderTaskUI.__init__(self, preset, FnTranscodeExporter.TranscodeExporter, "Transcode Images")
    self._tags = []

  def movCodecComboBoxChanged(self):
    FnExternalRenderUI.NukeRenderTaskUI.movCodecComboBoxChanged(self)
    self._enableReadAllLinesForCodec()

  def populateUI (self, widget, exportTemplate):
    layout = widget.layout()

    formLayout = TaskUIFormLayout()
    self._formLayout = formLayout
    layout.addLayout(formLayout)

    self.buildCodecUI(formLayout, itemTaskType = self.taskItemType())

    ###RETIME
    formLayout.addDivider("Retiming")
    retimeToolTip = """Sets the retime method used if retimes are enabled.\n-Motion - Motion Estimation.\n-Blend - Frame Blending.\n-Frame - Nearest Frame"""
    key, value = "method", ("None", "Motion", "Frame", "Blend")
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label="Retime Method", tooltip=retimeToolTip)
    self._uiProperties.append(uiProperty)
    formLayout.addRow(uiProperty._label + ":", uiProperty)

    ###Effects
    formLayout.addDivider("Effects & Annotations")
    includeEffectsToolTip = """Enable this to include soft effects in the exported script."""
    key, value, label = "includeEffects", True, "Include Effects"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=includeEffectsToolTip)
    formLayout.addRow(label+":", uiProperty)
    self._uiProperties.append(uiProperty)

    includeAnnotationsToolTip = """Enable this to include annotations in the exported script."""
    key, value, label = "includeAnnotations", True, "Include Annotations"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=includeAnnotationsToolTip)
    formLayout.addRow(label+":", uiProperty)
    self._uiProperties.append(uiProperty)

    ### AUDIO
    formLayout.addDivider("Audio")
    self._audioLayout = TaskUIFormLayout();
    formLayout.addRow(self._audioLayout)

    includeAudioToolTip = ("This will include audio in the video export if the selected file type supports it." 
                           " If not, it will create a separate audio file for the exported video.")
    deleteAudioToolTip = ("This will delete the separate audio file created after the export is complete "
                          "(this option will be disabled if the selected file type does not support audio).")
    codecToolTip = ("Audio Codec (If the file type is set to MOV, it will only support the liner PCM codec).")

    key, value = "includeAudio", False
    includeAudioWidget = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties)
    includeAudioWidget.setToolTip(includeAudioToolTip)
    self._uiProperties.append(includeAudioWidget)
    includeAudioWidget.propertyChanged.connect(self.onIncludeAudioChanged)
    self._audioLayout.addRow("Include Audio:", includeAudioWidget)

    FnAudioHelper.createCodecProperty(self, self._audioLayout, self.updateAudioSettings, codecToolTip)

    key, value = "deleteAudio", True
    deleteAudioWidget = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties)
    deleteAudioWidget.setToolTip(deleteAudioToolTip)
    self._uiProperties.append(deleteAudioWidget)
    self._deleteAudioWidget = deleteAudioWidget
    formLayout.addRow("Delete Audio File:", deleteAudioWidget)

    self.updateAudioSettings()

    ###BURN-IN
    formLayout.addDivider("Burn-in")
    burninToolTip = """When enabled, a text burn-in is applied to the media using a Nuke Gizmo.\nClick Edit to define the information applied during burn-in. Burn-in fields accept any combination of dropdown tokens and custom text, for example {clip}_myEdit.\nYou can also include Nuke expression syntax, for example [metadata input/ctime], will add the creation time metadata in the Nuke stream."""

    burninLayout = QtWidgets.QHBoxLayout()
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
    formLayout.addRow("Burn-in Gizmo:", burninLayout)

    ###ADDITIONAL NODES
    formLayout.addDivider("Additional Nodes")

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

    ###NUKE SCRIPT
    # create checkbox for whether the EDL task should add Absolute Paths
    formLayout.addDivider("Nuke Script")
    keepNukeScriptCheckbox = QtWidgets.QCheckBox()
    keepNukeScriptCheckbox.setCheckState(QtCore.Qt.Unchecked)
    if self._preset.properties()["keepNukeScript"]:
      keepNukeScriptCheckbox.setCheckState(QtCore.Qt.Checked)
    keepNukeScriptCheckbox.stateChanged.connect(self.keepNukeScriptCheckboxChanged)
    keepNukeScriptCheckbox.setToolTip("A Nuke script is created for each transcode. If you'd like to keep the temporary .nk file from being destroyed, enable this option. The script will get generated into the same directory as the transcode output")
    formLayout.addRow("Keep Nuke Script:", keepNukeScriptCheckbox)

    # create checkbox for whether exports should read all lines from the input in one go (where possible).
    self._codecTypeComboBox.currentIndexChanged.connect(self._enableReadAllLinesForCodec)
    self._readAllLinesCheckbox = QtWidgets.QCheckBox()
    checkBoxState = QtCore.Qt.Checked if self._preset.properties()["readAllLinesForExport"] else QtCore.Qt.Unchecked
    self._readAllLinesCheckbox.setCheckState(checkBoxState)

    self._readAllLinesCheckbox.stateChanged.connect(self.readAllLinesCheckboxChanged)
    self._readAllLinesCheckbox.setToolTip("Select this to set up the export script to read all lines from the inputs in one go, where possible (currently, this only applies to dpx inputs). This option can be faster for I/O-heavy export scripts.")
    formLayout.addRow("Read All Lines:", self._readAllLinesCheckbox)

    self._useSingleSocketCheckbox = QtWidgets.QCheckBox()
    checkBoxState = QtCore.Qt.Checked if self._preset.properties()["useSingleSocket"] else QtCore.Qt.Unchecked
    self._useSingleSocketCheckbox.setCheckState(checkBoxState)
    self._useSingleSocketCheckbox.stateChanged.connect(self._useSingleSocketClicked)
    self._useSingleSocketCheckbox.setToolTip("Select this to set up the export process to be limited to a single cpu socket, this can increase performance. This option is only available for machines with multiple cpu sockets and when using Single Render Process.")
    formLayout.addRow("Use Single Socket:", self._useSingleSocketCheckbox)

    enableSingleSocketOption = hiero.core.taskRegistry.isSingleSocketAllowed()
    self._useSingleSocketCheckbox.setEnabled(enableSingleSocketOption)
    useSingleSocketLabel = formLayout.labelForField(self._useSingleSocketCheckbox)
    useSingleSocketLabel.setEnabled(enableSingleSocketOption)

  def _enableReadAllLinesForCodec(self):
    checkBoxState = QtCore.Qt.Checked if self._preset._defaultReadAllLinesForCodec() else QtCore.Qt.Unchecked
    self._readAllLinesCheckbox.setCheckState(checkBoxState)
    assert(self._readAllLinesCheckbox.isChecked() == self._preset.properties()["readAllLinesForExport"])

  def _useSingleSocketClicked(self, state):
    self._preset.properties()["useSingleSocket"] = state == QtCore.Qt.Checked

  def _additionalNodesEnableClicked(self, state):
    self._preset.properties()["additionalNodesEnabled"] = state == QtCore.Qt.Checked
    pass
    
  def _additionalNodesEditClicked(self):
    dialog = FnAdditionalNodesDialog.AdditionalNodesDialog(self._preset.properties()["additionalNodesData"], self._tags)
    if dialog.exec_():
      self._preset.properties()["additionalNodesData"] = dialog.data()
    """ release the all entries in the panel after closing it to prevent TP 200161 """
    dialog.cleanup()
    pass
        
  def setTags ( self, tags ):
    """setTags passes the subset of tags associated with the selection for export"""
    self._tags = tags

  def onIncludeAudioChanged(self):
    self.updateAudioSettings()

  def codecTypeComboBoxChanged(self, value):
    FnExternalRenderUI.NukeRenderTaskUI.codecTypeComboBoxChanged(self, value)
    self.updateAudioSettings()

  def updateAudioSettings(self):
    deleteAudioValid = self._preset.deleteAudioValid()
    self._formLayout.setWidgetEnabled(self._deleteAudioWidget, deleteAudioValid)
    enabled = self._preset.includeAudio()

    # If delete audio is valid, that would imply a mov container, which does not support
    # non PCM codecs yet
    self._audioLayout.setWidgetEnabled(self._codecProperty, enabled and not deleteAudioValid)
    if (deleteAudioValid):
        self._preset.properties()[FnAudioConstants.kCodecKey] = FnAudioConstants.kNonCompressedCodec
        self._codecProperty.update()

    FnAudioHelper.createCodecSpecificProperties(self, self._audioLayout, enabled)

hiero.ui.taskUIRegistry.registerTaskUI(FnTranscodeExporter.TranscodePreset, TranscodeExporterUI)
