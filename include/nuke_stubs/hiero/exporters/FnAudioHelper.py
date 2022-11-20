# Copyright (c) 2019 The Foundry Visionmongers Ltd.  All Rights Reserved.
# Helper file to implement audio export functionality shared by the Audio and Transcode Images export task/UI

from . import FnAudioConstants
from hiero.ui.FnUIProperty import UIPropertyFactory

# Defines the required audio export properties in the preset decitionary
def defineExportPresetProperties(exportPreset):
  exportPreset.properties()[FnAudioConstants.kNumChannelsKey] = FnAudioConstants.kDefaultChannels
  exportPreset.properties()[FnAudioConstants.kCodecKey] = FnAudioConstants.kDefaultCodec
  exportPreset.properties()[FnAudioConstants.kSampleRateKey] = FnAudioConstants.kDefaultSampleRate
  exportPreset.properties()[FnAudioConstants.kBitDepthKey] = FnAudioConstants.kDefaultBitDepth
  exportPreset.properties()[FnAudioConstants.kBitRateKey] = FnAudioConstants.kDefaultBitRate

# Sets the audio export settings from the preset to the current export task
def setAudioExportSettings(exportTask):
  exportTask._outputChannels = FnAudioConstants.kChannels[exportTask._preset.properties()[FnAudioConstants.kNumChannelsKey]]
  exportTask._sampleRate = FnAudioConstants.kSampleRates[exportTask._preset.properties()[FnAudioConstants.kSampleRateKey]]
  exportTask._bitDepth = FnAudioConstants.kBitDepths[exportTask._preset.properties()[FnAudioConstants.kBitDepthKey]]
  exportTask._bitRate = FnAudioConstants.kBitRates[exportTask._preset.properties()[FnAudioConstants.kBitRateKey]]

# Creates the codec menu and connects it to a provided callback
def createCodecProperty(exportUI, formLayout, callback, tooltip):
  codecToolTip = tooltip
  codecKey, codecValue = FnAudioConstants.kCodecKey, list(FnAudioConstants.kCodecs.keys())
  codecProperty = UIPropertyFactory.create(type(codecValue), key=codecKey, value=codecValue, dictionary=exportUI._preset._properties, label="Codec")
  codecProperty.setToolTip(codecToolTip)
  formLayout.addRow("Codec:", codecProperty)
  exportUI._codecProperty = codecProperty
  codecProperty.propertyChanged.connect(callback)

# Creates property menus for the audio export depending on what the current codec selected is
def createCodecSpecificProperties(exportUI, formLayout, enabled):  
  if hasattr(exportUI, '_sampleRateProperty'):
    formLayout.removeRow(exportUI._sampleRateProperty)
    delattr(exportUI, '_sampleRateProperty')
  
  srateKey, srateValue = FnAudioConstants.kSampleRateKey, list(FnAudioConstants.kSampleRates.keys())
  srateToolTip = ("Audio Sample Rate.")
  sampleRateProperty = UIPropertyFactory.create(type(srateValue), key=srateKey, value=srateValue, dictionary=exportUI._preset._properties, label="Sample Rate")
  sampleRateProperty.setToolTip(srateToolTip)
  formLayout.addRow("Sample Rate:", sampleRateProperty)
  formLayout.setWidgetEnabled(sampleRateProperty, enabled)
  exportUI._sampleRateProperty = sampleRateProperty

  # If the selected codec is mp2 or ac3, we disable 96k as it is not supported
  if (exportUI._preset.properties()[FnAudioConstants.kCodecKey] == FnAudioConstants.kAC3Codec 
  or exportUI._preset.properties()[FnAudioConstants.kCodecKey] == FnAudioConstants.kMP2Codec):
    ninetySixKhzIndex = srateValue.index(FnAudioConstants.k96khzKey)
    sampleRateProperty._widget.model().item(ninetySixKhzIndex).setEnabled(False)
  
  # If the previous sample rate is no longer supported, select the next highest sample rate
  compressedSampleRates = list(FnAudioConstants.kCompressedSampleRates.keys())
  if exportUI._preset.properties()[FnAudioConstants.kSampleRateKey] not in compressedSampleRates:
    exportUI._preset.properties()[FnAudioConstants.kSampleRateKey] = compressedSampleRates[-1]
    sampleRateProperty.update()
  
  if hasattr(exportUI, '_bitDepthProperty'):
    formLayout.removeRow(exportUI._bitDepthProperty)
    delattr(exportUI, '_bitDepthProperty')
  if hasattr(exportUI, '_bitRateProperty'):
    formLayout.removeRow(exportUI._bitRateProperty)
    delattr(exportUI, '_bitRateProperty')
  
  # Bit depth is only relevant for PCM export, while bit rate is only relevant for the compressed formats
  if exportUI._preset.properties()[FnAudioConstants.kCodecKey] == FnAudioConstants.kNonCompressedCodec:
    bitDepthToolTip = ("Audio Bit Depth.")
    bdKey, bdValue = FnAudioConstants.kBitDepthKey, list(FnAudioConstants.kBitDepths.keys())
    bitDepthProperty = UIPropertyFactory.create(type(bdValue), key=bdKey, value=bdValue, dictionary=exportUI._preset._properties, label="Bit Depth")
    bitDepthProperty.setToolTip(bitDepthToolTip)
    formLayout.addRow("Bit Depth:", bitDepthProperty)
    formLayout.setWidgetEnabled(bitDepthProperty, enabled)
    exportUI._bitDepthProperty = bitDepthProperty
  else:
    bitRateToolTip = ("Audio Bit Rate.")
    brKey, brValue = FnAudioConstants.kBitRateKey, list(FnAudioConstants.kBitRates.keys())
    bitRateProperty = UIPropertyFactory.create(type(brValue), key=brKey, value=brValue, dictionary=exportUI._preset._properties, label="Bit Rate")
    bitRateProperty.setToolTip(bitRateToolTip)
    formLayout.addRow("Bit Rate:", bitRateProperty)
    formLayout.setWidgetEnabled(bitRateProperty, enabled)
    exportUI._bitRateProperty = bitRateProperty
  
  if hasattr(exportUI, '_numChannelsProperty'):
    formLayout.removeRow(exportUI._numChannelsProperty)
    delattr(exportUI, '_numChannelsProperty')
  
  audioChannelToolTip = ("The audio channel configuration. Supports up to 7.1 surround for PCM, \nup to 5.1 surround for AC-3, and stereo for MP2")
  cKey, cValue = FnAudioConstants.kNumChannelsKey, list(FnAudioConstants.kChannels.keys())
  
  channelsProperty = UIPropertyFactory.create(type(cValue), key=cKey, value=cValue, dictionary=exportUI._preset._properties, label="Output Channels")
  channelsProperty.setToolTip(audioChannelToolTip)
  exportUI._numChannelsProperty = channelsProperty
  formLayout.addRow("Output Channels:", channelsProperty)
  formLayout.setWidgetEnabled(channelsProperty, enabled)
  
  # If the selected codec is mp2 or ac3, these support different channel layouts
  if exportUI._preset.properties()[FnAudioConstants.kCodecKey] == FnAudioConstants.kAC3Codec:
    sevenPointOneIndex = cValue.index(FnAudioConstants.kSevenPointOneLayout)
    channelsProperty._widget.model().item(sevenPointOneIndex).setEnabled(False)
    # If the previous channel layout is no longer supported, select the next channel layout
    if exportUI._preset.properties()[FnAudioConstants.kNumChannelsKey] == FnAudioConstants.kSevenPointOneLayout:
      exportUI._preset.properties()[FnAudioConstants.kNumChannelsKey] = FnAudioConstants.kFivePointOneLayout
    channelsProperty.update()
  
  elif exportUI._preset.properties()[FnAudioConstants.kCodecKey] == FnAudioConstants.kMP2Codec:
    fivePointOneIndex = cValue.index(FnAudioConstants.kFivePointOneLayout)
    sevenPointOneIndex = cValue.index(FnAudioConstants.kSevenPointOneLayout)
    channelsProperty._widget.model().item(fivePointOneIndex).setEnabled(False)
    channelsProperty._widget.model().item(sevenPointOneIndex).setEnabled(False)
    # If the previous channel layout is no longer supported, select the next channel layout
    if exportUI._preset.properties()[FnAudioConstants.kNumChannelsKey] == FnAudioConstants.kSevenPointOneLayout\
    or exportUI._preset.properties()[FnAudioConstants.kNumChannelsKey] == FnAudioConstants.kFivePointOneLayout:
      exportUI._preset.properties()[FnAudioConstants.kNumChannelsKey] = FnAudioConstants.kStereoLayout
    channelsProperty.update()
