# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import re
import os.path
import nuke
import nukescripts

prev_inrange = ""
prev_userrange = ""

def flipbook(command, node, framesAndViews = None):
  """Runs an arbitrary command on the images output by a node. This checks
  to see if the node is a Read or Write and calls the function directly
  otherwise it creates a temporary Write, executes it, and then calls
  the command on that temporary Write, then deletes it.

  By writing your own function you can use this to launch your own
  flipbook or video-output programs.

  Specify framesAndViews as a tuple if desired, like so: ("1,5", ["main"])
  This can be useful when running without a GUI."""

  if nuke.env['nc'] and command == nukescripts.framecycler_this:
    raise RuntimeError("Framecycler is not available in NC mode.")

  global prev_inrange
  global prev_userrange

  if node is None or (node.Class() == "Viewer" and node.inputs() == 0): return

  a = int( nuke.numvalue(node.name()+".first_frame") )
  b = int( nuke.numvalue(node.name()+".last_frame") )
  if a < b:
    a = int( nuke.numvalue("root.first_frame") )
    b = int( nuke.numvalue("root.last_frame") )

  try:
    inrange= str( nuke.FrameRange(a, b, 1) )
  except ValueError as e:
    # In this case we have to extract from the error message the
    # correct frame range format string representation.
    # I'm expecting to have a error like: "Frame Range invalid (-1722942,-1722942)"

    msg = e. __str__()
    inrange = msg[ msg.index("(")+1:  msg.index(")") ]

  same_range = (inrange == prev_inrange)
  prev_inrange = inrange

  if same_range:
    inrange = prev_userrange

  if framesAndViews is None:
    r = nuke.getFramesAndViews(label = "Frames to flipbook:", default = inrange, \
                               maxviews = 1)
    if r is None: return
  else:
    r = framesAndViews

  range_input = r[0]
  views_input = r[1]

  prev_userrange = range_input

  f = nuke.FrameRange( range_input )

  start =f.first()
  end = f.last()
  incr = f.increment()

  if (start) < 0 or (end<0):
    raise RuntimeError("Flipbook cannot be executed, negative frame range not supported(%s)." % ( str(f),) )

  proxy = nuke.toNode("root").knob("proxy").value()

  if (node.Class() == "Read" or node.Class() == "Write") and not proxy:
    try:
      command(node, start, end, incr, views_input)
    except Exception as msg:
      nuke.message("Error running flipbook:\n%s" % (msg,))
    return

  if node.Class() == "Viewer":
    input_num = int(nuke.knob(node.name()+".input_number"))
    input = node.input(input_num)
    if input is None: return

    if (input.Class() == "Read" or input.Class() == "Write") and not proxy:
      try:
        command(input, start, end, incr, views_input)
      except Exception as msg:
        nuke.message("Error running flipbook:\n%s" % (msg,))
      return

  # okay now we must execute it...
  flipbooktmp=""
  if flipbooktmp == "":
    try:
      flipbooktmp = os.environ["FC_DISK_CACHE"]
    except:
      try:
        flipbooktmp = os.environ["NUKE_DISK_CACHE"]
      except:
        flipbooktmp = nuke.value("preferences.DiskCachePath")

  if len(views_input) > 1:
    flipbookFileNameTemp = "nuke_tmp_flip.%04d.%V.rgb"
  else:
    flipbookFileNameTemp = "nuke_tmp_flip.%04d.rgb"
  flipbooktmp = os.path.join(flipbooktmp, flipbookFileNameTemp)

  if nuke.env['WIN32']:
    flipbooktmp = re.sub("\\\\", "/", str(flipbooktmp))

  fieldname="file"
  if proxy:
    fieldname="proxy"

  write = nuke.createNode("Write", fieldname+" {"+flipbooktmp+"} "+"tile_color 0xff000000", inpanel = False)
  #If called on a Viewer connect Write node to the one immediately above if exists.
  input = node
  if node.Class() == "Viewer":
    input = node.input(int(nuke.knob(node.name()+".input_number")))
  write.setInput(0, input)

  try:
    # Throws exception on render failure
    nuke.executeMultiple((write,), ([start,end,incr], ), views_input)
    command(write, start, end, incr, views_input)
  except Exception as msg:
    nuke.message("Flipbook render failed:\n%s" % (msg,))
  nuke.delete(write)
