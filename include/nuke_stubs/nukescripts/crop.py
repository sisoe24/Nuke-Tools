# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
from . import nodes

def autocrop(first=None, last=None, inc=None, layer="rgba"):
  """Run the CurveTool's AutoCrop function on each selected node over the
  specified frame range and channels. If the range values are None, the
  project first_frame and last_frame are used; if inc is None, 1 is used.
  After execution, the CurveTool AutoCrop results are copied into a Crop
  node attached to each selected node."""

  # Sort out execute range
  root = nuke.root()
  if first is None:
    first = int(root.knob("first_frame").value())
  if last is None:
    last = int(root.knob("last_frame").value())
  if inc is None:
    inc = 1

  # Remember original set of selected nodes...we'll need this
  original_nodes = nuke.selectedNodes()

  # Deselect everything so we can add CurveTool nodes
  all_nodes = nuke.allNodes()
  for i in all_nodes:
    i.knob("selected").setValue(False)

  for i in original_nodes:
    # Reselect originally selected nodes and create a CurveTool node,
    # which will automatically connect to the last selected.
    i.knob("selected").setValue(True)
    autocropper = nuke.createNode("CurveTool",
      '''operation 0 ROI {0 0 input.width input.height} Layer %s label "Processing Crop..." selected true''' % (str(layer), ), False)

    # Execute the CurveTool node thru all the frames
    nuke.executeMultiple([autocropper,], ([first, last, inc],))

    # select the curvewriter
    autocropper.knob("selected").setValue(True)

    # add crop node
    cropnode = nuke.createNode("Crop", "label AutoCrop", False)

    # put the new data from the autocrop into the new crop
    cropbox = cropnode.knob("box");
    autocropbox = autocropper.knob("autocropdata");
    cropbox.copyAnimations(autocropbox.animations())

    # turn on the animated flag
    cropnode.knob("indicators").setValue(1)

    # deselect everything
    all_nodes = nuke.allNodes()
    for j in all_nodes:
      j.knob("selected").setValue(False)

    # select the curvewriter and delete it
    autocropper.knob("selected").setValue(True)

    # delete the autocropper to make it all clean
    nodes.node_delete()

    # deselect everything
    all_nodes = nuke.allNodes()
    for j in all_nodes:
      j.knob("selected").setValue(False)

    # select the new crop
    cropnode.knob("selected").setValue(True)

    # place it in a nice spot
    nuke.autoplace(cropnode)

    # De-Select it
    cropnode.knob("selected").setValue(False)
