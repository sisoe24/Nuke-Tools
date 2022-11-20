# Example to submit a Transcode render to a Rush render farm

# This will pass the relevant render information (name, path to Nuke script, framerange) and open the submit window

import hiero.core
from hiero.exporters.FnSubmission import Submission
import re
import os
import subprocess
from PySide2 import QtCore

# Set the path to your Rush submit script here
rushFile = None

# Create a Task to handle Sequences and Clips for Transcoding. This is pulled from site-packages/hiero/exporters/FnLocalNukeRender.py
# Modify this to pass the information you want to your own external processes
class RushRenderTask(hiero.core.TaskBase):
  def __init__(self, jobType, initDict, scriptPath):
    hiero.core.TaskBase.__init__(self, initDict)
    self._scriptPath = scriptPath
    self._logFileName = os.path.splitext(self._scriptPath)[0] + ".log"
    self._jobDoneFile = os.path.splitext(self._scriptPath)[0] + ".done"
    self._jobDoneCmd = os.path.join(os.path.dirname(self._scriptPath), "jobdonecommand")
    self._logFile = None
    self._finished = False
    self._progress = 0.0
    self.rushProcess = None
    self._frame = 0
    self._first = 0
    if isinstance(self._item, hiero.core.Sequence):
      self._last = self._sequence.duration()-1
    if isinstance(self._item, hiero.core.Clip):
      start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)
      self._last = end
    if isinstance(self._item, hiero.core.TrackItem):
      start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)      
      self._last = end
    self.job_title = os.path.splitext(os.path.basename(self._scriptPath))[0]
    self._jobID = 0

  # Create the command to start IRush and populate the submit window with relevant information  
  def sendToRush(self, scriptPath, first, last, job_title):
    assert rushFile is not None, "A path to your Rush submit script must be set before you run this example"
    f = open(self._jobDoneCmd, 'w')
    f.write("touch " + self._jobDoneFile)
    f.close()
    os.chmod(self._jobDoneCmd, 0o777)
    cmd = rushFile + " -field NukeScript " + scriptPath + " -field Frames " + str(first) + "-" + str(last) + " -field JobTitle " + job_title + " -field JobDoneCommand " + self._jobDoneCmd
    self.rushProcess = subprocess.Popen(cmd, shell=True, stdout=self._logFile, stderr=subprocess.PIPE)
    return self.rushProcess

  def startTask(self):
    self._logFile = open( self._logFileName, 'w' )
    self.sendToRush(self._scriptPath, self._first, self._last, self.job_title)

  # Process is considered a Background task when taskStep returns False and progress is less than 1.0
  def taskStep(self):
    if self._finished == True:
      return True
    else:
      return False

  """
  Clean up after render.
  """
  def finishTask(self):
    # Close log file
    self._logFile.close()

  # Abort will not affect the external render. If you want to abort the rush render from Hiero you need the job ID which doesn't get passed back from the submit window
  def forcedAbort(self):
    # If process is running, terminate
    if self.rushProcess is not None:
      returncode = self.rushProcess.poll()
      if returncode is None:
        self.rushProcess.terminate()
    return

  """
  Get the render progress.
  """
  def progress(self):
    # Check to see that the rush jobdonecommand has completed
    if os.access(self._jobDoneFile, os.R_OK):
      self._finished = True
      # Delete the rush job done command files
      os.unlink(self._jobDoneCmd)
      os.unlink(self._jobDoneFile)

    if self._finished:
      return 1.0
    return float(self._progress)

# Create a Submission and add your Task
class RushRenderSubmission(Submission):
  def __init__(self):
    Submission.__init__(self)    
  
  def addJob(self, jobType, initDict, filePath):
    return RushRenderTask( Submission.kCommandLine, initDict, filePath )

# Add the Custom Task Submission to the Export Queue           
registry = hiero.core.taskRegistry
registry.addSubmission( "Start IRush", RushRenderSubmission )
