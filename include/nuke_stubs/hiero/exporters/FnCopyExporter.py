# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import os
import sys
import shutil

import hiero.core
from hiero.core import util
from . import FnFrameExporter


class CopyExporter(FnFrameExporter.FrameExporter):
  def __init__( self, initDict ):
    """Initialize"""
    FnFrameExporter.FrameExporter.__init__( self, initDict )
    if self.nothingToDo():
      return

  def _tryCopy(self,src, dst):
    """Attempts to copy src file to dst, including the permission bits, last access time, last modification time, and flags"""

    hiero.core.log.info("Attempting to copy %s to %s" % (src, dst))
    
    try:
      shutil.copy2(util.asUnicode(src), util.asUnicode(dst))
    except shutil.Error as e:
      # Dont need to report this as an error
      if e.message.endswith("are the same file"):
        pass
      else:
        self.setError("Unable to copy file. %s" % e.message)
    except OSError as err:
      # If the OS returns an ENOTSUP error (45), for example when trying to set
      # flags on an NFS mounted volume that doesn't support them, Python should
      # absorb this.  However, a regression in Python 2.7.3 causes this not to
      # be the case, and the error is thrown as an exception.  We therefore
      # catch this explicitly as value 45, since errno.ENOTSUP is not defined
      # in Python 2.7.2 (which is part of the problem).  See the following
      # link for further information: http://bugs.python.org/issue14662
      # See TP 199072.
      if err.errno == 45: # ENOTSUP
        pass
      else:
        raise

  def doFrame(self, src, dst):
    hiero.core.log.info( "CopyExporter:" )
    hiero.core.log.info( "  - source: " + str(src) )
    hiero.core.log.info( "  - destination: " + str(dst) )

    # Find the base destination directory, if it doesn't exist create it
    dstdir = os.path.dirname(dst)
    util.filesystem.makeDirs(dstdir)

    # Copy file including the permission bits, last access time, last modification time, and flags
    self._tryCopy(src, dst)


class CopyPreset(hiero.core.TaskPresetBase):
  def __init__(self, name, properties):
    hiero.core.TaskPresetBase.__init__(self, CopyExporter, name)
    # Set any preset defaults here
    # self.properties()["SomeProperty"] = "SomeValue"
    
    # Update preset with loaded data
    self.properties().update(properties)

  def supportedItems(self):
    return (hiero.core.TaskPresetBase.kTrackItem | hiero.core.TaskPresetBase.kClip) | hiero.core.TaskPresetBase.kAudioTrackItem


hiero.core.taskRegistry.registerTask(CopyPreset, CopyExporter)
