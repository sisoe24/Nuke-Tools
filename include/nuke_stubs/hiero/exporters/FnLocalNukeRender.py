import platform
import hiero.core
import hiero.core.nuke as nuke
import os.path
import re
import subprocess
from hiero.core import util
from .FnSubmission import Submission


class LocalNukeRenderTask(hiero.core.TaskBase):
  """
  Task for rendering Nuke scripts locally.

  This is for rendering synchronously, that is taskStep()
  returns True until the render has finished.
  """

  kNukeLicenseErrorReturnCode = 100

  def __init__(self, initDict, scriptPath):
    hiero.core.TaskBase.__init__(self, initDict)
    self._scriptPath = scriptPath
    self._logFileName = os.path.splitext(self._scriptPath)[0] + ".log"
    self._logFile = None
    self._finished = False
    self._returnCode = None
    self._progress = 0.0
    self._nukeProcess = None
    self._frame = 0
    self._usingSingleSocket = None


  def startTask(self):
    """
    Start the Nuke process.
    """
    presetProperties = self._preset.properties()
    self._usingSingleSocket = presetProperties.get("useSingleSocket", False)
    self._logFile = util.filesystem.openFile( self._logFileName, 'w' )
    self._nukeProcess = nuke.executeNukeScript(self._scriptPath, self._logFile, self._usingSingleSocket)


  def taskStep(self):
    """
    Check the state of the Nuke process.  Returns True while it is running.
    """
    # Check the progress.  This is updated every 10 times taskStep is called.
    self._frame += 1
    if self._frame % 10 == 0:
      self.parseProgressOutput()

    # If the return code is not None, process has finished.  Checking the value
    # is done in finishTask()
    self._returnCode = self._nukeProcess.poll()
    if self._returnCode is not None:
      self._finished = True

    return (self._finished == False)


  def finishTask(self):
    """
    Clean up after render.
    """
    # Close log file
    self._logFile.close()

    # Check for errors
    self.checkNukeProcessError()

    # If options not set, delete nk and log files
    if not self._preset.properties()["keepNukeScript"]:
      # clean up the script
      self.deleteTemporaryFile(self._scriptPath)
      self.deleteTemporaryFile(self._logFileName)


  def forcedAbort(self):
    """
    Abort the Nuke process.
    """
    # If process is running, terminate
    if self._nukeProcess is not None:
      returncode = self._nukeProcess.poll()
      if returncode is None:
        if platform.system() == "Windows" and self._usingSingleSocket:
          # subprocess.Popen.terminate only kills the top level process, child processes are not killed.
          # On Windows launching a single socket export creates several processes, the last of which is Nuke.
          # Killing the parent does not kill Nuke, so we need to explicitly kill the whole tree.
          subprocess.call(["taskkill", "/F", "/T", "/PID", str(self._nukeProcess.pid)])
        else:
          self._nukeProcess.terminate()

        self._nukeProcess.wait()

        # Check for any errors in the log. Is this useful when aborting?
        errorString = self.parseErrorFromLog()
        if errorString:
          self.setError(errorString)


  def progress(self):
    """
    Get the render progress.
    """
    if self._finished:
      return 1.0
    return float(self._progress)


  def _readLogFile(self):
    """
    Read the log file and return the output lines.  Returns an empty list if
    reading the file failed.
    """
    try:
      with util.filesystem.openFile( self._logFileName,'r') as logFile:
        return logFile.readlines()
    except IOError:
      return []


  def parseProgressOutput (self):
    """
    Parse progress from the log file.
    """
    logOutput = self._readLogFile()
    for line in reversed(logOutput):
      if line:
        framesRegEx = "Frame [\d]* \(([\d]*) of ([\d]*)\)"
        matches = re.match(framesRegEx, line)
        if matches:
          frame, numframes = matches.groups()
          self._progress = float(frame) / float(numframes)
          # Once we have established the progress, no need to go any further
          break


  def parseErrorFromLog(self):
    """
    Parse any errors in the log file and return the result.  If no errors were
    found, will return an empty string.
    """
    errorString = ""

    logOutput = self._readLogFile()
    for line in logOutput:
      if line:
        errorRegEx = "[\[\w\]\.\:]*(warning:|error:|failure:|cannot\sbe\sexecuted).*"
        matches = re.search(errorRegEx, line, re.IGNORECASE)
        if matches:
          errorString += line

    if errorString:
      errorString = "Nuke Errors:\n" + errorString

    return errorString


  def checkNukeProcessError(self):
    """
    Determine if there was a render error, and if so set an appropriate error message
    on the task.
    """
    errorString = None

    # First check for licensing errors
    if self._returnCode == LocalNukeRenderTask.kNukeLicenseErrorReturnCode:
      errorString = "Licensing failed for Nuke render process."
    else:
      # Otherwise, next try to parse any errors from the log file
      errorString = self.parseErrorFromLog()

      # If there were no errors in the log file check if Nuke exited with an
      # unexpected code (meaning it probably crashed).
      unexpectedReturnCode = (self._returnCode is not None) and (self._returnCode != 0)
      if not errorString and unexpectedReturnCode:
        errorString = "Nuke process closed unexpectedly, exit code: %s" % self._returnCode

    # If an error was detected, set it on the task
    if errorString:
      self.setError(errorString)



class LocalNukeSubmission(Submission):
  """
  Submission for rendering Nuke scripts locally.
  This is the default.
  """
  def __init__(self):
    Submission.__init__(self)

  def addJob(self, jobType, initDict, filePath):
    if jobType == Submission.kNukeRender:
      # Return a LocalNukeRenderTask which handles the render synchronously
      return LocalNukeRenderTask( initDict, filePath )
    else:
      raise Exception("LocalNukeSubmission.addJob unknown type: " + jobType)
