import foundry.frameserver.nuke.frameserver as frameserver
import foundry.frameserver.nuke.errorhandler as errorhandler
import foundry.frameserver.log
from foundry.frameserver import constants
from foundry.frameserver.nuke.bases import IBackgroundRenderer
import hiero.core
import nuke_internal as nuke
from PySide2 import (QtCore, QtWidgets)

# The Nuke executeInMainThread can't be used in Hiero mode, so we have
# to switch. Additionally the hiero one has a slightly different interface
# which we need to adapt. FIXME: Put this somewhere more appropriate
if nuke.env['hiero']:
  from hiero.core import executeInMainThread as _executeInMainThread
  executeInMainThread = lambda callableObject, args: _executeInMainThread(callableObject, *args)
else:
  from nuke import executeInMainThread

#We need to try the import of psutil because we don't have a debug version for windows
#it is None checked in the places where it is used.
#this was initially added in CL 100581 in the nukestudio.py file
try:
  import psutil
except:
  psutil = None
import sys


def configureFrameServerFromCommandArgs():
  """ Check for the --frameserverloglevel command line argument for setting the
      frame server log level.  Note that this can't be done on module import because
      hiero.core.rawArgs is not available until afterwards. """
  for i, arg in enumerate(hiero.core.rawArgs):
    if arg == "--frameserver-loglevel":
      try:
        foundry.frameserver.log.setLogLevel(hiero.core.rawArgs[i+1])
      except IndexError:
        pass
      break


def workerCount():
  settings = hiero.core.ApplicationSettings()
  return int(settings.value("frameserver/workercount"))

frameserver.workerCount = workerCount

frameServer = frameserver.FrameServer(hiero.core.getBundledNukePath(), hiero.core.getBundledPythonPath(), pathRemapFunc=hiero.core.remapPath)

# Create an observer for background render progress
backgroundRenderObserver = hiero.core.BackgroundRenderObserver()
frameServer.addBackgroundRenderObserver( backgroundRenderObserver )

# Create an observer for render progress of individual frames
renderProgressObserver = hiero.core.RenderProgressObserver()
frameServer.addRenderProgressObserver(renderProgressObserver)

# A variable for a potentially custom background renderer implementation
backgroundRenderer = frameServer


def startServer():
  """ Start the Nuke frame server. """
  hiero.core.log.debug( "nukestudio.startServer" )

  configureFrameServerFromCommandArgs()

  nukeWorkerThreads, nukeWorkerMemory = hiero.core.nuke.nukeThreadsMemoryPreferences()
  pathRemappings = hiero.core.util.flattenedPathRemappings()

  frameserverErrorHandler = errorhandler.FrameserverErrorHandler(onFatalError, onError)

  global frameServer
  frameServer.start(nukeWorkerThreads, nukeWorkerMemory, pathRemappings, frameserverErrorHandler)


def stopServer(event):
  """ Handle shutdown event to stop the frame server. """
  global frameServer

  hiero.core.log.debug( "nukestudio.stopServer" )
  frameServer.stop()


def promptFrameServerKill(port):
  if psutil is None:
    QtWidgets.QMessageBox.warning(
      hiero.ui.mainWindow(),
      "Frame Server",
      "Frame Server failed to bind TCP port %s. Please ensure port %s is " \
      "available and restart Nuke." % (port, port),
    )
    return

  processes = []
  for process in psutil.process_iter():
    try:
      if any(
        'workerapplication.py' in arg or 'runframeserver.py' in arg
        for arg in process.cmdline()
      ):
        processes.append(process)
    except psutil.AccessDenied:
      pass

  if not processes:
    QtWidgets.QMessageBox.warning(
      hiero.ui.mainWindow(),
      "Frame Server",
      "Frame Server failed to bind TCP port %s. Please ensure port %s is " \
      "available and restart Nuke." % (port, port),
    )
  else:
    reply = QtWidgets.QMessageBox.question(
      hiero.ui.mainWindow(),
      "Frame Server",
      "Frame Server failed to bind TCP port %s and found existing Frame " \
      "Server processes. Would you like Nuke to attempt to kill these " \
      "processes?" % port,
      QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
    )
    if reply == QtWidgets.QMessageBox.Yes:
      failed = False
      for process in processes:
        try:
          process.kill()
        except psutil.AccessDenied:
          failed = True
      if not failed and not psutil.wait_procs(processes, timeout=1)[1]:
        stopServer(None)
        startServer()
      else:
        QtWidgets.QMessageBox.warning(
          hiero.ui.mainWindow(),
          "Frame Server",
          "Failed to kill processes with PIDs: %s\nPlease kill these " \
          "processes manually and restart Nuke." % ', '.join(
            str(p.pid) for p in processes if p.is_running()
          ),
        )


def onFatalError(exitcode):
  """
  A callback which gets called when frameserver encounters a fatal error.
  It returns a known exit code which indicates the reason for the fatal failure.

  This will get called from some random thread, so take care calling UI.
  """
  if constants.MIN_CANNOT_BIND <= exitcode <= constants.MAX_CANNOT_BIND:
    port = exitcode - constants.MIN_CANNOT_BIND + constants.CANNOT_BIND_BASE
    executeInMainThread(promptFrameServerKill, args=(port,))
  elif exitcode == constants.CANNOT_BIND_WORKER:
    executeInMainThread(QtWidgets.QMessageBox.warning, args=(
      hiero.ui.mainWindow(),
      "Frame Server",
      "Frame Server unable to create sockets for worker communications.  This requires TCP ports in the range %s-%s.  Your system may need to be configured to allow use of these ports." % constants.WORKER_PORT_RANGE
    ))
  elif exitcode == constants.FATAL_EXCEPTION:
    executeInMainThread(QtWidgets.QMessageBox.warning, args=(
      hiero.ui.mainWindow(),
      "Frame Server",
      "Frame Server has encountered a fatal error. Please see console output for more information.",
    ))


def onError(message):
  """
  A callback which gets called when the framserver encounters a non-fatal error.
  """
  # FIXME This class is a hack to work around the fact you cant resize a QMessageBox.
  # Since the detailed text could be quite long being resizable makes it much easier to read.
  # It's based on http://www.qtcentre.org/threads/24888-Resizing-a-QMessageBox
  class DetailedResizableMessageBox(QtWidgets.QMessageBox):
    def __init__(self, parent, title, summaryText, detailedText):
      super(DetailedResizableMessageBox, self).__init__(QtWidgets.QMessageBox.Critical, title, summaryText, QtWidgets.QMessageBox.Ok, parent)
      self.setDetailedText(detailedText)


    # Note that event gets called before __init__, so we can get errors when using members specific to DetailedResizableMessageBox.
    def event(self, event):
      result = super(DetailedResizableMessageBox, self).event(event)

      # QWIDGETSIZE_MAX doesn't seem to be available in PySize. It's defined as ((1<<24)-1) in qwidget.h
      maximumWidgetSize = QtCore.QSize(16777215, 16777215)
      self.setMaximumSize(maximumWidgetSize)

      detailsTextEdit = self.findChild(QtWidgets.QTextEdit)
      if detailsTextEdit is not None:
        detailsTextEdit.setMaximumSize(maximumWidgetSize)

      return result


  executeInMainThread(lambda *args: DetailedResizableMessageBox(*args).exec_(), args=(
      hiero.ui.mainWindow(),
      "Error",
      "The Frame Server has encountered an error.",
      message
    ))


def isServerRunning(timeout=1):
  """ Test if the Nuke frame server is running.  This is done by sending a message to it
      and waiting for a response.  Returns false if no reply was received within timeout seconds.
      @param timeout: time in seconds to wait for a response.  Defaults to 1 """
  global frameServer, backgroundRenderer
  return frameServer.isRunning(timeout) and (backgroundRenderer == frameServer or backgroundRenderer.isRunning(timeout))


def renderFrames(scriptPath, frameRanges, writeNode, views ):
  """ Queue background render of a range of frames for a script. """

  hiero.core.log.debug( "nukestudio.renderFrames " + scriptPath )
  global backgroundRenderer
  backgroundRenderer.renderFrames(scriptPath, frameRanges, writeNode, views )

def renderScript(scriptName):
  """ Queue background render of all the frames for a script. """

  global backgroundRenderer
  backgroundRenderer.renderScript(scriptName)


def cancelFrames(scriptPath, nodeName=""):
  """ Cancel background render of all the frames for the given script. """

  hiero.core.log.debug( "nukestudio.cancelFrames " + scriptPath +","+nodeName)
  global backgroundRenderer
  backgroundRenderer.cancelFrames(scriptPath, nodeName)


def setBackgroundRenderer(renderer):
  """ Set the background renderer instance to be used for rendering. """

  assert issubclass(renderer.__class__, IBackgroundRenderer), 'Not a subclass of IBackgroundRenderer'

  global backgroundRenderer, backgroundRenderObserver
  renderer.addBackgroundRenderObserver(backgroundRenderObserver)
  backgroundRenderer.removeBackgroundRenderObserver(backgroundRenderObserver)
  backgroundRenderer = renderer


def postProcessScript(scriptPath):
  """ Send a command to post-process the Nuke script to the post processor."""
  global backgroundRenderer
  backgroundRenderer.postProcessScript(scriptPath)

def removeBackgroundRenderObserver(observer):
  global backgroundRenderer
  backgroundRenderer.removeBackgroundRenderObserver(observer)

def addBackgroundRenderObserver(observer):
  global backgroundRenderer
  backgroundRenderer.addBackgroundRenderObserver(observer)

