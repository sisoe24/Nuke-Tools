# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import nuke_internal as nuke

class FnPySingleton(object):
  def __new__(type, *args, **kwargs):
    if not '_the_instance' in type.__dict__:
      type._the_instance = object.__new__(type)
    return type._the_instance

def script_directory():

  # Use thisRoot to ensure we're using the root node of the current
  # context (which may or may not be the node graph's global root).
  #
  # This sometimes gets called before the Root node is attached. Fixing this is
  # quite difficult, so handle the exception that results if we try and access
  # the node in this state
  try:
    scriptFilePath = nuke.thisRoot().knob("name").value()
  except ValueError:
    scriptFilePath = None

  if not scriptFilePath:
    return ""

  return os.path.dirname(scriptFilePath)

