# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import hiero.core
import sys
import os.path
import subprocess
import PySide2.QtCore
import _fnpython
import nuke_internal as nuke
import platform
from hiero.core import util
from hiero.core.util import asUnicode


class NodeLayoutContext(object):
  """ Class to assist with grouping nodes for layout purposes.
      May have nested child contexts and a list of nodes.
      Each context is initialised with a type, which can be used to decide the layout strategy,
      a name, which is used for to uniquely identify the context and for labelling purposes (unless a separate label is given,
      and arbitrary other data which can be used for determining the layout. """

  def __init__(self, type='', name='', **data):
    self._type = type
    self._name = name
    self._children = []
    self._nodes = []
    self._data = data


  def addChild(self, child):
    """ Add a child context. """
    self._children.append(child)


  def getChildren(self):
    """ Get the list of child contexts. """
    return self._children


  def __addNode(self, node):
    """ Internal function for adding a node.  Checks if the object actually is a node. """
    if node.isNode():
      self._nodes.append(node)


  def addNode(self, node):
    """ Add a node or a sequence of nodes. """
    if hasattr(node, "__iter__"):
      for n in node:
        self.__addNode(n)
    else:
      self.__addNode(node)


  def getNodes(self):
    """ Get the nodes added to this context. """
    return self._nodes


  def getType(self):
    """ Get the context type. """
    return self._type


  def getName(self):
    """ Get the context name. """
    return self._name


  def getLabel(self):
    """ Get the context label.  Returns the 'label' data if it was given, otherwise the name. """
    label = self.getData("label")
    if not label:
      label = self._name
    return label


  def getData(self, key):
    """ Try to retrieve extra data given to the context.  Returns the data, or None
        if it was not set. """
    try:
      return self._data[key]
    except:
      return None



class ScriptWriter:
  def __init__(self):
    self._nodes = []
    self._nodeOutput = ""

    # Initialise the layout context stack
    self._layoutContextStack = []
    self._layoutContextStack.append( NodeLayoutContext("main") )
    
  def _postProcessNodes(self):

    # We may have created PostageStamp nodes to replace Read nodes if had multiple Read nodes referencing
    # the same source footage.
    # If we did this, we need to make sure inputs are connected properly - this needs to be done using 
    # the tcl set and push commands. 
    # Due to the way Nuke's script parsing works, all of the set commands (associated with the Read nodes) need to 
    # go above the push commands (associated with the PostageStamp nodes.
    # To achieve this we'll now post-process the script to emulate what Nuke's script saving does, which is to place 
    # any nodes which need a set above the other nodes. We've already added an associated push into the script for each 
    # Read, which marks the node's original position so will stay where it is, so everything should still connect up properly

    # We will search for the Push node associated with a Read, then check that the 2 previous nodes are Read and Set.
    # These nodes will then be moved to the start.
    newNodes = []
    readInsertPosition = 0
    # User nodes at the top of the script are disconneced, we need to skip over them until we hit something which is
    # not Root, Backdrop or User Node (probably a Read or PostageStamp)
    nonNodeTreeNodes = True

    for node in self._nodes:
      isBackdrop = isinstance(node, hiero.core.nuke.BackdropNode)
      isRoot = isinstance(node, hiero.core.nuke.RootNode)
      isDisconnectedUserNode= isinstance(node, hiero.core.nuke.UserDefinedNode) and nonNodeTreeNodes

      if isBackdrop or isRoot or isDisconnectedUserNode:
        # Keep the RootNode at the start, as well as any Backdrop nodes (as before)
        # and user defined nodes, which may be disconnected
        readInsertPosition += 1
      else:
        # We have hit a node which is not the root, backdrop or disconnecetd user nodes.
        # All subsequent user nodes should be conneceted to a read or postage stamp in some way
        nonNodeTreeNodes = False

      # Check the type of the last 2 added nodes
      if len(newNodes) > 1:
        hasSet = isinstance(newNodes[-1],  hiero.core.nuke.SetNode)
        hasRead = isinstance(newNodes[-2],  hiero.core.nuke.ReadNode)
      else:
        hasSet = False
        hasRead = False

      if isinstance(node, hiero.core.nuke.PushNode) and hasSet and hasRead:
        # This is the Push associated with a Read. Move the Read and its set to the start
        set = newNodes.pop()
        newNodes.insert(readInsertPosition, set)

        read = newNodes.pop()
        newNodes.insert(readInsertPosition, read)

        # Leave the Push in its original position
        newNodes.append(node)
      else:
        # Just copy the node across
        newNodes.append(node)

    self._nodes = newNodes
      

  def __repr__(self):
    # post process the script to add anything extra in
    self._postProcessNodes()

    # Dealing with non-ascii is a bit tricky here.  Ideally we'd use unicode strings everywhere, only choosing an encoding when actually
    # writing the file, but that's a significant amount of work.  So, self._nodeOutput is a utf-8 string, and fileContents is unicode, which is
    # then encoded as utf-8.  This seems very hacky, but it was the only way I could figure out to stop Python from complaining.
    
    # create the script
    fileContents = str()
    for node in self._nodes:
      # reset our node output
      self._nodeOutput = ""
      
      # serialize out the node, using ourself to catch the node and knob settings
      node.serialize(self)

      # add the per node output to our final output
      fileContents += asUnicode(self._nodeOutput)

    return fileContents
  
  def addNode(self, node):
    if node is None:
      raise RuntimeError("Attempting to add None as a node.")
    if hasattr(node, "__iter__"):
      self._nodes.extend(node)
    else:
      self._nodes.append(node)

    # Add the node(s) to the current layout context
    self._layoutContextStack[-1].addNode(node)


  def getNodes(self):
    return self._nodes

    
  def writeToDisk(self, scriptFilename):
    # Find the base destination directory, if it doesn't exist create it
    dstdir = os.path.dirname(scriptFilename)
    util.filesystem.makeDirs(dstdir)

    # Delete any existing file
    if util.filesystem.lexists(scriptFilename):
      util.filesystem.remove(scriptFilename)
      
    # create the script
    fileContents = str(self)

    # Then write the file
    nuke.saveToScript( scriptFilename, fileContents )

  
  ############################################################################################
  # Methods that allow this object to be sent to the serialize method of KnobFormatter objects
  ############################################################################################
  
  def beginSerializeNode(self, nodeType):
    self._nodeOutput += nodeType + " { \n"
  
  def endSerializeNode(self):
    self._nodeOutput += "}\n"
  
  def serializeKnob(self, knobType, knobValue):
    self._nodeOutput += " " + knobType + " "

    # Special case for "inputs" with a value of "2+1". the quotes shouldn't be there, 
    # but are the only way to prevent setKnob evaluating 2+1 as 3. (They need to be
    # serialised as 2+1, since that what Nuke expects for the Merge node if something's
    # connected to the Mask input.
    noQuotes = False
    if knobType == "inputs" and knobValue == "2+1":
      noQuotes = True

    # knobValue sometimes comes in as unicode, make sure it's converted to utf-8
    if isinstance(knobValue, str) and \
      not knobValue.startswith('{') and \
      not knobValue.startswith('"') and \
      not noQuotes:
      self._nodeOutput += '"' + knobValue + '"'
    else:
      self._nodeOutput += asUnicode(knobValue)
    self._nodeOutput += "\n"
  
  def serializeKnobs(self, knobValues):
    for (key, value) in knobValues.items():
      self.serializeKnob(key, value)
      
  def serializeUserKnob(self, type, knobName, text, tooltip, value, visible):
    # should end looking like this: addUserKnob {2 projectpath l "project path" t "Stores the path to the Hiero project that this node was created with."}
    self._nodeOutput += " addUserKnob {"
    self._nodeOutput += str(type)
    self._nodeOutput += " "
    self._nodeOutput += str(knobName)
    
    if not visible:
      self._nodeOutput += " l INVISIBLE"
    elif text:
      self._nodeOutput += " l \"" + text + "\""
      
    if tooltip:
      self._nodeOutput += " t \"" + tooltip + "\""

    if not visible:
      self._nodeOutput += " +INVISIBLE"
      
    self._nodeOutput += "}\n"
    
    if value is not None:
      # now that we've added the knob definition above, we can just serialize setting the value the same as any other knob
      self.serializeKnob(knobName, value)
      
  def serializeUserKnobs(self, userKnobs):
    # array of (type, knobName, text, tooltip, value)
    for userKnob in userKnobs:
      self.serializeUserKnob(*userKnob)


  def serializeRawKnobs(self, rawKnobs):
    for rawKnob in rawKnobs:
      self._nodeOutput += " " + rawKnob + "\n"

      
  def serializeNode(self, nodeType, knobValues, userKnobs, rawKnobs):
    self.beginSerializeNode(nodeType)
    # Write out the knobs, starting with user knobs.  Any setting of the user
    # knob value needs to come after it was created.
    self.serializeUserKnobs(userKnobs)
    self.serializeKnobs(knobValues)
    self.serializeRawKnobs(rawKnobs)
    self.endSerializeNode()


  def getMainLayoutContext(self):
    """ Get the main layout context for the script. """
    return self._layoutContextStack[0]


  def pushLayoutContext(self, type, name, **data):
    """ Push a layout context to the stack.  Any nodes added to the script will be included in the new
        layout context.  If the current context already has a child with the same type and name, that
        will be used instead of creating a new one. """
    currentContext = self._layoutContextStack[-1]

    # Check if a matching context already exists and if so use it
    for context in currentContext.getChildren():
      if context.getType() == type and context.getName() == name:
        self._layoutContextStack.append(context)
        return

    # Otherwise, create a new context
    newContext = NodeLayoutContext(type, name, **data)
    currentContext.addChild(newContext)
    self._layoutContextStack.append(newContext)


  def popLayoutContext(self):
    """ Pop the current layout context from the stack. """
    self._layoutContextStack.pop()


  
 
def _getNukeExecutable():
  nukePath = sys.executable
  return nukePath

def useBundledNuke():

  settings = hiero.core.ApplicationSettings()

  return not _getBoolSetting(settings, "useCustomNuke", False)


def _bundledNukePath():
  # Get the Nuke exe bundled for NukeStudio.
  appDirPath = PySide2.QtCore.QCoreApplication.applicationFilePath()
  return appDirPath

def hieroNukePath():
  """hiero.core.hieroNukePath() -> returns the HieroNuke executable path which ships with Hiero. DEPRECATED Use getBundledNukePath() instead.

  @return: A string containing the HieroNuke executable path."""
  return getBundledNukePath()

def getBundledNukePath():
  """ hiero.core.getBundledNukePath() -> return the bundled Nuke executable

  @return: A string containing the bundled Nuke executable path."""
  return _bundledNukePath()



def getBundledPythonPath():
  """ hiero.core.getBundledPythonPath() -> return the bundled Python executable

  @return: A string containing the bundled Python executable path."""
  base = os.path.dirname(getBundledNukePath())
  if sys.platform == "win32":
    if nuke.env.get('DEBUG'):
      return os.path.join(base, "python_d.exe")
    return os.path.join(base, "python.exe")
  return os.path.join(base, "python3")


def getRenderOnlyNukeExecutablePath():
  settings = hiero.core.ApplicationSettings()

  useDefault = True
  if not useBundledNuke():
    nukePath = _getNukeExecutable()
    if util.filesystem.exists(nukePath):
      useDefault = False
    else:
      #print "Could not find the custom version of Nuke selected in the Preferences. Defaulting to the built-in version."
      #useDefault = True
      
      # for now, let's not default to the built-in, so that we still have proper errors
      useDefault = False
      
  if useDefault:
    # Get the HieroNuke Path that we ship with Hiero
    nukePath = getBundledNukePath()

  return nukePath

def _getBoolSetting(settings, name, defaultValue):
  ret = settings.value(name, str(defaultValue))
  if (ret == "False") or (ret == "0") or (ret == "false"):
    return False
  return True
  
def useNukeXForInteractive():
  settings = hiero.core.ApplicationSettings()
    
  # if we're using the installed HieroNuke, then force an interactive license, so that it
  # uses the same license as the running Hiero
  return _getBoolSetting(settings, "launchNukeX", False)

def getInteractiveNukeExecutablePath():  
  settings = hiero.core.ApplicationSettings()
  
  # otherwise, use the one specified by setting
  nukePath = _getNukeExecutable()
      
  if not util.filesystem.exists(nukePath):
    raise RuntimeError( "The specified Nuke application path does not exist (\"%s\")." % (nukePath, ) )
  return nukePath

# copied from C++ options in fnStormPreferencesDialog.cpp
RESPONSIVE_UI = 0
FAST_TRANSCODES = 1
USER_CONFIGURATION = 2


def _addNukeLicenseArgs(args):
  if nuke.env['hiero'] and not nuke.env['hieroStudio']:
    args.append("--usehierolicense")
  """ For Studio and Hiero, always specify an interactive license. """
  args.append("-i")
  #if running nc mode, append flag
  if nuke.env["nc"]:
    args.append("--nc")
  #if running Indie mode, append flag
  if nuke.env["indie"]:
    args.append("--indie")


def nukeThreadsMemoryPreferences():
  """ Get the number of threads and memory in MB to be used for Nuke render processes from the application preferences. """
  settings = hiero.core.ApplicationSettings()
  try:
    configSetting = int(settings.value("userConfigureNuke", "0"))
  except:
    configSetting =  0

  numThreads = 0
  memoryInMBs = 0

  systemMemoryInBytes = hiero.core.env["SystemMemory"]

  # Minimal default, use 2 threads and 1/4 of system RAM
  if configSetting == RESPONSIVE_UI:
    numThreads = 2
    memoryInBytes = systemMemoryInBytes / 4
    memoryInMBs = int(memoryInBytes/pow(1024,2))
    # If for some reason, MB value is zero, give it 1GB as a fail-safe, because this is reasonable for a render
    if memoryInMBs <= 0:
      memoryInMBs = 1024

  # Configured by the user
  elif configSetting == USER_CONFIGURATION:
    try:
      memoryInGbs = int(settings.value("nukeCacheMemoryInGbs", "0"))
      memoryInMBs = memoryInGbs * 1024
    except:
      pass

    try:
      numThreads = int(settings.value("nukeNumberOfThreads", "0"))
    except:
      pass

  # FAST_TRANSCODES, don't limit threads and use 1/2 of system RAM
  else:
    memoryInBytes = systemMemoryInBytes / 2
    memoryInMBs = int(memoryInBytes/pow(1024,2))
    numThreads = 0

  return numThreads, memoryInMBs


def openNukeProcess(*args, **kwargs):
  """ Helper function wrap around a Popen call to run Nuke.  On Macs, there
  seems to be a possibility of some output to stderr between the fork and
  exec calls, which results in an error in CoreFoundation because it's attempting
  to redirect the output to the script editor.  Temporarily reset stdout/err
  while calling Popen."""
  try:
    oldStdout = sys.stdout
    oldStderr = sys.stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    return subprocess.Popen(*args, **kwargs)
  finally:
    sys.stdout = oldStdout
    sys.stderr = oldStderr


def executeNukeScript(path, logfile, executeOnSingleSocket = False):
  # Make sure the playback cache is unlocked from memory, otherwise it can interfere with launching Nuke.  See Bug 30188
  _fnpython._unlockPlaybackCacheInMemory()

  nukePath = getRenderOnlyNukeExecutablePath()
  process = None
  
  # Arguments list, first argument is exectubale path
  
  if util.filesystem.exists(nukePath):
    args = []
    if executeOnSingleSocket:
      args.extend(hiero.core.util.singleCPUSocketLaunchArguments())

    args.append(nukePath)
    _addNukeLicenseArgs(args)

    args.append("-x")

    numThreads, memoryInMBs = nukeThreadsMemoryPreferences()

    if numThreads:
      if executeOnSingleSocket:
        # Limit the number of threads to the number of available cores
        numThreads = min(numThreads, hiero.core.util.coresPerCPUSocket())

      args.extend( ["-m", str(numThreads)] )

    if memoryInMBs:
      args.extend( ["-c", "%iM" % memoryInMBs] )

    # Add the script path to the arguments. On Windows, need to get the short
    # path name as otherwise this fails if there are non-ASCII characters in
    # the path. It's not possible to pass unicode to Popen unfortunately.
    if platform.system() == "Windows":
      path = util.filesystem.getShortPathName(path)
    args.append(path)

    return openNukeProcess(args, bufsize=100, shell=False, stdout=logfile, stderr=logfile)
  else:
    raise RuntimeError("No Nuke executable at \"%s\".\n\nThis path can be configured in the 'Nuke / Export' page within the application preferences." % (nukePath,))

def launchNuke(path=None, *extraArgs):
  """
  Launches the version of Nuke specified in Hiero's Nuke/Hiero Preferences, optionally with a Nuke Script, specfied by 'path'.
  
  Extra arguments may also be used by specifying a tuple/list of arguments in 'extraArgs'.
  
  launchNuke automatically checks your Hiero Preference for 'Launch as Nuke X', and also adds a '-q' switch, to stop the Nuke splash screen from appearing.
  
  @param path - (optional) path to a Nuke Script (.nk) file to open.
  @param extraArgs - (optional) list/tuple of additional command line arguments.
  
  @return the subprocess.Popen object for the Nuke instance launched

  """
  # Make sure the playback cache is unlocked from memory, otherwise it can interfere with launching Nuke.
  _fnpython._unlockPlaybackCacheInMemory()

  nukePath = getInteractiveNukeExecutablePath()
  if util.filesystem.exists(nukePath):
    args = [nukePath, "-q"]
    if useNukeXForInteractive():
      args.append("--nukex")
    if path:
      args.append(path)
    if extraArgs:
      args.extend(extraArgs)
    # Set close_fds here, because otherwise the Nuke process inherits any open sockets and this causes bad things to happen with the Hiero-Nuke bridge
    return openNukeProcess(args, shell=False, close_fds=True)
  raise IOError("Nuke Executable Path Not Found!")
