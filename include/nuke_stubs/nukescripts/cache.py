# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

def cache_clear(args = None):
  """
  Clears the buffer memory cache by calling nuke.memory("free")
  If args are supplied they are passed to nuke.memory as well
  eg. nuke.memory( "free", args )
  """
  if args is not None and len(args) > 0:
    nuke.memory("free", args)
  else:
    nuke.memory("free")

def cache_report(args = None):
  """
  Gets info on memory by calling nuke.memory("info")
  If args are supplied they are passed to nuke.memory as well
  eg. nuke.memory( "info", args )
  """
  if args is not None and len(args) > 0:
    return nuke.memory("info", args)
  else:
    return nuke.memory("info")

def clearAllCaches():
  """
  Clears all caches. The disk cache, viewer playback cache and memory buffers.
  """
  nuke.clearDiskCache()
  nuke.clearRAMCache()
  nuke.clearBlinkCache()
  cache_clear()
