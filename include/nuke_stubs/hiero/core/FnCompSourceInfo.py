#!/usr/bin/env python
# -*- coding: utf-8 -*-


from hiero.core import (TrackItem,
                        MediaSource,
                        Clip,
                        remapPath)
import _nuke


def isNukeScript(filename):
  """Returns True if filename ends with .nk (.nk / .nknc for NC)
     (or .nk / .nkind for Nuke Indie)
  """
  if _nuke.env['nc']:
    return filename.endswith(('.nk', '.nknc'))
  elif _nuke.env['indie']:
    return filename.endswith(('.nk', '.nkind'))
  else:
    return filename.endswith('.nk')


class CompSourceInfo(object):
  """ Helper class for getting render information from a comp MediaSource.
  Raises an exception if the expected metadata can't be found.
  Sets the following attributes:
    writePath - The path being rendered to. For multi-view comps which render to %v
                paths, this will be formatted with the first view name
    unexpandedWritePath - For multi-view comps this will contain the render path
                          including any %v placeholders
    firstFrame - the first frame rendered
    lastFrame - the last frame rendered
  """

  # Metadata keys which are added to the MediaSource through nkReader
  kNkWritePathKey = "media.nk.writepath"
  kNkUnexpandedWritePathKey = "media.nk.unexpandedwritepath"
  kNkFirstFrameKey = "media.nk.firstframe"
  kNkLastFrameKey = "media.nk.lastframe"

  def __init__(self, comp):

    # Accept various types and try to get a MediaSource object out of them
    if isinstance(comp, MediaSource):
      self.compSource = comp
    elif isinstance(comp, Clip):
      self.compSource = comp.mediaSource()
    elif isinstance(comp, TrackItem):
      self.compSource = comp.source().mediaSource()
    elif isinstance(comp, str):
      self.compSource = MediaSource(comp)
    else:
      raise RuntimeError("Unexpected type: %s" % type(comp))

    self.nkPath = None
    self.writePath = None
    self.unexpandedWritePath = None
    self.firstFrame = None
    self.lastFrame = None

    try:
      # First check if the source is a comp, then get the render info out of its metadata
      sourcePath = self.compSource.fileinfos()[0].filename()
      if isNukeScript(sourcePath):
        self.nkPath = sourcePath
        metadata = self.compSource.metadata()
        self.writePath = metadata.value(CompSourceInfo.kNkWritePathKey)
        self.writePath = remapPath(self.writePath) # Make sure path remapping is applied

        # Get the unexpanded write path key. This might not exist in projects created
        # before it was added, so fall back to the writePath, which will be the same
        # unless it was a multi-view comp
        try:
          self.unexpandedWritePath = remapPath(metadata.value(CompSourceInfo.kNkUnexpandedWritePathKey))
        except:
          self.unexpandedWritePath = self.writePath

        self.firstFrame = int(metadata.value(CompSourceInfo.kNkFirstFrameKey))
        self.lastFrame = int(metadata.value(CompSourceInfo.kNkLastFrameKey))
    except:
      import traceback
      traceback.print_exc()
      raise RuntimeError("Error retrieving comp info: %s" % self.compSource)

  def isComp(self):
    """ Get if the source is actually a comp. """
    return self.nkPath is not None

  def __str__(self):
    return ("CompSourceInfo(script=%s writePath=%s firstFrame=%s lastFrame=%s)" %
              (self.nkPath, self.writePath, self.firstFrame, self.lastFrame))

