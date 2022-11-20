# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import os
import sys
import subprocess
import hiero.core
from . import FnFrameExporter


class SymLinkExporter(FnFrameExporter.FrameExporter):
  def __init__( self, initDict ):
    """Initialize"""
    FnFrameExporter.FrameExporter.__init__( self, initDict )
    if self.nothingToDo():
      return

  def doFrame(self, src, dst):
    hiero.core.log.debug( "SymLinkExporter:" )
    hiero.core.log.debug( "  - source: " + src )
    hiero.core.log.debug( "  - destination: " + dst )

    # Find the base destination directory, if it doesn't exist create it
    dstdir = os.path.dirname(dst)
    hiero.core.util.filesystem.makeDirs(dstdir)

    # If the destination file exists, delete it
    if os.path.lexists(dst):
      os.remove(dst)

    # create the sym link
    # Windows (all variants, as far as I know) doesn't have os.symlink
    # so we have to special case for it.
    # Also, as far as I can tell from the interwebs, Python on Windows always returns "win32" for sys.platform, for historical reasons
    # (http://stackoverflow.com/questions/2144748/is-it-safe-to-use-sys-platform-win32-check-on-64-bit-python)
    # So, check first for non-windows platforms and symlink
    if sys.platform != "win32":
      os.symlink(src, dst)
    else:
      srcPath = src.replace('/', '\\')
      dstPath = dst.replace('/', '\\')
      
      # we're on a variant of windows, so use mklink
      # the following assumes we're running on Windows Vista or higher (http://www.howtogeek.com/howto/windows-vista/using-symlinks-in-windows-vista/)
      result = subprocess.Popen(("cmd", "/c", "mklink", "/H", dstPath, srcPath), stdout = subprocess.PIPE, stderr = subprocess.PIPE)
      stdout, stderr = result.communicate()
      
      if stdout is None or "Hardlink created" not in stdout:
        if stderr is not None:
          errorstring = stderr + "\nsrc: " + srcPath + "\ndst: " + dstPath 
          self.setError(errorstring)


class SymLinkPreset(hiero.core.TaskPresetBase):
  def __init__(self, name, properties):
    hiero.core.TaskPresetBase.__init__(self, SymLinkExporter, name)
    # Set any preset defaults here
    # self.properties()["SomeProperty"] = "SomeValue"
    
    # Update preset with loaded data
    self.properties().update(properties)
    

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kTrackItem | hiero.core.TaskPresetBase.kClip

hiero.core.taskRegistry.registerTask(SymLinkPreset, SymLinkExporter)
