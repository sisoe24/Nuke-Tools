"""Utility functions for Hiero."""
import re
import os.path
import sys
import hiero.core
from . import system

_hashre = re.compile(r'(\#+)')
_percentre = re.compile(r'%(\d+)d')
def HashesToPrintf(original):
  """Convert hashes in the given string into printf style notation."""  
  def replace(match):
    if len(match.group())<2:
      return r"%d"
    else:
      return "%%0%dd" % len(match.group())
  return _hashre.sub(replace, original)


def ResizePadding (path, minimum):
  """Return path with padding width increased to minimum size"""
  path = HashesToPrintf(path)
  matches = _percentre.findall(path)
  if matches:
    for match in matches:
      if int(match) < minimum:
        path = path.replace("%%0%sd" % int(match), "%%0%dd" % minimum)
   
  return path
    
def HasFrameIdentifier (path):
  """Returns true if the path contains either ### or %4d notation for the frame identifier"""
  return _percentre.findall(path) or _hashre.findall(path)
    
def GetClipFrameRange(clip, trimmed=True):
  # If the clip has soft trims and trimmed is True, then use that range.
  # Otherwise use the whole clip range.
  fi = clip.mediaSource().fileinfos()[0]
  clipStart = fi.startFrame()
  clipEnd = fi.endFrame()

  if trimmed and clip.softTrimsEnabled():
    start = clipStart + clip.softTrimsInTime()
    end = clipStart + clip.softTrimsOutTime()
  else:
    start = clipStart
    end = clipEnd

  return (start, end)


    
def SequenceifyFilename(filename, addPadding):
  sequenceTypeExtensions = (".dpx", ".jpg", ".jpeg", ".exr", ".tga", ".cin", ".png")
  # Check if this is a frame sequence
  ext = os.path.splitext(filename)[1]
  if ext.lower() in sequenceTypeExtensions:
    lastDot = filename.rfind(".")
    if (lastDot > -1):
      secondLastDot = filename.rfind (".", 0, lastDot)
      if (secondLastDot > -1):
        numDigits = _percentre.findall(filename[secondLastDot:lastDot])
        if numDigits:
          numDigits = numDigits[0]
        else:
          numDigits = lastDot - secondLastDot - 1
          
        newFilename = filename[:secondLastDot] + "." + "#"* int(numDigits) + filename[lastDot:]        
        return newFilename
      elif addPadding:
        base, ext = os.path.splitext(filename)
        filename = base +".####" + ext

  return filename

def uniquify(seq):
  """uniquify(seq)
      Returns a unique, order-preserved list of items in a Python list or tuple.
      Compatible with hashable items such as dicts.
      @param seq: a Python list or sequence.
      @returns: list of unique items.

      Example:\n
      A = ['a', (0,1), [4,'2'], (0,1), 'b', {'foo':1}, 'b', 'a', [4,'2'], {'foo':1}]
      uniquify(A)
      Result: ['a', (0, 1), [4, '2'], 'b', {'foo': 1}]
      """

  uniqueDict = {}
  return [uniqueDict.setdefault(repr(e),e) for e in seq if repr(e) not in uniqueDict]

def uniqueKey( key, dictionary ):
  """uniqueKey (key, dictionary)
    If key clashes in dictionary, add/identify trailing number and increment.
    return new key"""
  assert(hasattr(dictionary, '__contains__'))
  
  # if preset name exists already
  if key in dictionary:
    # isolate name and index
    match = re.match("([\w\s]+?)([0-9]*$)", key)
    fixedName = key
    if match:
      tokens = match.groups()
      key = tokens[0]
      fixedName = key
      if len(tokens[1]):
        index = int(tokens[1])
      else:
        index = 1
      # Increment index until unique name is found
      while fixedName in dictionary:
        fixedName = key + str(index)
        index += 1
      return fixedName
  return key

def version_get(string, prefix, suffix = None):
  """Extract version information from filenames
  These are _v# or /v# or .v# where v is a prefix string, in our case
  we use "v" for render version and "c" for camera track version.
  See the version.py and camera.py plugins for usage."""
  
  if string is None:
    raise ValueError("Empty version string - no match")

  regex = "[/_.]"+prefix+"\d+"
  matches = re.findall(regex, string, re.IGNORECASE)
  if not len(matches):
    msg = "No \"_"+prefix+"#\" found in \""+string+"\""
    raise ValueError(msg)
  return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())

def version_set(string, prefix, oldintval, newintval):
  """Changes version information from filenames
  These are _v# or /v# or .v# where v is a prefix string, in our case
  we use "v" for render version and "c" for camera track version.
  See the version.py and camera.py plugins for usage."""

  regex = "[/_.]"+prefix+"\d+"
  matches = re.findall(regex, string, re.IGNORECASE)
  if not len(matches):
    return ""

  # Filter to retain only version strings with matching numbers
  matches = [s for s in matches if int(s[2:]) == oldintval]

  # Replace all version strings with matching numbers
  for match in matches:
    # use expression instead of expr so 0 prefix does not make octal
    fmt = "%%(#)0%dd" % (len(match) - 2)
    newfullvalue = match[0] + match[1] + str(fmt % {"#": newintval})
    string = re.sub(match, newfullvalue, string)
  return string


def hasMultipleCPUSockets():
  '''
  Return whether this system has multiple CPU sockets.
  '''
  systemInfo = system.SystemInfo()
  return systemInfo.socketCount() > 1


def singleCPUSocketLaunchArguments():
  '''
  Return the arguments required to launch a process that is limited to
  a single CPU. These arguments should be prepended to the command that
  is to be run.
  '''
  systemInfo = system.SystemInfo()
  return systemInfo.singleSocketLaunchArguments()


def coresPerCPUSocket():
  '''
  Return how many cores are availble on a single cpu socket. This assumes that all CPUs on
  a multi CPU system have the same number of cores.
  '''
  systemInfo = system.SystemInfo()
  return systemInfo.coresPerSocket()

def asUnicode(value):
  """ Get value as a unicode string. If the input is bytes, decode it from UTF-8. """
  if isinstance(value, str):
    return value

  if isinstance(value, bytes):
    return value.decode('UTF-8')

  return str(value)

def asBytes(value):
  """ Get value as bytes, encoded as a UTF-8 string if the input was not bytes """
  if isinstance(value, bytes):
    return value
  else:
    return bytes(str(value), 'UTF-8')

def flattenedPathRemappings():
  """ Get a list of path remappings set in the preferences where each entry is a
  tuple of from/to paths appropriate for the current OS """

  # This is a list of mappings where each is specified in terms of platform (win, mac, linux)
  # To get this in a form that can be passed to Nuke on the command line, we just want a set of pairs (fromPath, toPath).
  platformMappings = hiero.core.pathRemappings()

  # First check the platform and determine the index into the platform mappings
  if 'win32' in sys.platform:
    platformIndex = 0
  elif 'darwin' in sys.platform:
    platformIndex = 1
  else:
    platformIndex = 2

  mappings = []

  # For each platform mapping, toPath is given by the platformIndex, the other two are the from paths
  # In the preferences, unset paths are stored as '-'.  Filter those out.
  for platformMapping in platformMappings:
    toPath = platformMapping[platformIndex]
    if toPath and toPath != '-':
      for i in range(1, 3):
        fromPath = platformMapping[(platformIndex+i)%3]
        if fromPath and fromPath != '-':
          mappings.append( (fromPath, toPath) )

  return mappings


def remapPath(path):
  """ Apply remapping preferences to a path and return the remapped path, or if
  no remaps were found, the original path.
  """
  for remapFrom, remapTo in flattenedPathRemappings():
    if path.startswith(remapFrom):
      path = remapTo + path[len(remapFrom):]
      break
  return path


from .pathviews import (findViewInPath, isMultiViewPath, formatMultiViewPath)

# Import this last as it needs access to asUnicode..
from . import filesystem
