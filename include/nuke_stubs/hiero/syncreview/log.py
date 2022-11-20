import nuke_internal as nuke
import datetime
import logging
import os
import traceback

"""
Logging functionality for sync review.
Logs are written to a file under NUKE_TEMP_DIR/logs.
It must be initialised with the name of the file to write to when the session starts.
"""

_logDir = os.path.join(os.environ['NUKE_TEMP_DIR'], 'logs')
_rootLogger = logging.getLogger('syncreview')
_rootLogger.propagate = False
_logFormatter = logging.Formatter('%(asctime)s.%(msecs)03d: %(message)s', '%H:%M:%S')
_fileLogger = None

def initLogger(name):
  """ Create the logger instance with the given name """
  global _fileLogger
  global _rootLogger
  _fileLogger = _rootLogger.getChild(name)
  logPath = os.path.join(_logDir, '{}.log'.format(name))
  fileHandler = logging.FileHandler(logPath, mode="w")
  fileHandler.setFormatter(_logFormatter)
  fileHandler.setLevel(logging.DEBUG)
  _fileLogger.setLevel(logging.DEBUG)
  _fileLogger.addHandler(fileHandler)


def closeLogger():
  """ Close the logger instance """
  # Can't destroy the logger object, make sure files are closed etc.
  global _fileLogger
  if _fileLogger:
    handlers = _fileLogger.handlers[:]
    for handler in handlers:
      handler.close()
      _fileLogger.removeHandler(handler)
    _fileLogger = None


def logMessage(message):
  """ Write a message to the current log file """
  global _fileLogger
  if _fileLogger:
    _fileLogger.info(message)

def logException(msg=None):
  """ Log the current exception details """
  trace = traceback.format_exc()
  if msg:
    msg = msg + '\n' + trace
  else:
    msg = trace
  logMessage(msg)

LOG_DEBUG_ENABLED = False

def logDebug(message):
  """ Debug log message. These aren't printed unless LOG_DEBUG_ENABLED is set """
  global LOG_DEBUG_ENABLED
  if LOG_DEBUG_ENABLED:
    logMessage(message)
