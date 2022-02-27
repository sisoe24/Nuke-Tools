"""Functions used by the ModelBuilder node"""

import nuke
import nukescripts


#
# Initialisation
##

def populateBakeMenu(mb):
  """Populate the bake menu on a ModelBuilder node."""
  entries = [
    # Label                 # Script to execute when the bake button is pressed.
    ( 'Selected geometry',  'nukescripts.modelbuilder.bakeSceneSelection(nuke.thisNode())' ),
    ( 'Projection',         'nukescripts.modelbuilder.bakeProjection(nuke.thisNode())' ),
    ( 'Apply texture',      'nukescripts.modelbuilder.bakeApplyTexture(nuke.thisNode())' )
    # Add your own entries here, if desired.
  ]
  k = mb['bakeMenu']
  k.setValues([ "%s\t%s" % (script, label) for label, script in entries ])


#
# Bake functions
#

def bakeSceneSelection(mb):
  """Create a ModelBuilderGeo node containing a copy of the currently selected geometry."""
  if mb.Class() != "ModelBuilder":
    return

  # Note that if the "expand/collapse panels to match selection" setting is
  # true, Nuke will collapse the ModelBuilder panel when createNode is called
  # below. That seems to have the side effect of making the ModelBuilder think
  # nothing is selected in its tree knob, which means it'll come back with an
  # empty string when we execute the serializeScene knob (the cause of bugzilla
  # bug #32592). So it's important to do the serialisation and save the results
  # *before* calling createNode.

  mb['serializeScene'].execute()
  serializeStr = mb['serializeStr'].getValue()
  serializeName = mb['serializeName'].getValue()
  mb['serializeName'].setValue('')
  mb['serializeStr'].setValue('')

  geo = nuke.createNode('ModelBuilderGeo','',False)
  geo.setXYpos( int(mb.xpos() + mb.screenWidth() * 1.5), int(mb.ypos()) )
  geo['scene'].fromScript( serializeStr )
  geo['label'].setValue( serializeName )


def bakeProjection(mb):
  """Create a projection setup for the current frame."""
  if mb.Class() != "ModelBuilder":
    return

  clearNodeSelection()
  srcCam = mb.input(1)
  if not srcCam:
    return
  w = mb.screenWidth()
  h = mb.screenHeight()
  src = mb.input(0)
  frame = nuke.frame()
  if (mb['textureType'].getValue() > 0):
    frame = mb['textureFrame'].getValue()
  label = '(frame ' + str(frame) + ')'

  srcdot = nuke.createNode('Dot','',False)
  srcdot.setInput(0, src)
  srchold = nuke.createNode('FrameHold','',False)
  stamp = nuke.createNode('PostageStamp','',False)
  project = nuke.createNode('Project3D','',False)
  apply = nuke.createNode('ApplyMaterial','',False)

  cam = copyCamera(srcCam)

  camhold = nuke.clone(srchold,'',False)
  camdot = nuke.createNode('Dot','',False)
  project.setInput(1, camdot)

  srcdot.setXYpos(  int(mb.xpos() + w * 3.5),                                             int(mb.ypos())                                                                )
  srchold.setXYpos( int(srchold.xpos()),                                                  int(srcdot.ypos() + w)                                                        )
  stamp.setXYpos(   int(stamp.xpos()),                                                    int(stamp.ypos() + srchold.screenHeight() + h * 2)                            )
  cam.setXYpos(     int(srchold.xpos() - w * 1.5),                                        int(srchold.ypos() + srchold.screenHeight() / 2 - cam.screenHeight() / 2)     )
  camhold.setXYpos( int(cam.xpos() + cam.screenWidth() / 2 - srchold.screenWidth() / 2),  int(stamp.ypos() + h)                                                         )
  project.setXYpos( int(stamp.xpos()),                                                    int(stamp.ypos() + stamp.screenHeight() + h * 2)                              )
  camdot.setXYpos(  int(camdot.xpos()),                                                   int(project.ypos() + project.screenHeight() / 2 - camdot.screenHeight() / 2)  )
  apply.setXYpos(   int(stamp.xpos()),                                                    int(apply.ypos() +  w)                                                        )

  srchold.knob('first_frame').setValue( frame )
  srcdot.setSelected( True )
  srchold.setSelected( True )
  stamp.setSelected( True )
  project.setSelected( True )
  apply.setSelected( True )
  cam.setSelected( True )
  camhold.setSelected( True )
  camdot.setSelected( True )
  bd = nukescripts.autoBackdrop()
  bd['label'].setValue('Frame %d' % frame)


def bakeApplyTexture(mb):
  if mb.Class() != "ModelBuilder":
    return

  texture = mb.input(3)
  if not texture:
    return

  clearNodeSelection()
  mb.setSelected(True)

  amat = nuke.createNode('ApplyMaterial')
  amat.setInput(1, texture)
  amat['filter_type'].setValue('name')
  amat['filter_name_match'].setValue('equals')
  amat['filter_refresh'].execute()


#
# Helpers
#

def clearNodeSelection():
  for n in nuke.selectedNodes():
    n.setSelected(False)


def copyCamera(srcCam):
  while srcCam is not None and srcCam.Class() == 'Dot':
    srcCam = srcCam.input(0)
  if srcCam.Class() == 'Camera':
    newCam = nuke.createNode('Camera')
    newCam.readKnobs(srcCam.writeKnobs(nuke.TO_SCRIPT))
  else:
    clearNodeSelection()
    newCam = nuke.clone(srcCam, '', False)
    newCam.setSelected(True)
  return newCam


#
# Callbacks
#

def modelbuilderCreateCallback():
  populateBakeMenu(nuke.thisNode())


assist = nuke.env['assist']
if not assist:
  nuke.addOnCreate(modelbuilderCreateCallback, nodeClass='ModelBuilder')
