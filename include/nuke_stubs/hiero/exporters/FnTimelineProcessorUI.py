import itertools

import hiero.core
import hiero.ui

from PySide2 import(QtCore, QtGui, QtWidgets)

from . FnTimelineProcessor import TimelineProcessorPreset
from . FnTrackSelectionWidget import TrackSelectionWidget


class TimelineProcessorUI(hiero.ui.ProcessorUIBase, QtCore.QObject):

  def getTaskItemType(self):
    return hiero.core.TaskPresetBase.kSequence

  def __init__(self, preset):
    QtCore.QObject.__init__(self)
    hiero.ui.ProcessorUIBase.__init__(self, preset, itemTypes=hiero.core.TaskPresetBase.kSequence)



  def displayName(self):
    return "Process as Sequence"


  def toolTip(self):
    return "Process as Sequence generates an output for an entire sequence, or subset of a sequence (e.g. EDL, XML, full sequence transcode)."


  def validateSelection(self, exportItems):
    """Validate if any items in the selection are suitible for processing by this processor"""

    invalidItems = []
    # Look for selected items which arent of the correct type
    for item in exportItems:
      if not item.sequence() and not item.trackItem():
        invalidItems.append(item)
    hiero.core.log.debug( "validateSelection TimelineProcessor " + str(len(invalidItems) < len(exportItems)) )
    return len(invalidItems) < len(exportItems)

  def validate ( self, exportItems ):
    """Validate settings in UI. Return False for failure in order to abort export."""
    if not hiero.ui.ProcessorUIBase.validate(self, exportItems):
      return False

    invalidItems = []
    # Look for selected items which arent of the correct type
    for item in exportItems:
      if not item.sequence() and not item.trackItem():
        invalidItems.append(item.item().name() + " <span style='color: #CC0000'>(Not a Sequence)</span>")

    # Found invalid items
    if invalidItems:
      # Show warning
      msgBox = QtWidgets.QMessageBox()
      msgBox.setTextFormat(QtCore.Qt.RichText)
      result = msgBox.information(None, "Export", "The following items will be ignored by this export:<br/>%s" % str("<br/>".join(invalidItems)), QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
      # Continue if user clicks OK
      return result == QtWidgets.QMessageBox.Ok

    # Do any ShotProcessor-specific validation here...
    return True


  def createProcessorSettingsWidget(self, exportItems):
    widget = QtWidgets.QWidget()

    mainLayout = QtWidgets.QVBoxLayout()
    mainLayout.setContentsMargins(0, 0, 0, 0)
    widget.setLayout(mainLayout)
    # Horizontal layout to stack group boxes side by side
    hLayout = QtWidgets.QHBoxLayout()
    hLayout.setContentsMargins(0,0,9,0)
    mainLayout.addLayout(hLayout)


    sequences = []
    for item in exportItems:
      if not item.trackItem() and item.sequence():
        sequence = item.sequence()
      elif item.trackItem():
        sequence = item.trackItem().parentSequence()
      if not sequence in sequences:
        sequences.append(sequence)

    trackWidget = TrackSelectionWidget(sequences,
                                           self._preset.nonPersistentProperties()["excludedTracks"],
                                           excludedTrackIDs = self._preset._excludedTrackIDs)
    hLayout.addWidget(trackWidget)

    ##RANGE WIDGET
    rangeWidget = QtWidgets.QWidget()

    rangeLayout = QtWidgets.QVBoxLayout()
    rangeLayout.setContentsMargins(0,0,0,0)
    hLayout.addWidget(rangeWidget)
    rangeWidget.setLayout(rangeLayout)
    rangeLabel = QtWidgets.QLabel("Range:")
    rangeLayout.addWidget(rangeLabel)


    selectedTrackItemsToolTip = "Export the range defined by the currently selected subset of the sequence."
    wholeSequenceToolTip = "Export the whole range of the sequnce"
    inOutToolTip = "Export the range defined by the current In/Out Points"

    # Disable in/out points option if no in out points set
    hasInOutPoints = self.selectionHasInOutPoints(exportItems)
    inOutTrim = self._preset.properties()["inOutTrim"] and hasInOutPoints

    exportSelection = False
    # Establish if selected items are individual trackitems or a whole sequence.
    for item in exportItems:
      if item.trackItem():
        exportSelection = True
        break

    # If exporting from selection, the export range will be clipped to the range of the seleciton
    # If exporting the whole sequence the export range will be the full sequence frame range
    fullRadioButton = QtWidgets.QRadioButton ( "Selected Track Items" if exportSelection else "Whole Sequence")
    fullRadioButton.setToolTip(selectedTrackItemsToolTip if exportSelection else wholeSequenceToolTip)
    fullRadioButton.setChecked( not inOutTrim)
    rangeLayout.addWidget(fullRadioButton)

    # if In/Out points are set on the sequence the option to export only this range will be enabled
    inOutRadioButton = QtWidgets.QRadioButton ("In/Out Points")
    inOutRadioButton.setToolTip(inOutToolTip)
    inOutRadioButton.setChecked(inOutTrim)
    inOutRadioButton.setEnabled(hasInOutPoints)
    rangeLayout.addWidget(inOutRadioButton)
    inOutRadioButton.toggled.connect(self.setInOutTrim)

    startFrameToolTip = "The first frame of the sequence is mapped to:\n-Sequence : directly onto sequence frame index.\n-Custom : Enter custom offset for the first frame of the sequence."

    # Startframe layout
    startFrameLayout = QtWidgets.QHBoxLayout()
    startFrameLayout.setContentsMargins(0,0,0,0)
    self._startFrameSource = QtWidgets.QComboBox()
    self._startFrameSource.setToolTip(startFrameToolTip)

    startFrameSourceItems = ("Sequence", "Custom")
    for index, item in zip(list(range(0,len(startFrameSourceItems))), startFrameSourceItems):
      self._startFrameSource.addItem(item)
      if item == str(self._preset.properties()["startFrameSource"]):
        self._startFrameSource.setCurrentIndex(index)
    # Custom Startframe line edit, enabled only if 'Custom' start frame source selected
    self._startFrameIndex = QtWidgets.QLineEdit()
    self._startFrameIndex.setValidator(QtGui.QIntValidator())
    self._startFrameIndex.validator().setBottom(0)
    self._startFrameIndex.setText(str(self._preset.properties()["startFrameIndex"]))

    startFrameLayout.addWidget(QtWidgets.QLabel("Start Frame"))
    startFrameLayout.addWidget(self._startFrameSource)
    startFrameLayout.addWidget(self._startFrameIndex)
    startFrameLayout.addStretch(1)

    self._startFrameSource.currentIndexChanged.connect(self.startFrameSourceChanged)
    self._startFrameIndex.textChanged.connect(self.startFrameIndexChanged)
    self.startFrameSourceChanged(0)
    rangeLayout.addLayout(startFrameLayout)

    rangeLayout.addStretch()

    return widget


  def processorSettingsLabel(self):
    return "Tracks && Range"


  def setInOutTrim (self, checked):
    # checked == True means In/Out points selected
    self._preset.properties()["inOutTrim"] = checked

  def sequenceHasInOutPoints(self, sequence):
    try:
      sequence.inTime()
      return True
    except:
      pass

    try:
      sequence.outTime()
      return True
    except:
      pass
    return False

  def selectionHasInOutPoints (self, selection):

    for itemWrapper in selection:
      if itemWrapper.sequence():
        if self.sequenceHasInOutPoints(itemWrapper.sequence()):
          return True

      if itemWrapper.trackItem():
        sequence = itemWrapper.trackItem().parent()
        if self.sequenceHasInOutPoints(sequence):
          return True
    return False

  def startFrameSourceChanged(self, index):
    value = self._startFrameSource.currentText()
    if str(value) == "Sequence":
      self._startFrameIndex.setEnabled(False)
    if str(value) == "Custom":
      self._startFrameIndex.setEnabled(True)
    self._preset.properties()["startFrameSource"] = str(value)

  def startFrameIndexChanged(self, value):
    self._preset.properties()["startFrameIndex"] = int(value)



hiero.ui.taskUIRegistry.registerProcessorUI(TimelineProcessorPreset, TimelineProcessorUI)
