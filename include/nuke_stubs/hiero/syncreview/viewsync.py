import hiero.core
from hiero.core.util import asUnicode
import hiero.ui
from hiero.ui import TracksMask, Viewer, Player
from . import messages
from . synctool import (SyncTool, localCallback, remoteCallback)
from PySide2.QtCore import QCoreApplication
from . log import logMessage

"""
Classes for syncing the view state between connected clients.
"""

messages.defineMessageType('SyncViewerSequence', ('sequenceAGuid', str), ('sequenceBGuid', str))
messages.defineMessageType('SyncViewerTime', ('time', int))
messages.defineMessageType('SyncViewerPlaybackSpeed', ('speed', int))
messages.defineMessageType('SyncViewerTargetFrameRate', ('numerator', int), ('denominator', int))
messages.defineMessageType('SyncViewerShuttleTargetFPS', ('fps', float))
messages.defineMessageType('SyncViewerAnnotationsTool', ('active', messages.Bool))


class SyncViewerSubTool(SyncTool):
  """ Base class for sub-tools which implement different parts of the viewer sync
  logic. These are owned and managed by the SyncViewerTool class.
  """
  def __init__(self, syncViewerTool):
    super(SyncViewerSubTool, self).__init__(syncViewerTool.messageDispatcher)
    self._syncViewerTool = syncViewerTool

  def viewerChanged(self, viewer, oldViewer):
    """ Called when the current viewer changes """
    pass

  def viewer(self):
    """ Get the current viewer """
    return self._syncViewerTool.currentViewer

  def pushState(self):
    """ Push the tool state to remotes """
    pass


class SyncViewerAnnotationTool(SyncViewerSubTool):
  """ Tool for syncing the state of the annotations tool in the viewer. """
  def __init__(self, syncViewerTool):
    super(SyncViewerAnnotationTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerAnnotationsTool, self.onRemoteAnnotationsToolChanged)
    self._viewerAnnotationTool = None

  def viewerChanged(self, viewer, oldViewer):
    if self._viewerAnnotationTool:
      self._viewerAnnotationTool.activeChanged.disconnect(self.pushState)
      self._viewerAnnotationTool = None
    if viewer:
      self._viewerAnnotationTool = viewer.annotationTool()
      self._viewerAnnotationTool.activeChanged.connect(self.pushState)

  @remoteCallback
  def onRemoteAnnotationsToolChanged(self, msg):
    if self._viewerAnnotationTool:
      self._viewerAnnotationTool.setActive(msg.active)

  @localCallback
  def pushState(self):
    if self._viewerAnnotationTool:
      msg = messages.SyncViewerAnnotationsTool(active=int(self._viewerAnnotationTool.isActive()))
      self._syncViewerTool.sendMessage(msg)


class SyncViewerInOutTool(SyncViewerSubTool):
  """ Tool for syncing the 'in' and 'out' points of the viewer. """

  def __init__(self, syncViewerTool):
    super(SyncViewerInOutTool, self).__init__(syncViewerTool)

  def pushState(self):
    """ Push the 'in' and 'out' points of the current viewer. """
    viewer = self.viewer()
    if viewer:
      sequence = viewer.player().sequence()
      if sequence and sequence.inOutEnabled():

        # Someone made the unfortunate decision that trying to get the sequence
        # in or out time when they're not set should cause an exception.
        # Handle this and return an invalid value
        def _getTime(func):
          try:
            return func()
          except:
            return -1

        inOutMsg = messages.InOutChange(sequenceGuid=sequence.guid(),
                                        inTime=_getTime(sequence.inTime),
                                        outTime=_getTime(sequence.outTime))
        self._syncViewerTool.sendMessage(inOutMsg)


messages.defineMessageType('SyncViewerPlaybackMode', ('mode', str))

class SyncViewerPlaybackModeTool(SyncViewerSubTool):
  """ Tool for syncing the playback mode (bounce/repeat/etc) setting on the viewer """
  def __init__(self, syncViewerTool):
    super(SyncViewerPlaybackModeTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerPlaybackMode, self._onRemotePlaybackModeChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.playbackModeChanged.disconnect(self.pushState)
    if viewer:
      viewer.playbackModeChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    # Send the mode as a string
    mode = viewer.playbackMode()
    msg = messages.SyncViewerPlaybackMode(mode=mode.name)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemotePlaybackModeChanged(self, msg):
    # Lookup the mode value on the enum object
    mode = getattr(Viewer.PlaybackMode, msg.mode)
    viewer = self.viewer()
    if viewer:
      viewer.setPlaybackMode(mode)

messages.defineMessageType('SyncViewerGamma', ('gamma', float))

class SyncViewerGammaTool(SyncViewerSubTool):
  """ Tool for syncing the gamma in the viewer """
  def __init__(self, syncViewerTool):
    super(SyncViewerGammaTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerGamma, self._onRemoteGammaChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.gammaChanged.disconnect(self.pushState)
    if viewer:
      viewer.gammaChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    gamma = viewer.gamma()
    msg = messages.SyncViewerGamma(gamma=gamma)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteGammaChanged(self, msg):
    gamma = msg.gamma
    viewer = self.viewer()
    if viewer:
      viewer.setGamma(gamma)


messages.defineMessageType('SyncViewerGain', ('gain', float))

class SyncViewerGainTool(SyncViewerSubTool):
  """ Tool for syncing the gain in the viewer """
  def __init__(self, syncViewerTool):
    super(SyncViewerGainTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerGain, self._onRemoteGainChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.gainChanged.disconnect(self.pushState)
    if viewer:
      viewer.gainChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    gain = viewer.gain()
    msg = messages.SyncViewerGain(gain=gain)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteGainChanged(self, msg):
    gain = msg.gain
    viewer = self.viewer()
    if viewer:
      viewer.setGain(gain)


messages.defineMessageType('SyncViewerCompareMode', ('mode', str))

class SyncViewerCompareModeTool(SyncViewerSubTool):
  """ Tool for syncing the compare mode of the A/B buffers in the viewer """
  def __init__(self, syncViewerTool):
    super(SyncViewerCompareModeTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerCompareMode, self._onRemoteCompareModeChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.compareModeChanged.disconnect(self.pushState)
    if viewer:
      viewer.compareModeChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    # Send the mode as a string
    mode = viewer.compareMode()
    msg = messages.SyncViewerCompareMode(mode=mode.name)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteCompareModeChanged(self, msg):
    # Lookup the mode value on the enum object
    mode = getattr(Viewer.CompareMode, msg.mode)
    viewer = self.viewer()
    if viewer:
      viewer.setCompareMode(mode)


messages.defineMessageType('SyncViewerLayoutMode', ('mode', str))

class SyncViewerLayoutModeTool(SyncViewerSubTool):
  """ Tool for syncing the layout mode of the A/B buffers in the viewer """
  def __init__(self, syncViewerTool):
    super(SyncViewerLayoutModeTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerLayoutMode, self._onRemoteLayoutModeChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.layoutModeChanged.disconnect(self.pushState)
    if viewer:
      viewer.layoutModeChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    # Send the mode as a string
    mode = viewer.layoutMode()
    msg = messages.SyncViewerLayoutMode(mode=mode.name)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteLayoutModeChanged(self, msg):
    # Lookup the mode value on the enum object
    mode = getattr(Viewer.LayoutMode, msg.mode)
    viewer = self.viewer()
    if viewer:
      viewer.setLayoutMode(mode)


# Each buffer is a list containing the following:
# * TracksMask's visibleByDefault attribute.
# * TracksMask's list of tracks Guids.
messages.defineMessageType('SyncViewerBuffer', ('bufferA', messages.Json), ('bufferB', messages.Json))


class SyncViewerBufferTool(SyncViewerSubTool):
  """ Tool for syncing the viewer's A/B buffer options. Sequences are handled by SyncViewerTool. """

  def __init__(self, syncViewerTool):
    super(SyncViewerBufferTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerBuffer, self._onRemoteBufferChanged)

  def viewerChanged(self, viewer, oldViewer):
    """ Called when the current viewer changes """
    if oldViewer:
      oldViewer.trackSelectionChanged.disconnect(self.pushState)
    if viewer:
      viewer.trackSelectionChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    """ Push the tool state to remotes """
    viewer = self.viewer()
    if not viewer:
      return
    # Get track Guids from both buffers and send them.
    tracksMaskA = viewer.tracksMask(0)
    bufferA = [tracksMaskA.visibleByDefault(), [track.guid() for track in tracksMaskA.tracks()]]
    tracksMaskB = viewer.tracksMask(1)
    bufferB = [tracksMaskB.visibleByDefault(), [track.guid() for track in tracksMaskB.tracks()]]
    msg = messages.SyncViewerBuffer(bufferA=bufferA, bufferB=bufferB)
    self._syncViewerTool.sendMessage(msg)

  def _setBuffer(self, indexOfPlayer, buffer):
    # Check the definition of the SyncViewerBuffer for a description of the buffer fields.
    tracksMask = TracksMask()
    tracksMask.setVisibleByDefault(buffer[0])
    tracks = hiero.core.findItemsByGuid(buffer[1], filter=[hiero.core.VideoTrack])
    tracksMask.setTracks(tracks)
    self.viewer().setTracksMask(indexOfPlayer, tracksMask)

  @remoteCallback
  def _onRemoteBufferChanged(self, msg):
    if self.viewer():
      self._setBuffer(0, msg.bufferA)
      self._setBuffer(1, msg.bufferB)


messages.defineMessageType('SyncViewerWipeToolState', ('translateX', float), ('translateY', float), ('gauge', float), ('rotation', float))

class SyncViewerWipeTool(SyncViewerSubTool):
  """ Logic for syncing the wipe tools state within a session. """

  def __init__(self, syncViewerTool):
    super(SyncViewerWipeTool, self).__init__(syncViewerTool)
    self._wipeTool = None
    self.messageDispatcher._registerCallback(messages.SyncViewerWipeToolState, self._onRemoteWipeStateChanged)

  def viewerChanged(self, viewer, oldViewer):
    """ Called when the current viewer changes """
    if oldViewer:
      if self._wipeTool:
        self._wipeTool.wipeToolStateChanged.disconnect(self.pushState)
        self._wipeTool = None
    if viewer:
      self._wipeTool = viewer.wipeTool()
      if self._wipeTool:
        self._wipeTool.wipeToolStateChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer or not self._wipeTool:
      return
    wipeState = self._wipeTool.wipeToolState()
    msg = messages.SyncViewerWipeToolState(translateX=wipeState.translateX, translateY=wipeState.translateY, gauge=wipeState.gauge, rotation=wipeState.rotation)
    self.messageDispatcher.sendMessage(msg)

  @remoteCallback
  def _onRemoteWipeStateChanged(self, msg):
    wipeToolState = hiero.ui.WipeToolState(msg.translateX, msg.translateY, msg.gauge, msg.rotation)
    self._wipeTool.setWipeToolState(wipeToolState)


messages.defineMessageType('SyncViewerLayerState', ('layerName', str))

class SyncViewerLayerTool(SyncViewerSubTool):
  """ Logic for syncing the channels layer state within a session. """

  def __init__(self, syncViewerTool):
    super(SyncViewerLayerTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerLayerState, self._onRemoteLayerChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.currentLayerChanged.disconnect(self.pushState)
    if viewer:
      viewer.currentLayerChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    layerName = viewer.currentLayerName()
    msg = messages.SyncViewerLayerState(layerName=layerName)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteLayerChanged(self, msg):
    layerName = msg.layerName
    viewer = self.viewer()
    if viewer:
      viewer.setLayer(layerName)


messages.defineMessageType('SyncViewerChannels', ('channels', str))


class SyncViewerChannelsTool(SyncViewerSubTool):
  """ Tool for syncing the channel setting on the viewer """
  def __init__(self, syncViewerTool):
    super(SyncViewerChannelsTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerChannels, self._onRemoteChannelsChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.channelsChanged.disconnect(self.pushState)
    if viewer:
      viewer.channelsChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    # Send the channel as a string
    channels = viewer.channels()
    msg = messages.SyncViewerChannels(channels=channels.name)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteChannelsChanged(self, msg):
    # Lookup the channel value on the enum object
    channels = getattr(Player.Channels, msg.channels)
    viewer = self.viewer()
    if viewer:
      viewer.setChannels(channels)


# playersZoom is a list containing zoom data for each player.
# Each zoom data is a tuple with (zoomMode, (centerX, centerY, zoomLevel))
# The second field is None unless zoomMode is equal to eZoomFixed.
messages.defineMessageType('SyncViewerZoom', ('playersZoom', messages.Json))


class SyncViewerZoomTool(SyncViewerSubTool):
  """ Tool for syncing the zoom mode of the players of the viewer. """

  def __init__(self, syncViewerTool):
    super(SyncViewerZoomTool, self).__init__(syncViewerTool)
    self._handlingRemoteChange = False
    self.messageDispatcher._registerCallback(messages.SyncViewerZoom, self._onRemoteTransformChanged)

  def viewerChanged(self, viewer, oldViewer):
    """ Called when the current viewer changes. """
    if oldViewer:
      oldViewer.transformChanged.disconnect(self.pushState)
    if viewer:
      viewer.transformChanged.connect(self.pushState)

  def pushState(self):
    """ Push the zoom state to remote clients. """
    viewer = self.viewer()
    if not viewer or self._handlingRemoteChange:
      return

    playersZoom = []
    for indexOfPlayer in range(0, 2):
      player = viewer.player(indexOfPlayer)
      zoomMode = player.zoomMode()
      zoomData = None
      if zoomMode == getattr(Player.ZoomMode, 'eZoomFixed'):
        # The translation is in screen coordinates. Convert to relative coordinates where {0.5, 0.5} is the center.
        center = player.translation()
        rect = player.rect()
        x = (center.x() - rect.x()) / rect.width()
        y = (center.y() - rect.y()) / rect.height()
        zoomData = (x, y, player.zoom())
      playersZoom.append((asUnicode(zoomMode.name), zoomData, ))

    msg = messages.SyncViewerZoom(playersZoom=playersZoom)
    self._syncViewerTool.sendMessage(msg)

  def _onRemoteTransformChanged(self, msg):
    self._handlingRemoteChange = True

    viewer = self.viewer()
    if viewer and len(msg.playersZoom) == 2:
      indexOfPlayer = 0
      for zoomData in msg.playersZoom:
        player = viewer.player(indexOfPlayer)
        zoomMode = getattr(Player.ZoomMode, zoomData[0])
        if zoomMode == getattr(Player.ZoomMode, 'eZoomFixed'):
          player.zoomAbsolute(zoomData[1][0], zoomData[1][1], zoomData[1][2])
        else:
          player.setZoomMode(zoomMode)
        indexOfPlayer += 1

    self._handlingRemoteChange = False


messages.defineMessageType('SyncViewerTimeDisplayFormat', ('displayTimecode', messages.Bool),
                           ('displayDropFrames', messages.Bool))


class SyncViewerTimeDisplayFormatTool(SyncViewerSubTool):
  """ Tool for syncing the time display format of the viewer. """

  def __init__(self, syncViewerTool):
    super(SyncViewerTimeDisplayFormatTool, self).__init__(syncViewerTool)
    self._handlingRemoteChange = False
    self.messageDispatcher._registerCallback(messages.SyncViewerTimeDisplayFormat, self._onRemoteFormatChanged)

  def viewerChanged(self, viewer, oldViewer):
    """ Called when the current viewer changes. """
    if oldViewer:
      oldViewer.timeDisplayFormatChanged.disconnect(self.pushState)
    if viewer:
      viewer.timeDisplayFormatChanged.connect(self.pushState)

  def pushState(self):
    """ Push the zoom state to remote clients. """
    viewer = self.viewer()
    if not viewer or self._handlingRemoteChange:
      return

    msg = messages.SyncViewerTimeDisplayFormat(displayTimecode=viewer.displayTimecode(),
                                               displayDropFrames=viewer.displayDropFrames())
    self._syncViewerTool.sendMessage(msg)

  def _onRemoteFormatChanged(self, msg):
    self._handlingRemoteChange = True

    viewer = self.viewer()
    if viewer:
      viewer.setTimeDisplayFormat(msg.displayTimecode, msg.displayDropFrames)

    self._handlingRemoteChange = False


messages.defineMessageType('SyncViewerGuideOverlay', ('guideOverlayNames', messages.Json), ('availableGuideOverlays', messages.Json))

class SyncViewerGuideOverlayTool(SyncViewerSubTool):
  """ Logic for syncing the guide overlays within a session. """

  def __init__(self, syncViewerTool):
    super(SyncViewerGuideOverlayTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerGuideOverlay, self._onRemoteGuideOverlayChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.guideOverlayChanged.disconnect(self.pushState)
    if viewer:
      viewer.guideOverlayChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    guideOverlays = viewer.selectedGuideOverlayNames()
    availableOverlays = viewer.availableGuideOverlayNames()
    msg = messages.SyncViewerGuideOverlay(guideOverlayNames=guideOverlays, availableGuideOverlays=availableOverlays)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteGuideOverlayChanged(self, msg):
    viewer = self.viewer()
    if viewer:
      overlayNames = msg.guideOverlayNames
      remoteOverlaysAvailable = msg.availableGuideOverlays
      viewer.setGuideOverlayFromRemote(overlayNames, remoteOverlaysAvailable)


messages.defineMessageType('SyncViewerMaskOverlay', ('maskOverlayName', str))

class SyncViewerMaskOverlayTool(SyncViewerSubTool):
  """ Logic for syncing the mask overlay within a session. """

  def __init__(self, syncViewerTool):
    super(SyncViewerMaskOverlayTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerMaskOverlay, self._onRemoteMaskOverlayChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.maskOverlayChanged.disconnect(self.pushState)
    if viewer:
      viewer.maskOverlayChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    overlayName = viewer.maskOverlayName()
    msg = messages.SyncViewerMaskOverlay(maskOverlayName=overlayName)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteMaskOverlayChanged(self, msg):
    viewer = self.viewer()
    if viewer:
      overlayName = msg.maskOverlayName
      viewer.setMaskOverlayFromRemote(overlayName)


messages.defineMessageType('SyncViewerMaskOverlayStyle', ('maskOverlayStyle', str))

class SyncViewerMaskOverlayStyleTool(SyncViewerSubTool):
  """ Logic for syncing the mask overlay style within a session. """

  def __init__(self, syncViewerTool):
    super(SyncViewerMaskOverlayStyleTool, self).__init__(syncViewerTool)
    self.messageDispatcher._registerCallback(messages.SyncViewerMaskOverlayStyle, self._onRemoteMaskOverlayStyleChanged)

  def viewerChanged(self, viewer, oldViewer):
    if oldViewer:
      oldViewer.maskOverlayStyleChanged.disconnect(self.pushState)
    if viewer:
      viewer.maskOverlayStyleChanged.connect(self.pushState)

  @localCallback
  def pushState(self):
    viewer = self.viewer()
    if not viewer:
      return
    overlayStyle = viewer.maskOverlayStyle()
    msg = messages.SyncViewerMaskOverlayStyle(maskOverlayStyle=overlayStyle.name)
    self._syncViewerTool.sendMessage(msg)

  @remoteCallback
  def _onRemoteMaskOverlayStyleChanged(self, msg):
    viewer = self.viewer()
    if viewer:
      # Lookup the MaskOverlayStyle value on the enum object
      overlayStyle = getattr(Player.MaskOverlayStyle, msg.maskOverlayStyle)
      viewer.setMaskOverlayStyle(overlayStyle)


class SyncViewerTool(SyncTool):
  """ Logic for a syncing the view within a session.
  """

  # Flags for handling changes to the viewer which are asynchronous
  SYNC_NONE = 0
  SYNC_TIME = 1
  SYNC_PLAYBACK = 2

  def __init__(self, messageDispatcher):
    super(SyncViewerTool, self).__init__(messageDispatcher)

    # List of sub-tools for handling syncing things in the viewer
    self.subTools = [
      SyncViewerAnnotationTool(self),
      SyncViewerInOutTool(self),
      SyncViewerPlaybackModeTool(self),
      SyncViewerGammaTool(self),
      SyncViewerGainTool(self),
      SyncViewerCompareModeTool(self),
      SyncViewerLayoutModeTool(self),
      SyncViewerBufferTool(self),
      SyncViewerWipeTool(self),
      SyncViewerLayerTool(self),
      SyncViewerChannelsTool(self),
      SyncViewerZoomTool(self),
      SyncViewerTimeDisplayFormatTool(self),
      SyncViewerGuideOverlayTool(self),
      SyncViewerMaskOverlayTool(self),
      SyncViewerMaskOverlayStyleTool(self),
    ]

    self.messageDispatcher._registerCallback(messages.SyncViewerSequence, self._onSyncSequence)
    self.messageDispatcher._registerCallback(messages.SyncViewerTime, self._onSyncTime)
    self.messageDispatcher._registerCallback(messages.SyncViewerPlaybackSpeed, self._onSyncPlaybackSpeed)
    self.messageDispatcher._registerCallback(messages.SyncViewerTargetFrameRate, self._onSyncTargetFrameRate)
    self.messageDispatcher._registerCallback(messages.SyncViewerShuttleTargetFPS, self._onSyncViewerShuttleTargetFPS)

    # Get the current viewer state and connect to signals we're interested in.
    self.syncState = SyncViewerTool.SYNC_NONE
    self.currentPlaybackSpeed = 0
    self.currentViewer = None
    self.pendingSyncTime = False
    # Sequence Guids for the buffer A (index 0) and B (index 1). Empty buffers are represented with an empty string.
    self._currentSequenceGuids = ['', '']

    # Counter blocking message sending when non-zero. Make sure no sync messages get sent yet
    self._messageSendBlockCounter = 1
    self._setViewer(hiero.ui.currentViewer())
    self._messageSendBlockCounter = 0

    # Register for the event emitted when the Viewer changes
    self.registerEventCallback('kCurrentViewerChanged', self._onViewerChanged)

  def stopPlayback(self):
    """ Stop the playback on the viewer. This change is not pushed to other participants. """
    if self.currentPlaybackSpeed != 0:
      self.currentPlaybackSpeed = 0
      if self.currentViewer:
        self.currentViewer.setPlaybackSpeed(0)

  def setProjectLoading(self, loading):
    """
    Block viewer tool messages the while the project is being loaded to avoid extra callbacks.
    Stop the playback until the project has been loaded.
    """
    if loading:
      self._messageSendBlockCounter += 1
      self.stopPlayback()
      # Without forcing a processEvents the viewer is sometimes left empty but still playing.
      QCoreApplication.instance().processEvents()
    else:
      self._messageSendBlockCounter -= 1

  def sendMessage(self, msg):
    if self._messageSendBlockCounter == 0:
      self.messageDispatcher.sendMessage(msg)

  def _onSyncSequence(self, msg):
    """ Get the guid of the sequences to sync the current viewer with, find those
    sequences in the current project and open them in the viewer.
    """
    self._messageSendBlockCounter += 1
    newSequenceGuids = [msg.sequenceAGuid, msg.sequenceBGuid]
    if newSequenceGuids != self._currentSequenceGuids:
      seqA = hiero.core.findItemByGuid(msg.sequenceAGuid, filter=[hiero.core.Sequence, hiero.core.Clip]) if msg.sequenceAGuid else None
      seqB = hiero.core.findItemByGuid(msg.sequenceBGuid, filter=[hiero.core.Sequence, hiero.core.Clip]) if msg.sequenceBGuid else None
      # Call openInViewer() if the A input has changed. Need to do this rather than just calling
      # setSequence() to ensure linked timeline/spreadsheet views get handled correctly in the UI.
      # This will trigger callbacks to _setViewer if it switches to a new Viewer object,
      # but _messageSendBlocked is set here so it's safe to do that
      if seqA and (not self.currentViewer or self.currentViewer.player(0).sequence() != seqA):
        hiero.ui.openInViewer(seqA)
      elif not seqA and self.currentViewer:
        self.currentViewer.setSequence(hiero.core.Sequence(), 0)

      # Set the B buffer. Use sendToViewerB() to try and keep consistency with the UI behaviour
      oldSeqB = self.currentViewer.player(1).sequence() if self.currentViewer else None
      if seqB != oldSeqB:
        if seqB:
          hiero.ui.sendToViewerB(seqB)
        else:
          self.currentViewer.setSequence(hiero.core.Sequence(), 1)
      if msg.sequenceAGuid and not seqA:
        logMessage("_onSyncSequence could not find sequence A with id {}".format(msg.sequenceAGuid))
      if msg.sequenceBGuid and not seqB:
        logMessage("_onSyncSequence could not find sequence B with id {}".format(msg.sequenceBGuid))

      self._currentSequenceGuids = newSequenceGuids
    self._messageSendBlockCounter -= 1

  def _onSyncTime(self, msg):
    """ Handle a message to set the current time in the viewer. The time can't
    be changed while the viewer is being stopped, so if in this state we need
    to schedule a time change after recieving notification the viewer has stopped
    """
    self.currentTime = msg.time
    if self.syncState == SyncViewerTool.SYNC_NONE:
      self.syncState = SyncViewerTool.SYNC_TIME
      self.currentViewer.setTime(self.currentTime)
    elif self.syncState == SyncViewerTool.SYNC_PLAYBACK:
      self.pendingSyncTime = True

  def _onTimeChanged(self, time, forceSync=False):
    """ Callback when the time in the current viewer changes. Send a message
    to sync other participants unless it was caused by a sync.
    """
    isPlaying = self.currentPlaybackSpeed != 0
    shouldSync = forceSync or (self.syncState != SyncViewerTool.SYNC_TIME and
                    (isPlaying or self.currentTime != time))
    if shouldSync:
      self.currentTime = time
      msg = messages.SyncViewerTime(time=time)
      self.sendMessage(msg)
    self.syncState = SyncViewerTool.SYNC_NONE

  def _onSyncPlaybackSpeed(self, msg):
    """ Handle a message to set the playback speed in the viewer. Note that this
    happens asynchronously, the viewer won't actually be playing/stopped until
    an _onPlaybackSpeedChanged callback is received.
    """
    if msg.speed != self.currentPlaybackSpeed:
      self.syncState = SyncViewerTool.SYNC_PLAYBACK
      self.currentPlaybackSpeed = msg.speed
      self.currentViewer.setPlaybackSpeed(msg.speed)

  def _onSyncTargetFrameRate(self, msg):
    """ Handle a message to change the viewer target frame rate. """
    self.currentViewer.syncTargetFrameRate(msg.numerator, msg.denominator)

  def _onSyncViewerShuttleTargetFPS(self, msg):
    self.currentViewer.syncShuttleTargetFPS(msg.fps)

  def _onPlaybackSpeedChanged(self, speed, fromPlaybackMode):
    """ Callback when the playback speed in the current viewer changes. Send a
    message to sync other participants unless it was caused by a sync. If stopping
    also need to sync the time.
    """
    if self.syncState == SyncViewerTool.SYNC_NONE and self.currentPlaybackSpeed != speed:
      self.currentPlaybackSpeed = speed

      # If the change was caused by the playback mode logic, not triggered by the user,
      # store the value but don't send a sync message. The bounce/stop will happen
      # on remotes on its own
      if fromPlaybackMode:
        return

      msg = messages.SyncViewerPlaybackSpeed(speed=speed)
      self.sendMessage(msg)
      if speed == 0:
        self._onTimeChanged(self.currentViewer.time())
    else:
      self.syncState = SyncViewerTool.SYNC_NONE
      if speed == 0 and self.pendingSyncTime:
        self.pendingSyncTime = False
        self.currentViewer.setTime(self.currentTime)

  def _onTargetFrameRateChanged(self, numerator, denominator):
    """ Callback executed when the target frame rate of the current viewer changes. """
    msg = messages.SyncViewerTargetFrameRate(numerator=numerator, denominator=denominator)
    self.sendMessage(msg)

  def _onShuttleTargetFPS(self, fps):
    self.sendMessage(messages.SyncViewerShuttleTargetFPS(fps=fps))

  def updateCurrentSequences(self):
    """ Update the current sequence GUIDs cached in the tool.
    """
    sequenceA = self.currentViewer.player(0).sequence()
    sequenceB = self.currentViewer.player(1).sequence()
    newSequenceGuids = ['' if not sequenceA else sequenceA.guid(), '' if not sequenceB else sequenceB.guid()]
    sequenceGuidsChanged = newSequenceGuids != self._currentSequenceGuids
    self._currentSequenceGuids = newSequenceGuids
    return sequenceGuidsChanged

  def _onSequenceChanged(self):
    """ If the new sequences are not the same as the current sequences, broadcast a
    message to all other clients with the new sequence guids
    """
    if self.updateCurrentSequences():
      self.pushViewerState()

  def pushViewerState(self):
    """ Send the current state of the viewer to other participants. This should
    sync the current sequences, time, etc
    """
    if self._messageSendBlockCounter > 0:
      return
    if self._currentSequenceGuids[0] or self._currentSequenceGuids[1]:
      msg = messages.SyncViewerSequence(sequenceAGuid=self._currentSequenceGuids[0],
                                        sequenceBGuid=self._currentSequenceGuids[1])
      self.sendMessage(msg)
      self._onTimeChanged(self.currentViewer.time(), forceSync=True)

      for t in self.subTools:
        t.pushState()

  def _onViewerChanged(self, event):
    """ Handle callback that the current viewer has changed. """
    self._setViewer(event.viewer)

  def _setViewer(self, viewer):
    """ Disconnect from old viewer signals, connect to new viewer signals, and
    update the view to desplay the sequence in the new viewer
    """
    oldViewer = self.currentViewer
    if oldViewer:
        try:
          oldViewer.sequenceChanged.disconnect(self._onSequenceChanged)
          oldViewer.timeChanged.disconnect(self._onTimeChanged)
          oldViewer.playbackSpeedChanged.disconnect(self._onPlaybackSpeedChanged)
          oldViewer.targetFrameRateChanged.disconnect(self._onTargetFrameRateChanged)
          oldViewer.shuttleTargetFPSChanged.disconnect(self._onShuttleTargetFPS)
        except RuntimeError:
          # Sometimes this gets called when the c++ object for the viewer has been
          # deleted. PySide throws an exception in this case but it can be ignored
          # Reset to None for passing to the sub-tools
          oldViewer = None

    # Reset state from old viewer
    self._currentSequenceGuids = ['', '']
    self.currentTime = None
    self.currentPlaybackSpeed = 0

    self.currentViewer = viewer
    if self.currentViewer:
        self.currentViewer.sequenceChanged.connect(self._onSequenceChanged)
        self.currentViewer.timeChanged.connect(self._onTimeChanged)
        self.currentViewer.playbackSpeedChanged.connect(self._onPlaybackSpeedChanged)
        self.currentViewer.targetFrameRateChanged.connect(self._onTargetFrameRateChanged)
        self.currentViewer.shuttleTargetFPSChanged.connect(self._onShuttleTargetFPS)
        self._onSequenceChanged()

    for t in self.subTools:
      t.viewerChanged(viewer, oldViewer)

  def shutdown(self):
    super(SyncViewerTool, self).shutdown()
    self._setViewer(None)

