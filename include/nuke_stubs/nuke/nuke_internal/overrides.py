# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import sys, types, _nuke, os, re


def pluginAddPath(args, addToSysPath = True):
  """ Adds all the paths to the beginning of the Nuke plugin path.
      If the path already exists in the list of plugin paths, it is moved
      to the start. If this command is executed inside an init.py then
      the init.py in the path will be executed.
      It also adds the paths to the sys.path, if addToSysPath is True."""
  if type(args) != tuple and type(args) != list:
    args = [args]

  # Trim any trailing slashes or backslashes from the path, because they confuse python
  args = [re.sub(r"[/\\]+$", "", arg) for arg in args]
  # Remove any empty strings from the list
  args = [arg for arg in args if arg]

  # Nuke does it's own resolution of relative filenames, so that they end up
  # relative to the right location. Rather than duplicating that logic here,
  # we just get the difference between the pluginPath before and after we've
  # added the new paths.

  if addToSysPath:
    oldPluginPath = tuple(_nuke.pluginPath())

  for i in args:
    _nuke.pluginAddPath(i)

  if addToSysPath:
    newPaths = [ p for p in _nuke.pluginPath() if p not in oldPluginPath ]
    for path in newPaths:
      if path not in sys.path:
        sys.path.insert(0, path)


def pluginAppendPath(args, addToSysPath = True):
  """ Add a filepath to the end of the Nuke plugin path.  If the path
      already exists in the list of plugin paths, it will remain at its
      current position.
      It also appends the paths to the sys.path, if addToSysPath is True."""
  if type(args) != tuple and type(args) != list:
    args = [args]

  # Nuke does it's own resolution of relative filenames, so that they end up
  # relative to the right location. Rather than duplicating that logic here,
  # we just get the difference between the pluginPath before and after we've
  # added the new paths.

  if addToSysPath:
    oldPluginPath = tuple(_nuke.pluginPath())

  for i in args:
    _nuke.pluginAppendPath(i)

  if addToSysPath:
    newPaths = [ p for p in _nuke.pluginPath() if p not in oldPluginPath ]
    for path in newPaths:
      if path not in sys.path:
        sys.path.append(path)


def dependencies(nodes, what = _nuke.INPUTS | _nuke.HIDDEN_INPUTS | _nuke.EXPRESSIONS | _nuke.LINKINPUTS):
  """ List all nodes referred to by the nodes argument. 'what' is an optional integer (see below).
  You can use the following constants or'ed together to select the types of dependencies that are looked for:
  \t nuke.EXPRESSIONS = expressions
  \t nuke.LINKINPUTS = link knob inputs
  \t nuke.INPUTS = visible input pipes
  \t nuke.HIDDEN_INPUTS = hidden input pipes.
  The default is to look for all types of connections.
  \nExample:
  n1 = nuke.nodes.Blur()
  n2 = nuke.nodes.Merge()
  n2.setInput(0, n1)
  deps = nuke.dependencies([n2], nuke.INPUTS | nuke.HIDDEN_INPUTS | nuke.EXPRESSIONS)"""

  if type(nodes) != tuple and type(nodes) != list:
    nodes = [nodes]

  deps = []
  for i in nodes: deps += i.dependencies(what)
  seen = set()
  deps = [i for i in deps if i not in seen and not seen.add(i)]

  return deps

def dependentNodes(what = _nuke.INPUTS | _nuke.HIDDEN_INPUTS | _nuke.EXPRESSIONS | _nuke.LINKINPUTS, nodes = [], evaluateAll = True):
  """ List all nodes referred to by the nodes argument. 'what' is an optional integer (see below).
  You can use the following constants or'ed together to select what types of dependent nodes are looked for:
  \t nuke.EXPRESSIONS = expressions
  \t nuke.LINKINPUTS = link knob inputs
  \t nuke.INPUTS = visible input pipes
  \t nuke.HIDDEN_INPUTS = hidden input pipes.
  The default is to look for all types of connections.

  evaluateAll is an optional boolean defaulting to True. When this parameter is true, it forces a re-evaluation of the entire tree.
  This can be expensive, but otherwise could give incorrect results if nodes are expression-linked.

  \nExample:
  n1 = nuke.nodes.Blur()
  n2 = nuke.nodes.Merge()
  n2.setInput(0, n1)
  ndeps = nuke.dependentNodes(nuke.INPUTS | nuke.HIDDEN_INPUTS | nuke.EXPRESSIONS, [n1])

  @param what: Or'ed constant of nuke.EXPRESSIONS, nuke.LINKINPUTS, nuke.INPUTS and nuke.HIDDEN_INPUTS to select the types of dependent nodes. The default is to look for all types of connections.
  @param evaluateAll: Specifies whether a full tree evaluation will take place. Defaults to True.
  @return: List of nodes. """

  if type(nodes) != tuple and type(nodes) != list:
    nodes = [nodes]

  deps = []
  for i in nodes:
    deps += i.dependent(what, forceEvaluate = evaluateAll)
    evaluateAll = False
  seen = set()
  deps = [i for i in deps if i not in seen and not seen.add(i)]

  return deps

def selectConnectedNodes():
  """ Selects all nodes in the tree of the selected node. """
  allDeps = set()
  depsList = [_nuke.selectedNode()]
  evaluateAll = True
  while depsList:
    deps = dependencies(depsList, _nuke.INPUTS | _nuke.HIDDEN_INPUTS)
    deps += dependentNodes(_nuke.INPUTS | _nuke.HIDDEN_INPUTS, depsList, evaluateAll)
    evaluateAll = False
    depsList = [i for i in deps if i not in allDeps and not allDeps.add(i)]

  for i in allDeps: i['selected'].setValue(True)

