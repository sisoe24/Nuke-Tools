"""
Constants etc. used in the sync client-server code.
"""

import nuke_internal as nuke

# Note: the heartbeat values are somewhat arbitrary and will probably need tuning

# Interval at which the client will send pings to the server
HEARTBEAT_INTERVAL = 1000

# Time after which the client or server will assume a connection to have been lost
HEARTBEAT_TIMEOUT = 10000

# Interval for polling sockets
SOCKET_POLL_INTERVAL = 1000

# Versioning for the sync protocol which at some point will be used to determine
# connection compatibility
PROTOCOL_VERSION = "1.0"

# Application version identifier which will be used to determine connection compatibility
APPLICATION_VERSION = nuke.env['NukeVersionString']

# Sync review preference keys
NAME_SETTING_KEY = "syncreview/defaultName"
COLOR_SETTING_KEY = "syncreview/defaultColor"
OPEN_PANEL_ON_STARTUP_KEY = "syncreview/defaultOpenPanelOnSessionStart"
PREVIOUS_PORT_NUMBER_KEY = "syncreview/previousPortNumber"
PREVIOUS_HOST_KEY = "syncreview/previousHost"

# The last hostname and port selected in the 'Session Setup' dialog
LAST_SHARED_HOST_KEY = "syncreview/lastSharedHost"
LAST_SHARED_PORT_KEY = "syncreview/lastSharedPort"

SHOW_UNSAVED_WORK_WARNING = "syncreview/showUnsavedWorkWarning"
PROJECT_SAVE_DIR_KEY = "syncReviewProjectSaveDir"

# Port number configuration
DEFAULT_PORT = 45124 # This is the same as RV
PORT_MAX = 65535
PORT_MIN = 1

# Convenient for testing purposes until we have a preference or something for this
DEFAULT_HOST = 'localhost'


def __readMachineId():
  # Try to get a unique id for the machine. QSysInfo.machineUniqueId() doesn't
  # work properly on Mac, so fallback to uuid.getnode() which I believe reads a
  # network MAC address
  from PySide2.QtCore import QSysInfo
  import sys
  if sys.version_info.major == 3:
    id = str(QSysInfo.machineUniqueId(), "ascii") # Decode the QByteArray, which should be in hex
  else:
    id = str(QSysInfo.machineUniqueId())
  if not id:
    import uuid
    id = str(uuid.getnode())
  return id

MACHINE_ID = __readMachineId()

# Fixed ID for the host connection
HOST_ID = "host"

# Tooltips
HOST_BUTTON_TOOL_TIP = "Start hosting a new Sync session. Setup your Hostname and Port."
END_SESSION_BUTTON_TOOL_TIP = "End the Session. Close the project for all the Participants."
CONNECT_BUTTON_TOOL_TIP = "Connect to an existing Sync session."
PUSH_SESSION_TOOL_TIP = "Force an update for all other participants to the state of your project and UI. (Ctrl/Cmd + P)"
COPY_INFO_TOOL_TIP = "Copy Host and Port information for this session to the clipboard to share with other participants."
NAME_TOOL_TIP = "Your name as it appears to other participants in the session."
COLOR_TOOL_TIP = "Your color as it appears to other participants in the session."
HOST_HOSTNAME_TOOL_TIP = "The Hostname or IP address to share with other participants."
PORT_TOOL_TIP = "The Port number needed to connect to the host session."
CONNECTION_INFO_TOOL_TIP = "The Connection Information as it appears when copied to the clipboard."
CONNECT_HOSTNAME_TOOL_TIP = "The Hostname or IP address of the Sync session host."
