# Copyright (c) 2010 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
import nukescripts
from . import flipbooking
from nukescripts import pyAppUtils
import os
import string
import subprocess
import uuid
import re

from threading import Thread
from nukescripts import utils, sys, os, captureViewer
from .fnFlipbookRenderer import getFlipbookRenderer

#import traceback

##############################################################################
# Constants for the module
##############################################################################

_USE_SETTINGS_FROM_CUSTOM = 'Custom'
_FRAME_RANGE_GLOBAL = 'global'
_FRAME_RANGE_INPUT = 'input'
_FRAME_RANGE_INOUT = 'in-out'
_FRAME_RANGE_VISIBLE = 'visible'
_FRAME_RANGE_CUSTOM = 'custom'


##############################################################################
# Dialogs
##############################################################################

class DialogState:
  def __init__(self):
    self._state = {}

  def get(self, knob, defaultValue = None):
    """Return the given knob's stored last state value.
    If none exists, defaultValue is returned.
    Values are stored in a dict referenced by knob name, so names must be unique!"""
    return self.getValue(knob.name(), defaultValue)

  def save(self, knob):
    """Store the knob's current value as the 'last state' for the next time the dialog is opened.
    Values are stored in a dict referenced by knob name, so names must be unique!"""
    self.saveValue(knob.name(), knob.value())

  def setKnob(self, knob, defaultValue = None):
    """Convenience method for setting a value straight on a knob."""
    knob.setValue(self.get(knob, defaultValue))
  def saveValue(self, id, value):
    """Stores the value with the given id."""
    self._state[id] = value
  def getValue(self, id, defaultValue = None):
    """Recalls the value. If it was not set before, it will return the defaultValue."""
    return self._state.get(id, defaultValue)

_gRenderDialogState = DialogState()
_gFlipbookDialogState = DialogState()
_gViewerCaptureDialogState = DialogState()

class ExecuteDialog(nukescripts.PythonPanel):
  def _titleString(self):
    return "Execute"

  def _idString(self):
    return "uk.co.thefoundry.ExecuteDialog"

  def _addLeadingKnobs(self):
    """Add knobs that must appear first."""
    return

  def _addPreKnobs(self):
    """Add knobs that must appear before the render knobs."""
    return

  def _addPostKnobs(self):
    """Add knobs that must appear after the render knobs."""
    return

  def _addTrailingKnobs(self):
    """Add knobs that must appear at the very end."""
    return

  def _getDefaultViews(self):
    oc = nuke.OutputContext()
    allViews = [oc.viewname(i) for i in range(1, oc.viewcount())]
    return " ".join(allViews)

  def _addViewKnob(self):
    """Add knobs for view selection."""
    oc = nuke.OutputContext()
    if (oc.viewcount() > 2):
      self._viewSelection = nuke.MultiView_Knob("multi_view", "Views")
      self._viewSelection.fromScript(self._state.get(self._viewSelection, self._getDefaultViews()))
      self.addKnob(self._viewSelection)
      self._viewSelection.clearFlag(nuke.NO_MULTIVIEW)

  def addKnob(self, knob):
    """Add the knob and make sure it cannot be animated."""
    knob.setFlag(nuke.NO_ANIMATION | nuke.NO_MULTIVIEW)
    super(ExecuteDialog, self).addKnob(knob)

  def __init__(self, dialogState, groupContext, nodeSelection = [], exceptOnError = True):
    self._state = dialogState
    self._nodeSelection = nodeSelection
    self._exceptOnError = exceptOnError
    self._dialogKnobs = None


    nukescripts.PythonPanel.__init__(self, self._titleString(), self._idString(), False)

    self._viewers = {}
    for n in nuke.allNodes("Viewer", groupContext):
      self._viewers[n.name()] = n

    self._addKnobs()

  def _addKnobs(self):
    self._dialogKnobs = []
    beforeKnobs = self.knobs()
    self._addLeadingKnobs()

    self._addPreKnobs()

    # Frame range knobs
    specialRanges = [_FRAME_RANGE_GLOBAL, _FRAME_RANGE_INPUT, _FRAME_RANGE_CUSTOM]
    for viewer in self._viewers.keys():
      specialRanges.append(viewer + '/' + _FRAME_RANGE_INOUT)
      specialRanges.append(viewer + '/' + _FRAME_RANGE_VISIBLE)

    self._rangeEnum = nuke.CascadingEnumeration_Knob( "frame_range", "Frame range", specialRanges )
    self._rangeEnum.setTooltip("Select the frame range for the flipbook")
    self._state.setKnob(self._rangeEnum, _FRAME_RANGE_INPUT)
    self.addKnob( self._rangeEnum )

    self._frameRange = nuke.String_Knob( "frame_range_string", "")
    self._frameRange.setTooltip("Custom frame range")
    self._frameRange.clearFlag(nuke.STARTLINE)
    if self._rangeEnum.value() == _FRAME_RANGE_CUSTOM:
      self._state.setKnob(self._frameRange, str(nuke.root().frameRange()))
    else:
      self._setFrameRangeFromSource(self._rangeEnum.value())

    self.addKnob(self._frameRange)

    self._addPostKnobs()

    self._addViewKnob()

    self._addTrailingKnobs()

    self._continueOnError = nuke.Boolean_Knob("continue", "Continue on error")
    self._continueOnError.setTooltip("Continue on error")
    self._state.setKnob(self._continueOnError, True)
    self._continueOnError.setFlag(nuke.STARTLINE)
    self.addKnob(self._continueOnError)

    self._dialogKnobs = set(beforeKnobs.values()) ^ set(self.knobs().values())


  def knobChanged( self, knob ):
    self._state.save(knob)
    if (knob == self._frameRange):
      self._rangeEnum.setValue("custom")
      self._state.save(self._rangeEnum)
      self._state.saveValue("customRange", knob.value())
    if (knob == self._rangeEnum):
      self._setFrameRangeFromSource(knob.value())
      self._state.save(self._frameRange)

  def _setFrameRangeFromSource(self, source):
    if (source == _FRAME_RANGE_INPUT):
      try:
        activeInput = nuke.activeViewer().activeInput()
        self._frameRange.setValue(str(nuke.activeViewer().node().upstreamFrameRange(activeInput)))
      except:
        self._frameRange.setValue(str(nuke.root().frameRange()))
    elif (source == _FRAME_RANGE_GLOBAL):
      self._frameRange.setValue(str(nuke.root().frameRange()))
    elif (source == _FRAME_RANGE_CUSTOM):
      customRange = self._state.getValue("customRange", None)
      if customRange:
        self._frameRange.setValue(str(customRange))
    else:
      self._frameRangeFromViewer(*source.split('/'));

  def _frameRangeFromViewer( self, viewer, frameRange ):
    """Set the framerange knob to have the framerange from the given viewer."""
    if frameRange == _FRAME_RANGE_VISIBLE:
      viewerRange = str(self._viewers[viewer].visibleRange())
    else:
      viewerRange = str(self._viewers[viewer].playbackRange())
    self._frameRange.setValue(viewerRange)

  def _selectedViews(self):
    try:
      return self._viewSelection.value().split()
    except AttributeError:
      # If we didn't add the view selection knob, there should be just the one view.
      return [nuke.OutputContext().viewname(1)]

  def addToPane(self):
    nukescripts.PythonPanel.addToPane(self, pane = nuke.thisPane())

  def run(self):
    frame_ranges = nuke.FrameRanges(self._frameRange.value().split(','))
    views = self._selectedViews()
    try:
      nuke.Undo().disable()
      nuke.executeMultiple(self._nodeSelection, frame_ranges, views, continueOnError = self._continueOnError.value())
    except RuntimeError as e:
      if self._exceptOnError or e.args[0][0:9] != "Cancelled":   # TO DO: change this to an exception type
        raise
    finally:
      nuke.Undo().enable()

class RenderDialog(ExecuteDialog):
  deprecatedWarningShown = False
  shouldShowBGRender = False
  ShowWarning = True
  def _titleString(self):
    return "Render"


  def _idString(self):
    return "uk.co.thefoundry.RenderDialog"

  def __init__(self,
               dialogState,
               groupContext,
               nodeSelection = [],
               exceptOnError = True,
               allowFrameServer = True):
    self._allowFrameServer = allowFrameServer
    ExecuteDialog.__init__(self, dialogState, groupContext, nodeSelection, exceptOnError)

  def _addPreKnobs( self ):
    if self.isTimelineWrite():
      self._timelineRender = nuke.Boolean_Knob("timeline_render", "Render to timeline" )
      self._state.setKnob( self._timelineRender, True)
      self._timelineRender.setFlag(nuke.STARTLINE)
      self.addKnob(self._timelineRender)


  def _showDeprecatedWarningMessage(self):
    if not RenderDialog.deprecatedWarningShown:
      RenderDialog.deprecatedWarningShown = True;
      nuke.tprint("Render in Background option functionality has been deprecated and replaced with the Frame Server.")

  def _addTrailingKnobs(self):
    # Proxy
    self._useProxy = nuke.Boolean_Knob("use_proxy", "Use proxy")
    self._useProxy.setTooltip("Use proxy")
    self._useProxy.setFlag(nuke.STARTLINE)
    self._state.setKnob(self._useProxy, nuke.root().proxy())
    self.addKnob(self._useProxy)

    self._frameserverRender = nuke.Boolean_Knob("frameserver_render", "Render using frame server")
    self._frameserverRender.setTooltip("Render using frame server")
    select_frame_server = nuke.toNode("preferences").knob("RenderWithFrameServer").getValue()
    self._state.setKnob(self._frameserverRender, select_frame_server)
    self._frameserverRender.setVisible(self.frameserverRenderAvailable())
    self._frameserverRender.setFlag(nuke.STARTLINE)
    self.addKnob(self._frameserverRender)

    self._bgRender = nuke.Boolean_Knob("bg_render", "Render in background")
    self._state.setKnob(self._bgRender, False)
    self._bgRender.setVisible(self.backgroundRenderAvailable())
    self._bgRender.setFlag(nuke.STARTLINE)
    self.addKnob(self._bgRender)

    self._numThreads = nuke.Int_Knob("num_threads", "Thread limit")
    self._numThreads.setVisible(self.isBackgrounded())
    self._state.setKnob(self._numThreads, max(int(nuke.NUM_CPUS / 2), 1))
    self.addKnob(self._numThreads)
    self._maxMem = nuke.String_Knob("max_memory", "Memory limit")
    self._state.setKnob(self._maxMem, str(max(int(nuke.memory("max_usage") / 2097152), 16)) + "M")
    self._maxMem.setVisible(self.isBackgrounded())
    self.addKnob(self._maxMem)
    if self.isBackgrounded():
      self._showDeprecatedWarningMessage()

  def _getBackgroundLimits(self):
    #Deprecated
    if re.search("^(?<![\d.])[0-9]+(?![\d.])[kmgt]", self._maxMem.value(), re.IGNORECASE) == None:
      # regex to match a string that starts with an int not float followed by letter kmgt, any training string or spaces are ignored.
      raise Exception('The memory limit specified does not match the required format.')
    return {
      "maxThreads": self._numThreads.value(),
      "maxCache": self._maxMem.value() }

  def knobChanged( self, knob ):
    ExecuteDialog.knobChanged(self, knob)

    timelineRender = False
    try:
      timelineRender = self._timelineRender.value()
    except:
      pass

    bgRenderVisible = not timelineRender and self.backgroundRenderAvailable()
    showBGRenderOptions = bgRenderVisible and self.isBackgrounded()
    self._bgRender.setVisible(bgRenderVisible)
    self._numThreads.setVisible(showBGRenderOptions)
    self._maxMem.setVisible(showBGRenderOptions)
    #if knob changed is the bgRender, set it visible
    if knob is self._bgRender:
      self._showDeprecatedWarningMessage()


    if timelineRender and self.isTimelineWrite():
      self._rangeEnum.setValue( _FRAME_RANGE_GLOBAL )
      self._setFrameRangeFromSource(self._rangeEnum.value())
      self._rangeEnum.setEnabled( False )
      self._frameRange.setEnabled( False )
      self._frameserverRender.setVisible(False)
      self._useProxy.setVisible( False )
      self._continueOnError.setVisible( False )
    else:
      self._rangeEnum.setEnabled( True )
      self._frameRange.setEnabled( True )
      if self._allowFrameServer:
        self._frameserverRender.setVisible(self.frameserverRenderAvailable())
      self._useProxy.setVisible( True )
      self._continueOnError.setVisible( True )


  def isBackgrounded(self):
    """Return whether the background rendering option is enabled."""
    #Deprecated
    return self._bgRender.value() and self.backgroundRenderAvailable()


  def isFrameserverEnabled(self):
    """Return whether the frame server option is enabled."""
    return self._frameserverRender.value() and self.frameserverRenderAvailable()


  def backgroundRenderAvailable(self):
      """Return whether background rendering should be allowed for this render"""
      # If frame server is not available for any reason, show the 'Render in background' option
      return RenderDialog.shouldShowBGRender or not self.frameserverRenderAvailable()


  def frameserverRenderAvailable(self):
    import hiero.ui.nuke_bridge.FnNsFrameServer
    return (hiero.ui.nuke_bridge.FnNsFrameServer.isServerRunning() and
            self._allowFrameServer and not self.renderContainsContainers())


  def extractContainerNodes(self, nodeSelection):
    containerWriteNodes = []
    nonContainerWriteNodes = []
    #extract mov nodes from the rest
    for node in nodeSelection:
      knob = node.knobs().get("file_type",None)
      if knob:
        fileType = knob.value()
        if fileType in ("mov", "mov32", "mov64", "ffmpeg", "mxf"):
          containerWriteNodes.append(node)
        else:
          nonContainerWriteNodes.append(node)
    return (nonContainerWriteNodes, containerWriteNodes)


  def isTimelineWrite(self):

    if not nuke.env['studio']:
      return False

    if len(self._nodeSelection) > 1 or len(self._nodeSelection) < 1:
      return False

    write = self._nodeSelection[0]

    if write == nuke.root():
      ## must be a render of all 'write' nodes, this is tricky as there may be other executable nodes apart from write nodes
      ## lets assume the write nodes are write, writegeo, particlecache, and diskcache

      # there is a bug here however as there may be groups they are executable which will be skipped right now

      writeNodes = nuke.allNodes( 'Write' )
      writeNodes.extend( nuke.allNodes( 'WriteGeo') )
      writeNodes.extend( nuke.allNodes( 'ParticleCache') )
      writeNodes.extend( nuke.allNodes( 'DiskCache') )

      if len(writeNodes) > 1:
        return False

      if len(writeNodes) > 0:
        write = writeNodes[0]

    timelineWriteNode = None

    try:
      from foundry.frameserver.nuke.workerapplication import GetWriteNode
      timelineWriteNode = GetWriteNode()
    except:
      pass

    if not timelineWriteNode:
      return False

    if timelineWriteNode.fullName() != write.fullName():
      return False

    ## double check that this script is actually in a timeline
    try:
      from hiero.ui import isInAnyProject
      return isInAnyProject( nuke.scriptName() )
    except:
      pass

    return False

  def saveFileToRender(self, prefix, forceSaveNew):
    import datetime
    now = datetime.datetime.now()
    timestamp = now.strftime('%H%M_%S.%f_%d-%m-%Y')

    if nuke.env['nc']:
      nukeExt = ".nknc"
    if nuke.env['indie']:
      nukeExt = ".nkind"
    else:
      nukeExt = ".nk"

    wasSaved = False
    #if file is unsaved
    if nuke.Root().name() == 'Root':
      fileName = "%s.%s%s"%(prefix,timestamp, nukeExt)
      filePath = "/".join([os.environ["NUKE_TEMP_DIR"], fileName])
      nuke.scriptSaveToTemp(filePath)
      wasSaved = True
    else:
      originalPath = nuke.scriptName()
      #if file is saved but not up to date
      if nuke.Root().modified() == True or forceSaveNew:
        extensionIndex = originalPath.rfind(nukeExt)
        noExt = originalPath[:extensionIndex] if extensionIndex>=0 else originalPath
        head, tail = os.path.split(noExt)
        fileName = "%s.%s.%s%s"%(prefix,tail,timestamp,nukeExt)
        filePath = "/".join([head,fileName])
        try:
          nuke.scriptSaveToTemp(filePath)
          wasSaved = True
        except RuntimeError:
          nuke.tprint("Exception when saving script to: %s. Saving to NUKE_TEMP_DIR"%filePath)
          fileName = originalPath.split()[-1]
          filePath = "/".join([os.environ["NUKE_TEMP_DIR"], fileName])
          nuke.scriptSaveToTemp(filePath)
          wasSaved = True
      #if file is saved
      else:
        filePath = originalPath
    return  (filePath, wasSaved)

  def getNodeSelection(self):
    nodeSelection = self._nodeSelection
    nodesToRenderCount= len(nodeSelection)
    if nodesToRenderCount==1:
      if nodeSelection[0] == nuke.root():
        nodeSelection = nuke.allNodes("Write")
        nodeSelection.extend(nuke.allNodes("DeepWrite"))
    return nodeSelection

  def renderContainsContainers(self):
    (_, containerNodesToRender) = self.extractContainerNodes(self.getNodeSelection())
    if containerNodesToRender:
      return True
    return False

  def renderToFrameServer(self,frame_ranges, views):
    nodeSelection = self.getNodeSelection()
    (nodesToRender, containerNodesToRender) = self.extractContainerNodes(nodeSelection)

    #check views and frame pading
    for node in nodeSelection:
      path = node["file"].getText()
      needsPadding = frame_ranges.getRange(0).frames()>1
      hasPadding = nuke.filename( node, nuke.REPLACE ) != path or node["file_type"].value()=="mov"
      if needsPadding and not hasPadding:
        nuke.message("%s cannot be executed for multiple frames."%node.fullName())
        return
      #there's no way to find if writer can write multiple views per file in python
      needsViews = (len(views)!=1 or views[0] != "main" )
      hasViews = path.find("%v")!=-1 or path.find("%V")!=-1 or node["file_type"].value()=="exr"
      if needsViews and not hasViews:
        nuke.message("%s cannot be executed for multiple views."%node.fullName())
        return

    #if there's any container to be rendered, show a warning, render synchronously later
    if containerNodesToRender:
      if RenderDialog.ShowWarning:
        from PySide2.QtWidgets import (QMessageBox, QCheckBox)
        message = "It is currently not possible to render container formats using the frame server. Select Continue to render in the current Nuke session.\n\nPlease see the user guide for more information."
        messageBox = QMessageBox(QMessageBox.Warning, "Warning", message, QMessageBox.Cancel)
        messageBox.addButton("Continue",QMessageBox.AcceptRole)
        dontShowCheckBox = QCheckBox("Don't show this message again")
        dontShowCheckBox.blockSignals(True)
        messageBox.addButton(dontShowCheckBox, QMessageBox.ResetRole)
        result = messageBox.exec_()
        if result != QMessageBox.AcceptRole:
          return
        if dontShowCheckBox.isChecked():
          RenderDialog.ShowWarning = False

    import hiero.ui.nuke_bridge.FnNsFrameServer as FrameServer
    sortRenderOrder = lambda w : w.knobs()["render_order"].getValue()
    if nodesToRender:
      nodesToRender.sort(key = sortRenderOrder)
      name, wasSaved = self.saveFileToRender("tmp_unsaved",False)
      try:
        for node in nodesToRender:
          FrameServer.renderFrames(
            name,
            frame_ranges,
            node.fullName(),
            self._selectedViews())
      finally:
        if wasSaved:
          os.unlink(name)

    if containerNodesToRender:
      containerNodesToRender.sort(key = sortRenderOrder)
      nuke.executeMultiple(containerNodesToRender, frame_ranges, views, continueOnError = self._continueOnError.value())


  def run(self):
    ##this will render the full framerange of the script
    if self.isTimelineWrite() and self._timelineRender.value():
      from hiero.ui.nuke_bridge.nukestudio import scriptSaveAndReRender
      scriptSaveAndReRender()
      return

    frame_ranges = nuke.FrameRanges(self._frameRange.value().split(','))
    views = self._selectedViews()
    rootProxyMode = nuke.root().proxy()
    try:
      nuke.Undo().disable()
      nuke.root().setProxy(self._useProxy.value())
      if self.isFrameserverEnabled():
        self.renderToFrameServer(frame_ranges,views)
      elif self.isBackgrounded():
        nuke.executeBackgroundNuke(nuke.EXE_PATH, self._nodeSelection,
          frame_ranges, views, self._getBackgroundLimits(), continueOnError = self._continueOnError.value())
      else:
        nuke.executeMultiple(self._nodeSelection, frame_ranges, views, continueOnError = self._continueOnError.value())
    except RuntimeError as e:
      if self._exceptOnError or e.args[0][0:9] != "Cancelled":   # TO DO: change this to an exception type
        raise
    finally:
      nuke.root().setProxy(rootProxyMode)
      nuke.Undo().enable()

class FlipbookDialog( RenderDialog ):
  def _titleString( self ):
    return "Flipbook"

  def _idString( self ):
    return "uk.co.thefoundry.FlipbookDialog"

  def __init__(self, dialogState, groupContext, node, takeNodeSettings):
    # Init attributes
    self._node = node
    self._takeNodeSettings = takeNodeSettings
    self._customKnobs = []

    # init super
    RenderDialog.__init__(self, dialogState, groupContext)

    # Override the initial frame range value
    self._state.setKnob(self._rangeEnum, _FRAME_RANGE_INPUT)
    self._setFrameRangeFromSource(self._rangeEnum.value())

    if self._takeNodeSettings:
      self._viewerForSettings.setValue(node.name())
      self.knobChanged(self._viewerForSettings)

  def _addLeadingKnobs( self ):
    flipbookNames = flipbooking.gFlipbookFactory.getNames()
    self._flipbookEnum = nuke.Enumeration_Knob( "flipbook", "Flipbook", flipbookNames )
    self._flipbookEnum.setTooltip("Select Flipbook Player")
    defaultFlipbook = nuke.toNode('preferences').knob('defaultFlipbook').getValue()
    if not defaultFlipbook or not defaultFlipbook in flipbookNames:
      defaultFlipbook = flipbookNames[0]
    self._state.setKnob(self._flipbookEnum, defaultFlipbook)
    self.addKnob( self._flipbookEnum )

    self._viewerForSettings = nuke.Enumeration_Knob("viewer_settings", "Use Settings From", list(self._viewers.keys()) + [_USE_SETTINGS_FROM_CUSTOM])
    self._viewerForSettings.setTooltip("Select your viewer setting for the flipbook")
    if not self._takeNodeSettings:
      self._viewerForSettings.setValue(_USE_SETTINGS_FROM_CUSTOM)
    self.addKnob(self._viewerForSettings)

  def _addPreKnobs( self ):
    # Region of Interest knobs
    self._useRoi = nuke.Boolean_Knob("use_roi", "Enable ROI")
    self._useRoi.setTooltip("Use Region of Interest (ROI)")
    self._useRoi.setFlag(nuke.STARTLINE)
    self._state.setKnob(self._useRoi, False)
    self.addKnob(self._useRoi)
    self._roi = nuke.BBox_Knob("roi", "Region of Interest")
    self._state.setKnob(self._roi, (0, 0, 0, 0))
    self.addKnob(self._roi)
    self._roi.setVisible(self._useRoi.value())

    # Channel knobs
    self._channels = nuke.Channel_Knob( "channels_knob", "Channels")
    self._channels.setTooltip("Select channels for the flipbook")
    if self._node.Class() == "Write":
      self._channels.setValue(self._node.knob("channels").value())
    else:
      self._state.setKnob(self._channels, "rgba")
    self._channels.setFlag(nuke.STARTLINE | nuke.NO_CHECKMARKS)
    self.addKnob( self._channels )

  def _addPostKnobs( self ):
    # LUT knobs
    self._luts = nuke.Enumeration_Knob("lut", "LUT", nuke.ViewerProcess.registeredNames())
    self._luts.setTooltip("Select LUT for the flipbook")
    if self._takeNodeSettings:
      self._state.setKnob(self._luts, self._lutFromViewer(self._viewerForSettings.value()))
    else:
      self._state.setKnob(self._luts, self._lutFromViewer())
    self.addKnob(self._luts)

    self._burnInLUT = nuke.Boolean_Knob("burnin", "Burn in the LUT")
    self._burnInLUT.setTooltip("Burn in the LUT")
    self._state.setKnob(self._burnInLUT, False)
    self.addKnob(self._burnInLUT)

    # Audio knobs
    audioList = []
    audioList.append( "None" )
    for node in nuke.allNodes("AudioRead"):
      audioList.append( node.name() )
    self._audioSource = nuke.Enumeration_Knob( "audio", "Audio", audioList )
    self._audioSource.setTooltip("Include audio to flipbook")
    self._state.setKnob(self._audioSource, audioList[0] )
    self.addKnob( self._audioSource )

    super(FlipbookDialog, self)._addPostKnobs()

    self.flipbookKnobs()

  def flipbookKnobs(self):
    try:
      beforeKnobs = self.knobs()
      flipbookToRun = flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())
      flipbookToRun.dialogKnobs(self)
      afterKnobs = self.knobs()
      self._customKnobs = list(set(beforeKnobs.values()) ^ set(afterKnobs.values()))
    except NotImplementedError:
      pass

  def _getDefaultViews(self):
    return nuke.activeViewer().view()

  def _addViewKnob(self):
    oc = nuke.OutputContext()
    self._views = [oc.viewname(i) for i in range(1, oc.viewcount())]
    if (oc.viewcount() > 2):
      supportedViews = self._selectedFlipbook().capabilities()["maximumViews"]
      if (int(supportedViews) > 1):
        self._viewSelection = nuke.MultiView_Knob("views", "Views")
      else:
        self._viewSelection = nuke.OneView_Knob("views", "View", self._views)
      activeView = nuke.activeViewer().view()
      if activeView == "":
        activeView = self._views[0]

      # Retrieve previous view selection or default to selecting all available views
      previousViews = self._state.getValue(self._viewSelection.name(), " ".join(self._views)).split()
      # Get the intersection of the previous selection and the available views
      viewsToRestore = set(self._views).intersection(previousViews)
      if viewsToRestore:
        self._viewSelection.setValue(" ".join(viewsToRestore))
      else:
        self._viewSelection.setValue(activeView)
      self.addKnob(self._viewSelection)
      self._viewSelection.clearFlag(nuke.NO_MULTIVIEW)

  def _selectedFlipbook(self):
    return flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())

  def _lutFromViewer(self, viewerName = ""):
    try:
      if viewerName == "":
        return nuke.ViewerProcess.node().knob("current").value()
      else:
        return nuke.ViewerProcess.node(viewer=viewerName).knob("current").value()
    except AttributeError:
      return "None"

  def _isViewerSettingKnob(self, knob):
    return knob == self._useRoi or knob == self._roi or knob == self._channels or knob == self._useProxy or knob == self._frameRange or knob == self._rangeEnum or knob == self._luts

  def _setKnobAndStore(self, knob, val):
    knob.setValue(val)
    self._state.save(knob)

  def knobChanged(self, knob):
    RenderDialog.knobChanged(self, knob)
    if (knob == self._viewerForSettings):
      if self._viewerForSettings.value() != _USE_SETTINGS_FROM_CUSTOM:
        viewer = self._viewers[self._viewerForSettings.value()]
        self._setKnobAndStore(self._useRoi, viewer.roiEnabled())
        roi = viewer.roi()
        if roi != None:
          self._roi.fromDict(roi)
          self._state.save(self._roi)
        self._channels.fromScript(viewer.knob("channels").toScript())
        self._state.save(self._channels)
        self._setKnobAndStore(self._useProxy, nuke.root().proxy())
        self._frameRangeFromViewer(viewer.name(), _FRAME_RANGE_INOUT)
        self._state.save(self._frameRange)
        self._setKnobAndStore(self._rangeEnum, viewer.name() + '/' + _FRAME_RANGE_INOUT)
        self._roi.setVisible(self._useRoi.value())
        self._setKnobAndStore(self._luts, self._lutFromViewer(viewer.name()))
    elif (knob == self._useRoi):
      self._roi.setVisible(self._useRoi.value())
    elif self._isViewerSettingKnob(knob):
      self._viewerForSettings.setValue(_USE_SETTINGS_FROM_CUSTOM)
      self._state.save(self._viewerForSettings)
    elif knob == self._luts:
      self._burnInLUT.setEnabled(self._luts.value() != "None")

    if knob == self._flipbookEnum:
      for k in self._dialogKnobs:
        self.removeKnob(k)
      self.removeKnob(self.okButton)
      self.removeKnob(self.cancelButton)
      self._customKnobs = []
      self._addKnobs()
      self._makeOkCancelButton()
    elif knob in self._customKnobs:
      try:
        flipbookToRun = flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())
        flipbookToRun.dialogKnobChanged(self, knob)
      except NotImplementedError:
        pass

  def _getIntermediateFileType(self):
    return _gFlipbookDialogState.getValue('intermediateFormat', 'exr')

  def _getIntermediatePath(self):
    """Get the path for the temporary files. May be filled in using printf syntax."""
    flipbooktmp=""
    if flipbooktmp == "":
      try:
        flipbooktmp = self._selectedFlipbook().cacheDir()
      except:
        try:
          flipbooktmp = os.environ["NUKE_DISK_CACHE"]
        except:
          flipbooktmp = nuke.value("preferences.DiskCachePath")

    if len(self._selectedViews()) > 1:
      flipbookFileNameTemp = "nuke_tmp_flip.%04d.%V." + self._getIntermediateFileType()
    else:
      flipbookFileNameTemp = "nuke_tmp_flip.%04d." + self._getIntermediateFileType()
    flipbooktmpdir = os.path.join(flipbooktmp, "flipbook")
    if not os.path.exists(flipbooktmpdir):
      os.mkdir(flipbooktmpdir)

    if not os.path.isdir(flipbooktmpdir):
      raise RuntimeError("%s already exists and is not a directory, please delete before flipbooking again" % flipbooktmpdir)
    flipbooktmp = os.path.join(flipbooktmpdir, flipbookFileNameTemp)

    if nuke.env['WIN32']:
      flipbooktmp = re.sub(r"\\", "/", str(flipbooktmp))
    return flipbooktmp

  def _requireIntermediateNode(self, nodeToTest):
    if nodeToTest.Class() == "Read" or nodeToTest.Class() == "Write":
      flipbookToRun = flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())
      flipbookCapabilities = flipbookToRun.capabilities()

      # Check if we can read it in directly..
      filePath = nuke.filename(nodeToTest)
      # There might be a prefix that overrides the extension, if so, this will
      # confuse the flipbook probably, so just create a render.
      if ':' in filePath:
        readerPrefix = filePath.split(':')[0]
        if len(readerPrefix) > 1: # 1 is a drive letter
          return True
      fileExtension = os.path.splitext(filePath)[1].lower()[1:]

      # Check if the flipbook supports the file extension. Allow a wildcard to
      # indicate 'all files' (such as for the internal flipbook functionality)
      supportedFileTypes = flipbookCapabilities.get("fileTypes", [])
      flipbookSupportsFileType = (supportedFileTypes == ["*"]) or (fileExtension in supportedFileTypes)
      if not flipbookSupportsFileType:
        return True

      # Not all flipbooks can handle weird channels
      flipbookSupportsArbitraryChannels = flipbookCapabilities.get("arbitraryChannels", False)
      if self._channels.value() not in set(["rgb", "rgba", "alpha"]) and not flipbookSupportsArbitraryChannels:
        return True
      channelKnob = nodeToTest.knob("channels")
      if channelKnob != None and channelKnob.value() != self._channels.value():
        return True

      ## if flipbook doesn't support roi and the roi option is on we need the intermediate node because we're going to insert a crop
      if self._useRoi.value() and self._useRoi.enabled():
          if not flipbookCapabilities.get("roi", False):
            return True

      if self._burnInLUT.value() and self._burnInLUT.enabled():
        return True

      # Separate view files
      # TODO Temporary workaround to deal with MediaSource not being aware of
      # the %V notation for specifiying separate view files.
      if "%V" in filePath or "%v" in filePath:
        return True

      return False
    else:
      return True

  def _getBurninWriteColorspace(self):
    """Helper function to get the appropriate colorspace to set on the Write node when burning the
    viewer color transform into the render."""
    
    writeColorspace = None
  
    lut = self._getLUT()
    
    # Determine whether we're using original Nuke, rather than OCIO, color management.
    usingNukeColorspaces = False
    rootNode = nuke.root()
    if rootNode:
      colorManagementKnob = rootNode.knob("colorManagement")
      if colorManagementKnob:
        usingNukeColorspaces = (colorManagementKnob.value() == "Nuke")  # Note: Must use value() rather than getValue().

    if usingNukeColorspaces:

      # We're using Nuke colorspace management so the our lut knob will correspond to the appropriate
      # colorspace name, except for rec1886, which we need to map to Gamma2.4.
      # If the lut is the special case of None then don't set writeColorspace (to match the original behaviour).
      # (The rec1886 -> Gamma2.4 mapping matches what's done in register_default_viewer_processes, in
      # NukeScripts/src/ViewerProcess.py - I suppose we could consider adding something into
      # nuke/src/Python/PythonObjects/ViewerProcess.cpp to allow the python code to look-up into ViewerProcessMap
      # so we could parse the registered args to obtain the colorspace but that seems like overkill and not much
      # less fragile.)
      if lut == "rec1886":
        writeColorspace = "Gamma2.4"
      elif lut != "None":
        writeColorspace = lut
        
    else:

      # We're using OCIO color management so we expect our lut string to contain a view name
      # followed by a single space and a display name in parantheses.
      # For example, the aces 1.0.1 config has lots of views but all for the display called ACES,
      # hence here we might get lut set to, for example,
      #   DCDM P3 gamut clip (ACES)
      # As another example, the spi-vfx config has views for two displays, DCIP3 and sRGB, so we might get
      #   Film (DCIP3)
      # or
      #   Film (sRGB)
      # etc.
      # The nuke-default config has a single display called 'default' so we get lut set to
      #   None (default)
      # or
      #   sRGB (default)
      # etc. The nuke-default case is a bit confusing because the _view_ names almost match colorspace names
      # and also correspond to legacy Nuke colorspace managament options.
      #
      # Anyway, what we actually need to return is the actual colorspace the particualr combination of
      # view and display name map to, as defined in the relevant OCIO config file.
      
      displayName = ""
      viewName = ""
      
      NUKE_LUT_FORMAT = '(.*) \((.*)\)$'
      matchResult = re.match( NUKE_LUT_FORMAT , lut)
      if matchResult is not None:

        viewName = matchResult.group(1)
        displayName = matchResult.group(2)
        
        if rootNode:
          writeColorspace = rootNode.getOCIOColorspaceFromViewTransform(displayName, viewName)

    return writeColorspace
    

  def _createIntermediateNode(self):
    """Create a write node to render out the current node so that output may be used for flipbooking."""
    flipbooktmp = self._getIntermediatePath()

    fieldname = "file"
    if self._useProxy.value():
      fieldname = "proxy"

    fixup = nuke.createNode("Group", "tile_color 0xff000000", inpanel = False)
    with fixup:
      fixup.setName("Flipbook")
      inputNode = nuke.createNode("Input", inpanel = False)
      shuffle = nuke.createNode("Shuffle", inpanel = False)
      shuffle.knob("in").setValue(self._channels.value())
      if self._useRoi.value():
        crop = nuke.createNode( "Crop", inpanel = False )
        crop['box'].fromScript( self._roi.toScript() )
      write = nuke.createNode("Write", fieldname+" {"+flipbooktmp+"}", inpanel = False)
      write.knob('file_type').setValue(self._getIntermediateFileType())
      selectedViews = self._selectedViews()
      write.knob('views').fromScript(" ".join(selectedViews))

      if self._getIntermediateFileType() == "exr": 
        write.knob('compression').setValue("B44")
        # Set the 'heroview' to be the first of the selected views. If we don't
        # do this then then 'heroview' is by default set to be 1 which may not
        # be a valid view for this clip. The 'heroview' is used as a fallback if
        # no view has been set on the reader. This assumes the user has selected
        # sensible views if they haven't then the write may still fail.
        if len(selectedViews) > 0:
          firstView = nuke.OutputContext().viewFromName(selectedViews[0])
          write.knob('heroview').setValue(firstView)

      writeColorspace = ""
      
      if self._burnInLUT.value():
        # The user has chosen to burn the viewer transform into the intermedate render so set the colorspace
        # on the Write node appropriately.
        writeColorspace = self._getBurninWriteColorspace()
      else:
        # The viewer transform is not being burnt into the intermediate render, set the Write node's colorspace
        # to whatever the current working space is - when reading the file back in the flipbook we'll ssume
        # the media was written out in the working space.
        rootNode = nuke.root()
        if rootNode:
          workingSpaceKnob = rootNode.knob("workingSpaceLUT")
          if workingSpaceKnob:
            writeColorspace = workingSpaceKnob.value()

      if writeColorspace:
        write.knob('colorspace').setValue(writeColorspace)

      outputNode = nuke.createNode("Output", inpanel = False)
    #If called on a Viewer connect fixup node to the one immediately above if exists.
    if self._node.Class() == "Viewer":
      fixup.setInput(0, self._node.input(int(nuke.knob(self._node.fullName()+".input_number"))))
    else:
      fixup.setInput(0, self._node)

    return (fixup, write)

  def _getLUT(self):
    return self._luts.value()

  def _getAudio(self):
    nukeNode = nuke.toNode( self._audioSource.value() )
    ret = ""
    if nukeNode != None:
      ret = nukeNode["file"].getEvaluatedValue()

    return ret

  def _getOptions(self, nodeToFlipbook):
    options = {
    }

    try:
      options['pixelAspect'] = float(nuke.value(nodeToFlipbook.name()+".pixel_aspect"))
    except:
      pass

    try:
      f = nodeToFlipbook.format()
      options['dimensions'] = { 'width' : f.width(), 'height' : f.height() }
    except:
      pass

    # LUT
    if not self._burnInLUT.value():
      inputColourspace = "linear"
      outputColourspace = "linear"
      # Check if we have a different than linear input
      if self._node.Class() == "Read" or self._node.Class() == "Write":
        lut = self._node.knob("colorspace").value()
        # Might be in the format of "default (foo)", if so, get at "foo".
        if lut[:7] == "default":
          lut = lut[9:-1]
        inputColourspace = lut

      # Check our output
      lut = self._getLUT()
      if lut != "None":
        outputColourspace = lut

      if inputColourspace == outputColourspace:
        options["lut"] = inputColourspace
      else:
        options["lut"] = inputColourspace + "-" + outputColourspace
    # AUDIO
    audioTrack = self._getAudio()
    if audioTrack != "":
      options["audio"] = audioTrack

    # ROI
    if self._useRoi.value():
      roi = self._roi.toDict()
      if (roi["r"] - roi["x"] > 0) and (roi["t"] - roi["y"] > 0):
        options["roi"] = bboxToTopLeft(int(nuke.value(nodeToFlipbook.name()+".actual_format.height")), roi)


    return options

  def run(self):
    flipbookToRun = flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())
    if (flipbookToRun):
      if not os.access(flipbookToRun.path(), os.X_OK):
        raise RuntimeError("%s cannot be executed (%s)." % (flipbookToRun.name(), flipbookToRun.path(),) )

      nodeToFlipbook = None
      rootProxyMode = nuke.root().proxy()
      try:
        # Need this to prevent Bug 5295
        nuke.Undo().disable()
        nuke.root().setProxy(self._useProxy.value())

        calledOnNode = self._node
        if self._node.Class() == "Viewer":
          self._node = self._node.input(int(self._node.knob("input_number").value()))

        renderer = getFlipbookRenderer(self, flipbookToRun)
        renderer.doFlipbook()

      except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        print("exception ",e)
      finally:
        #if an intermediate node was created, delete it
        if self._node != renderer._nodeToFlipbook:
          nuke.delete(renderer._nodeToFlipbook)
        nuke.root().setProxy(rootProxyMode)
        nuke.Undo().enable()
    else:
        raise RuntimeError("No flipbook called " + self._flipbookEnum.value() + " found. Was it deregistered while the dialog was open?")

class ViewerCaptureDialog( FlipbookDialog ):
  def _titleString( self ):
    return "Capture"

  def _idString( self ):
    return "uk.co.thefoundry.ViewerCaptureDialog"

  def __init__(self, dialogState, groupContext, node):

    # init super
    FlipbookDialog.__init__(self, dialogState, groupContext, node, True)
    self._frameserverRender.setVisible(False)
    self._bgRender.setVisible(False)
    self._useProxy.setVisible(False)
    self._continueOnError.setVisible(False)

    self._viewerForSettings.setVisible(False)

    self._useRoi.setVisible(False)
    self._roi.setVisible(False)

    self._channels.setVisible(False)
    self._luts.setVisible(False)

    self._audioSource.setVisible(False)
    self._burnInLUT.setVisible(False)

    try:
      ## this may not exist, just ignore if not present
      self._viewSelection.setVisible(False)
    except:
      pass

    customWriteActive = node['file'].getValue() != self._getIntermediatePath() and node['file'].getValue() != ''
    self._customWrite = nuke.Boolean_Knob( 'custom', 'Customise write path' )
    self._customWrite.setValue( customWriteActive )
    self.addKnob( self._customWrite )

    self._noFlipbook = nuke.Boolean_Knob( 'write', 'No flipbook' )
    self._noFlipbook.setFlag( nuke.STARTLINE )
    self._noFlipbook.setVisible( customWriteActive  )
    self._noFlipbook.setValue( self._state.get( self._noFlipbook, False ) )
    self.addKnob( self._noFlipbook )

    self._file = nuke.File_Knob( 'file', 'Write path' )
    defaultPath = self._node['file'].value()
    if defaultPath == self._getIntermediatePath():
      defaultPath = ''
    self._file.setValue ( self._state.get(self._file, defaultPath ) )
    self._file.setVisible( customWriteActive )

    self.addKnob( self._file )

  def knobChanged( self, knob ):
    try:
      FlipbookDialog.knobChanged(self, knob)
      self._frameserverRender.setVisible(False)
      if (knob == self._customWrite):
        self._noFlipbook.setVisible( self._customWrite.value() )
        self._file.setVisible( self._customWrite.value() )
        if ( not self._customWrite.value() ):
          self._node['file'].setValue( self._getIntermediatePath() )
      elif( knob == self._noFlipbook ):
        self._flipbookEnum.setEnabled( not self._noFlipbook.value() )
    except:
      pass

  def _getIntermediateFileType(self):
    return 'jpg'

  def captureViewer(self):
    """ Return an instance of a CaptureViewer class, which when executed captures the viewer.
    """
    flipbook = flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())
    if flipbook and not os.access(flipbook.path(), os.X_OK):
       raise RuntimeError("%s cannot be executed (%s)." % (flipbook.name(), flipbook.path(),) )

    # build up the args
    frameRange = self._frameRange.value()
    viewer = self._node
    selectedViews = self._selectedViews()
    defaultWritePath = self._getIntermediatePath()
    customWritePath = self._file.value() if self._customWrite.value() else ""
    doFlipbook = not self._noFlipbook.value()
    doCleanup = False

    return captureViewer.CaptureViewer(flipbook, frameRange, viewer, selectedViews, defaultWritePath, customWritePath, doFlipbook, doCleanup)

def _showDialog( dialog ):
  """ Shows the with showModalDialog() and then calls dialog.run() if it returns True """
  # If there is a viewer playing, stop it, it interferes with updating knobs on the dialog
  if nuke.activeViewer():
    nuke.activeViewer().stop()

  if (dialog.showModalDialog() == True):
    dialog.run()

def showExecuteDialog(nodesToExecute, exceptOnError = True): 
  """Present a dialog that executes the given list of nodes."""
  groupContext = nuke.root()
  d = ExecuteDialog(_gRenderDialogState, groupContext, nodesToExecute, exceptOnError)
  _showDialog(d)

def showRenderDialog(nodesToRender, exceptOnError = True, allowFrameServer = True):
  """Present a dialog that renders the given list of nodes."""
  groupContext = nuke.root()
  d = RenderDialog(_gRenderDialogState, groupContext, nodesToRender, exceptOnError, allowFrameServer)
  _showDialog(d)

def _getFlipbookDialog(node, takeNodeSettings = False):
  """Returns the flipbook dialog object created when flipbooking node"""
  if node is None:
    raise RuntimeError("Can't launch flipbook, require a node.");
  if node.Class() == "Viewer" and node.inputs() == 0:
    raise RuntimeError("Can't launch flipbook, there is nothing connected to the viewed input.");

  if not (nuke.canCreateNode("Write")):
    nuke.message("Flipbooking is not permitted in Nuke Assist")
    return

  groupContext = nuke.root()

  e = FlipbookDialog(_gFlipbookDialogState, groupContext, node, takeNodeSettings)
  return e

def showFlipbookDialog(node, takeNodeSettings = False):
  """Present a dialog that flipbooks the given node."""
  e = _getFlipbookDialog( node, takeNodeSettings )
  _showDialog(e)

# because the capture button could have been triggered via a progress bar in update_handles
# we defer the capture run until the main event loop is pumped
class ViewerCaptureDialogThread(Thread):
  def __init__(self, captureViewer):
    Thread.__init__(self)
    self.captureViewer = captureViewer

  def run(self):
    ## only runs the dialog capture function when we are outside update_handles
    utils.executeInMainThreadWithResult( self.captureViewer,  )

def showViewerCaptureDialog(node):
  if node is None:
    raise RuntimeError("Can't launch flipbook, requires a viewer node.");
  if node.Class() != "Viewer" and node.inputs() == 0:
    raise RuntimeError("Can't launch flipbook, this is not a viewer node.");

  if not (nuke.canCreateNode("Write")):
    nuke.message("Viewer capture is not permitted in Nuke Assist")
    return

  groupContext = nuke.root()
  e = ViewerCaptureDialog(_gViewerCaptureDialogState, groupContext, node)
  if (e.showModalDialog() == True):
    # Bug 38516 - Be careful about what gets passed to the ViewerCaptureDialogThread, since anything
    # created here will be destroyed in a different thread. This can cause problems, such as crashes,
    # if a Qt widget gets passed.
    captureViewer = e.captureViewer()
    thread = ViewerCaptureDialogThread(captureViewer)
    thread.start()

def showFlipbookDialogForSelected():
  """Present a dialog that flipbooks the currently selected node."""
  try:
    showFlipbookDialog(nuke.selectedNode())
  except ValueError as ve:
    raise RuntimeError("Can't launch flipbook, %s." % (ve.args[0]))

def bboxToTopLeft(height, roi):
  """Convert the roi passed from a origin at the bottom left to the top left.
     Also replaces the r and t keys with w and h keys.
     @param height: the height used to determine the top.
     @param roi: the roi with a bottom left origin, must have x, y, r & t keys.
     @result dict with x, y, w & h keys"""
  topLeftRoi = {
      "x": roi["x"],
      "y": height - roi["y"] - (roi["t"] - roi["y"]),
      "w": roi["r"] - roi["x"],
      "h": roi["t"] - roi["y"] }
  return topLeftRoi

def setRenderDialogDefaultOption(name, value):
  """ Set a particular option to the given value. The type of the value differs per option, giving the wrong value may result in exceptions. The options are read every time the dialog is opened, though not every knob in the dialog has it's value stored."""
  _gRenderDialogState.saveValue(name, value)

def setFlipbookDefaultOption(name, value):
  """ Set a particular option to the given value. The type of the value differs per option, giving the wrong value may result in exceptions. The options are read every time the dialog is opened, though not every knob in the dialog has it's value stored."""
  _gFlipbookDialogState.saveValue(name, value)
