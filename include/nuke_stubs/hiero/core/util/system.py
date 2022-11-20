'''
Module for querying CPU related system information
'''

import platform
import subprocess

from hiero.core import log

def _linuxNUMALaunchArguments(preferredNode = 0):
  '''
  Return the numa arguments for launching a process on a single CPU, specified by preferredNode
  '''
  # TODO: Error if the preferred node is invalid
  return ("numactl", "--cpunodebind=%s" % preferredNode, "--membind=%s" % preferredNode)

def _linuxSocketCount():
  '''
  Query how many CPU sockets are available when in Linux.
  '''
  # /proc/cpuinfo return information for each core on the system. This information includes the physical id
  # of the core. We can count the number of unique physical ids to get the number of sockets.
  cpuinfoCommand = "cat /proc/cpuinfo"
  try:
    cpuinfoOutput = subprocess.check_output(cpuinfoCommand, shell=True)
  except subprocess.CalledProcessError as exception:
    log.error("Error when querying CPU info - %s", exception.message)
    socketCount = 1
  else:
    physicalIds = [line for line in cpuinfoOutput.splitlines() if line.startswith("physical id")]
    physicalIds = set(physicalIds)
    socketCount = len(physicalIds)
    if socketCount == 0:
      log.error("/proc/cpuinfo does not contain physical id information, assuming only 1 CPU socket is available")
      socketCount = 1

  return socketCount

def _windowsSocketCount():
  '''
  Query how many CPU sockets are available when in Windows.
  '''
  command = "wmic cpu list brief"
  try:
    cpuInfo = subprocess.check_output(command)
  except WindowsError as exception:
    log.error("Error when querying CPU socket info - %s", exception.message)
    socketCount = 1
  else:
    cpuInfo = cpuInfo.strip()
    cpuInfo = cpuInfo.split("\n")
    assert(len(cpuInfo) > 1)
    # wmic cpu list brief returns various bits of information for each processor in the system, along
    # with a row containing labels for column. We can get the socket count by ignoring the row of labels
    # and counting the remaining lines.
    socketCount = len(cpuInfo) - 1
  return socketCount

def _windowsStartAffinityLaunchArguments(coresPerSocket, preferredNode = 0):
  '''
  Return the arguments for launching a process on a single CPU, specified by preferredNode
  '''
  # TODO: Error if the preferred node is invalid
  # We need to specify which cores to use in addition to the NUMA node to run on. We assume that NUMA nodes
  # map to physical processors. Since we want to limit a process to a single socket we need to use all the cores
  # available on a single socket which is specified by the affinity mask and the processor to use, set by
  # the node argument.
  # http://stackoverflow.com/questions/7759948/set-affinity-with-start-affinity-command-on-windows-7
  decimalAffinityMask = (2**coresPerSocket - 1) << (coresPerSocket * preferredNode)
  hexAffinityMask = hex(decimalAffinityMask)
  # We should be able to just run "start /B /Node ..." however start is only available when a subprocess is launched
  # with the shell=True argument. When shell=True is used on Linux the numactl arguments are not executed correctly and
  # the process fails to launch. Instead of using shell=true we add "cmd /C" to the start command so it gets executed
  # via a Windows command interpreter.
  # Even though we're running in the background with "/B" we need to specify an empty argument for title otherwise the path argument,
  # which gets appended later, doesn't get processed correctly.
  return ("cmd", "/C", "start", "", "/B", "/NODE", str(preferredNode), "/AFFINITY", hexAffinityMask, "/WAIT")

class SystemInfo(object):
  '''
  Query CPU related information about this system.
  '''
  def __init__(self):
    self._platformName = platform.system()

  def socketCount(self):
    '''
    Return how many CPU sockets are available.
    '''
    if self._platformIsLinux():
      return _linuxSocketCount()
    elif self._platformIsWindows():
      return _windowsSocketCount()
    else:
      return 1

  def singleSocketLaunchArguments(self):
    '''
    Return the arguments requried to launch a process that is limited to
    a single CPU. These arguments should be prepended to the command that
    is to be run.
    '''
    if self._platformIsLinux():
      return _linuxNUMALaunchArguments()
    elif self._platformIsWindows():
      return _windowsStartAffinityLaunchArguments(self.coresPerSocket())
    else:
      raise OSError("Launching on a single socket is not supported on this platform")

  def coresPerSocket(self):
    '''
    Return how many cores are available per CPU socket. This assumes that all CPUs on
    a multi CPU system have the same number of cores.
    '''
    import multiprocessing
    cores =  multiprocessing.cpu_count()
    return cores / self.socketCount()

  def _platformIsWindows(self):
    '''
    Return whether we're currently on Windows.
    '''
    return self._platformName == "Windows"

  def _platformIsLinux(self):
    '''
    Return whether we're currently on Linux.
    '''
    return self._platformName == "Linux"
