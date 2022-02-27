"""The Python interface for RotoPaint

Use help('_rotopaint') to get detailed help on the classes exposed here.
"""

from .curveknob import *

import _rotopaint
from _nuke import Hash


def _convert(fromScript, toScript, overwrite):
  import nuke
  nuke.scriptOpen(fromScript)
  nuke.scriptSaveAs(toScript, overwrite)
  nuke.scriptClose()

def _convertDir(fromDir, toDir, matchPattern, overwrite):
  import os
  import re

  if fromDir == toDir:
    raise RuntimeError("Source and destination directories are the same")
  if not os.path.isdir(fromDir):
    raise RuntimeError("Source not a directory")
  if not os.path.isdir(toDir):
    raise RuntimeError("Destination not a directory")
  if not os.access(toDir, os.W_OK):
    raise RuntimeError("Destination directory is not writable")

  pattern = re.compile(matchPattern)
  for f in os.listdir(fromDir):
    if (re.match(pattern, f)):
      fromScript = os.path.join(fromDir, f)
      toScript = os.path.join(toDir, f)
      print("Converting %s to %s" % (fromScript, toScript))
      _convert(fromScript, toScript, overwrite)

def convertToNuke6(fromScript, toScript, overwrite = False):
  """Convert a script containing NUKE 7 roto in one containing the old format."""
  import os
  # This environment variable makes NUKE write out the old Roto format.
  os.environ["NUKE_CURVE_LONG_FORMAT"] = "1"
  _convert(fromScript, toScript, overwrite)
  # Pop it from the environment so we don't affect other scripts
  os.environ.pop("NUKE_CURVE_LONG_FORMAT")

def convertToNuke7(fromScript, toScript, overwrite = False):
  """Convert a script containing NUKE 6 roto in one containing the new format."""
  import os
  # This environment variable makes NUKE write out the old Roto format so make
  # sure it's disabled.
  if "NUKE_CURVE_LONG_FORMAT" in os.environ:
    os.environ.pop("NUKE_CURVE_LONG_FORMAT")
  _convert(fromScript, toScript, overwrite)

def convertDirectoryToNuke6(fromDir, toDir, matchPattern =".*\.nk", overwrite = False):
  """Convert a directory containing NUKE 7 roto scripts in one containing the old format.
     Note that the pattern is a regular expression."""
  import os
  # This environment variable makes NUKE write out the old Roto format.
  os.environ["NUKE_CURVE_LONG_FORMAT"] = "1"
  _convertDir(fromDir, toDir, matchPattern, overwrite)
  # Pop it from the environment so we don't affect other scripts
  os.environ.pop("NUKE_CURVE_LONG_FORMAT")

def convertDirectoryToNuke7(fromDir, toDir, matchPattern=".*\.nk", overwrite = False):
  """Convert a directory containing NUKE 6 roto scripts in one containing the new format.
     Note that the pattern is a regular expression."""
  import os
  # This environment variable makes NUKE write out the old Roto format so make
  # sure it's disabled.
  if "NUKE_CURVE_LONG_FORMAT" in os.environ:
    os.environ.pop("NUKE_CURVE_LONG_FORMAT")
  _convertDir(fromDir, toDir, matchPattern, overwrite)

