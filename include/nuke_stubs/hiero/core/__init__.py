# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from core import *
from _fnpython import getPluginPath, pluginPath
from . import util
from . import log
import threading
import _fnpython
from . import events
from . import find_plugins
from . import find_startup_projects
from . import deprecated
from . import FnAddClipToSequence

from .find_items import (findItems,
                        findItemsInProject,
                        findItemsInBin,
                        findProjectTags,
                        findItemByGuid,
                        findItemsByGuid)
from .localisation_helpers import *


def filenameList(directory, splitSequences=False, returnDirectories=True, returnHiddenFiles=True):
  """hiero.core.filenameList(directory, splitSequences, returnDirectories, returnHiddenFiles) -> Returns a list of strings representing the items found in the specified directory, putting image sequences together as one element.
  
  @param directory: path to the directory to query
  
  @param splitSequences: optional, defaults to False. If set to True, then splits broken image sequences up. Otherwise, broken sequences create only one entry in the returned list
  
  @param returnDirectories: optional, defaults to True. If set to True, sub directories will be included in the returned list
  
  @param returnHiddenFiles: optional, defaults to True. If set to True, hidden/system files will be returned in the list
  
  For a directory with the following items:
  item1.txt
  item2.txt
  quicktime.mov
  highres1.dpx

  You'd get a tuple with the same list of items (txt files are recognized as not being image sequences).

  With a directory with the following items:
    * quicktime.mov
    * highres1.dpx
    * highres2.dpx
    * highres3.dpx
    * highres4.dpx
    * highres5.dpx

  You'd get a tuple with:
  ("quicktime.mov", "highres#.dpx 1-4")

  If you had the following in a directory:
    * highres1.dpx
    * highres2.dpx

    * highres4.dpx
    * highres5.dpx

  Note the missing 3 in the above list.
  If you set splitSequences to False, you'd get:
  ("highres#.dpx 1-5")

  If instead you set splitSequences to True, you'd get:
  ("highres#.dpx 1-3", "highres#.dpx 4-5")

  If you had a directory with this:
    * highres001.dpx
    * highres002.dpx
    * highres003.dpx
    * highres004.dpx
    * highres005.dpx

  You'd get a tuple like this:
  ("highres###.dpx 1-5")

  If you had a directory with this:
    * highres99.dpx
    * highres100.dpx

  You'd get this:
  ("highres#.dpx 99-100")

  In the above example, the sequence number crosses over from 2 digits to 3, so it is treated as one and the number of hashes (#) is put to 1, which means the number is wild.

  If instead you had a directory with this:
    * highres099.dpx
    * highres100.dpx

  You'd get this:
  ("highres###.dpx 99-100")

  Note that in this last example, the 99 is prefixed with 0."""
  # We have to expose getFilenameList so that we can call it here, and it's defined on the hiero.core.module
  # meaning it's exposed to users, but it's not very friendly.
  # It has parameters that make no sense and are not optional.
  # So instead, we define this method here to wrap it up.
  # The False parameter below is to tell the FileManager whether or not to retrieve the extra information on files, such as the last modification date and file size.
  # Since this method just returns a list of strings, it's a completely unnecessary parameter.
  # It wasn't removed because I was worried someone, somewhere was still using it.
  return getFilenameList(directory, splitSequences, False, returnDirectories, returnHiddenFiles)

# We only have a GUI version at the moment
GUI = True

def presetProjects():
  """hiero.core.projects() -> returns a tuple of all of the currently loaded preset projects.\n\n
  @deprecated: Use hiero.core.projects(Project.kStartupProjects) instead\n
  @return: tuple of hiero.core.Project objects"""
  # Print deprecated warning:
  log.info( "hiero.core.presetProjects is DEPRECATED. Use hiero.core.projects(Project.kStartupProjects) instead" )
  # Old presetProjects would just return a tuple containing only the Hiero Project. Imitate this behaviour here:
  startup = projects(Project.kStartupProjects)
  if len(startup) > 0:
    return (startup[0],)
  else:
    return ()

# Functions for parallel threads to run stuff that can only be
# in the main thread.
__main_thread_lock = threading.Lock()
__main_thread_event = threading.Event()

def executeInMainThreadWithResult(call, *args, **kwargs):
  """ Execute the callable 'call' with optional arguments 'args' and named arguments 'kwargs' in
      the main thread and wait for the result.
      Note that this method expects a single item for args or a tuple, and a dictionary for kwargs.
      It will not accept anything else.
      
      Examples of how to use this method (that work):
        
      def someMethod(firstParameter, kwArg0=None, kwArg1=None)
        print( firstParameter )
        return kwArg1
        
      result = executeInMainThreadWithResult(someMethod, "First positional parameter")
      result = executeInMainThreadWithResult(someMethod, "First positional parameter", {'kwArg0': "arg0"})
      result = executeInMainThreadWithResult(someMethod, ("First positional parameter", "kwArg0 passed as positional parameter"))
      result = executeInMainThreadWithResult(someMethod, ("First positional parameter", "kwArg0 passed as positional parameter"), {'kwArg1': "arg1 as well"})
      result = executeInMainThreadWithResult(someMethod, "First positional parameter", {'kwArg1': "arg1"})
      
      An example of what won't work:
        
      result = executeInMainThreadWithResult(someMethod, "First positional parameter", "Second positional parameter")
      
      The above fails because the second parameter to executeInMainThread must be a dictionary.
  """
  import types
  if type(args) != tuple:
    args = (args,)
  __main_thread_lock.acquire()
  _fnpython.RunInMainThread.request(call, args, kwargs, __main_thread_event)
  __main_thread_event.wait()
  try:
    r = _fnpython.RunInMainThread.result()
  finally:
    __main_thread_event.clear()
    __main_thread_lock.release()
  return r

'''
# The following is as yet untested, and I don't like the name (it's too verbose)
def executeInMainThreadWithResultVariableArgs(call, *args, **kwargs):
  if not args:
    args = ()
  else:
    # the non _ variants of this method only accept tuples. Awesome, right?
    args = (x for x in args)
  if not kwargs:
    kwargs = {}
  return executeInMainThreadWithResult(call, args, kwargs)'''

def executeInMainThread(call, *args, **kwargs):
  """ Execute the callable 'call' with optional arguments 'args' and named arguments 'kwargs' in
      the main thread and return immediately.
      Note that this method expects a single item for args or a tuple, and a dictionary for kwargs.
      It will not accept anything else.
      
      Examples of how to use this method (that work):
        
      def someMethod(firstParameter, kwArg0=None, kwArg1=None)
        print( firstParameter )
        
      executeInMainThread(someMethod, "First positional parameter")
      executeInMainThread(someMethod, "First positional parameter", {'kwArg0': "arg0"})
      executeInMainThread(someMethod, ("First positional parameter", "kwArg0 passed as positional parameter"))
      executeInMainThread(someMethod, ("First positional parameter", "kwArg0 passed as positional parameter"), {'kwArg1': "arg1 as well"})
      executeInMainThread(someMethod, "First positional parameter", {'kwArg1': "arg1"})
      
      An example of what won't work:
        
      executeInMainThread(someMethod, "First positional parameter", "Second positional parameter")
      
      The above fails because the second parameter to executeInMainThread must be a dictionary.
  """
  import types
  if type(args) != tuple:
    args = (args,)
  __main_thread_lock.acquire()
  _fnpython.RunInMainThread.request(call, args, kwargs)
  __main_thread_lock.release()

'''
# The following is as yet untested, and I don't like the name (it's too verbose)
def executeInMainThreadVariableArgs(call, *args, **kwargs):
  if not args:
    args = ()
  else:
    # the non _ variants of this method only accept tuples. Awesome, right?
    args = (x for x in args)
  if not kwargs:
    kwargs = {}
  executeInMainThread(call, args, kwargs)'''

# List of extensions for known QuickTime/ffmpeg formats
QuickTimeExtensions = [".mov", ".m4v", ".mp4", ".m4a", ".m4p", ".m4b", ".m4r", ".mpg", ".mpeg", ".avi"]

# List of extensions for all video media formats which Nuke must read at frame 1 or later (not frame zero)
# TODO This list is duplicated in hrox_convert.py and the C++ code. Should be cleaned up
NonZeroStartFrameMovieFileExtensions = QuickTimeExtensions + [".mxf"]

# List of extensions for all video media formats, not image sequences
VideoFileExtensions = NonZeroStartFrameMovieFileExtensions + [".r3d"]

def isQuickTimeFileExtension(fileExtension):
  """Returns True if the fileExtension is a recognised QuickTime extension, False otherwise."""
  fileExtension = fileExtension.lower()
  if not fileExtension.startswith("."):
    fileExtension = "." + fileExtension
  return fileExtension in QuickTimeExtensions

def isVideoFileExtension(fileExtension):
  """Returns True if the fileExtension is a recognised video format extension, i.e not an image Sequence (QuickTime/MXF/R3D media)"""
  fileExtension = fileExtension.lower()
  if not fileExtension.startswith("."):
    fileExtension = "." + fileExtension
  
  isVideoFileExtension = False
  if fileExtension in VideoFileExtensions:
    isVideoFileExtension = True
  return isVideoFileExtension

from . import FnNukeHelpers

def _projectSetting ( project, func ):
  try:
    return func()
  except Exception as e:
    raise e

def  _Project_extractSettings (self):
  """self.extractSettings() -> returns a dict of the project's settings. \
  \
  @return: dict
  """
  # Build dictionary of project settings
  projectsettings = {
      'lutSettingViewer'           : _projectSetting(self, self.lutSettingViewer),
      'lutSetting8Bit'             : _projectSetting(self, self.lutSetting8Bit),
      'lutSetting16Bit'            : _projectSetting(self, self.lutSetting16Bit),
      'lutSettingLog'              : _projectSetting(self, self.lutSettingLog),
      'lutSettingFloat'            : _projectSetting(self, self.lutSettingFloat),
      'lutSettingWorkingSpace'     : _projectSetting(self, self.lutSettingWorkingSpace),
      'lutUseOCIOForExport'        : _projectSetting(self, self.lutUseOCIOForExport),
      'ocioConfigPath'             : _projectSetting(self, self.ocioConfigPath),
      'ocioConfigName'             : _projectSetting(self, self.ocioConfigName),
      'useOCIOEnvironmentOverride' : _projectSetting(self, self.useOCIOEnvironmentOverride)
  }
  
  return projectsettings
  
Project.extractSettings = _Project_extractSettings

# ApplicationSettings setValue takes strings, but we often use it with Qt stuff, which returns QStrings, and causes a crash if not cast.
# So we override it here so that we can pass QStrings and other things along
def overrideApplicationSettingsSetValue():
  oldSetValue = ApplicationSettings.setValue
  def setValueOverride(self, name, value):
    """self.setValue(key, value) -> saves the value with the application's settings using the key
  
    @param key: string name of the value to save
  
    @param value: the value to store"""
    name = str(name)
    if type(value) is bool:
      self.setBoolValue(name, value)
    else:
      oldSetValue(self, name, str(value))
  ApplicationSettings.setValue = setValueOverride
  
  oldGetValue = ApplicationSettings.value
  def getValueOverride(self, name, defaultValue=None):
    """self.value(key, defaultValue=None) -> returns the previously stored string value named by the key parameter, or the defaultValue parameter
    
    @param key: string name of the value to retrieve
    @param defaultValue: the value to return if this setting hasn't been saved before. Does not save the value to the default
    @return: string, unless the defaultValue is set, in which case, the return value will be the same type as the defaultValue (string, int or bool)"""
    name = str(name)
    if defaultValue != None:
      if type(defaultValue) is bool:
        return self.boolValue(name, defaultValue)
      elif type(defaultValue) is int:
        return int(oldGetValue(self, name, str(defaultValue)))
      elif type(defaultValue) is float:
        return float(oldGetValue(self, name, str(defaultValue)))
      return oldGetValue(self, name, str(defaultValue))
    return oldGetValue(self, name)
  ApplicationSettings.value = getValueOverride

overrideApplicationSettingsSetValue()


def defaultFrameRates():
  '''hiero.core.defaultFrameRates() -> returns the list of frame rates displayed in Hiero's user interface.
  
  @return: tuple of floats'''
  return (8.0,10.0,12.0,12.5,15.0,23.98,24.0,25.0,29.97,30.0,50.0,59.94,60.0)

def _setFindMethods():
  def sequences(self, partialName=None):
    '''self.sequences(partialName) -> returns all sequences in a project. User can filter by by partial name.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.
  @return: an array of hiero.core.Sequence objects.

  Example: finds all sequences in a project with 30Sec in the name:
  
  sequences = myProject.sequences('30Sec')
  '''

    return findItemsInProject(self, filter=Sequence, partialName=partialName)
  
  Project.sequences = sequences
  
  def bins(self, partialName=None):
    '''self.bins(partialName) -> returns all bins in a project. Searches recursively, so will return bins within other bins in the list.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.Bin objects.

  Example: finds all bins in a project with MyBin in the name:
  
  bins = myProject.bins('MyBin')
  '''

    return findItemsInProject(self, filter=Bin, partialName=partialName)
  
  Project.bins = bins
  
  def clips(self, partialName=None):
    '''self.clips(partialName) -> returns all clips in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.Clip objects.

  Example: finds all clips in a project with 30Sec in the name:
  
  clips = myProject.clips('30Sec')
  '''

    return findItemsInProject(self, filter=Clip, partialName=partialName)

  Project.clips = clips

  def tracks(self, partialName=None):
    '''self.tracks(partialName) -> returns all tracks in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.VideoTrack and hiero.core.AudioTrack objects.

  Example: finds all tracks in a project with 30Sec in the name:
  
  tracks = myProject.tracks('30Sec')
  '''

    return findItemsInProject(self, filter="Tracks", partialName=partialName)

  Project.tracks = tracks

  def videoTracks(self, partialName=None):
    '''self.videoTracks(partialName) -> returns all video tracks in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.VideoTrack objects.

  Example: finds all video tracks in a project with 30Sec in the name:
  
  tracks = myProject.videoTracks('30Sec')
  '''

    return findItemsInProject(self, filter=VideoTrack, partialName=partialName)

  Project.videoTracks = videoTracks

  def audioTracks(self, partialName=None):
    '''self.audioTracks(partialName) -> returns all audio tracks in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.AudioTrack objects.

  Example: finds all audio tracks in a project with 30Sec in the name:
  
  tracks = myProject.audioTracks('30Sec')
  '''

    return findItemsInProject(self, filter=AudioTrack, partialName=partialName)

  Project.audioTracks = audioTracks

  def trackItems(self, partialName=None):
    '''self.trackItems(partialName) -> returns all track items in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.TrackItem objects.

  Example: finds all track items in a project with 30Sec in the name:
  
  trackItems = myProject.trackItems('30Sec')
  '''

    return findItemsInProject(self, filter="TrackItems", partialName=partialName)

  Project.trackItems = trackItems

  def videoTrackItems(self, partialName=None):
    '''self.videoTrackItems(partialName) -> returns all video track items in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.TrackItem objects.

  Example: finds all video track items in a project with 30Sec in the name:
  
  trackItems = myProject.videoTrackItems('30Sec')
  '''

    items = findItemsInProject(self, filter=TrackItem, partialName=partialName)
  
    return [x for x in items if x.mediaType() == TrackItem.MediaType.kVideo]

  Project.videoTrackItems = videoTrackItems

  def audioTrackItems(self, partialName=None):
    '''self.audioTrackItems(partialName) -> returns all audio track items in a project.
  @param partialName: optional string with partial name to match against. Will match if this string is anywhere in the name.

  @return: an array of hiero.core.TrackItem objects.

  Example: finds all audio track items in a project with 30Sec in the name:
  
  trackItems = myProject.audioTrackItems('30Sec')
  '''

    items = findItemsInProject(self, filter=TrackItem, partialName=partialName)
  
    return [x for x in items if x.mediaType() == TrackItem.MediaType.kAudio]

  Project.audioTrackItems = audioTrackItems


# set up our find methods
_setFindMethods()

deprecated.markDeprecated()


def __TrackItem_unlinkAll(self):
  """
  self.unlinkAll() -> Unlink all track items that are linked to this one.
  """
  # Only unlink TrackItems, effects should be left
  for linkedItem in [ item for item in  self.linkedItems() if isinstance(item, TrackItem) ]:
    try:
      self.unlink(linkedItem)
    except:
      pass

TrackItem.unlinkAll = __TrackItem_unlinkAll


# For consistency with regular TrackItems, give EffectTrackItem name() and setName() methods,
# which pass through to the name of the node they own.  This is easier to achieve in Python,
# so do it here.

def __EffectTrackItem_name(self):
  """
  self.name() -> Get the name of the effect's node.

  @return: string
  """
  return self.node().name()


def __EffectTrackItem_setName(self, name):
  """
  self.setName() -> Set the name of the effect's node.
  """
  self.node().setName(name)

EffectTrackItem.name = __EffectTrackItem_name
EffectTrackItem.setName = __EffectTrackItem_setName


def __VideoTrack_addMethods():
  def createEffect( self,
                    effectType=None,
                    cloneFrom=None,
                    copyFrom=None,
                    trackItem=None,
                    timelineIn=None,
                    timelineOut=None,
                    subTrackIndex=None):
    """
    self.createEffect(trackItem=None, timelineIn=None, timelineOut=None, subTrackIndex=None) -> Create an effect item and add it to the track.

    The effect's node will be of type effectType or if cloneFrom is given, will be a clone of that.  It will use timing either based on trackItem if given or timelineIn and timelineOut.  If none of these are specified,
    the effect will cover the full duration of the track's parent sequence.

    @param effectType: the node type to create a soft effect for

    @param cloneFrom: if given, the new effect item will be cloned from this

    @param copyFrom: if given, the new effect item will be copied from this

    @param trackItem: if specified, the effect will be linked to the track item and use the same timing

    @param timelineIn: the effect start time

    @param timelineOut: the effect end time

    @param subTrackIndex: if specified, will be placed on the appropriate sub-track, otherwise will be placed on a new sub-track

    @return: the created EffectTrackItem object
    """

    if not effectType and not cloneFrom and not copyFrom:
      raise RuntimeError("No effect type or existing effect to clone from specified.")

    # If a TimeWarp is being created, it must be linked to a track item.  Check this and raise an exception
    if effectType == "TimeWarp" and not trackItem:
      raise RuntimeError("TimeWarp effects must be linked to a TrackItem")

    # If track item was given, use the timing from that
    if trackItem:
      timelineIn, timelineOut = trackItem.timelineIn(), trackItem.timelineOut()

    # If times were not given, use the full sequence duration
    if timelineIn is None:
      timelineIn = 0
    if timelineOut is None:
      timelineOut = self.parent().duration()-1

    # If no index given, check for collisions on the top sub-track.  If none are found, use that,
    # otherwise create a new sub-track
    if subTrackIndex is None:
      subTrackItems = self.subTrackItems()
      if subTrackItems:
        subTrackIndex = len(subTrackItems)-1
        for item in subTrackItems[-1]:
          if item.timelineIn() <= timelineOut and item.timelineIn()+item.duration() > timelineIn:
            subTrackIndex = len(subTrackItems)
            break
          elif item.timelineIn() > timelineOut:
            break
      else:
        subTrackIndex = 0

    if cloneFrom:
      if cloneFrom.project() != self.project():
        raise RuntimeError("Can only clone from effects which belong to the same project.")

      assert not copyFrom and not effectType, "Only one of effectType, cloneFrom or copyFrom can be specified."

      effect = cloneFrom.clone()
      effect.setTimelineOut(timelineOut)
      effect.setTimelineIn(timelineIn)
    elif copyFrom:
      assert not cloneFrom and not effectType, "Only one of effectType, cloneFrom or copyFrom can be specified."

      effect = copyFrom.copy()
      effect.setTimelineOut(timelineOut)
      effect.setTimelineIn(timelineIn)
    else:
      assert not copyFrom and not cloneFrom, "Only one of effectType, cloneFrom or copyFrom can be specified."

      effect = EffectTrackItem(effectType, timelineIn, timelineOut)

    self.addSubTrackItem(effect, subTrackIndex)
    return effect

  VideoTrack.createEffect = createEffect

__VideoTrack_addMethods()


# Wrapper around the Bin.createClip and BinItem.createClipVersion methods defined 
# in C++. This is to allow arbitrary knob values to be given as keyword args 
# rather than having to explicitly construct a dict

def __createClip_wrapper(func):
  def wrapper(self, *args, **knobs):
    # Convert all values to strings as expected by the C++ bindings
    knobs = { k : str(v) for k, v in knobs.items() }
    return func(self, *args, knobs=knobs)
  wrapper.__doc__ = func.__doc__
  wrapper.__name__ = func.__name__
  return wrapper

Bin.createClip = __createClip_wrapper(Bin.createClip)
BinItem.createClipVersion = __createClip_wrapper(BinItem.createClipVersion)


# Registers a callback to be notified when a sequence output format is changed
from . import FnSequenceFormatHandler

# Application logic run after a project is loaded
from . import FnOnProjectLoad

from .nuke.Script import getBundledNukePath, getBundledPythonPath
# the following are Hiero/Studio only things, check if the exports feature is enabled
if 'exports' in env['Features']:
  from .FnResolveTable import ResolveTable
  from .FnExporterBase import (TaskBase,
                              TaskPresetBase,
                              TaskPreset,
                              RenderTaskPreset,
                              TaskGroup,
                              TaskData,
                              FolderTask,
                              FolderTaskPreset)
  from .FnProcessor import ProcessorBase, ProcessorPreset
  from .FnExportRegistry import TaskRegistry, taskRegistry
  from .FnExportStructure import ExportStructure2, ExportStructureElement

