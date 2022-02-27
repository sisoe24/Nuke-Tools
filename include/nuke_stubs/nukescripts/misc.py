# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
import nukescripts
import random
import os
import textwrap


def copy_knobs(args):
  thisGroup = nuke.thisGroup()

  if( thisGroup is not nuke.root() and ( thisGroup.locked() or thisGroup.subgraphLocked() ) ):
    raise RuntimeError("Can't paste knob values because " + thisGroup.name() + " is locked")

  selNodes = thisGroup.selectedNodes()

  groupCopy = nuke.nodes.Group(name = "____tempcopyknobgroup__")
  with groupCopy:
    nuke.nodePaste(nukescripts.cut_paste_file())

  excludedKnobs = ["name", "xpos", "ypos"]

  try:
    nodes = groupCopy.nodes()
    for i in groupCopy.nodes():
      for j in selNodes:
        k1 = i.knobs()
        k2 = j.knobs()
        intersection = dict([(item, k1[item]) for item in list(k1.keys()) if item not in excludedKnobs and item in k2])
        for k in list(intersection.keys()):
          x1 = i[k]
          x2 = j[k]
          x2.fromScript(x1.toScript())
  except Exception as e:
    nuke.delete(groupCopy)
    raise e
  nuke.delete(groupCopy)


def connect_selected_to_viewer(inputIndex):
  """Connects the selected node to the given viewer input index, ignoring errors if no node is selected."""

  selection = None
  try:
    selection = nuke.selectedNode()
  except ValueError:  # no node selected
    pass

  if selection is not None and selection.Class() == 'Viewer':
    selection = None

  nuke.connectViewer(inputIndex, selection)


def toggle_monitor_out():
  """Toggles monitor out (switches it on if it's off, or vice versa) for the currently active viewer."""
  viewer = nuke.activeViewer()
  if viewer is not None:
    enableKnob = nuke.toNode('MonitorOutNode').knob("enable")
    enableKnob.setValue(not enableKnob.value())


def clear_selection_recursive(group = nuke.root()):
  """Sets all nodes to unselected, including in child groups."""
  for n in group.selectedNodes():
    n.setSelected(False)
  groups = [i for i in group.nodes() if i.Class() == 'Group']
  for i in groups:
    clear_selection_recursive(i)


def goofy_title():
  """Returns a random message for use as an untitled script name.
  Can be assigned to nuke.untitled as a callable.
  Put a goofy_title.txt somewhere in your NUKE_PATH to customise."""

  goofyFile = None
  for dir in nuke.pluginPath():
      fileName = os.path.join(dir, "goofy_title.txt")
      if os.path.exists(fileName):
          goofyFile = fileName
          break

  if goofyFile is None:
      return "Missing goofy_title.txt"

  file = open(goofyFile)
  lines = file.readlines()
  file.close()

  lines = [line.strip() for line in lines]
  lines = [line for line in lines if len(line) > 0 and line[0] != '#']

  if len(lines) < 1:
    return "Empty goofy_title.txt"

  return random.choice(lines)


def declone(node):
  if node.clones() == 0:
    return
  args = node.writeKnobs(nuke.WRITE_ALL | nuke.WRITE_USER_KNOB_DEFS | nuke.WRITE_NON_DEFAULT_ONLY | nuke.TO_SCRIPT)
  newnode = nuke.createNode(node.Class(), knobs = args)
  nuke.inputs(newnode, nuke.inputs(node))
  num_inputs = nuke.inputs(node)
  for i in range(num_inputs):
     newnode.setInput(i, node.input(i))
  node.setInput(0, newnode)
  nuke.delete(node)


def showname():
  '''Shows the current script path and, if the selected node is a Read or Write node, the filename from it.'''

  # get the nuke script path
  # we always need this
  nukescript = nuke.value("root.name")

  # look if there is a selected node
  # if not, output the script only
  p = nuke.Panel("Current Info", 500)
  try:
    n = nuke.selectedNode()
    if n.Class() == "Read" or n.Class() == "Write":
      a = nuke.value(n.name()+".first", nuke.value("root.first_frame"))
      b = nuke.value(n.name()+".last", nuke.value("root.last_frame"))
      curfile = n.knob("file").value()+" "+str(a)+"-"+str(b)
      p.addSingleLineInput("Filename", curfile)
      p.addSingleLineInput("Script", nukescript)
      p.show()
    else:
      p.addSingleLineInput("Script", nukescript)
      p.show()
  except:
    p.addSingleLineInput("Script", nukescript)
    p.show()


def swapAB(n):
  """Swaps the first two inputs of a node."""
  thisGroup = nuke.thisGroup()
  if thisGroup is not nuke.root() and ( thisGroup.locked() or thisGroup.subgraphLocked() ) :
    lockedReason = "published" if thisGroup.subgraphLocked() else "locked"
    raise RuntimeError("Can't swap nodes because " + thisGroup.name() + " is " + lockedReason)

  if max(n.inputs(), n.minimumInputs()) > 1:
    a = n.input(0)
    n.setInput(0, n.input(1))
    n.setInput(1, a)


def print_callback_info(verbose=False, callbackTypes=None):
  """
  Returns a list of all currently active callbacks, with the following optional
  arguments:
      verbose=False      : prints the documentation as well as the callback
      callbackTypes=None : limit the callback info to a particular callback
                           type (e.g. ['OnCreates'])
  """
  # list of all callback types
  all_Callback_Types = [ 'onUserCreates',
                         'onCreates',
                         'onScriptLoads',
                         'onScriptSaves',
                         'onScriptCloses',
                         'onDestroys',
                         'knobChangeds',
                         'updateUIs',
                         'autolabels',
                         'beforeRenders',
                         'beforeFrameRenders',
                         'afterRenders',
                         'afterFrameRenders',
                         'renderProgresses',
                         'filenameFilters',
                         'validateFilenames',
                         'autoSaveFilters',
                         'autoSaveRestoreFilters',
                         'autoSaveDeleteFilters',
                      ]

  #if no callbackTypes defined or is an invalid type, then default search all callback types
  is_valid_type = (type(callbackTypes) is dict) or (type(callbackTypes) is list)
  if ( not callbackTypes or (not is_valid_type ) ):
    callbackTypes = all_Callback_Types

  callback_defs = {}

  for callbackType in callbackTypes:
    callback_defs[callbackType] = eval('nuke.%s' %(callbackType))

  # find the max target name length
  maxTargetNameLen = max( list(map( len,' '.join( [ (k+'').join( list(callback_defs[k].keys()) ) for k in list(callback_defs.keys()) ] ).split(' ') )) )

  indent = (maxTargetNameLen+8)*' '

  sortedCallbackTypes = sorted( callback_defs.keys() )
  for callbackType in sortedCallbackTypes:
    for callbackTarget in list(callback_defs[callbackType].keys()):
      for func, a, b, c in callback_defs[callbackType][callbackTarget]:
        id = '%s%s%s : '%(callbackType[:-1],'_'*(maxTargetNameLen-len(callbackType)-len(callbackTarget)+1),callbackTarget)
        print('%s%s' %(id, func.__name__))
        if verbose:
          doc = func.__doc__
          if not doc:
            doc='NO DOCUMENTATION'
          docNoReturns = str(doc).lstrip().replace('\n','')
          docNoConsecutiveSpaces = " ".join(docNoReturns.split())
          docWrappedText = textwrap.wrap(docNoConsecutiveSpaces, 60)
          for line in docWrappedText:
            print(indent + line.replace('\n', '\n' + indent))

