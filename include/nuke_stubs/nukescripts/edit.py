# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

# cut the current node and then paste a copy after every other node.
# This was a throb invention, not sure how useful it is.

import nuke
import nukescripts

# Edit menu
def cut_paste_file():
	return "%clipboard%"

def node_copypaste():
  nuke.nodeCopy(cut_paste_file())
  nodes = nuke.allNodes();
  for i in nodes:
    i.knob("selected").setValue(False)
  nuke.nodePaste(nukescripts.cut_paste_file())

def remove_inputs():
  thisGroup = nuke.thisGroup()
  if thisGroup is not nuke.root() and ( thisGroup.locked() or thisGroup.subgraphLocked() ) :
    lockedReason = "published" if thisGroup.subgraphLocked() else "locked"
    raise RuntimeError("Can't remove input because " + thisGroup.name() + " is " + lockedReason)

  nodes = nuke.selectedNodes()
  for i in nodes:
    for j in range(i.inputs()): i.setInput(j, None)

def extract():
  """Disconnect all arrows between selected and unselected nodes, and move selected nodes to the right.
  This function is maintained only for compatibility.  Please use nuke.extractSelected() instead."""
  nuke.extractSelected()

def branch():
  thisGroup = nuke.thisGroup()
  if thisGroup is not nuke.root() and ( thisGroup.locked() or thisGroup.subgraphLocked() ) :
    lockedReason = "published" if thisGroup.subgraphLocked() else "locked"
    raise RuntimeError("Can't branch because " + thisGroup.name() + " is " + lockedReason)
    
  top_node = None
  selnodes = nuke.selectedNodes()
  for i in selnodes:
    totalinputs = i.inputs()
    for j in range(totalinputs):
      if i.input(j).knob("selected").value() is False:
        top_node = i.input(j)

  if top_node is None: return

  nuke.nodeCopy(nukescripts.cut_paste_file())
  nuke.nodePaste(nukescripts.cut_paste_file())

  firstpastenode = None

  selnodes = nuke.selectedNodes()
  for i in selnodes:
    firstpastenode = i
    xpos = i.knob("xpos").value()
    i.knob("xpos").setValue(xpos+80)

  if firstpastenode is not None:
    firstpastenode.setInput(0, top_node)

