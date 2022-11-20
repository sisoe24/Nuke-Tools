import os.path
from PySide2 import QtWidgets

import hiero.ui
from . import FnAudioExportTask
from . import FnAudioConstants
from . import FnAudioHelper
from hiero.ui.FnUIProperty import UIPropertyFactory
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout

class AudioExportUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """Initialize"""
    hiero.ui.TaskUIBase.__init__(self, FnAudioExportTask.AudioExportTask, preset, "Audio Export")

  def populateUI(self, widget, exportTemplate):
    layout = widget.layout()

    formLayout = TaskUIFormLayout()
    self._formLayout = formLayout

    FnAudioHelper.createCodecProperty(self, formLayout, self.codecChanged, ("Audio Codec."))

    FnAudioHelper.createCodecSpecificProperties(self, self._formLayout, True)

    layout.addLayout(formLayout)

  def codecChanged(self):
    FnAudioHelper.createCodecSpecificProperties(self, self._formLayout, True)
    
hiero.ui.taskUIRegistry.registerTaskUI(FnAudioExportTask.AudioExportPreset, AudioExportUI)
