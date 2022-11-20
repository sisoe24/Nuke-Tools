# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import math
import os
import os.path
import re

import hiero.core
import hiero.core.util
import hiero.core.log

from . import FnShotExporter


class FrameExporter(FnShotExporter.ShotTask):
  """ Base class for exporters which want to process individual files from clips.
  The name is somewhat misleading because it's used for processing files, not frames,
  which are only the same thing for clips with frame sequences
  """
  def __init__( self, initDict ):
    """Initialize"""
    FnShotExporter.ShotTask.__init__( self, initDict )

    self._paths = [] # List of (srcPath, dstPath) tuples
    self._currentPathIndex = 0

    if not self._source.isMediaPresent() and self._skipOffline:
      return

    if self._source.singleFile():
      self._buildVideoClipPaths()
    else:
      self._buildFileSequencePaths()

  def _buildVideoClipPaths(self):
    """ Build the list of src/dst paths for video clips. """
    srcPath = self._source.fileinfos()[0].filename()

    # If the source is r3d, include 'associated files' which covers sequences
    # of r3d files, and rmd sidecar files.
    includeAssociatedFiles = srcPath.lower().endswith(".r3d")
    if includeAssociatedFiles:
      srcPaths = [srcPath] + self._source.associatedFilePaths()
      # For each source file, temporarily replace the _filename variable which is used
      # for resolving the destination path
      for srcPath in srcPaths:
        tmp = self._filename
        self._filename = os.path.basename(srcPath)
        self._paths.append( (srcPath, self.resolvedExportPath()) )
        self._filename = tmp
    else:
      self._paths.append( (srcPath, self.resolvedExportPath()) )


  def _buildFileSequencePaths(self):
    """ Build the list of src/dst paths for each frame in a file sequence """
    start = self._clip.sourceIn()
    end = self._clip.sourceOut()
    # If exporting just the cut
    if self._cutHandles is not None:
      handles = self._cutHandles

      if self._retime:
        # Compensate for retime
        handles *= abs(self._item.playbackSpeed())

      # Ensure _start <= _end (for negative retimes, sourceIn > sourceOut)
      sourceInOut = (self._item.sourceIn(), self._item.sourceOut())
      start = min(sourceInOut)
      end = max(sourceInOut)

      # This accounts for clips which do not start at frame 0 (e.g. dpx sequence starting at frame number 30)
      # We offset the TrackItem's in/out by clip's start frame.
      start += self._clip.sourceIn()
      end += self._clip.sourceIn()

      # Add Handles
      start = max(start - handles, self._clip.sourceIn())
      end   = min(end + handles, self._clip.sourceOut())

    # Make sure values are integers
    start = int(math.floor(start))
    end = int(math.ceil(end))

    srcPath = hiero.core.util.HashesToPrintf(self._source.fileinfos()[0].filename())
    dstPath = hiero.core.util.HashesToPrintf(self.resolvedExportPath())
    dstFrameOffset = self._startFrame - start if self._startFrame is not None else 0
    for srcFrame in range(start, end+1):
      srcFramePath = srcPath % srcFrame
      dstFrame = srcFrame + dstFrameOffset
      dstFramePath = self.formatFrameNumbers(dstPath, dstFrame, 1)
      self._paths.append( (srcFramePath, dstFramePath) )

  def nothingToDo(self):
    return len(self._paths) == 0

  def startTask(self):
    pass

  def preFrame(self, src, dst):
    pass

  def doFrame(self, src, dst):
    pass
      
  def postFrame(self, src, dst):
    pass

  def formatFrameNumbers(self, string, frame, count=None):
    """Recursively split a string and modify with the % operation to replace the frame index.\n"""
    """@param count is the maximum number of replaces to do"""
    pos = string.rfind("%")
    if pos != -1 and (count > 0 or count is None):
      return self.formatFrameNumbers( string[:pos], frame, count -1) + string[pos:] % (frame, )
    return string

  def taskStep(self):
    FnShotExporter.ShotTask.taskStep(self)

    if self._currentPathIndex < len(self._paths):
      srcPath, dstPath = self._paths[self._currentPathIndex]
      self.preFrame(srcPath, dstPath)
      self.doFrame(srcPath, dstPath)
      self.postFrame(srcPath, dstPath)
      self._currentPathIndex += 1
      return True
    else:
      return False
    
  def progress(self):
    if self.nothingToDo():
      return 1.0
    return float(self._currentPathIndex) / float(len(self._paths))
