import os
from PySide2 import QtCore
import hiero.core
import hiero.ui
from hiero.ui.nuke_bridge.FnNsFrameServer import (isServerRunning, startServer, stopServer)

"""
Contains logic for running the frame server on application startup. Importing the
module will automatically trigger this unless it was disabled by the user.
"""

isPlayer = hiero.core.isHieroPlayer();
if isPlayer:
  raise ImportError("frameserver should not be imported in Hiero Player")

try:
  import hiero.ui.FnStatusBar
except ImportError as e:
  hiero.core.log.debug("Importing FnStatusBar failed %s" % e)

FRAMESERVER_DISABLED_ENV = "NUKE_DISABLE_FRAMESERVER"
FRAMESERVER_DISABLED_ENV_DEFAULT = 0

def isFrameServerEnabled():
  """ Check if running the frameserver on startup is enabled. """
  disabledByCommandLine = "--disable-nuke-frameserver" in hiero.core.rawArgs
  disabledByEnvVar = int(os.environ.get(FRAMESERVER_DISABLED_ENV, FRAMESERVER_DISABLED_ENV_DEFAULT))
  return not (disabledByCommandLine or disabledByEnvVar)

def startServerIfEnabled():
  """ Start the Nuke frame server unless it was disabled by the user """
  hiero.core.log.debug( "nukestudio.startServerIfEnabled" )

  if isFrameServerEnabled():
    if not isServerRunning():
      startServer()

      # Register interest in shutdown message
      hiero.core.events.registerInterest(hiero.core.events.EventType.kShutdownFinal, stopServer)

# If the GUI is running, trigger the automatic start of the frame server
runningInGui = QtCore.QCoreApplication.instance().inherits("QApplication")
if runningInGui:
  def setup():
    # autostart the server, unless it's disabled
    startServerIfEnabled()

  # initialize the gui for the hiero nuke bridge a bit later
  QtCore.QTimer.singleShot(0, setup)
