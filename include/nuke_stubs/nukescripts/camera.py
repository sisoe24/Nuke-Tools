# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
import nukescripts
import math


def camera_up():
  """All new camera_up that uses the version_get/set functions.
  This script takes the render camera up one in selected iread/writes.
  Camera may be _c# or _p# for previs camera number"""

  n = nuke.selectedNodes()
  for i in n:
    _class = i.Class()
    if _class == "Read" or _class == "Write":
      name = nuke.filename(i)
      if name is not None:
        (prefix, v) = nukescripts.version_get(name, "[cp]")
        if v is not None:
	      # use expression instead of expr so 0 prefix does not make octal
	      # format result so it has 2 digits
          v = str("%(#)02d" % {"#":int(nuke.expression(v+"+1"))})
          i.knob("file").setValue(nukescripts.version_set(i.knob("file").value(), prefix, v))
          i.knob("proxy").setValue(nukescripts.version_set(i.knob("proxy").value(), prefix, v))
          nuke.modified(True)

def camera_down():
  """All new camera_down that uses the version_get/set functions.
  This script takes the render camera up one in selected iread/writes.
  Camera may be _c# or _p# for previs camera number"""

  camera_up()

def create_camera_here():
  # get selected nodes
  selected_nodes = nuke.selectedNodes()

  # deselect all nodes so the camera doesn't link
  for n in selected_nodes:
    n["selected"].setValue ( False )

  camera = nuke.createNode("Camera3")

  viewer = nuke.activeViewer()

  m = viewer.getGLCameraMatrix()
  t = m.translation()
  p = m.rotationsZXY()

  camera.knob("rotate").setValue(math.degrees(p[0]), 0)
  camera.knob("rotate").setValue(math.degrees(p[1]), 1)
  camera.knob("rotate").setValue(math.degrees(p[2]), 2)

  camera.knob("translate").setValue(t[0], 0)
  camera.knob("translate").setValue(t[1], 1)
  camera.knob("translate").setValue(t[2], 2)
