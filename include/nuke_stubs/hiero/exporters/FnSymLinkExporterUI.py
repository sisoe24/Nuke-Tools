import os.path

from PySide2 import QtWidgets


import hiero.ui
from . import FnSymLinkExporter


class SymLinkExporterUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """Initialize"""
    hiero.ui.TaskUIBase.__init__(self, FnSymLinkExporter.SymLinkExporter, preset, "SymLink Generator")

  def populateUI(self, widget, exportTemplate):
    layout = widget.layout()
    info = QtWidgets.QLabel("""<i>Windows Note:</i> Symbolic links will only work in Vista or later.\n
To link across filesystems the remote file server must also be running Vista or later.\n
You may also need administrator privileges to create symbolic links on Windows.""")
    info.setWordWrap(True)
    layout.addWidget(info)

hiero.ui.taskUIRegistry.registerTaskUI(FnSymLinkExporter.SymLinkPreset, SymLinkExporterUI)
