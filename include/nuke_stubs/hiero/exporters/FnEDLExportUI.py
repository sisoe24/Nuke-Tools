# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from PySide2 import (QtCore, QtWidgets)

import hiero.ui
from . import FnEDLExportTask
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout


class EDLExportUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """Initialize"""
    hiero.ui.TaskUIBase.__init__(self, FnEDLExportTask.EDLExportTask, preset, "EDL Exporter")
    self._fromClipLineEdit = None
    
  def absPathCheckboxChanged(self, state):
    # Slot to handle change of checkbox state
    self._preset.properties()["abspath"] = state == QtCore.Qt.Checked
  
  def truncateCheckboxChanged(self, state):
    # Slot to handle change of checkbox state
    self._preset.properties()["truncate"] = state == QtCore.Qt.Checked
  
  def fromClipChanged(self):
    self._preset.properties()["fromClip"] = self._fromClipLineEdit.text()
  
  def reelNameChanged(self):
    self._preset.properties()["reelName"] = self._reelNameLineEdit.text()
  
  def populateUI(self, widget, exportTemplate):
    layout = widget.layout()
    formLayout = TaskUIFormLayout()
    layout.addLayout(formLayout)
    
    # create checkbox for whether the EDL task should add Absolute Paths
    absPathCheckbox = QtWidgets.QCheckBox()
    absPathCheckbox.setToolTip("Enable to use the absolute file path for filenames instead of just the filename part.")
    absPathCheckbox.setCheckState(QtCore.Qt.Unchecked)
    if self._preset.properties()["abspath"]:
      absPathCheckbox.setCheckState(QtCore.Qt.Checked)
    absPathCheckbox.stateChanged.connect(self.absPathCheckboxChanged)

    kTrackItemTokensToolTip = "Valid tokens are: {shot}, {clip}, {track}, {sequence}, {event}, {fps}, {filename}, {filebase}, {fileext}, {filehead}"

    kReelNameToolTip = "Define the text to output as the reel name in the EDL. If not set, the reel name of the clip will be used.\n" + kTrackItemTokensToolTip
    kFromClipToolTip = "Define the text to append to 'from' comment fields like '* FROM CLIP NAME:'.\n" + kTrackItemTokensToolTip
    
    self._reelNameLineEdit = QtWidgets.QLineEdit()
    self._reelNameLineEdit.setToolTip(kReelNameToolTip)
    self._reelNameLineEdit.setText("")
    if self._preset.properties()["reelName"]:
      self._reelNameLineEdit.setText(self._preset.properties()["reelName"])
    self._reelNameLineEdit.textChanged.connect(self.reelNameChanged)

    truncateCheckBox = QtWidgets.QCheckBox()
    truncateCheckBox.setToolTip("Enable to truncate reel names to 8 characters (required by some applications).")
    truncateCheckBox.setCheckState(QtCore.Qt.Unchecked)
    if self._preset.properties()["truncate"]:
      truncateCheckBox.setCheckState(QtCore.Qt.Checked)
    truncateCheckBox.stateChanged.connect(self.truncateCheckboxChanged)
    
    self._fromClipLineEdit = QtWidgets.QLineEdit()
    self._fromClipLineEdit.setToolTip(kFromClipToolTip)
    self._fromClipLineEdit.setText("{filename}")
    if self._preset.properties()["fromClip"]:
      self._fromClipLineEdit.setText(self._preset.properties()["fromClip"])
    self._fromClipLineEdit.textChanged.connect(self.fromClipChanged)
    
    # Add Checkbox to formLayout
    formLayout.addRow("Reel Name:", self._reelNameLineEdit)
    formLayout.addRow("Truncate Reel Name:", truncateCheckBox)
    formLayout.addRow("Use Absolute Path:", absPathCheckbox)
    formLayout.addRow("From Clip Name:", self._fromClipLineEdit)
 
    
hiero.ui.taskUIRegistry.registerTaskUI(FnEDLExportTask.EDLExportPreset, EDLExportUI)
