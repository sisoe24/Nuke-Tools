import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory

from hiero.ui.FnNodePropertyWidget import NodePropertyWidget

import nuke_internal as nuke

import copy

kEXRTooltips = {
  "metadata": ("Which metadata to write out to the EXR file."
               "<p>'no metadata' means that no custom attributes will be created and only metadata that fills required header fields will be written.<p>'default metadata' means that the optional timecode, edgecode, frame rate and exposure header fields will also be filled using metadata values."),
  "noprefix": ("By default unknown metadata keys have the prefix 'nuke' attached to them before writing them into the file.  Enable this option to write the metadata 'as is' without the nuke prefix."),
  "interleave" : ("Which groups to interleave in the EXR data."
                  "<p>'interleave channels, layers and views' for backwards compatibility. "
                  "This writes all the channels to a single part ensuring compatibility with earlier versions of Nuke.</p>"
                  "<p>'interleave channels and layers' for forwards compatibility. "
                  "This creates a multi-part file optimised for size.</p>"
                  "<p>'interleave channels' to resolve layers into separate parts. "
                  "This creates a multi-part file optimized for read performance.</p>"
                  "For full compatibility with versions of Nuke using OpenEXR 1.x "
                  "'truncate channel names' should be used to ensure that channels "
                  "do not overflow the name buffer."),
  "standard_layer_name_format" : ("Older versions of Nuke write out channel names in the format: view.layer.channel. "
                                  "Check this option to follow the EXR standard format: layer.view.channel"),
  "write_full_layer_names" : ("Older versions of Nuke just stored the layer name in the part "
                              "name of multi-part files. Check this option to always write the "
                              "layer name in the channel names following the EXR standard."),
  "truncateChannelNames" : ("Truncate channel names to a maximum of 31 characters for backwards compatibility"),
  "write_ACES_compliant_EXR" : ("Write out an ACES compliant EXR file")

}
# Tooltips for codec properties.  Currently only some of the mov encoder property tooltips are defined.
kCodecTooltips = {
  "exr" : kEXRTooltips
}


class CodecUIController(QtWidgets.QWidget):
  """CodecUIController is the base class used to control the widgets for specific Codecs.
  This allows to customize layout of the widgets and signals and slots"""
  propertyChanged = QtCore.Signal()

  def __init__(self, file_type, propertyDictionaries, presetDictionary):
    QtWidgets.QWidget.__init__(self)
    self._file_type = file_type
    self._widgets = []
    self.initializeUI(propertyDictionaries, presetDictionary)


  def connectProperty(self,propertyWidget):
    """reimplement this to allow setup custom signals and slots"""
    propertyWidget.propertyChanged.connect(self.propertyChanged)


  def getTooltip(self, label, propertyKey):
    # Create the tooltip.  This matches how tooltips appear from knob widgets.  Adding the HTML markup
    # also has the effect of making Qt apply wrapping to the text.
    tooltip = "<b>" + label + "</b>"
    tooltipsForCodec = kCodecTooltips.get(self._file_type, dict())
    propertyTooltip = tooltipsForCodec.get(propertyKey, None)
    if propertyTooltip is not None:
      tooltip = tooltip + "<br>" + propertyTooltip
    return tooltip


  def getLabelAndProperty(self, propertyKey):
    label = propertyKey
    # If key is not a string, assume its a tupe containing (label, key)
    if not isinstance(propertyKey, str):
      label, propertyKey = propertyKey
    return label, propertyKey


  def initializeUI(self, propertyDictionaries, presetDictionary):
    """Creates all the properties from the propertyDictionaries"""
    layout = TaskUIFormLayout()
    self.setLayout(layout)
    for properties in propertyDictionaries:
      # Flatten dictionary into tupes of keyvalue pairs
      for (propertyKey, propertyValue) in properties.items():
        label, propertyKey = self.getLabelAndProperty(propertyKey)
        tooltip = self.getTooltip(label,propertyKey)
        propertyWidget = UIPropertyFactory.create(type(propertyValue), key=propertyKey, value=propertyValue, dictionary=presetDictionary, label=label, tooltip=tooltip)
        if propertyWidget is not None:
          # Force the widget to commit its value back to the preset.  This
          # ensures that the property values are stored in the preset even if
          # the user hasn't changed them from the defaults.  Mixing this with
          # the UI is not ideal, but the property widgets do already have all
          # the logic for determining the defaults and writing them to the
          # preset.
          propertyWidget.update(commit=True)
          self.connectProperty(propertyWidget)
          layout.addRow(propertyWidget._label+ ":", propertyWidget)



class EXRCodecUIController(CodecUIController):
  kDataType = "datatype"
  kCompression = "compression"
  kCompressionLevel = "dw_compression_level"
  kMetadata = "metadata"
  kPrefix = "noprefix"
  kInterleave = "interleave"
  kLayerNameFormat= "standard_layer_name_format"
  kFullLayerNames = "write_full_layer_names"
  kTruncateChannelNames = "truncateChannelNames"
  kWriteACESCompliantEXR = "write_ACES_compliant_EXR"

  def __init__(self, file_type, propertyDictionaries, presetDictionary):
     CodecUIController.__init__(self,"exr",propertyDictionaries, presetDictionary)


  def createProperty(self,properties, propertyKey, presetDictionary):
    label, propertyValue = properties[propertyKey]
    tooltip = self.getTooltip(label, propertyKey)
    propertyWidget = UIPropertyFactory.create(type(propertyValue), key=propertyKey, value=propertyValue, dictionary=presetDictionary, label=label, tooltip=tooltip)
    propertyWidget.update(commit=True)
    self.connectProperty(propertyWidget)
    return propertyWidget


  def initializeUI(self, propertyDictionaries, presetDictionary):
    """Creates all the properties from the propertyDictionaries"""
    properties = dict()
    #construct a dictionary of tuples (label,propertyValue)
    for prop in propertyDictionaries:
      # Flatten dictionary into tupes of keyvalue pairs
      for (propertyKey, propertyValue) in prop.items():
        label, propertyKey = self.getLabelAndProperty(propertyKey)
        properties[propertyKey] = (label, propertyValue)

    layout = TaskUIFormLayout()
    self.setLayout(layout)

    #datatype
    widget = self.createProperty(properties, self.kDataType, presetDictionary)
    layout.addRow(widget._label+ ":", widget)

    #compression
    widget = self.createProperty(properties, self.kCompression, presetDictionary)
    layout.addRow(widget._label+ ":", widget)
    self._compressionWidget = widget

    widget = self.createProperty(properties, self.kCompressionLevel, presetDictionary)
    layout.addRow(widget._label+ ":", widget)
    self._compressionLevelWidget = widget
    self.compressionChanged()

    #metadata
    self._writeACESCompliantEXRWidget = self.createProperty(properties, self.kWriteACESCompliantEXR, presetDictionary)
    layout.addRow(self._writeACESCompliantEXRWidget._label + ":", self._writeACESCompliantEXRWidget)

    metadataWidget = self.createProperty(properties, self.kMetadata, presetDictionary)
    prefixWidget = self.createProperty(properties, self.kPrefix, presetDictionary)
    self._metadataWidget = metadataWidget
    self._prefixWidget = prefixWidget
    layout.addMultiWidgetRow((metadataWidget._label, prefixWidget._label),
                             (metadataWidget, prefixWidget))
    self.metadataChanged()

    #interleaving
    self._interleavingWidget = self.createProperty(properties, self.kInterleave, presetDictionary)
    self._standardLayerNameWidget = self.createProperty(properties, self.kLayerNameFormat, presetDictionary)
    self._fullLayerNamesWidget = self.createProperty(properties, self.kFullLayerNames, presetDictionary)
    self._truncateLayerNamesWidget = self.createProperty(properties, self.kTruncateChannelNames, presetDictionary)
    layout.addRow(self._interleavingWidget._label+":",self._interleavingWidget)
    layout.addRow(self._standardLayerNameWidget._label+":",self._standardLayerNameWidget)
    layout.addRow(self._fullLayerNamesWidget._label+":",self._fullLayerNamesWidget)
    layout.addRow(self._truncateLayerNamesWidget._label+":",self._truncateLayerNamesWidget)
    self.interleaveChanged()


  #Slots
  def compressionChanged(self):
    layout = self.layout()
    text = self._compressionWidget._widget.currentText()
    if "DWA" in text:
      layout.setWidgetVisible(self._compressionLevelWidget, True)
    else:
      layout.setWidgetVisible(self._compressionLevelWidget, False)
    self.propertyChanged.emit()


  def interleaveChanged(self):
    layout = self.layout()
    index = self._interleavingWidget._widget.currentIndex()
    if index == 0:
      layout.setWidgetEnabled(self._standardLayerNameWidget, True)
      layout.setWidgetEnabled(self._fullLayerNamesWidget, False)
      layout.setWidgetEnabled(self._truncateLayerNamesWidget, True)
    elif index == 1:
      layout.setWidgetEnabled(self._standardLayerNameWidget, True)
      layout.setWidgetEnabled(self._fullLayerNamesWidget, False)
      layout.setWidgetEnabled(self._truncateLayerNamesWidget, False)
    elif index == 2:
      layout.setWidgetEnabled(self._standardLayerNameWidget, True)
      layout.setWidgetEnabled(self._fullLayerNamesWidget, True)
      layout.setWidgetEnabled(self._truncateLayerNamesWidget, False)
    self.propertyChanged.emit()


  def metadataChanged(self):
    layout = self.layout()
    text = self._metadataWidget._widget.currentText()
    if "all" in text:
      layout.setWidgetEnabled(self._prefixWidget,True)
    else:
      layout.setWidgetEnabled(self._prefixWidget,False)
    self.propertyChanged.emit()

  def connectProperty(self, propertyWidget):
    if propertyWidget._label == "compression":
      propertyWidget.propertyChanged.connect(self.compressionChanged)
    elif propertyWidget._label == "interleave":
      propertyWidget.propertyChanged.connect(self.interleaveChanged)
    elif propertyWidget._label == "metadata":
      propertyWidget.propertyChanged.connect(self.metadataChanged)
    else:
      propertyWidget.propertyChanged.connect(self.propertyChanged)


class WriteNodePropertyWidget(NodePropertyWidget):
  """NodePropertyWidget subclass that creates property widgets for a write node with the
  passed in fileType."""
  def __init__(self, fileType, propertyDictionaries, presetDictionary):
    self._writeNode = nuke.createNode("Write", "", False)
    fileTypeKnob = self._writeNode.knobs()["file_type"]
    fileTypeKnob.setValue(fileType)

    NodePropertyWidget.__init__(self, self._writeNode, propertyDictionaries, presetDictionary)

  def __del__(self):
    nuke.delete(self._writeNode)
