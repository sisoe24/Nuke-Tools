import hiero.core
import hiero.ui

from PySide2 import (QtCore, QtGui, QtWidgets)
from . FnBinProcessor import BinProcessorPreset


class BinProcessorUI(hiero.ui.ProcessorUIBase, QtCore.QObject):

  def getTaskItemType(self):
    return hiero.core.TaskPresetBase.kClip

  def __init__(self, preset):
    QtCore.QObject.__init__(self)
    hiero.ui.ProcessorUIBase.__init__(self, preset, itemTypes=hiero.core.TaskPresetBase.kClip)


  def displayName(self):
    return "Process as Clips"


  def toolTip(self):
    return "Process as Clips generates an output per clip within a bin structure.\nUse the {binpath}/{fullbinpath} tokens to maintain the bin structure when exporting."


  def startFrameSourceChanged(self, index):
    value = self._startFrameSource.currentText()
    if str(value) == "Source":
      self._startFrameIndex.setEnabled(False)
    if str(value) == "Custom":
      self._startFrameIndex.setEnabled(True)
    self._preset._properties["startFrameSource"] = str(value)


  def startFrameIndexChanged(self, value):
    self._preset._properties["startFrameIndex"] = int(value)


  def createProcessorSettingsWidget(self, exportItems):
    widget = QtWidgets.QWidget()

    mainLayout = QtWidgets.QVBoxLayout()
    mainLayout.setContentsMargins(0, 0, 0, 0)
    widget.setLayout(mainLayout)

    startFrameToolTip = "Set how clip Start Frames are derived using the dropdown menu:\n-Source : use the source clip's start frame.\n-Custom : specify a start frame for all clips"

    # Startframe layout
    startFrameLayout = QtWidgets.QHBoxLayout()
    self._startFrameSource = QtWidgets.QComboBox()
    self._startFrameSource.setToolTip(startFrameToolTip)
    startFrameSourceItems = ("Source", "Custom")
    for index, item in zip(list(range(0,len(startFrameSourceItems))), startFrameSourceItems):
      self._startFrameSource.addItem(item)
      if item == str(self._preset.properties()["startFrameSource"]):
        self._startFrameSource.setCurrentIndex(index)


    self._startFrameIndex = QtWidgets.QLineEdit()
    self._startFrameIndex.setToolTip(startFrameToolTip)
    self._startFrameIndex.setValidator(QtGui.QIntValidator())
    self._startFrameIndex.setText(str(self._preset.properties()["startFrameIndex"]))

    startFrameLayout.addWidget(QtWidgets.QLabel("Start Frame"))
    startFrameLayout.addWidget(self._startFrameSource)
    startFrameLayout.addWidget(self._startFrameIndex)
    startFrameLayout.addStretch()

    self._startFrameSource.currentIndexChanged.connect(self.startFrameSourceChanged)
    self._startFrameIndex.textChanged.connect(self.startFrameIndexChanged)
    self.startFrameSourceChanged(0)
    mainLayout.addLayout(startFrameLayout)


    return widget


  def validateSelection(self,exportItems):
    """Validate if any items in the selection are suitable for processing by this processor"""

    invalidItems = []
    # Look for selected items which arent of the correct type
    for item in exportItems:
      if not item.clip():
        invalidItems.append(item)

    return len(invalidItems) < len(exportItems)


  def validate ( self, exportItems ):
    """Validate settings in UI. Return False for failure in order to abort export."""
    if not hiero.ui.ProcessorUIBase.validate(self, exportItems):
      return False

    # Look for selected items which arent of the correct type
    offlineItems = []
    invalidItems = []
    onlineItems = []
    for item in exportItems:
      if item.clip() and not item.clip().mediaSource().isMediaPresent():
        offlineItems.append(item.item().name() + " (Media Offline)")
        hasOffline = True
      elif not item.clip():
        invalidItems.append(item.item().name() + " (Not a Clip)")
      else:
        onlineItems.append(item)
    # Found invalid items
    if offlineItems:
      messageText = "Some items are offline.  Do you want to continue?"
      messageDetails = ""
      if offlineItems:
        messageDetails = messageDetails + "\n".join(offlineItems)
      if invalidItems:
        messageDetails = messageDetails + "\n\nThe following items will be ignored by this export:\n%s" % str("\n".join(invalidItems))
      return self.offlineMediaPrompt(messageText, messageDetails, onlineItems)
    elif invalidItems:
      # Show warning
      messageText = "The following items will be ignored by this export:\n%s" % str("\n".join(invalidItems))
      result = QtWidgets.QMessageBox.information(None, "Export", messageText, QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
      # Continue if user clicks OK
      return result == QtWidgets.QMessageBox.Ok

    # Do any ShotProcessor-specific validation here...
    return True


  def processorSettingsLabel(self):
    return "Settings"


hiero.ui.taskUIRegistry.registerProcessorUI(BinProcessorPreset, BinProcessorUI)
