# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import re
import nuke
import nukescripts

def execute_panel(_list, exceptOnError = True):
  # If we're called by Tcl, _list is actually a string with nodes names that
  # are space separated.
  if type(_list) is str:
    nodes = [nuke.toNode(x) for x in _list.split()]
  else:
    nodes = _list
  return nukescripts.showExecuteDialog(nodes, exceptOnError)

