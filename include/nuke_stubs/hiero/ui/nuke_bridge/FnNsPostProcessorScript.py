from foundry.frameserver.nuke import errorhandler, postprocessscript as postProcessScript
from . import FnNsFrameServer
import hiero.core
import sys
import os.path


def stopServer(event):
  global postProcessServer
  postProcessServer.stop()  

pathRemaps = hiero.core.util.flattenedPathRemappings()

nukePath = hiero.core.getBundledNukePath()
exeDir = os.path.dirname(sys.executable)
scriptPath = os.path.abspath( os.path.join(exeDir, "pythonextensions", "site-packages") )
postProcessServer = postProcessScript.PostProcessScript()
postProcessServer.start(nukePath, scriptPath, pathRemaps, errorhandler.FrameserverErrorHandler(FnNsFrameServer.onFatalError, FnNsFrameServer.onError))
hiero.core.events.registerInterest(hiero.core.events.EventType.kShutdownFinal, stopServer)

def postProcessScript(scriptPath):
  """ Send a command to post-process the Nuke script to the post processor. If
  an error occurs, returns a string containing an error message, otherwise
  returns None."""

  #When the postprocessor receives a message from the worker application with an
  #error, it will raise a RunTimeError.
  #Catch it here and return string that will be handled in NukeShotExporter.
  #All Exceptions are caught becase calling code does not use exceptions
  #for handling errors.
  #This behaviour matches the one in postProcessScript in frameserver.py.

  global postProcessServer
  try:
    postProcessServer.postProcessScript(scriptPath)
  except Exception as e:
    return str(e)

