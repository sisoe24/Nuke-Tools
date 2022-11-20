# This item registers for timeline context menu events and on receiving one,
# inserts itself into the menu. When invoked, it shows a dialog asking for the
# new clip name and sets it onto the selected track item.

import hiero.core
import hiero.ui
import foundry.ui
from PySide2 import (QtCore, QtGui, QtWidgets)
import tempfile
import os
import os.path
import pickle
from hiero.core import TimeBase, Timecode
from hiero.core.FnNukeHelpers import isNonZeroStartFrameMovieFile
from hiero.core.nuke import ScriptWriter, PythonScriptWriter, Script
from hiero.core.nuke.Node import *
NUM_DECIMALS = 3

class SendToNukeDialog(QtWidgets.QDialog):
  kRetimeNoneText = 'None'
  kRetimeAdd32PulldownText = 'Add 3:2 Pulldown'
  kRetimeRemove32PulldownText = 'Remove 3:2 Pulldown'
  kRetimeTimebaseText = 'To Timebase'
  kRetimeSpeedText = 'Speed'

  def __init__(self, enableSoftTrims, clipFps, settingsPrefix, force32Mode=False, parent=None, windowTitle="Send To Nuke"):
    super(SendToNukeDialog,  self).__init__(parent)

    # make some settings names
    self.kSendToNukeScriptPathKey = settingsPrefix + "sendToNukeScriptPath"
    self.kSendToNukeWritePathKey = settingsPrefix + "sendToNukeWritePath"
    self.kSendToNukePresetKey = settingsPrefix + "sendToNukePreset"
    self.kSendToNukeRetimeSettingKey = settingsPrefix + "sendToNukeRetimeMode"
    self.kSendToNukeRetimeFpsKey = settingsPrefix + "sendToNukeRetimeFps"
    self.kSendToNukeRetimeSpeedKey = settingsPrefix + "sendToNukeRetimePercentage"

    self._settingsPrefix = settingsPrefix

    self.setToolTip("Automates creation of a .nk script with the selected clip as a read node, connected to a write node, and automatically launches Nuke.\nCurrently only works on Clips and for single selections.")

    self._clipFps = clipFps

    # load the settings first!!!
    import hiero.core
    try:
      settings = hiero.core.ApplicationSettings()
    except:
      settings = ApplicationSettings()

    presetProperties = {}
    presetData = settings.value(self.kSendToNukePresetKey, "")
    if presetData != "":
      try:
        presetProperties = pickle.loads(presetData)
      except:
        # ignore any error in unpickling
        exception( "Error parsing sendToNukePreset user preference data" )
        pass

    self.setWindowTitle(windowTitle)
    self.setSizeGripEnabled(True)

    self._ui = self.createTranscodeUI(presetProperties)

    layout = QtWidgets.QFormLayout()
    self.setLayout(layout)

    self._scriptPathWidget = foundry.ui.FnFilenameField(isDirectory=False, isSaveFile=True, caption="Save file as", filter="Nuke Scripts (*.nk)")
    self._scriptPathWidget.setFilename(settings.value(self.kSendToNukeScriptPathKey, ""))
    self._scriptPathWidget.setToolTip("Use this field to set the location and name of the output Nuke script.")
    layout.addRow("Nuke Script Path:", self._scriptPathWidget)

    # add soft trim option here
    self._useSoftTrims = QtWidgets.QCheckBox("Use Soft Trims")
    if not enableSoftTrims:
      self._useSoftTrims.setEnabled(False)
    self._useSoftTrims.setToolTip("Tick this if you'd like the soft trims to be used for the frame range sent to Nuke.\nThis option is only enabled if the selected clips have soft trims enabled.")
    layout.addRow("", self._useSoftTrims)

    # get the supported file extensions
    imageFilter = ""
    for (codecType, codecSettings) in self._ui._preset._codecSettings.items():
      if len(imageFilter) > 0:
        imageFilter += " *." + codecSettings["extension"]
      else:
        imageFilter = "*."+ codecSettings["extension"]

    self._outputPathWidget = foundry.ui.FnFilenameField(isDirectory=False, isSaveFile=True, caption="Save to file", filter=("Image Files (%s)" % imageFilter))
    self._outputPathWidget.setFilename(settings.value(self.kSendToNukeWritePathKey, ""))
    self._outputPathWidget.setToolTip("Use this field to set the directory where you'd like the Nuke output to be written to.")
    layout.addRow("Nuke Write Path:", self._outputPathWidget)

    # catch the change of the filename so that we can auto change the file type
    self._outputPathWidget.filenameChanged.connect(self.filenameChanged)

    if self._ui != None:
      self._ui.buildCodecUI(layout)

    self._ingestButton = QtWidgets.QCheckBox("Ingest Nuke Output")
    self._ingestButton.setToolTip("Tick this field if you'd like the output from the Nuke script to be ingested back into the selected bin.")
    layout.addRow("", self._ingestButton)

    self._retimeBox = QtWidgets.QComboBox()

    self._retimeBox.setToolTip("Use these options to retime the clip in Nuke.")

    if not force32Mode:
      self._retimeBox.addItem(SendToNukeDialog.kRetimeNoneText)

    if TimeBase.k24NTSC.__eq__(clipFps) or TimeBase.k24.__eq__(clipFps):
      self._retimeBox.addItem(SendToNukeDialog.kRetimeAdd32PulldownText)

    if TimeBase.k30NTSC.__eq__(clipFps) or TimeBase.k30.__eq__(clipFps):
      self._retimeBox.addItem(SendToNukeDialog.kRetimeRemove32PulldownText)

    if not force32Mode:
      self._retimeBox.addItem(SendToNukeDialog.kRetimeTimebaseText)
      self._retimeBox.addItem(SendToNukeDialog.kRetimeSpeedText)

    self._retimeBox.setDisabled(force32Mode)

    self._retimeBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self._retimeBox.currentIndexChanged.connect(self.retimeChanged)

    import hiero.core.FnExporterBase
    fps = hiero.core.FnExporterBase.GetFramerates()
    self._retimeFpsBox = QtWidgets.QComboBox()
    for f in fps:
      self._retimeFpsBox.addItem("%0.2f" % f)
    self._retimeFpsBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self._retimeFpsLabel = QtWidgets.QLabel("fps")

    self._retimeSpeedBox = QtWidgets.QLineEdit()
    self._retimeSpeedBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self._retimePercentageLabel = QtWidgets.QLabel("%")

    retimeWidget = PySide2.QtWidgets.QWidget()
    subLayout = QtWidgets.QHBoxLayout()
    subLayout.setContentsMargins(0, 0, 0, 0)
    retimeWidget.setLayout(subLayout)
    subLayout.addWidget(self._retimeBox)
    subLayout.addWidget(self._retimeFpsBox)
    subLayout.addWidget(self._retimeFpsLabel)
    self._retimeFpsBox.hide()
    self._retimeFpsLabel.hide()
    self._retimeSpeedBox.hide()
    self._retimePercentageLabel.hide()
    subLayout.addWidget(self._retimeSpeedBox)
    subLayout.addWidget(self._retimePercentageLabel)
    layout.addRow("Retime:", retimeWidget)

    self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Launch Nuke")
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDefault(True)
    self._buttonbox.accepted.connect(self.accept)
    self._buttonbox.rejected.connect(self.reject)
    layout.addRow("", self._buttonbox)

    # load retime options settings
    self._retimeSpeedBox.setText(settings.value(self.kSendToNukeRetimeSpeedKey, "50"))
    self._retimeFpsBox.setCurrentIndex(self._loadComboBoxSetting(settings, self.kSendToNukeRetimeFpsKey, self._retimeFpsBox))
    self._retimeBox.setCurrentIndex(self._loadComboBoxSetting(settings, self.kSendToNukeRetimeSettingKey, self._retimeBox))

    self.setLayout(layout)

  def _showWarning(self, text):
    msgBox = QtWidgets.QMessageBox()
    msgBox.setText(text)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
    msgBox.exec_()

  def accept(self):

    # check if the nuke script path is valid
    scriptPath = self.scriptPath()
    if len(scriptPath) == 0:
      self._showWarning("Please enter a valid script path and try again.")
      self._scriptPathWidget.setFocus()
      return

    writePath = self.outputPath()
    if len(writePath) == 0:
      self._showWarning("Please enter a write node path and try again.")
      self._outputPathWidget.setFocus()
      return

    QtWidgets.QDialog.accept(self)

  def _loadComboBoxSetting(self, settings, name, comboBox):
    lookFor = settings.value(name, "")
    count = comboBox.count()
    i = 0
    while i < count:
      if comboBox.itemText(i) == lookFor:
        return i
      i += 1
    return 0

  def _setFps(self, newFps):
    if self._ui != None:
      fileType = self._ui._preset._properties["file_type"]
      if str(fileType) != "mov":
        return

      for uiProperty in self._ui._uiProperties:
        if str(uiProperty._key) == "fps":
          # tell the ui that the value has changed
          uiProperty.setFloatValue(newFps, 0.01)
          break

  def retimeChanged(self, index):
    retimeText = self._retimeBox.itemText(index)
    hideEverythingElse = False
    if retimeText == SendToNukeDialog.kRetimeTimebaseText:
      self._retimeSpeedBox.hide()
      self._retimePercentageLabel.hide()
      self._retimeFpsBox.show()
      self._retimeFpsLabel.show()
    elif retimeText == SendToNukeDialog.kRetimeSpeedText:
      self._retimeFpsBox.hide()
      self._retimeFpsLabel.hide()
      self._retimeSpeedBox.show()
      self._retimePercentageLabel.show()
      self._retimeSpeedBox.setFocus()
    elif retimeText == SendToNukeDialog.kRetimeAdd32PulldownText:
      newFps =  TimeBase.k30
      if self._isNTSC():
        newFps = TimeBase.k30NTSC
      self._setFps(newFps.toFloat())
      hideEverythingElse = True
    elif retimeText == SendToNukeDialog.kRetimeRemove32PulldownText:
      newFps =  TimeBase.k24
      if self._isNTSC():
        newFps = TimeBase.k24NTSC
      self._setFps(newFps.toFloat())
      hideEverythingElse = True
    else:
      hideEverythingElse = True

    if hideEverythingElse:
      self._retimeSpeedBox.hide()
      self._retimePercentageLabel.hide()
      self._retimeFpsBox.hide()
      self._retimeFpsLabel.hide()

  def saveSettings(self):
    settings = hiero.core.ApplicationSettings()
    settings.setValue(self.kSendToNukeScriptPathKey, self.scriptPath())
    settings.setValue(self.kSendToNukeWritePathKey, self.outputPath())
    if self._ui != None:
      settings.setValue(self.kSendToNukePresetKey, pickle.dumps(self._ui._preset._properties))
    settings.setValue(self.kSendToNukeRetimeSettingKey, self._retimeBox.itemText(self._retimeBox.currentIndex()))
    settings.setValue(self.kSendToNukeRetimeFpsKey, self._retimeFpsBox.itemText(self._retimeFpsBox.currentIndex()))

    speedText = self._retimeSpeedBox.text()
    if speedText == None:
      speedText = ""
    settings.setValue(self.kSendToNukeRetimeSpeedKey, speedText)

  def filenameChanged(self):
    # get the filename out of the widget
    filename = self._outputPathWidget.filename()

    # get the extension
    (filename, extension) = os.path.splitext(filename)
    if (len(extension) > 0):
      # extension is ".ext" so strip off the .
      extension = extension[1:]

      # go through all of the codec's in the ui's codec settings to get the right file type
      comboBoxFileType = None
      for (filetype, codecSettings) in self._ui._codecSettings.items():
        # have to specifically check against the extension, not just the filetype
        if (codecSettings["extension"] == extension):
          comboBoxFileType = filetype

          # done looking, get out of here
          break

      # now tell the combo box to set that as the current index
      if str(self._ui._codecComboBox.currentText()) != comboBoxFileType:
        for i in range(0, self._ui._codecComboBox.count()):
          if str(self._ui._codecComboBox.itemText(i)) == comboBoxFileType:
            if self._ui._codecComboBox.currentIndex() != i:
              self._ui._codecComboBox.setCurrentIndex(i)
            break


  def fileTypeChanged(self):
    filename = self._outputPathWidget.filename()
    if len(filename) > 0:
      fileType = self._ui._preset._properties["file_type"]
      newExtension = "." + self._ui._preset._codecSettings[fileType]["extension"]
      (filename, extension) = os.path.splitext(filename)

      # make sure that the extension was in the old file, and only change things if the extension is different
      # otherwise, we'll have an infinite signal going on because this change will trigger filenameChanged above, and vice versa
      if (len(extension) > 0) and (extension != newExtension):
        self._outputPathWidget.setFilename(filename + newExtension)

  def createTranscodeUI(self, presetProperties):
    import hiero.exporters.FnExternalRender
    import hiero.exporters.FnExternalRenderUI

    class SpecialTranscodeExporterUI(hiero.exporters.FnExternalRenderUI.NukeRenderTaskUI):
      def __init__(self, dialog):
        hiero.exporters.FnExternalRenderUI.NukeRenderTaskUI.__init__(self, hiero.exporters.FnExternalRender.NukeRenderPreset("SendToNukePreset", presetProperties))
        self._dialog = dialog

      def codecComboBoxChanged (self, value):
        # call the base class
        hiero.exporters.FnExternalRenderUI.NukeRenderTaskUI.codecComboBoxChanged(self, value)

        # tell the containing dialog
        self._dialog.fileTypeChanged()

    return SpecialTranscodeExporterUI(self)

  def scriptPath(self):
    return self._scriptPathWidget.filename()
    #return self._scriptPathWidget.text()

  def outputPath(self):
    return self._outputPathWidget.filename()
    #return self._outputPathWidget.text()

  #def resolveOutputFileName(self, outputPath):
  #  if self._ui != None:
  #    fileType = self._ui._preset._properties["file_type"]
  #    isVideo = False
  #    if "isVideo" in self._ui._preset._codecSettings[fileType]:
  #      isVideo = self._ui._preset._codecSettings[fileType]["isVideo"]
  #
  #    # strip out the extension
  #    (filename, extension) = os.path.splitext(outputPath)
  #
  #    outputPath = filename + "." + self._ui._preset._codecSettings[fileType]["extension"]
  #
  #    # check if it's a video and if it's got sequence stuff in the name
  #
  #
  #    outputPath = outputPath.replace("\\", "/")
  #    return final
  #
  #  return sourceMediaFilePath

  def addWriteNode(self, outputPath, inputNode, framerate, projectsettings):
    import hiero.exporters.FnExternalRender
    if self._ui != None:
      writeNode = hiero.exporters.FnExternalRender.createWriteNode(self, outputPath, self._ui._preset, inputNode=inputNode, framerate=framerate, projectsettings=projectsettings)
    else:
      writeNode = WriteNode(outputPath, inputNode)
    return writeNode

  def _getRetimeType(self):
    return self._retimeBox.itemText(self._retimeBox.currentIndex())

  def addRetimeNode(self):
    node = None
    type = self._getRetimeType()
    if type == SendToNukeDialog.kRetimeAdd32PulldownText:
      node = Node("add32p")
    if type == SendToNukeDialog.kRetimeRemove32PulldownText:
      node = Node("remove32p")
    if type == SendToNukeDialog.kRetimeTimebaseText:
      node = Node("OFXuk.co.thefoundry.time.oflow_v100")
      node.setKnob("timing", "Speed")
      fps = str(self._retimeFpsBox.itemText(self._retimeFpsBox.currentIndex()))
      node.setKnob("timingSpeed", "{{\"%s / %s\"}}" % (fps, self._clipFps))
    if type == SendToNukeDialog.kRetimeSpeedText:
      node = Node("OFXuk.co.thefoundry.time.oflow_v100")
      node.setKnob("timing", "Speed")
      node.setKnob("timingSpeed", "{{\"%s / 100.0\"}}" % str(self._retimeSpeedBox.text()))
    return node

  def addReformatNode(self, rootNode):
    reformat = None
    rf = self._ui._preset._properties["reformat"]
    # If the reformat field has been set, create a reformat node imediately before the write.
    if str(rf["to_type"]) == ReformatNode.kToFormat:
      if "width" in rf and "height" in rf and "pixelAspect" in rf and "name" in rf and "resize" in rf:
        format = hiero.core.Format(rf["width"], rf["height"], rf["pixelAspect"], rf["name"])
        resize = rf["resize"]
        reformat = format.addToNukeScript(None, resize=resize)
        rootNode.setKnob("format", reformat.knob("format"))
    return reformat

  def _getRetimeFps(self):
    return float(self._retimeFpsBox.itemText(self._retimeFpsBox.currentIndex()))

  def _getRetimeSpeed(self):
    return float(self._retimeSpeedBox.text()) / 100.0

  def _getInvertedRetimeSpeed(self):
    return 100.0 / float(self._retimeSpeedBox.text())

  def _isNTSC(self):
    return TimeBase.k24NTSC.__eq__(self._clipFps) or TimeBase.k30NTSC.__eq__(self._clipFps)

  def retimeFrameRange(self, start, end):
    type = self._getRetimeType()

    # if there was an fps selected by the user, then use that
    newFps = self.getFps()
    if newFps == None:
      # since there wasn't, default to the first clip's rate found
      newFps = self._clipFps
    else:
      # convert to a Timebase object
      newFps = TimeBase(str(newFps))

    if type == SendToNukeDialog.kRetimeNoneText:
      return (start, end, newFps)

    if type == SendToNukeDialog.kRetimeSpeedText:
      end = start + ((end - start) * self._getInvertedRetimeSpeed())
      return (start, end, newFps)

    if type == SendToNukeDialog.kRetimeAdd32PulldownText:
      if self._isNTSC():
        convertFps = TimeBase.k30NTSC
      else:
        convertFps = TimeBase.k30
    elif type == SendToNukeDialog.kRetimeRemove32PulldownText:
      if self._isNTSC():
        convertFps = TimeBase.k24NTSC
      else:
        convertFps = TimeBase.k24
    elif type == SendToNukeDialog.kRetimeTimebaseText:
      convertFps = TimeBase(self._getRetimeFps())

    end = start + TimeBase.convert((end - start), self._clipFps, convertFps)

    # always set the newly ingested media's fps to what the user selected in the mov drop down, if it's specified
    if self.getFps() != None:
      return (start, end, TimeBase(str(self.getFps())))
    return (start, end, convertFps)

  def getFps(self):
    if self._ui != None:
      fileType = self._ui._preset._properties["file_type"]
      preset = self._ui._preset
      if "fps" in preset._properties[fileType]:
        return preset._properties[fileType]["fps"]
    return None


  def ingest(self):
    return self._ingestButton.isChecked()

  def useSoftTrims(self):
    return self._useSoftTrims.isChecked()

class SendToNukeAction(QtWidgets.QAction):
  def __init__(self, menuText, settingsPrefix = ""):
      QtWidgets.QAction.__init__(self, menuText, None)
      self._dialogTitle = menuText
      if self._dialogTitle.endswith("..."):
        self._dialogTitle = self._dialogTitle[:-3]
      self._settingsPrefix = settingsPrefix
      self.triggered.connect(self.doit)
      hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), self.eventHandler)

  def findClips(self, container, clips, parents):
    if isinstance(container, (list,tuple)):
      for i in container:
        self.findClips(i, clips, parents)
    else:
      if isinstance(container, hiero.core.BinItem) and isinstance(container.activeItem(), hiero.core.Clip):
        clip = container.activeItem()
        if isinstance(clip, hiero.core.Clip) and hasattr(clip, 'mediaSource'):
          clips.append(clip)
          parents[clip] = container.parentBin()

          # TimelineTakes have a timeline method
          # We don't currently handle timelines directly
          #if (hasattr(activeTake, 'timeline')):
          #  timeline = activeTake.timeline()
          #
          #  # Get all of the video tracks
          #  videoTracks = timeline.videoTracks()
          #  for videoTrack in videoTracks:
          #    items = videoTrack.items()
          #    for trackItem in items:
          #      clip = trackItem.source()
          #      if (hasattr(clip, "mediaSource")):
          #        clips.append(clip)

      if hasattr(container, 'items'):
        items = list(container.items())
        for i in items:
          self.findClips(i, clips, parents)

  def selectedClips(self):
    selection = hiero.ui.currentContextMenuView().selection()
    self._selection = selection

    clips = []
    parents = {}
    self.findClips(selection, clips, parents)
    return (clips, parents)

  def getMediaRange(self, clips, useSoftTrims):
    start = None
    end = None
    for clip in clips:
      mediaSource = clip.mediaSource()
      fileInfos = mediaSource.fileinfos()
      for fileInfo in fileInfos:
        if (start == None):
          start = fileInfo.startFrame()
          end = fileInfo.endFrame()
        else:
          if (start > fileInfo.startFrame()):
            start = fileInfo.startFrame()
          if (end < fileInfo.endFrame()):
            end = fileInfo.endFrame()
      if useSoftTrims and clip.softTrimsEnabled():
        if start < clip.softTrimsInTime():
          start = clip.softTrimsInTime()
        if end > clip.softTrimsOutTime():
          end = clip.softTrimsOutTime()
    return (start, end)

  def checkForSoftTrims(self, clips):
    for clip in clips:
      if clip.softTrimsEnabled():
        return True

    return False

  def doit(self, force32Mode = False):
    # get the currently selected clips from it
    (clips, parents) = self.selectedClips()

    enableSoftTrims = self.checkForSoftTrims(clips)

    if len(clips) == 0:
      hiero.core.log.info( "No clips selected" )
      return

    for clip in clips:
      clipfps = clip.framerate()
      break


    d = SendToNukeDialog(enableSoftTrims, clipfps, self._settingsPrefix, force32Mode, windowTitle=self._dialogTitle, parent=hiero.ui.mainWindow())
    if d.exec_() == QtWidgets.QDialog.Accepted:
      d.saveSettings()

      w = ScriptWriter()
      #w = PythonScript.PythonScriptWriter(autoConnectNodes=False)

      movOnRead = False
      for clip in clips:
        mediaSource = clip.mediaSource()
        fileInfos = mediaSource.fileinfos()
        for fileInfo in fileInfos:
          if (isNonZeroStartFrameMovieFile(fileInfo.filename())):
            movOnRead = True
            break
        if movOnRead:
          break

      outputPath = d.outputPath()
      frameOffset = 0
      if movOnRead:
        frameOffset = 1

      (start, end) = self.getMediaRange(clips, d.useSoftTrims())

      # adjust the ranges as appropriate for a retime
      (start, end, fpsForNewSource) = d.retimeFrameRange(start, end)

      rootNode = RootNode(first_frame=start+frameOffset, last_frame=end+frameOffset)
      fps = d.getFps()
      if fpsForNewSource != None:
        rootNode.setKnob("fps", round(fpsForNewSource.toFloat(), NUM_DECIMALS))
      w.addNode(rootNode)

      writeNodes = {}
      writeNodeIndex = 0
      for clip in clips:
        try:
          rootNode.addProjectSettings(clip.project().extractSettings())
        except Exception as e:
          msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, "Failed to Extract Project Settings", str(e), QtWidgets.QMessageBox.Ok)
          msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
          msgBox.exec_()
          return

        mediaSource = clip.mediaSource()
        fileInfos = mediaSource.fileinfos()
        width = mediaSource.width()
        height = mediaSource.height()
        pixelAspect = mediaSource.pixelAspect()
        metadata = mediaSource.metadata()

        readNodes = clip.addToNukeScript(w)

        assert len(readNodes) != 0

        # assume that the last node added is the final one in the chain
        writeNodeInput = readNodes[-1]

        metadataNode = MetadataNode(metadatavalues=[("hiero/project", clip.project().name())] )

        # Need a framerate inorder to create a timecode
        if fpsForNewSource:
          # Apply timeline offset to nuke output
          timecodeStart = clip.timecodeStart()

          if fpsForNewSource != clip.framerate():

            # we want the new timecode to be exactly the same as the original, so we convert it to a time code display type
            # then convert it back to frames using those values and the new timebase
            (hh, mm, ss, ff) = Timecode.framesToHMSF(timecodeStart, clip.framerate(), clip.dropFrame())
            timecodeStart = Timecode.HMSFToFrames(fpsForNewSource, clip.dropFrame(), hh, mm, ss, ff)

          # mat - fixing up the frame offsets so that they are 1 based for mov files
          startFrameWrite = start
          if movOnRead:
            startFrameWrite += 1

          # Proper time code support; will add later on, when AddTimeCodeNode gets added
          w.addNode(AddTimeCodeNode(timecodeStart=timecodeStart, fps=fpsForNewSource, dropFrames=clip.dropFrame(), frame=startFrameWrite))

          # The AddTimeCode field will insert an integer framrate into the metadata, if the framerate is floating point, we need to correct this
          metadataNode.addMetadata([("input/frame_rate",round(fpsForNewSource.toFloat(), NUM_DECIMALS))])

        w.addNode(metadataNode)
        writeNodeInput = metadataNode

        # assume that the first node added to the list is the read node
        readNode = readNodes[0]

        retimeNode = d.addRetimeNode()
        if retimeNode:
          w.addNode(retimeNode)

          # have to set it to hold, otherwise the output looks like crap when a retime is done (but only do when doing a retime)
          readNode.setKnob('before', 'hold')
          readNode.setKnob('after',  'hold')

          # change the write node's input
          writeNodeInput = retimeNode

        reformatNode = d.addReformatNode(rootNode)
        if reformatNode != None:
          writeNodeInput = reformatNode
          w.addNode(reformatNode)

        # create the write node and set stuff up
        try:
          projectsettings = clip.project().extractSettings()
          writeNode = d.addWriteNode(outputPath, writeNodeInput, fpsForNewSource, projectsettings)
        except Exception as e:
          msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, "Failed to Extract Project Settings", str(e), QtWidgets.QMessageBox.Ok)
          msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
          msgBox.exec_()
          return

        w.addNode(writeNode)
        writeNodes[writeNodeIndex] = writeNode
        writeNodeIndex += 1

        if d.ingest() and (clip in parents):
          mediaSourcePath = str(outputPath)

          movOnWrite = isNonZeroStartFrameMovieFile(mediaSourcePath)

          # special case image sequences to include the frame range in the file name
          newStart = start
          newEnd = end

          if (movOnWrite == False):
            # Nuke treats video formats as if they all start from 1, not 0, so we need to adjust our image sequence
            # frame range to account for this
            if (movOnRead):
              newStart += 1
              newEnd += 1
            mediaSourcePath = str(outputPath) + (" %d-%d" % (newStart, newEnd))
          newMediaSource = hiero.core.MediaSource.createOfflineVideoMediaSource(mediaSourcePath, newStart, newEnd - newStart + 1, fpsForNewSource)
          parents[clip].addItem(hiero.core.BinItem(hiero.core.Clip(newMediaSource)))

      viewerNode = Node("Viewer", inputNodes=writeNodes)
      if fps != None:
        viewerNode.setKnob("fps", fps)
      w.addNode(viewerNode)

      # add a bit at the end to save as the script to the new file name, forcing it to overwrite without asking the user
      if type(w) == PythonScriptWriter:
        script = str(w)
        script += "\n"
        script += ("nuke.scriptSaveAs(\"%s\", overwrite=1)\n" % (d.scriptPath()))

        hiero.core.log.info( script )

        # make a temp file to hold the script and write to it
        (fileDesc, path) = tempfile.mkstemp(suffix=".py", text="w")
        file = hiero.core.util.filesystem.openFile(path, 'w')
        file.write(script)
        file.close()
      else:
        path = d.scriptPath()
        w.writeToDisk(d.scriptPath())

      # send the temp script to nuke
      try:
        Script.launchNuke(path)
      except Exception as e:
        print(e)
        # If we got an exception, it's because the nuke path couldn't be found.
        # tell the user what we're looking for
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("The Nuke Path specified in the Application Preferences can not be found.\n\nPlease set the Nuke Path setting in the Application Preferences to a valid Nuke executable path.\n\nClick OK to open the Preferences dialog.")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        if msgBox.exec_() == QtWidgets.QMessageBox.Ok:
          # find the preferences menu action so that we can trigger it
          a = hiero.ui.findMenuAction("foundry.application.preferences")
          if a != None:
            a.trigger()


    # make sure we get cleaned up in this thread, instead of some other thread
    d.deleteLater()

  def eventHandler(self, event):
    if hasattr(event.sender, 'selection') and event.sender.selection() is not None and len( event.sender.selection() ) != 0:
      restricted = []
      if hasattr(event, 'restricted'):
        restricted = getattr(event, 'restricted');
      if not "sendToNuke" in restricted:
        # only handle single selection right now
        selection = event.sender.selection()
        if len(selection) == 1:
          clips = []
          parents = {}
          self.findClips(selection, clips, parents)
          if len(clips) > 0:
            hiero.ui.insertMenuAction( self, event.menu, after = "foundry.project.export" )

class Convert32Action(SendToNukeAction):
  def __init__(self, text, settingsPrefix, timebase, timebaseNTSC):
    SendToNukeAction.__init__(self, text, settingsPrefix)

    self._timebase = timebase
    self._timebaseNTSC = timebaseNTSC

  def doit(self):
    SendToNukeAction.doit(self, force32Mode=True)

  def eventHandler(self, event):
    if hasattr(event.sender, 'selection') and event.sender.selection() is not None and len( event.sender.selection() ) != 0:
      restricted = getattr(event, 'restricted');
      if not "threeTwoPullDown" in restricted:
        # only handle single selection right now
        selection = event.sender.selection()
        if len(selection) == 1:
          enabled = True
          clips = []
          parents = {}
          self.findClips(selection, clips, parents)
          if len(clips) > 0:
            # check if any of the clips have an appropriate framerate
            for clip in clips:
              clipFps = clip.framerate()
              if (not self._timebase.__eq__(clipFps)) and (not self._timebaseNTSC.__eq__(clipFps)):
                enabled = False

            # enable/disable the action each time
            self.setEnabled(enabled)
            event.menu.addAction( self )

# Instantiate the actions, but only if we're not HieroPlayer.
# HieroPlayer will use other stuff
if not hiero.core.isHieroPlayer():
  sendToNukeAction = SendToNukeAction("Advanced Send To Nuke...")
  add32Action = Convert32Action("Add 3:2...", "Add32/", TimeBase.k24, TimeBase.k24NTSC)
  remove32Action = Convert32Action("Remove 3:2...", "Remove32/", TimeBase.k30, TimeBase.k30NTSC)
