# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

def groupmake():
  """Builds a group from the current node selection.
  This function is only maintained for backwards compatibility.
  Please use nuke.makeGroup() instead."""
  nuke.makeGroup()
