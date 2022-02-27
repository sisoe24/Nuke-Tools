# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

def animation_loop():
  p = nuke.Panel("Loop")
  p.addSingleLineInput("First frame of loop:", 1)
  p.addSingleLineInput("Last frame of loop:", nuke.animationEnd())
  result = p.show()
  if result:
    anim = nuke.animations()
    for i in anim:
      loopstart = p.value("First frame of loop:")
      loopend = p.value("Last frame of loop:")
      nuke.animation(i, "expression", ("curve(((frame-"+loopstart+")%("+loopend+"-"+loopstart+"+1))+"+loopstart+")",))


def animation_move():
  pass

#uplevel #0 {
#    set am_x "x"
#    set am_y "y"
#}
#proc animation_move {} {
#    global am_x am_y am_dy am_ldy
#    # fail if no selected points:
#    animation selected test
#    while 1 {
#	if [catch {panel "Move Animation keys" {
#	    {x am_x}
#	    {y am_y}
#	    {slope am_dy}
#	    {"left slope" am_ldy}
#	}}] return
#	if [catch {animation selected move x $am_x y $am_y dy $am_dy ldy $am_ldy} result] {
#	    alert $result
#	} else break
#    }
#}


def animation_negate():
  anim = nuke.animations()
  for i in anim:
    expr = "-("+nuke.animation(i, "expression")+")"
    nuke.animation(i, "expression", (expr,))


def animation_reverse():
  a = nuke.animations()
  for i in a:
    anim = nuke.animation(i, "expression")
    if anim is not None and anim == "curve(first_frame+last_frame-frame)":
      nuke.animation(i, "expression", ("curve",))
    else:
      nuke.animation(i, "expression", ("curve(first_frame+last_frame-frame)",))

