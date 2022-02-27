# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.
# -*- coding: utf-8 -*-

import nuke
import os


def import_boujou():
  '''
  Nuke 5.0 Py import_boujou. Demonstrates the use of addKnob.

  Function called from the "import Boujou camera track" user knob of a
  Boujou Camera gizmo.

  read data from a Boujou text file:
  format is: FRAME TX TY TZ RX RY RZ VFOV
  this version will read fewer columns

  modified by Frank Rüter June 30th 2006 to work with Nuke 4.5

  Instead of writing out an obj like the old version this one creates
  lowres cylinders for each point found in your boujou export. Those
  are stuffed into a group which is hooked up to a render node along
  with the resulting camera.  It has size, colour and render
  parameters to control those proxies.  Keep in mind that there is a
  limit for scene nodes of 1000 inputs so try to keep your point
  export from Boujou below that ;).
  '''
  # call a panel that asks the user for the camera txt file
  try:
    filename = nuke.getFilename("Boujou Text File", "*.txt")

    # create the camera if one is not selected
    newCam = nuke.selectedNode();
    if newCam.Class() != "Camera":
      newCam = nuke.Camera()

    newCam.knob("label").setValue("BoujouCamera\n"+filename)
    file = open(filename, "r")
    for line in file:
      pass

  except:
    pass


def import_script():
  try:
    if nuke.env['nc']:
      spec = "*.nk; *.nknc; *.gizmo; *.gznc"
    elif nuke.env['indie']:
      spec = "*.nk; *.nkind; *.gizmo; *.gzind"
    else:
      spec = "*.nk; *.gizmo"
    s = nuke.getFilename("Import Script", spec, "", "script")
    nuke.nodePaste(s)
  except:
    pass


def export_nodes_as_script():
  try:
    if nuke.env['nc']:
      nukeExt = ".nknc"
    elif nuke.env['indie']:
      nukeExt = ".nkind"
    else:
      nukeExt = ".nk"
    s = nuke.getFilename("Export Nodes As Script", "*" + nukeExt, "", "script", "save", extension=nukeExt)
    if s is not None:
      nuke.nodeCopy(s)
  except:
    pass

