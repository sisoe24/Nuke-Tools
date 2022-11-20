# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import sys
import itertools
from hiero.core.FnExporterBase import classBasename

from PySide2 import(QtCore, QtGui, QtWidgets)

import hiero.core
from hiero.core import nuke
from hiero.core.FnFloatRange import FloatRange

from hiero.ui import *
from hiero.ui.FnUIProperty import *
from hiero.ui.FnPathQueryDialog import *
from hiero.ui.FnDisclosureButton import DisclosureButton
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnCodecUIController import CodecUIController
from hiero.ui.FnCodecUIController import EXRCodecUIController
from hiero.ui.FnCodecUIController import WriteNodePropertyWidget

class ReformatToolTips():
  """Class for defining refomat related tooltip text"""

  # Dict of tooltips for the 'to type' options, used by createToTypeToolTip()
  totype = {nuke.ReformatNode.kCompReformatToSequence :
              "Selecting 'To Sequence Resolution' will reformat the clip to the sequence resolution.",
            nuke.ReformatNode.kCompFormatAsPlate :
              "Selecting 'Plate Resolution' will use the clip's original format size.",
            (nuke.ReformatNode.kToScaleLabel, nuke.ReformatNode.kToScale):
              "Selecting 'To Scale' will scale the image by the selected proportion",
            (nuke.ReformatNode.kCompReformatToFormat, nuke.ReformatNode.kToFormat):
              "Selecting 'Custom' will reformat the clip/sequence to the chosen format.",
            "None" :
              "Selecting 'None' will apply no reformatting to the output and use the clip/sequence's format.",
           }

  @staticmethod
  def createToTypeToolTip(values):
    """ Different reformat options are available depending on the exporter.
    Construct the tooltip based on the options being used.
    """
    tooltip = "\n".join( ReformatToolTips.totype[v] for v in values )
    return tooltip

  format = """Sets the Output Resolution format size\nSelect Custom... to create formats that don't appear in the list of presets."""
  resize = """Resize - sets the method by which you want to preserve or override the original aspect ratio:\n
    -none - don't change the pixels.\n
    -width - scales the original until its width matches the format's width. Height is then scaled in such a manner as to preserve the original aspect ratio.\n
    -height - scales the original until its height matches the format's height. Width is then scaled in such a manner as to preserve the original aspect ratio.\n
    -fit - scales the original until its smallest side matches the format's smallest side. The original's longer side is then scaled in such a manner as to preserve original aspect ratio.\n
    -fill - scales the original until its longest side matches the format's longest side. The input's shorter side is then scaled in such a manner as to preserve original aspect ratio.\n
    -distort - scales the original until all its sides match the lengths specified by the format. This option does not preserve the original aspect ratio, so distortions may occur."""
  scale = """Sets the proportion to scale the output format by."""
  center = "Translate the image to center it in the output. If off, it is translated so the lower-left corners are lined up."
  filter = """Impulse\tno filtering - each output pixel equals some input pixel\n
  Cubic\tsmooth interpolation between pixels\n
  Keys\tcubic a=.50, approximates sync (*)\n
  Simon\tcubic a=.75, continuous 2nd derivative (*)\n
  Rifman\tcubic a=1.0, lots of sharpening (*)\n
  Mitchell    mix of sharpening and smoothing (*+)\n
  Parzen\tapproximating B-spline (+)\n
  Notch\thides moir\xC3\xA9 patterns (+)\n
  Lanczos4\t good for scaling down (*)\n
  Lanczos6\t good for scaling down with some sharpening (*)\n
  Sinc4\t good for scaling down with a lot of sharpening (*)\n
  (*) has negative lobes, can produce values that are
  outside the range of the input pixels.\n
  (+) not interpolatory, changes pixels even when no movement"""



def InvalidOutputResolutionMessage(message):
  msgBox = QtWidgets.QMessageBox(mainWindow())
  msgBox.setText(message)
  msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
  msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
  msgBox.exec_()



class TaskUIBase(ITaskUI, QtCore.QObject):
  """TaskUIBase is the base class from hich all TaskUI components should derrive"""

  # Signal fired whenever properties are updated
  propertiesChanged = QtCore.Signal()

  def __init__ (self, taskType, preset, displayName):
    """Initialise Exporter Preset Base Class"""
    ITaskUI.__init__(self, preset)
    QtCore.QObject.__init__(self)
    self._preset = preset
    self._displayName = displayName
    self._taskType = taskType
    self._project = None

  def setPreset (self, preset):
    """Assign Preset to ExporterUI"""
    self._preset = preset

  def setTags ( self, tags ):
    """setTags passes the subset of tags associated with the selection for export"""
    """Derrived classes are responsible for overriding this function if they require"""
    pass

  def preset (self):
    """Return Preset currently assigned to ExporterUI"""
    return self._preset

  def populateUI (self, widget, exportTemplate):
    """populateUI() Export dialog to allow the TaskUI to populate a QWidget with the ui widgets neccessary to reflect the current preset."""
    pass

  def setTaskItemType(self, type):
    self._taskItemType = type

  def taskItemType(self):
    return self._taskItemType

  def displayName (self):
    """Exporter name to be displayed in the UI"""
    return self._displayName

  def ident (self):
    return classBasename(self._taskType)

  def parentType ( self ):
    return self._taskType;

  def setProject(self, project):
    """ Set the project being used for the current export. """
    self._project = project
  
  def initializeAndPopulateUI(self, widget, exportTemplate):
    self.initializeUI(widget)
    self.populateUI(widget, exportTemplate)
    widget.layout().addStretch()
    
  def initializeUI(self,widget):
    layout = QtWidgets.QVBoxLayout(widget)
    layout.setContentsMargins(9, 9, 9, 9)
    layout.addWidget(QtWidgets.QLabel(self.displayName()))
    

class RenderTaskUIBase(TaskUIBase):
  """RenderTaskUIBase is a specialization of TaskUIBase which reflects the codec properties in RenderTaskPreset into UI"""

  def __init__(self, taskType, preset, displayName):
    """A task base that includes functionality for displaying output selection UI."""
    TaskUIBase.__init__(self, taskType, preset, displayName)
    self._codecSettings = preset._codecSettings
    self._uiProperties = []


  def codecTypeComboBoxChanged(self, value):
    selectedFileType = self._codecTypeComboBox.currentText()
    self.updateCodecPropertiesWidget(selectedFileType)
    self._preset._properties["file_type"] = self._codecTypeComboBox.currentText()
    self.updateChannelsForFileType(selectedFileType)
    self.propertiesChanged.emit()

  def updateChannelsForFileType(self, fileType):
    # Change the channels knob setting based on the file extension.  If exr is being written then set
    # channels to all, otherwise rgb.
    if fileType == "exr":
      channels = "all"
    else:
      channels = "rgb"

    # Set the correct text on the channels combo box
    self._channelsCombo.setCurrentIndex( self._channelsCombo.findText(channels) )


  def propertyChanged (self):
    for uiProperty in self._uiProperties:
      uiProperty.update()

    self.propertiesChanged.emit()


  def reformatChanged (self):
    """ Callback when the Reformat combo box selection has changed. Enable/disable
    the reformat property widgets as appropriate.
    """
    text = self._reformatCombo.currentText()
    widgetEnabledMap = ((self._formatChooser, text == nuke.ReformatNode.kCustomLabel),
                        (self._scaleWidget, text == nuke.ReformatNode.kToScaleLabel),
                        (self._resizeWidget, text in (nuke.ReformatNode.kCustomLabel,nuke.ReformatNode.kToScaleLabel)),
                        (self._filterWidget, text != "None"))

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


  def deleteFirstChildFromWidget(self, widget):
    """ Get the first child added to the widget's layout, and delete it, if it exists. """
    layout = widget.layout()
    if layout.count():
      oldWidget = layout.takeAt(0)
      if oldWidget and oldWidget.widget():
        oldWidget.widget().hide()
        oldWidget.widget().destroy()


  def updateCodecPropertiesWidget(self, file_type):
    """ Update the codec properties widget. If applicable, also updates the encoder properties (for movs). """

    # First delete the old widget
    self.deleteFirstChildFromWidget(self._codecPropertiesPlaceholderWidget)

    # Update the label to match the file type
    fileTypeLabel = file_type.upper()

    self._codecPropertiesLabel.setText(fileTypeLabel + " Options")

    # Create the new codec widget, and add it to the placeholder in the layout
    widget = self._buildCodecWidget(file_type)
    if widget:
      self._codecPropertiesPlaceholderWidget.layout().addWidget(widget)


  def _buildCodecWidget (self, file_type):
    """ Create the codec properties widget. """

    widget = None
    if file_type in self._codecSettings:

      if not file_type in self._preset._properties:
        self._preset._properties[file_type] = dict()

      codecSettings = None

      if file_type == "mov":
        if "encoder" not in self._preset._properties[file_type]:
          self._preset._properties[file_type]["encoder"] = "mov64"

        if self._preset._properties[file_type]["encoder"] == "mov64":
          codecSettings = self._codecSettings[file_type]["properties"]
        else:
          assert False, "Using an unrecognized encoder"
      else:
        codecSettings = self._codecSettings[file_type]["properties"]

      propertyDictionaries = [codecSettings, ]
      widget = self.createCodecPropertyWidgets(file_type, propertyDictionaries)

    return widget


  def createCodecPropertyWidgets(self, file_type, propertyDictionaries):
    """ Create widgets for the given property dictionaries, and add them to the given layout. """
    presetDictionaries = self._preset._properties[file_type]
    if file_type in [ "mov", "mxf" ]:
      widget = WriteNodePropertyWidget(file_type, propertyDictionaries, presetDictionaries)
    else:
      if file_type == "exr":
        widget = EXRCodecUIController(file_type, propertyDictionaries, presetDictionaries)
      else:
        widget = CodecUIController(file_type, propertyDictionaries, presetDictionaries)
      widget.propertyChanged.connect(self.propertyChanged)

    return widget


  def _getLutOptions(self):
    """
    Return the LUT options to use.
    """
    # If a project has been set on this object, use that, otherwise try to get
    # it from the preset.  If there are items being exported, then the project
    # should have been set from those by the processor UI.
    project = self._project or self._preset.project()
    includeFamilies = True
    luts = hiero.core.LUTs(self._project, includeFamilies) if self._project else hiero.core.LUTs()
    lutsWithRoleColorspaces = []
    for i in range(len(luts)):
      roleColorspace = hiero.core.getRoleColorspace(self._project, i) if self._project else hiero.core.getRoleColorspace(i)
      if roleColorspace:
        lutsWithRoleColorspaces.append(luts[i] + " (" + roleColorspace + ")")
      else:
        lutsWithRoleColorspaces.append(luts[i])
    return tuple(lutsWithRoleColorspaces)

  def buildCodecUI (self, layout, itemTaskType):
    """Populate layout with widgets reflected from the RenderPresetBase class"""
    self._uiProperties = []

    self.createChannelsWidget(layout)
    self.createColourSpaceWidget(layout)
    self.createViewsWidget(layout)
    self.createFileTypeWidget(layout)
    self.createCodecOptionsPlaceholder(layout)
    self.createReformatWidgets(layout, itemTaskType)


  def createChannelsWidget(self, layout):
    channelsToolTip = """Sets the image channels to export. The default, all, exports all channels in the image.\nIf you want to export a non-standard channel, type the name of the channel into the field manually."""
    # The CustomList type generates an Editable combo box when passed through the UIPropertyFactory
    name, label, value = "channels", "Channels:", CustomList("all", "rgb", "rgba", "alpha", "depth", default="rgb")

    containerWidget = QtWidgets.QWidget()
    comboBoxLayout = QtWidgets.QHBoxLayout(containerWidget)
    comboBoxLayout.setContentsMargins(0,0,0,0);

    uiProperty = UIPropertyFactory.create(type(value), key=name, value=value, dictionary=self._preset.properties(), label=label, tooltip=channelsToolTip)
    self._uiProperties.append(uiProperty)
    uiProperty._widget.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
    comboBoxLayout.addWidget(uiProperty._widget)
    comboBoxLayout.addStretch()

    layout.addRow(label, containerWidget)
    uiProperty.propertyChanged.connect(self.propertyChanged)
    self._channelsCombo = uiProperty._widget

  def createColourSpaceWidget(self, layout):
    colourspaceToolTip = """The colour transform (LUT) applied to rendered images.\n 'default' uses the default LUT determined by the output image file type."""

    def colourspaceWidgetHandler (widget, layout, value):
      lutIcon = QtGui.QIcon("icons:LUT.png")
      for i in range(0, widget.count()):
        widget.setItemIcon(i, lutIcon)

    key, value = "colourspace", ("default",) + self._getLutOptions()
    uiProperty = CascadingEnumerationProperty(key=key,
                                              value=value,
                                              dictionary=self._preset._properties,
                                              label="Colourspace",
                                              tooltip=colourspaceToolTip,
                                              addWidgetHandler=colourspaceWidgetHandler)
    self._uiProperties.append(uiProperty)
    layout.addRow(uiProperty._label + ":", uiProperty)
    uiProperty.propertyChanged.connect(self.propertyChanged)

  def createViewsWidget(self, layout):
    views = self._project.views()
    uiProperty = ViewsPropertyWidget(key="views",
                                     value=views,
                                     dictionary=self._preset._properties,
                                     label="Views")
    self._uiProperties.append(uiProperty)
    layout.addRow(uiProperty._label + ":", uiProperty)
    uiProperty.propertyChanged.connect(self.propertyChanged)

  def createFileTypeWidget(self, layout):
    codecComboToolTip = "The output image type for rendered images."
    index = 0
    presetFileType = self._preset._properties["file_type"]
    self._codecTypeComboBox = QtWidgets.QComboBox()
    self._codecTypeComboBox.setToolTip(codecComboToolTip)

    if presetFileType not in self._codecSettings:
      presetFileType = list(self._codecSettings.keys())[0]

    for file_type in sorted(self._codecSettings.keys()):
      self._codecTypeComboBox.addItem(file_type)
      if str(file_type) == str(presetFileType):
        self._codecTypeComboBox.setCurrentIndex(index)
      index += 1

    self._codecTypeComboBox.currentIndexChanged.connect(self.codecTypeComboBoxChanged)
    layout.addRow("File Type:", self._codecTypeComboBox)

  def createCodecOptionsPlaceholder(self, layout):
    self._codecPropertiesLabel = layout.addDivider("Options")
    self._codecPropertiesPlaceholderWidget = QtWidgets.QWidget()
    self._codecPropertiesPlaceholderWidget.setLayout(QtWidgets.QVBoxLayout())
    layout.addRow(self._codecPropertiesPlaceholderWidget)

    presetFileType = self._preset._properties["file_type"]
    self.updateCodecPropertiesWidget(presetFileType)

  def createReformatWidgets(self, layout, itemTaskType):
    layout.addDivider("Reformat")
    rfProperties = self._preset._properties["reformat"]
    # Reformat off/type option.

    key = "to_type"
    if itemTaskType == hiero.core.TaskPresetBase.kTrackItem:
      value = ('None',
               nuke.ReformatNode.kCompReformatToSequence,
               (nuke.ReformatNode.kToScaleLabel, nuke.ReformatNode.kToScale),
               (nuke.ReformatNode.kCustomLabel, nuke.ReformatNode.kToFormat) )
    else:
      value = ('None',
               (nuke.ReformatNode.kToScaleLabel, nuke.ReformatNode.kToScale),
               (nuke.ReformatNode.kCustomLabel, nuke.ReformatNode.kToFormat) )
    toTypeToolTip = ReformatToolTips.createToTypeToolTip(value)
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
    self._formatChooser.setToolTip(ReformatToolTips.format)
    self._formatChooser.setProject(self._project)
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

    # Reformat scale option.
    key, value = "scale", FloatRange(0.1, 10.0, 1.0)
    uiProperty = UIPropertyFactory.create(type(value),
                                          key=key,
                                          value=value,
                                          dictionary=rfProperties,
                                          label="Scale",
                                          tooltip=ReformatToolTips.scale)
    self._uiProperties.append(uiProperty)
    layout.addRow(uiProperty._label + ":", uiProperty)
    uiProperty.update()
    uiProperty.propertyChanged.connect(self.propertyChanged)
    self._scaleWidget = uiProperty
    self._reformatPropertyLabels[self._scaleWidget] = layout.labelForField(self._scaleWidget)

    # Reformat resize mode option.
    key, value, label = "resize", (nuke.ReformatNode.kResizeNone, nuke.ReformatNode.kResizeWidth, nuke.ReformatNode.kResizeHeight, nuke.ReformatNode.kResizeFit, nuke.ReformatNode.kResizeFill, nuke.ReformatNode.kResizeDistort), "Resize"
    uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=rfProperties, label=label, tooltip=ReformatToolTips.resize)
    self._uiProperties.append(uiProperty)
    containerWidget = QtWidgets.QWidget()
    resizeLayout = QtWidgets.QHBoxLayout(containerWidget)
    resizeLayout.setContentsMargins(0,0,0,0);
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
