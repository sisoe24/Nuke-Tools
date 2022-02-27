# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke


def color_nodes():
  """Set all selected nodes to be the same colour as the first selected node."""
  n = nuke.selectedNode()
  if n is None:
    nuke.message("No node selected")
    return

  c = n.knob("tile_color")
  c = nuke.getColor(c.value())
  n.knob("tile_color").setValue(c)

  # get other nodes:
  n = nuke.selectedNodes()
  for i in n:
    i.knob("tile_color").setValue(c)
  nuke.modified(True)


def node_delete(popupOnError = False):
  d = nuke.dependentNodes(nuke.EXPRESSIONS | nuke.LINKINPUTS | nuke.HIDDEN_INPUTS, nuke.selectedNodes(), False)
  l = ""
  for i in d:
    if i.Class() != "Viewer":
      l = l + i.fullName() + ", "
  l = l[0:len(l)-2]
  if len(l) > 0:
    if not nuke.ask("The nodes you are deleting are used by expressions in:\n" + l + "\nAre you sure you want to delete?"):
      return
  nuke.nodeDelete(popupOnError)

