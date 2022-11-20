import os.path

import hiero.ui
from . import FnCopyExporter


class CopyExporterUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """Initialize"""
    hiero.ui.TaskUIBase.__init__(self, FnCopyExporter.CopyExporter, preset, "Copy Exporter")


hiero.ui.taskUIRegistry.registerTaskUI(FnCopyExporter.CopyPreset, CopyExporterUI)
