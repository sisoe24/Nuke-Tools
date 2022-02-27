# Copyright (c) 2014 The Foundry Visionmongers Ltd.  All Rights Reserved.

# Warning: the code below is extracted from an internal test tool (Tests/Common/FnSysInfo.py) and is not recommended for
# use in your own scripts.

import os, sys, glob, math
import xml.sax.saxutils

#Helpers

#Temporary until we fix system profiler.
def RunCmdWithTimeout(cmd, timeout):
  import subprocess, time
  p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
  timerStep = 0.5
  runTime = 0
  while True:
    if p.poll() is not None:
      break
    runTime += timerStep
    if runTime > timeout:
      p.terminate()
      return -1
      sys.exit(1)
    time.sleep(timerStep)
  return 0
#End temporary

def ConvertUnits(s, token, multiplier):
  if s.find(token) != -1:
    realSpeed = s[:s.find(token)]
    realSpeedFlt = float(realSpeed)
    return str(int(realSpeedFlt * multiplier))

def ConvertSpeedUnitsToMhZ(s):
  p = ConvertUnits(s, "GHz", 1000)
  if p != None:
    return p
  return str(int(math.ceil(float(s))))

def ConvertMemSizeToKb(s):
  p = ConvertUnits(s, "MB", 1000)
  if p != None:
    return p
  p = ConvertUnits(s, "GB", 1000000)
  if p != None:
    return p
  p = ConvertUnits(s, "Gb", 1000000)
  if p != None:
    return p
  p = ConvertUnits(s, "kB", 1)
  if p != None:
    return p
  p = ConvertUnits(s, "KB", 1)
  if p != None:
    return p
  return s


#Standard Identifiers
gCPUSpeed = "CPUSpeed_Mhz"
gMachineName = "MachineName"
gNumCPUs = "NumCPUs"
gNumCores = "NumCores"
gRAM = "RAM_Kb"
gCPUType = "CPUType"
gOS = "OS"
gBusSpeed = "BusSpeed"
gL2Cache = "L2Cache_Kb"
gOSVersion = "OSVersion"
gKernelVersion = "KernelVersion"

class HardwareInfo:
  def __init__(self):
    self._standardDict = {}
    self.gLogStr = ""
    if sys.platform.lower() == "darwin":
      self.SafeCall(self.initMac)
    elif (sys.platform.lower() == "linux") | (sys.platform.lower() == "linux2"):
      self.SafeCall(self.initLinux)
    elif (sys.platform.lower().find("win") == 0):
      self.SafeCall(self.initWin)

  def SafeCall(self, f, *positional, **keyword):
    try:
      return f(*positional, **keyword)
    except Exception as e:
      self.gLogStr += "Function: calling " + f.__name__ + "\n"
      self.gLogStr += "\tDescription:" + str(f.__doc__) + "\n"
      self.gLogStr += "\tError:" + str(e) + "\n"

  def testCatCommand(self, info):
    if not os.path.exists(info):
      self.gLogStr += "Failed to find " + info
      return False
    return True

  def parseProcInfo(self, info):
    success = self.testCatCommand(info)
    if not success:
      return ([{}], False)
    import subprocess
    cpuinfo = subprocess.getoutput("cat " + info)
    return self.parseProcInfoStr(cpuinfo)

  def parseProcInfoStr(self, cpuinfo):
    import copy
    values = []
    currentDict = {}
    for i in cpuinfo.split("\n"):
      if i.find(":") == -1:
        values.append(copy.deepcopy(currentDict))
        currentDict = {}
        continue
      tokens = i.split(":")
      name = tokens[0]
      value = ":".join(tokens[1:])
      currentDict[name.strip()] = value.strip()
    if len(currentDict) != 0:
      values.append(copy.deepcopy(currentDict))
    return (values, True)

  def parseCPUInfo(self):
    (itemDict, success) = self.parseProcInfo("/proc/cpuinfo")
    if success:
      mapping = [["cpu MHz", gCPUSpeed],
                 ["model name", gCPUType],
                 ["cache size", gL2Cache]]
      self.MapDictionaries(itemDict, self._standardDict, mapping, "/proc/cpuinfo")
      self._standardDict[gL2Cache] =  ConvertMemSizeToKb(self._standardDict[gL2Cache])
      self._standardDict[gCPUSpeed] = ConvertSpeedUnitsToMhZ(self._standardDict[gCPUSpeed])
      self._standardDict[gNumCores] = len(itemDict)

  def ParseProcVersion(self):
    if self.testCatCommand("/etc/redhat-release"):
      import subprocess
      osVersion = subprocess.getoutput("cat /etc/redhat-release")
      self._standardDict[gOSVersion] = osVersion
    elif self.testCatCommand("/etc/lsb-release"):
      import subprocess
      lsbInfo = subprocess.getoutput("cat /etc/lsb-release")
      for i in lsbInfo.split("\n"):
        if i.find("DISTRIB_DESCRIPTION") != -1:
          self._standardDict[gOSVersion] = i.split("=")[1].replace("\"","")
    elif self.testCatCommand("/proc/version"):
      import subprocess
      osVersion = subprocess.getoutput("cat /proc/version")
      start = osVersion.find(" #1 ")
      osVersionShort = osVersion[:start]
      token = osVersionShort.split("(")[-1]
      self._standardDict[gOSVersion] = token.replace(")", "")

  def parseProcSimple(self, file, entry):
    import subprocess
    if os.path.exists(file):
      self._standardDict[entry] = subprocess.getoutput("cat " + file)
    else:
      self.gLogStr += file + " doesn't exist.\n"
      self._standardDict[entry] = "Unknown"

  def parseMemInfo(self):
    (itemDict, success) = self.parseProcInfo("/proc/meminfo")
    if success:
      self.MapDictionaries(itemDict, self._standardDict, [["MemTotal", gRAM]], "/proc/meminfo")
      self._standardDict[gRAM] =  ConvertMemSizeToKb(self._standardDict[gRAM])

  def initLinux(self):
    self._standardDict[gOS] = "linux"
    self.SafeCall(self.parseCPUInfo)
    self.SafeCall(self.ParseProcVersion)
    self.SafeCall(self.parseProcSimple, "/proc/sys/kernel/osrelease", gKernelVersion)
    self.SafeCall(self.parseProcSimple,	"/proc/sys/kernel/hostname", gMachineName)
    self.SafeCall(self.parseMemInfo)

  def getRegistryNumSubKeys(self, key, subkey):
    try:
      import winreg
      key = getattr(_winreg, key)
      handle = winreg.OpenKey(key, subkey)
      return winreg.QueryInfoKey(handle)[0]
    except:
      self.gLogStr += "Failed to find " + str(key) + ", " + str(subkey) + ", " + str(value) + "\n"
      return "Unknown"

  def getRegistryValue(self, key, subkey, value):
    try:
      import winreg
      key = getattr(_winreg, key)
      handle = winreg.OpenKey(key, subkey)
      (result, type) = winreg.QueryValueEx(handle, value)
      return result
    except:
      self.gLogStr += "Failed to find " + str(key) + ", " + str(subkey) + ", " + str(value) + "\n"
      return "Unknown"

  def getWindowsRam(self):
    try:
      from psutil import virtual_memory

      mem = virtual_memory()
      memGb =  mem.total * 0.000000001

      return str(memGb) + " Gb"
    except:
      return "unable to import psutil - memory information disabled"

  def RunCmdWin(cmd):
    import subprocess
    process = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    process.stdin.close()
    output = ""
    while line != "":
      line = process.stdout.readline()
      output += line
    return output

  def getWindowsL2Cache(self):
    output = RunCmdWin("wmic cpu get L2CacheSize")
    return output.split("\n")[-1]

  def getWindowsOSVersion(self):
    def get(key):
      return self.getRegistryValue("HKEY_LOCAL_MACHINE", "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", key)
    os = get("ProductName")
    sp = get("CSDVersion")
    build = get("CurrentBuildNumber")
    return "%s %s (build %s)" % (os, sp, build)

  def getWindowsMachineName(self):
   return self.getRegistryValue("HKEY_LOCAL_MACHINE",
                                "SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName",
                                "ComputerName")
  def initWin(self):
    import ctypes
    self._standardDict[gOS] = "win"
    self._standardDict[gCPUType] = self.getRegistryValue("HKEY_LOCAL_MACHINE", "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", "ProcessorNameString")
    self._standardDict[gCPUSpeed] = self.getRegistryValue("HKEY_LOCAL_MACHINE", "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", "~MHz")
    self._standardDict[gNumCores] = self.getRegistryNumSubKeys("HKEY_LOCAL_MACHINE", "HARDWARE\\DESCRIPTION\\System\\CentralProcessor")
    self._standardDict[gRAM] = self.SafeCall(self.getWindowsRam)
    self._standardDict[gRAM] =  ConvertMemSizeToKb(self._standardDict[gRAM])
    self._standardDict[gOSVersion] = self.SafeCall(self.getWindowsOSVersion)
    self._standardDict[gL2Cache] = self.SafeCall(self.getWindowsL2Cache)
    self._standardDict[gMachineName] = self.SafeCall(self.getWindowsMachineName)

  def MapDictionaries(self, originalDict, addTo, mapping, name):
    for i in mapping:
      try:
        addTo[i[1]] = originalDict[0][i[0]]
      except:
        self.gLogStr += "Failed to find key: " + i[0] + " in " + name + "\n"
        addTo[i[1]] = "Unknown"

  def initMac(self):
    """Initialises the object for mac - relies on system_profiler being in the path"""
    self._standardDict[gOS] = "mac"
    import tempfile
    (handle, tmpPList) = tempfile.mkstemp()
    try:
      os.close(handle)
      status = RunCmdWithTimeout("system_profiler -xml > " + tmpPList, 300.0)
      self.SafeCall(self.initMacFromFile, tmpPList)
    finally:
      os.remove(tmpPList)

  def initMacHardware(self, itemDicts):
    mapping = [["current_processor_speed", gCPUSpeed],
               ["physical_memory", gRAM],
               ["number_processors", gNumCores],
               ["cpu_type", gCPUType],
               ["l2_cache", gL2Cache]]

    self.MapDictionaries(itemDicts, self._standardDict, mapping, "SPHardwareDataType")
    if self._standardDict[gL2Cache] == "Unknown":
      fixMacChangingThingsMapping = [["l2_cache_share", gL2Cache]]
      self.MapDictionaries(itemDicts, self._standardDict, fixMacChangingThingsMapping, "SPHardwareDataType")
    self._standardDict[gCPUSpeed] = ConvertSpeedUnitsToMhZ(self._standardDict[gCPUSpeed])
    self._standardDict[gL2Cache] =  ConvertMemSizeToKb(self._standardDict[gL2Cache])
    self._standardDict[gRAM] =  ConvertMemSizeToKb(self._standardDict[gRAM])
    extendedMapping = [["boot_rom_version", gBootROMVersion],
                       ["machine_model", gMachineName]]
    self.MapDictionaries(itemDicts, self._extendedDict, extendedMapping, "SPHardwareDataType")

  def initMacSoftware(self, itemDicts):
    mapping = [["os_version", gOSVersion],
               ["kernel_version", gKernelVersion],
               ["local_host_name", gMachineName]]
    self.MapDictionaries(itemDicts, self._standardDict, mapping, "SPSoftwareDataType")

  def printDict(self, pDict, handle, indentLevel = 1):
    """
    outputs the elements from pDict in XML structure, nesting when an
    element contains another dict
    """
    for key in sorted(pDict):
      elem = pDict[key]
      handle.write("  " * indentLevel)
      if type(elem) == dict: #nest
        handle.write("<%s>\n" % key)
        self.printDict(elem, handle, indentLevel +1, isEnv=True)
        handle.write("  " * indentLevel)
        handle.write("</%s>" % key)
      else: #bottom level, just write the value of the key
        if type(elem) == str or type(elem) == str:
          elem = elem.encode('UTF-8')
        #if isinstance(elem, str):
        #  elem = elem.replace(u"\u001B", "")
        try:
          for badch in "<>&": #make sure anything with these is escaped, so XML doesn't screw up
            if badch in str(elem) and not str(elem).startswith("<![CDATA"):
              elem = "<![CDATA[\n%s\n]]>" % elem
            for c in str(elem):
              if ord(c) > 128:
                raise UnicodeDecodeError
          handle.write("<%(key)s>%(elem)s</%(key)s>" % {
            "key": xml.sax.saxutils.escape(key),
            "elem": elem
            })
        except UnicodeDecodeError as e:
            handle.write("<%(key)s>[--- unicode decoding problem ---]</%(key)s>" % {"key": key})
      handle.write("\n")

  def printXML(self, file, indentLevel = 1):
    self.printDict(self._standardDict, file, indentLevel);

def PrintMachineInfoToFile(file, indentLevel = 1):
  info = HardwareInfo()
  info.printXML(file, indentLevel)

