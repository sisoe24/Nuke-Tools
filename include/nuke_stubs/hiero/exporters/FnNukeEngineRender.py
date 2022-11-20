import platform
import hiero.core
import hiero.core.log as log
import hiero.core.nuke as nuke
import os.path
import os, sys, re, time, socket
import subprocess
from hiero.core import util
from .FnSubmission import Submission
from PySide import QtCore, QtGui
from .FnLocalNukeRender import LocalNukeRenderTask
from FnNukeEngineOpgraphServerConfig import NukeEngineOpgraphServerConfig
from FnOpgraphServerManager import OpgraphServerManager
import hiero.core.log as log


class OpgraphRenderError(Exception):
  """ 
  Very simple class for representing errors from the 'remote' opgraph creation process
  """
  SERVER_UNREACHABLE = 1 
  RENDER_ERROR       = 2 

  def __init__(self, message, failReason):
    Exception.__init__(self, message)
    self.message = message
    self.failReason = failReason

class LocalNukeEngineRenderTask(hiero.core.TaskBase):
  """
  Task for rendering NukeEngine opgraphs - this is where the actual work takes place.
  """

  def __init__(self, initDict, scriptPath):
    hiero.core.TaskBase.__init__(self, initDict)
    self._initDict  = initDict

    start_frame = initDict['startFrame']
    end_frame = initDict['endFrame']
    self._nFrames = (end_frame - start_frame) + 1

    self._scriptPath = scriptPath
    self._logFileName = os.path.splitext(self._scriptPath)[0] + ".log"
    self._logFile = None
    self._finished = False
    self._stepCalls = 0
    self._returnCode = None
    self._progress = 0.0
    self._nukeEngineProcess = None
    self._nukeProcess = None

    self._opgraphCreated = False

    self._frame = 0
    self._flag = 0
    self._opggraph_socket = None

    self._opgraph_creation_time = 0.0

    self._report_opgraph_time_as_error = False


  def _tryToConnectToOpgraphServer(self):
    try:
      self._opgraph_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self._opgraph_socket.connect((NukeEngineOpgraphServerConfig.OPGRAPH_HOST, NukeEngineOpgraphServerConfig.OPGRAPH_PORT))
      return True
    except:
      self._opggraph_socket = None
      return False

  def _renderOpgraphWithServer(self):
    hiero.core.log.debug('Rendering over port')
  
    self._opgraph_socket.sendall(self._scriptPath) # Very simple implementation - the only thing it's expecting is a path to a nk script

    #Block - wait for the signal from the process that the opgraph is created before rendering it in Nuke Engine
    opgraph_render_return = self._opgraph_socket.recv(1024)
    self._opgraph_socket.close()
    self._opggraph_socket = None

    if 'success' in str(opgraph_render_return).rstrip().lower():
      self._opgraphCreated = True
    else:
      raise OpgraphRenderError(opgraph_render_return, OpgraphRenderError.RENDER_ERROR)


  def _renderOpgraphLocally(self):
    log.debug("Rendering opgraph on a new process")
    nuke_executable = nuke.Script.getRenderOnlyNukeExecutablePath()
    log.debug(nuke_executable)
    log.debug(self._scriptPath)
    
    #Assuming that all opgraph node names get exported correctly as Write_OPGRAPH 
    args  = []
    args.append(nuke_executable)
    args.append(' -X Write_OPGRAPH ')
    args.append(self._scriptPath)

    # Block this thread until the opgraph is rendered before calling Nuke Engine with it

    self._nukeProcess =  subprocess.Popen(''.join(args), shell=True)
    self._nukeProcess.wait()

  def startTask(self):
    """
    Start the NukeEngine process
    """
    log.debug( 'Nuke Engine Start task called')
    # This point onwards is generating the opgraph, so time the 'real' time that this takes
    opgraph_creation_start_time = int((time.time() + 0.5) * 1000)

    # First, attempt to connect to an 'Opgraph server' - an already running instance of Nuke that will accept socket connections 
    # and a message with where to find the nk script that studio has generated
    
    connection_established = self._tryToConnectToOpgraphServer()
    hiero.core.log.debug('First attempt to connect to Opgraph server: %s' % ('Established' if connection_established else 'No connection'))
    

    if not connection_established:                                
      # The opgraph server wasn't already running try and start one and flag this as an error later if we were expecting it to
      OpgraphServerManager.startOpgraphRenderServer()     
      if 'START_OPGRAPH_SERVER' in list(os.environ.keys()):
        self._report_opgraph_time_as_error = True

      # There's no point waiting for the opgraph server to have started (complicated and will still take as much time) so do it 'locally' anyway 
      self._renderOpgraphLocally()

    else: 
      # We have a successful connection - create the opgraph on the server
      self._renderOpgraphWithServer()             

    opgraph_creation_end_time = int((time.time() + 0.5) * 1000)
    self._opgraph_creation_time = opgraph_creation_end_time - opgraph_creation_start_time
    log.debug("The opgraph generation took %dms" % self._opgraph_creation_time)

   
    #Now it's time to actually render the thing
    try:
      nuke_engine_executable = os.environ['ENGINE_PATH']
    except KeyError:
      raise Exception('No Nuke Engine Executable path specified. This can be specified in the ENGINE_PATH environment variable')


    opgraph_path = '.'.join(self._scriptPath.split('.')[:-1])+'.opgraph'

    if not os.path.exists(opgraph_path):
      raise Exception('Exporting the Nuke Engine opgraph failed - no opgraph file was found')

    self._logFile = util.filesystem.openFile( self._logFileName, 'w' )

    engine_args = []
    engine_args.append(nuke_engine_executable)
    engine_args.append(' -o '+opgraph_path)

    # -x Excecute opgraph 
    # -n Top down mode
    # -g Use graph colouring
    # -a5 Atomic workload balancing - 5 scanlines at a time
    engine_args.append(' -x -n -g -a5')

    self._nukeEngineProcess = subprocess.Popen(''.join(engine_args),stdout=self._logFile, stderr=subprocess.STDOUT, shell=True)

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

  def parseEngineOut(self):
    # Open up the logfile and have a look:
    # Here we are simply calcualating progress as a fraction of the number of time's we've seen
    # a ComputeVertex(WriteContainer / Write) over the number of frames we have from Nuke Studio
    write_finds = 0
    write_regex = re.compile('ComputeVertexI::compute\s+on\s+vertex\s+[0-9_]*(Write)[Container]*')
    log_lines = self._readLogFile()

    for line in log_lines:
      if line:
          matches = write_regex.search(line)
          if matches:
            write_finds += 1
    if write_finds > 0:
      self._progress = float(write_finds) / float(self._nFrames)

  def taskStep(self):
    """
    Check the state of the NukeEngine process.  Returns True while it is running.
    NOTE: Given that we're trying to make things a bit more efficient by not spamming this method 
    constantly and so letting the thread sleep, this will mean that the timings from a NukeEngine export will 
    always over-report by a bit, as (currently) we're only sampling the file every 10 * 0.01 = 0.1 seconds
    For accurate timings it's best to check out the results in the log file
    """
    self._stepCalls +=1
    if (self._stepCalls) % 10 == 0:
      self._stepCalls = 0
    
      self.parseEngineOut()
    
      self._returnCode = self._nukeEngineProcess.poll()
      if self._returnCode is not None:
        log.debug('Finished')
        self._finished = True
    else:
      time.sleep(0.01) # Give this thread a break!

    return (self._finished == False) # (Returns true while engine is running)

  def finishTask(self):
    self._logFile.close()
    if self._report_opgraph_time_as_error:
      self.setError("The opgraph was not rendered on a server and took: %dms to create" % self._opgraph_creation_time)
    # We would also delete the .nk and .opgraph files here too, but always keep them for now


  def forcedAbort(self):
    # Could be aborting either the Nuke or NukeEngine process (or both, somehow)
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

    if self._nukeEngineProcess is not None:
      returncode = self._nukeEngineProcess.poll()
      if returncode is None:
        if platform.system() == "Windows" and self._usingSingleSocket:
          # As above
          subprocess.call(["taskkill", "/F", "/T", "/PID", str(self._nukeEngineProcess.pid)])
        else:
          self._nukeEngineProcess.terminate()
        self._nukeEngineProcess.wait()


  def progress(self):
    """
    Get the render progress.
    """
    if self._finished:
      return 1.0
    return float(self._progress)


class LocalNukeEngineSubmission(Submission):
  """
  Submission for rendering NukeEngine scripts
  """
  def __init__(self):
    Submission.__init__(self)

  def ident(self):
    return 'hiero.exporters.FnNukeEngineRender.LocalNukeEngineSubmission'

  def addJob(self, jobType, initDict, filePath):
    log.debug('FilePath: ' + filePath )
    return LocalNukeEngineRenderTask( initDict, filePath )
