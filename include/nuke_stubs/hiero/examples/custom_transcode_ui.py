# Example of the user interface for a custom transcoder (goes with the custom_transcode.py code)

import hiero.ui
import sys

from PySide2 import (QtCore, QtWidgets)

from hiero.exporters import FnTranscodeExporterUI
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout

import custom_transcode

class CustomTranscodeUI(FnTranscodeExporterUI.TranscodeExporterUI):
  def __init__(self, preset):
    """Initialize"""
    FnTranscodeExporterUI.TranscodeExporterUI.__init__(self, preset)
    
    self._displayName = "Custom Transcode"
    self._taskType = custom_transcode.CustomTranscode
    
    
  def insertAudioCheckboxChanged(self, state):
    # Slot to handle change of checkbox state
    self._preset._properties["insertAudio"] = state == QtCore.Qt.Checked

  def populateUI (self, widget, exportTemplate):
    layout = TaskUIFormLayout(widget)
    widget.layout().addLayout(layout)
    self.buildCodecUI(layout, itemTaskType = self.taskItemType())
    
    platformUsesQuicktime = sys.platform.startswith("win32") or sys.platform.startswith("darwin")

    # Hide option of platform doesnt use quicktime
    if platformUsesQuicktime:
      # Create Checkbox
      audioCheckbox = QtWidgets.QCheckBox()
      
      # Set checkstate according to preset value
      audioCheckbox.setCheckState(QtCore.Qt.Unchecked)
      if self._preset._properties["insertAudio"]:
        audioCheckbox.setCheckState(QtCore.Qt.Checked)
      
      # Connect signal
      audioCheckbox.stateChanged.connect(self.insertAudioCheckboxChanged)
      
      # Set Tooltip
      audioCheckbox.setToolTip("If writing a mov it may be possible to inject audio from a single file. First audio file on first audio track will be used.")
      
      # Add Checkbox to layout
      layout.addRow("Insert Audio Where Possible:", audioCheckbox)


hiero.ui.taskUIRegistry.registerTaskUI(custom_transcode.CustomTranscodePreset, CustomTranscodeUI)
