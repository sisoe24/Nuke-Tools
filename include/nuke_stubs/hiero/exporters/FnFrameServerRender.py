import os
import hiero.core
from hiero.core import TaskBase
from . FnSubmission import Submission
from . FnLocalNukeRender import LocalNukeRenderTask
from foundry.frameserver.nuke.bases import RenderQueueObserverMixin



class FrameServerRenderTask(TaskBase, RenderQueueObserverMixin):
  """ Task for rendering Nuke scripts through the frame server. """

  def __init__(self, initDict, scriptPath):
    TaskBase.__init__(self, initDict)
    self._scriptPath = scriptPath
    self._startFrame = initDict["startFrame"]
    self._endFrame = initDict["endFrame"]
    self._totalFrames = self._endFrame - self._startFrame + 1
    self._renderedFrames = 0


  def startTask(self):
    # Register for render progress notifications
    hiero.ui.nuke_bridge.FnNsFrameServer.backgroundRenderer.addBackgroundRenderObserver(self)

    # Add the script to the render queue
    try:
      hiero.ui.nuke_bridge.FnNsFrameServer.renderScript(self._scriptPath)
    except Exception as e:
      self.setError(str(e))


  def taskStep(self):
    # If the task has finished or there was an error, return False
    if self._renderedFrames == self._totalFrames or self.error():
      return False
    else:
      return True


  def finishTask(self):
    # If the 'keep Nuke script' option isn't checked, remove it
    if not self._preset.properties()["keepNukeScript"]:
      self.deleteTemporaryFile(self._scriptPath)

    # Remove self from the observers list
    hiero.ui.nuke_bridge.FnNsFrameServer.backgroundRenderer.removeBackgroundRenderObserver(self)


  def forcedAbort(self):
    self.cancelRenders()


  def progress(self):
    # To get the UI to behave correctly, make sure we return 1.0 if the task
    # finished due to an error
    if self.error():
      return 1.0
    else:
      # Return render progress in range 0-1
      return float(self._renderedFrames) / float(self._totalFrames)


  def cancelRenders(self):
    """ Remove the script from the render queue. """
    hiero.ui.nuke_bridge.FnNsFrameServer.cancelFrames(self._scriptPath)


  def onFrameRendered(self, path, frame, writeNode):
    """ Callback when a frame is rendered.  If it's for the script being
    rendered, increment the count. """
    if path == self._scriptPath:
      self._renderedFrames = self._renderedFrames + 1


  def onFrameRenderError(self, path, frame, nodeName, errorMsg):
    """ Callback when there is an error rendering a frame.  Set the error state
    and cancel. """
    self.setError("Render error in script: %s node: %s frame: %s\n%s" %
                    (path, nodeName, frame, errorMsg))
    self.cancelRenders()


class FrameServerSubmission(Submission):
  """ Submission class for rendering an nk script through the frame server.  If
  that is not possible, will fall back to using the LocalNukeRenderTask. """
  def __init__(self):
    Submission.__init__(self)


  def addJob(self, jobType, initDict, filePath):
    if jobType == Submission.kNukeRender:

      # Check if this render can be run on the frame server.  If not, fall back
      # to the LocalNukeRenderTask
      if self.canRenderOnFrameServer(initDict):
        return FrameServerRenderTask( initDict, filePath )
      else:
        return LocalNukeRenderTask( initDict, filePath )

    else:
      raise Exception("FrameServerSubmission.addJob unknown type: " + jobType)


  def canRenderOnFrameServer(self, initDict):
    """ Check if this render can be done through the frame server.  Currently
    it can't be used to render video formats. """

    # Check if there's a connection to the frame server
    if not hiero.ui.nuke_bridge.FnNsFrameServer.isServerRunning():
      return False

    # Check if a comp is being rendered as part of an export.  Otherwise
    # if transcoding a sequence to a mov, and there are comp containers to be
    # rendered, that wouldn't use the frame server even though it could
    try:
      renderingComp = initDict["renderingComp"]
      if renderingComp:
        return True
    except KeyError:
      pass


    # Try to check if a video format is being rendered on the preset.  If (as
    # expected) it's a RenderTaskPreset, we can get that from it's codec
    # settings.  If that doesn't work, return False.
    try:
      preset = initDict['preset']
      return not preset.codecSettings()["isVideo"]
    except:
      return False

# Register our built in submission types. 
# Since this task is added after the single process,
# fnExporterPresetsDialog will set the appropiate default.
hiero.core.taskRegistry.addSubmission( "Frame Server", FrameServerSubmission )
