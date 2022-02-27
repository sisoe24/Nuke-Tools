from numbers import Number
from typing import *

import nuke
from . import *

class Viewer(Node):
    """

    """
    def __repr__(self, ):
        """
        Return repr(self).
        """
        return None

    def __str__(self, ):
        """
        Return str(self).
        """
        return None

    def __len__(self, ):
        """
        Return len(self).
        """
        return None

    def __getitem__(self, key, ):
        """
        Return self[key].
        """
        return None

    def roi(self,):
        """
        self.roi() -> dict
        Region of interest set in the viewer in pixel space coordinates.
        Returns None if the Viewer has no window yet.
        @return: Dict with keys x, y, r and t or None.
        """
        return dict()

    def roiEnabled(self,):
        """
        self.roiEnabled() -> bool
        Whether the viewing of just a region of interest is enabled.
        Returns None if the Viewer has no window yet.
        @return: Boolean or None.
        """
        return bool()

    def setRoi(self, box:dict):
        """
        self.setRoi(box) -> None.
        Set the region of interest in pixel space.
        @param box: A dictionary with the x, y, r and t keys.@return: None.
        """
        return None

    def playbackRange(self,):
        """
        self.playbackRange() -> FrameRange.
        Return the frame range that's currently set to be played back in the viewer.@return: FrameRange.
        """
        return FrameRange()

    def visibleRange(self,):
        """
        self.visibleRange() -> FrameRange.
        Return the frame range that is currently visible in the viewer.@return: FrameRange.
        """
        return FrameRange()

    def frameCached(self,f):
        """
        frameCached(f) -> Bool

        Determine whether frame /f/ is known to be in the memory cache.
        """
        return bool()

    def sendMouseEvent(self,):
        """
        sendMouseEvent() -> Bool

        Temporary:
        Post a mouse event to the viewer window.
        """
        return bool()

    def recordMouse(self,):
        """
        recordMouse() -> Bool

        Start viewer window mouse recording.@return: Recording started?
        """
        return bool()

    def recordMouseStop(self,):
        """
        recordMouseStop()

        Stop viewer window mouse recording.
        """
        return None

    def replayMouseSync(self,xmlRecordingFilename):
        """
        replayMouseSync(xmlRecordingFilename) -> Bool

        Start direct (synchronous) playback of a viewer window mouse recording.@param: Name of recording xml file to play@return: Replay succeeded?
        """
        return bool()

    def replayMouseAsync(self,xmlRecordingFilename):
        """
        replayMouseAsync(xmlRecordingFilename) -> Bool

        Start timer based (asynchronous) playback of a viewer window mouse recording.@param: Name of recording xml file to play@return: Replay started?
        """
        return bool()

    def isPlayingOrRecording(self,):
        """
        isPlayingOrRecording() -> Bool 

        @return: Is a recording being made or played?
        """
        return bool()

    def toggleMouseTrails(self,):
        """
        toggleMouseTrails() -> Bool 

        Toggle mouse trails in the viewer window on/off.@return: Trails now showing?
        """
        return bool()

    def toggleWaitOnEvents(self,):
        """
        toggleWaitOnEvents() -> Bool 

        Toggle whether asynchronous playback waits on each event.
        Otherwise events will be handled by the next nuke update.@return: Now waiting?
        """
        return bool()

    def capture(self,file):
        """
        capture(file) -> None

        Capture the viewer image to a file.  Only jpg files are supported at present.  The image is captured immediately even if the viewer is mid-render.To capture a fully rendered image at a frame or frame range use nuke.render passing in the viewer node you want to capture.When using nuke.render the filename is specified by the 'file' knob on the viewer node.
        """
        return None

    def __init__(self,  *args, **kwargs):
        """
        Initialize self.  See help(type(self)) for accurate signature.
        """
        return None