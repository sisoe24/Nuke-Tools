"""
This module contains classes for performing a capture of the viewer.
"""

# TODO: Move renderdialog.ViewerCaptureDialog, renderdialog.ViewerCaptureDialogThread and renderdialog.showViewerCaptureDialog here as well, but without introducing a circular dependency with
# the renderdialog module.

import string, os
import nuke

class CaptureViewer(object):
  """ This class provides a way of capturing the contents of the viewer to disk.
  """
  def __init__(self, flipbook, frameRange, viewer, selectedViews, defaultWritePath, customWritePath, doFlipbook, doCleanup):
    self._flipbook = flipbook
    self._frameRange = nuke.FrameRanges(frameRange.split(','))
    self._viewer = viewer
    self._selectedViews = selectedViews
    self._defaultWritePath = defaultWritePath
    self._customWritePath = customWritePath
    self._doFlipbook = doFlipbook
    self._doCleanup = doCleanup

  def _performCleanup(self):
    """ Remove temporary files created by a previous capture.
    """
    outputContext = nuke.OutputContext()
    fileKnob = self._viewer['file']

    frameList = self._frameRange.toFrameList()
    for frame in frameList:
      outputContext.setFrame( frame )
      fileName = fileKnob.getEvaluatedValue(outputContext)

      if os.access(fileName, os.F_OK):
        os.remove(fileName)

  def __call__(self):
    """ Start the capture.
    """
    writePath = self._customWritePath or self._defaultWritePath
    self._viewer['file'].setValue(writePath)

    # _performCleanup will remove whatever filepath is set in the self._viewer['file'] knob.
    # So if this changes between runs then the old files wont get cleaned up, probably
    # a bug.
    if self._doCleanup:
      self._performCleanup()

    try:
      nuke.executeMultiple((self._viewer,), self._frameRange, self._selectedViews, False)
    except RuntimeError as msg:
      if msg.args[0][0:9] == "Cancelled":
        splitMsg = string.split(msg.args[0])
        msg = """ Render did not complete, do you want to show the completed range ?
                Frame range %s contains %s frames but only %s finished.
            """ % (self._frameRange, splitMsg[3], splitMsg[1])
        self._doFlipbook = nuke.ask(msg)
      else:
        nuke.message("Flipbook render failed:\n%s" % (msg.args[0],))
        self._doFlipbook = False

    finally:
      if not self._customWritePath:
        self._viewer['file'].setValue(self._defaultWritePath)

    if self._doFlipbook:
      playbackPath = nuke.filename(self._viewer)
      if playbackPath is None or playbackPath == "":
        raise RuntimeError("Cannot run a flipbook on '%s', expected to find a filename and there was none." % (self._viewer.fullName(),))

      options = {}
      options["lut"] = 'sRGB'
      self._flipbook.run(playbackPath, self._frameRange, self._selectedViews, options)
