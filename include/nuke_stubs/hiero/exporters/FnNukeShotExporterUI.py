# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.


from PySide2 import(QtCore, QtGui, QtWidgets)
from . import FnAdditionalNodesDialog
import hiero.ui

from . import FnNukeShotExporter
from .FnNukeExporterWidgets import NukeProjectNodeSelectionWidget,TimelineWriteNodeWidget
from hiero.ui.FnExporterBaseUI import ReformatToolTips
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import *
from hiero.core import nuke


class NukeShotExporterUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """UI for NukeShotExporter task."""
    hiero.ui.TaskUIBase.__init__(self, preset.parentType(), preset, "Nuke Project File")
    
    self._uiProperties = []
    self._tags = []
    
    self._collateTimeProperty = None
    self._collateNameProperty = None
    self._includeAnnotationsProperty = None
    self._showAnnotationsProperty = None

    
  def readPresetChanged (self, topLeft, bottomRight):  
    hiero.core.log.debug( "readPresetChanged" )
    presetValue = self._preset.properties()["readPaths"] = []
    model = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kReadNode)
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
        presetValue.append(item.text())

    # Update the path changed callbacks
    self._preset.initialiseCallbacks(self._exportTemplate)
    
    if self._isShotExport():
      if len(presetValue) > 0:
        if self._collateTimeProperty._widget.checkState() == QtCore.Qt.Checked or self._collateNameProperty._widget.checkState() == QtCore.Qt.Checked:
          QtWidgets.QMessageBox.information(hiero.ui.mainWindow(), "Conflicting Options", "Overriding the Read node paths will disable the 'Collate' options. Currently these features are incompatible.")
          self._collateTimeProperty._widget.setChecked(False)
          self._collateNameProperty._widget.setChecked(False)

      self._collateTimeProperty.setEnabled(len(presetValue) == 0)
      self._collateNameProperty.setEnabled(len(presetValue) == 0)
        
    hiero.core.log.debug( "readPaths (%s)" % str(presetValue) )
            
  def writePresetChanged (self, topLeft, bottomRight):
    hiero.core.log.debug( "writePresetChanged" )
    presetValue = self._preset.properties()["writePaths"] = []

    model = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kWriteNode)
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
        presetValue.append(item.text())

    # Update the path changed callbacks
    self._preset.initialiseCallbacks(self._exportTemplate)
        
    hiero.core.log.debug( "writePaths (%s)" % str(presetValue) )


  def annotationsPreCompPresetChanged (self, topLeft, bottomRight):
    presetValue = self._preset.properties()["annotationsPreCompPaths"] = []
    model = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kAnnotationsNode)
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
        presetValue.append(item.text())

    # Update the path changed callbacks
    self._preset.initialiseCallbacks(self._exportTemplate)

    
  def timelineWriteNodeChanged(self, text):
    hiero.core.log.debug( "setting timelineWriteNode property to:\'%s\'"%text)
    self._preset.properties()["timelineWriteNode"] = text


  def propertyChanged (self):
    for uiProperty in self._uiProperties:
      uiProperty.update()

    self.propertiesChanged.emit()


  def reformatChanged (self):
    """ Callback when the Reformat combo box selection has changed.  Enable/disable the reformat property widgets
        as appropriate. """
    text = self._reformatCombo.currentText()
    widgetEnabledMap = ((self._formatChooser, text ==  nuke.ReformatNode.kCompReformatToFormat),
                        (self._resizeWidget, text == nuke.ReformatNode.kCompReformatToFormat),
                        (self._filterWidget, text != nuke.ReformatNode.kCompFormatAsPlate))

    for widget, enabled in widgetEnabledMap:
      # Set the widget and its label's enabled state.
      widget.setEnabled(enabled)
      self._reformatPropertyLabels[widget].setEnabled(enabled)

      # If a property widget is being enabled, make sure its value is stored in the property dictionary.
      # This is done at this point because otherwise, merely showing the UI could cause the preset to be modified,
      # which is bad.  e.g. if the 'scale' option is selected, the default value of the 'scale' knob should be
      # added to the preset, since the default is not actually defined anywhere other than in this class.
      # 
      # Probably this stuff should not be so tied to the UI.
      if enabled and isinstance(widget, UIPropertyBase):
        widget.update(commit=True)


  def formatChanged (self):
    if self._formatChooser.isEnabled():
      format = self._formatChooser.currentFormat()
      self.setFormat(format)
      self.propertiesChanged.emit()


  def setFormat (self, format):
    self._preset._properties["reformat"]["name"] = str(format.name())
    self._preset._properties["reformat"]["width"] = int(format.width())
    self._preset._properties["reformat"]["height"] = int(format.height())
    self._preset._properties["reformat"]["pixelAspect"] = float(format.pixelAspect())


  def createNodeSelectionWidget(self, layout, exportTemplate):
    self._nodeSelectionWidget = NukeProjectNodeSelectionWidget(exportTemplate, self._preset)
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
    self._nodeSelectionWidget.addNodeSelector(
      NukeProjectNodeSelectionWidget.kAnnotationsNode, "Annotations", "annotationsPreCompPaths",
      "Adds a PreComp node containing annotations being exported for this shot. ")
    layout.addWidget(self._nodeSelectionWidget)
    self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kReadNode).dataChanged.connect(self.readPresetChanged)
    self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kWriteNode).dataChanged.connect(self.writePresetChanged)
    self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kAnnotationsNode).dataChanged.connect(self.annotationsPreCompPresetChanged)


  def populateUI (self, widget, exportTemplate):
    if exportTemplate:
    
      self._exportTemplate = exportTemplate
      layout = widget.layout()

      # Node selection
      self.createNodeSelectionWidget(layout, exportTemplate)
      
      formLayout = TaskUIFormLayout()
      layout.addLayout(formLayout)

      writeModel = self._nodeSelectionWidget.getModel(NukeProjectNodeSelectionWidget.kWriteNode)
      self._timelineWriteNode =  TimelineWriteNodeWidget(writeModel, self._preset)
      formLayout.addRow("Timeline Write Node:",self._timelineWriteNode)
      self._timelineWriteNode.timelineWriteNodeChanged.connect(self.timelineWriteNodeChanged)

      #Retiming
      formLayout.addDivider("Retiming")
      
      retimeToolTip = """Sets the retime method used if retimes are enabled.\n-Motion - Motion Estimation.\n-Blend - Frame Blending.\n-Frame - Nearest Frame"""
      key, value = "method", ("None", "Motion", "Frame", "Blend")
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label="Retime Method", tooltip=retimeToolTip)
      self._uiProperties.append(uiProperty)
      formLayout.addRow(uiProperty._label + ":", uiProperty)

      #Effects
      formLayout.addDivider("Effects")
      includeEffectsToolTip = """Enable this to include soft effects in the exported script."""
      key, value, label = "includeEffects", True, "Include Effects"
      uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=includeEffectsToolTip)
      formLayout.addRow(label+":", uiProperty)
      self._uiProperties.append(uiProperty)

      #Reformat
      self._addReformatOptions(formLayout)
      #Collate
      self._addCollateOptions(formLayout)
      
      self.readPresetChanged(None, None)

      #Additional Nodes
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


  def _isShotExport(self):
    """ Check if the export task is for shots or whole sequences. The UI should
    be slightly different in these cases.
    """
    return (self._preset.supportedItems() & self._preset.kTrackItem)

  def _addReformatOptions(self, layout):
    """ Add reformat options to the UI. """

    # When doing process as sequence, we don't need these options
    if not self._isShotExport():
      return
    
    layout.addDivider("Reformat")
    
    # Reformat options
    # TODO: This code came from RenderTaskUIBase, and should be refactored
    rfProperties = self._preset._properties["reformat"]

    toTypeOptions = (nuke.ReformatNode.kCompFormatAsPlate,
                     nuke.ReformatNode.kCompReformatToSequence,
                     (nuke.ReformatNode.kCompReformatToFormat, nuke.ReformatNode.kToFormat))
    toTypeToolTip = ReformatToolTips.createToTypeToolTip(toTypeOptions)
    key, value = "to_type", toTypeOptions
    uiProperty = UIPropertyFactory.create(type(value),
                                          key=key,
                                          value=value,
                                          dictionary=rfProperties,
                                          label="Reformat",
                                          tooltip=toTypeToolTip)
    self._uiProperties.append(uiProperty)
    layout.addRow(uiProperty._label + ":", uiProperty)
    uiProperty.propertyChanged.connect(self.propertyChanged)

    # This will update the state of the format chooser
    uiProperty.propertyChanged.connect(self.reformatChanged)
    # if format is empty it will be updated whenever Reformat is enabled
    uiProperty.propertyChanged.connect(self.formatChanged)
    self._reformatCombo = uiProperty._widget

    # Store the labels which are created by the layout for each widget added, so they can be disabled when the widgets are.
    self._reformatPropertyLabels = dict()

    # Format chooser
    self._formatChooser = hiero.ui.FormatChooser()
    self._formatChooser.setProject(self._project)
    self._formatChooser.setToolTip(ReformatToolTips.format)
    self._formatChooser.formatChanged.connect(self.formatChanged)
    if "width" in rfProperties and "height" in rfProperties and "pixelAspect" in rfProperties and "name" in rfProperties:
      try:
        format = hiero.core.Format(rfProperties["width"], rfProperties["height"], rfProperties["pixelAspect"], rfProperties["name"])
        self._formatChooser.setCurrentFormat( format )
      except ValueError as e:
        message = self._preset.name() + "The selected preset has an invalid output resolution:\n"
        message += e.message
        InvalidOutputResolutionMessage(message)
      except:
        print(e)
    layout.addRow("Format:", self._formatChooser)
    self._reformatPropertyLabels[self._formatChooser] = layout.labelForField(self._formatChooser)

    # Reformat resize mode option.
    containerWidget =QtWidgets.QWidget()
    resizeLayout = QtWidgets.QHBoxLayout(containerWidget)
    resizeLayout.setContentsMargins(0,0,0,0);
    
    key, value, label = "resize", (nuke.ReformatNode.kResizeNone, nuke.ReformatNode.kResizeWidth, nuke.ReformatNode.kResizeHeight, nuke.ReformatNode.kResizeFit, nuke.ReformatNode.kResizeFill, nuke.ReformatNode.kResizeDistort), "Resize"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=rfProperties, label=label, tooltip=ReformatToolTips.resize)
    self._uiProperties.append(uiProperty)
    resizeLayout.addWidget(uiProperty._widget)
    layout.addRow(uiProperty._label + ":", containerWidget)
    uiProperty.update()
    uiProperty.propertyChanged.connect(self.propertyChanged)
    
    self._resizeWidget = containerWidget
    self._reformatPropertyLabels[self._resizeWidget] = layout.labelForField(self._resizeWidget)
    self._resizeCombo = uiProperty._widget

    key, value, label = "center", True, "Center"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=rfProperties, label=label, tooltip=ReformatToolTips.center)
    self._uiProperties.append(uiProperty)
    resizeLayout.addWidget(uiProperty._widget)
    resizeLayout.addWidget(QtWidgets.QLabel(uiProperty._label))
    uiProperty.update()
    uiProperty.propertyChanged.connect(self.propertyChanged)


    key, label = "filter", "Filter"
    value = ("Impulse", "Cubic", "Keys", "Simon", "Rifman", "Mitchell",
    "Parzen", "Notch", "Lanczos4", "Lanczos6", "Sinc4")
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=rfProperties, label=label, tooltip=ReformatToolTips.filter)
    self._uiProperties.append(uiProperty)
    layout.addRow(uiProperty._label + ":", uiProperty)
    uiProperty.update()
    uiProperty.propertyChanged.connect(self.propertyChanged)
    self._filterWidget = uiProperty
    self._reformatPropertyLabels[self._filterWidget] = layout.labelForField(self._filterWidget)

    self.reformatChanged()

  def _addCollateOptions(self, layout):
    """ Add collate options to the UI. """

    # When doing process as sequence, we don't need these options
    if not self._isShotExport():
      return
    
    #Collate
    layout.addDivider("Collate & Connect")
    
    collateTracksToolTip = """Enable this to include other shots which overlap the sequence time of each shot within the script. Cannot be enabled when Read Node overrides are set."""

    key, value, label = "collateTracks", False, "Collate Shot Timings"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=collateTracksToolTip)
    layout.addRow(label+":", uiProperty)
    self._uiProperties.append(uiProperty)
    self._collateTimeProperty = uiProperty

    collateShotNameToolTip = """Enable this to include other shots which have the same name in the Nuke script. Cannot be enabled when Read Node overrides are set."""
    key, value, label = "collateShotNames", False, "Collate Shot Name"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=collateShotNameToolTip)
    layout.addRow(label+":", uiProperty)
    self._collateNameProperty = uiProperty
    self._uiProperties.append(uiProperty)
    
    tooltip = ("If enabled, tracks will be merged together.  Otherwise, only the track containing the main track item "
              "is connected to the Write node, with any other tracks being placed in the script disconnected.")

    key, value, label = "connectTracks", self._preset.properties()["connectTracks"], "Connect Tracks"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=tooltip)
    layout.addRow(label+":", uiProperty)
    self._uiProperties.append(uiProperty)
    
    

  def _additionalNodesEnableClicked(self, state):
    self._preset.properties()["additionalNodesEnabled"] = state == QtCore.Qt.Checked

  def _additionalNodesEditClicked(self):
    dialog = FnAdditionalNodesDialog.AdditionalNodesDialog(self._preset.properties()["additionalNodesData"], self._tags)
    if dialog.exec_():
      self._preset.properties()["additionalNodesData"] = dialog.data()

  def setTags ( self, tags ):
    """setTags passes the subset of tags associated with the selection for export"""
    self._tags = tags


# Register the UI for NukeShotPreset and NukeSequencePreset. It's shared between
# them, with a bit of different behaviour in the class depending on which is used.
hiero.ui.taskUIRegistry.registerTaskUI(FnNukeShotExporter.NukeShotPreset, NukeShotExporterUI)
hiero.ui.taskUIRegistry.registerTaskUI(FnNukeShotExporter.NukeSequencePreset, NukeShotExporterUI)
