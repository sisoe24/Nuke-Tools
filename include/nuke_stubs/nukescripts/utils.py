# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
from nuke_internal import executeInMainThread
from nuke_internal import executeInMainThreadWithResult

def executeDeferred(call, args = (), kwargs = {}):
  executeInMainThread(call, args, kwargs)

def findNextNodeName(name):
  i = 1
  while nuke.toNode ( name + str(i) ) != None:
    i += 1

  return name + str(i)
