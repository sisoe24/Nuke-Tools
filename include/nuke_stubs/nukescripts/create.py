# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
import os

def create_curve():
  root = nuke.toNode("root")
  curve_name = nuke.getInput("New curve name", "f")
  if curve_name is not None:
    if not len(curve_name) > 0:
      nuke.message("Curve name can't be blank.")
    else:
      curve_knob = root.knob(curve_name)
      if curve_knob is None:
        root.addKnob(nuke.Double_Knob(curve_name, curve_name))
        nuke.animation("root."+curve_name, "expression", ("",))


def create_read(defaulttype="Read"):
  '''Create a Read node for a file selected from the file browser.
  If a node is currently selected in the nodegraph and it has a 'file'
  (or failing that a 'proxy') knob, the value (if any) will be used as the default
  path for the file browser.'''
  # Get the selected node, and the path on it's 'file' knob if it
  # has one, or failing that, it's 'proxy' node, if it has that.
  sel_node = None
  default_dir = None
  try:
    sel_node = nuke.selectedNode()
  except:
    pass
  if ( sel_node is not None ) and ( sel_node != '' ):
    if 'file' in sel_node.knobs():
      default_dir = sel_node['file'].value()
    if (default_dir == None or default_dir == '') and 'proxy' in sel_node.knobs():
      default_dir = sel_node['proxy'].value()

  # Revert default_dir to None if it's empty so that the file browser
  # will do it's default unset behaviour rather than open on an empty path.
  if default_dir == '': default_dir = None

  # Raise the file browser and get path(s) for Read node(s).
  files = nuke.getClipname( "Read File(s)", default=default_dir, multiple=True )
  if files != None:
    maxFiles = nuke.numvalue("preferences.maxPanels")
    n = len(files)
    for f in files:
      sceneBrowserRequired = False
      stripped = nuke.stripFrameRange(f)
      nodeType = defaulttype
      if isAudioFilename( stripped ):
        nodeType = "AudioRead"
      if isSceneBrowserFilename( stripped ):
        sceneBrowserRequired = True
      if isGeoFilename( stripped ):
        nodeType = "ReadGeo2"
      if isDeepFilename( stripped ):
        nodeType = "DeepRead"

      # only specify inpanel for the last n nodes. Old panels are kicked out using
      # a deferred delete, so reading large numbers of files can internally build
      # large numbers of active widgets before the deferred deletes occur.
      useInPanel = True
      if (maxFiles != 0 and n > maxFiles):
        useInPanel = False
      n = n-1

      if sceneBrowserRequired:
        nuke.createScenefileBrowser( f, "" )
      else:
        try:
          nuke.createNode( nodeType, "file {"+f+"}", inpanel = useInPanel)
        except RuntimeError as err:
          nuke.message(err.args[0])

def isSceneBrowserFilename(filename):
  filenameLower = filename.lower()
  _, ext = os.path.splitext( filenameLower )
  usd_extensions = ['.usd', '.usda', '.usdz', '.usdc']
  abc_extensions = ['.abc']

  if ext in usd_extensions + abc_extensions:
    return True
  return False

def isGeoFilename(filename):
  filenameLower = filename.lower()
  _, ext = os.path.splitext( filenameLower )

  if ext in ['.fbx', '.obj']:
    return True
  else:
    return False

def isDeepFilename(filename):
  filenameLower = filename.lower()
  _, ext = os.path.splitext( filenameLower )

  if ext in ['.dtex', '.dshd', '.deepshad']:
    return True
  else:
    return False

def isAudioFilename(filename):
  filenameLower = filename.lower()
  _, ext = os.path.splitext( filenameLower )

  if ext in ['.wav', '.wave', '.aif', '.aiff']:
    return True
  else:
    return False

def create_viewsplitjoin():
  views = nuke.views()
  if len(views) < 2:
    nuke.message("Only one view, nothing to split and rejoin.")
    return

  sel = nuke.selectedNode()
  if sel == None:
    nuke.message("You need to select a node to split views from and rejoin.")
    return

  nodes = []
  for i in views:
    n = nuke.createNode("OneView", inpanel=False)
    n.knob("label").setValue(i)
    nodes.append(n)

  selx = sel.knob("xpos").getValue()
  sely = sel.knob("ypos").getValue()

  join = nuke.createNode("JoinViews", inpanel=False)

  for idx in range(0, len(nodes)):
    nodes[idx].knob("view").setValue(idx+1)
    nodes[idx].setInput(0, sel)
    nodes[idx].knob("xpos").setValue(selx + idx * 100 - (len(nodes)-1)*50)
    nodes[idx].knob("ypos").setValue(sely + 90)
    join.setInput(idx, nodes[idx])

  join.knob("xpos").setValue(selx)
  join.knob("ypos").setValue(sely+180)


