"""Functions used by the CameraTracker node"""

import nuke
import nukescripts
import os

from . import camerapresets

#
# Initialisation
#

CAMERA_CLASS = "Camera3"

def populateExportMenu(cameraTracker):
  """Populate the export menu on a CameraTracker node."""
  # These are the entries that will appear in the CameraTracker's export menu.
  # You can extend this list with your own entries if you like.
  entries = [
             # Label                   # Script to execute when the bake button is pressed.                # Tooltip for this entry.
             ( 'Camera',               'nukescripts.cameratracker.createCamera(nuke.thisNode())',          "Create a Camera linked to the calculated projection."),
             ( 'Camera rig',           'nukescripts.cameratracker.createCameraRig(nuke.thisNode())',       "Create a multi-view rig with a Camera per view."),
             ( 'Camera set',           'nukescripts.cameratracker.createCameraSet(nuke.thisNode())',       "Create a set of Cameras, one Camera per solved frame."),
             ( 'Scene',                'nukescripts.cameratracker.createScene(nuke.thisNode())',           "Create a Scene with a Camera and PointCloud for the camera solve."),
             ( 'Scene+',                'nukescripts.cameratracker.createEverything(nuke.thisNode())',     "Create a Scene with a Camera, PointCloud, ScanlineRender, and LensDistortion (Undistort) node."),
             ( 'Point cloud',          'nukescripts.cameratracker.createPointCloud(nuke.thisNode())',      "Create a PointCloud for the camera solve."),
             ( 'Distortion',           'nukescripts.cameratracker.createLensDistortion(nuke.thisNode())',
              "Create a LensDistortion node preconfigured for distortion using the same settings as the CameraTracker. " +
              "You can use this node to distort your CG or other elements before comping them back over the input footage."),
             ( 'Undistortion',         'nukescripts.cameratracker.createUndistortion(nuke.thisNode())',
              "Create a LensDistortion node preconfigured for undistortion using the same settings as the CameraTracker. " +
              "You can apply this node to your input footage to make it match CG elements rendered using the calculated camera."),
             ( 'Cards',                'nukescripts.cameratracker.createCards(nuke.thisNode())',           "Create a group of cards.")
             # Add your own entries here, if desired.
             ]

  k = cameraTracker['exportMenu']
  k.setValues([ "%s\t%s" % (script, label) for label, script, _ in entries ])

  # Calculate a tooltip which describes all of the available export options.
  tooltipLines = [ "Create new camera and point cloud nodes based on the results of the solve. The available options are:", "" ]
  for label, _, tooltip in entries:
    tooltipLines.append("<b>%s:</b> %s" % (label, tooltip))

  k.setTooltip(os.linesep.join(tooltipLines))


def populateFilmBackPresets(cameraTracker):
  """Populate the film back presets menu on a CameraTracker node."""
  # These are the entries that will appear in the CameraTracker's film back presets menu.
  # You can extend this list with your own entries by modifying camerapresets.py

  k = cameraTracker['filmBackSizePresets']
  k.setValues(["%s\t%s" % (idx, label) for idx, label in enumerate(nukescripts.camerapresets.getLabels())])

#
# Export functions
#

def createCamera(solver):
  """Create a camera node based on the projection calculated by the solver."""
  x = solver.xpos()
  y = solver.ypos()
  w = solver.screenWidth()
  h = solver.screenHeight()
  m = int(x + w/2)
  numviews = len( nuke.views() )
  link = False
  linkKnob = solver.knob("linkOutput")
  if linkKnob:
    link = bool(linkKnob.getValue())

  camera = nuke.createNode(CAMERA_CLASS, '', False)
  camera.setInput(0,None)
  camera.setXYpos(m - int(camera.screenWidth()/2), y + w)
  if link:
    camera.knob("focal").setExpression(solver.name() + ".focalLength")
    camera.knob("haperture").setExpression(solver.name() + ".aperture.x")
    camera.knob("vaperture").setExpression(solver.name() + ".aperture.y")
    camera.knob("translate").setExpression(solver.name() + ".camTranslate")
    camera.knob("rotate").setExpression(solver.name() + ".camRotate")
    camera.knob("win_translate").setExpression(solver.name() + ".windowTranslate")
    camera.knob("win_scale").setExpression(solver.name() + ".windowScale")
  else:
    camera.knob("focal").fromScript(solver.knob("focalLength").toScript(False))
    camera.knob("translate").fromScript(solver.knob("camTranslate").toScript(False))
    camera.knob("rotate").fromScript(solver.knob("camRotate").toScript(False))
    camera.knob("win_translate").fromScript(solver.knob("windowTranslate").toScript(False))
    camera.knob("win_scale").fromScript(solver.knob("windowScale").toScript(False))
    for i in range(numviews):
      camera.knob("haperture").setValue(solver.knob("aperture").getValue(0,i+1),0,0,i+1)
      camera.knob("vaperture").setValue(solver.knob("aperture").getValue(1,i+1),0,0,i+1)

  return camera

def createCameraRig(solver):
  """Create a multi-view rig with a camera per view."""
  numviews = len( nuke.views() )
  if numviews < 2:
    nuke.message("Creating a camera rig requires multiple views.\n" +
                 "You can add additional views in your <em>Project Settings</em>, on the <em>Views</em> tab.")
    return

  x = solver.xpos()
  y = solver.ypos()
  w = solver.screenWidth()
  h = solver.screenHeight()
  m = int(x + w/2)
  link = False
  linkKnob = solver.knob("linkOutput")
  if linkKnob:
    link = bool(linkKnob.getValue())

  join = nuke.nodes.JoinViews()
  join.setInput(0,None)
  join.setXYpos(m + int(w*1.5) + int(w * numviews/2), y + w)

  for i in range(numviews):
    viewStr = nuke.views()[i]
    camera = nuke.nodes.Camera3()
    camera.setInput(0,None)
    if link:
      camera.knob("focal").setExpression(solver.name() + ".focalLength." + viewStr)
      camera.knob("haperture").setExpression(solver.name() + ".aperture." + viewStr + ".x")
      camera.knob("vaperture").setExpression(solver.name() + ".aperture." + viewStr + ".y")
      camera.knob("translate").setExpression(solver.name() + ".camTranslate." + viewStr)
      camera.knob("rotate").setExpression(solver.name() + ".camRotate." + viewStr)
      camera.knob("win_translate").setExpression(solver.name() + ".windowTranslate." + viewStr)
      camera.knob("win_scale").setExpression(solver.name() + ".windowScale." + viewStr)
    else:
      if solver.knob("focalLength").isAnimated():
        camera.knob("focal").copyAnimation(0,solver.knob("focalLength").animation(0,i+1))
      else:
        camera.knob("focal").setValue(solver.knob("focalLength").getValue(0,i+1),0,0,i+1)
      if solver.knob("camTranslate").isAnimated():
        camera.knob("translate").copyAnimation(0,solver.knob("camTranslate").animation(0,i+1))
        camera.knob("translate").copyAnimation(1,solver.knob("camTranslate").animation(1,i+1))
        camera.knob("translate").copyAnimation(2,solver.knob("camTranslate").animation(2,i+1))
      else:
        camera.knob("translate").setValue(solver.knob("camTranslate").getValue(0,i+1),0,0,i+1)
        camera.knob("translate").setValue(solver.knob("camTranslate").getValue(1,i+1),1,0,i+1)
        camera.knob("translate").setValue(solver.knob("camTranslate").getValue(2,i+1),2,0,i+1)
      if solver.knob("camRotate").isAnimated():
        camera.knob("rotate").copyAnimation(0,solver.knob("camRotate").animation(0,i+1))
        camera.knob("rotate").copyAnimation(1,solver.knob("camRotate").animation(1,i+1))
        camera.knob("rotate").copyAnimation(2,solver.knob("camRotate").animation(2,i+1))
      else:
        camera.knob("rotate").setValue(solver.knob("camRotate").getValue(0,i+1),0,0,i+1)
        camera.knob("rotate").setValue(solver.knob("camRotate").getValue(1,i+1),1,0,i+1)
        camera.knob("rotate").setValue(solver.knob("camRotate").getValue(2,i+1),2,0,i+1)
      camera.knob("win_translate").setValue(solver.knob("windowTranslate").getValue(0,i+1),0,0,i+1)
      camera.knob("win_scale").setValue(solver.knob("windowScale").getValue(0,i+1),0,0,i+1)
      camera.knob("haperture").setValue(solver.knob("aperture").getValue(0,i+1),0,0,i+1)
      camera.knob("vaperture").setValue(solver.knob("aperture").getValue(1,i+1),0,0,i+1)
    camera.setXYpos(m + 2*w + w*i, y)
    if numviews==2:
      if i==0:
        camera.knob("gl_color").setValue(0xFF0000FF)
        camera.knob("tile_color").setValue(0xFF0000FF)
      if i==1:
        camera.knob("gl_color").setValue(0x00FF00FF)
        camera.knob("tile_color").setValue(0x00FF00FF)
    camera.setName( viewStr )
    join.setInput(i,camera)


def createCameraSet(solver):
  """Create a set of Cameras, one Camera per solved frame."""
  numCameras = solver["camTranslate"].getNumKeys()

  if numCameras >= 100:
    ok = nuke.ask("This will create %d cards, which may take some time.\nAre you sure?" % numCameras)
    if not ok:
      return

  if numCameras == 0:
    nuke.message("You can only create a camera set when you have solved cameras.")
    return

  x = solver.xpos()
  y = solver.ypos()
  w = solver.screenWidth()
  h = solver.screenHeight()
  m = int(x + w*2)
  link = False
  linkKnob = solver.knob("linkOutput")
  if linkKnob:
    link = bool(linkKnob.getValue())
  exprStr = "[python {nuke.toNode('" + solver.fullName() +"')"

  group = nuke.createNode("Group", '', False)
  group.begin()
  group.setName("Cameras")
  group.setXYpos(m + w, y + w)
  if numCameras>0:
    scene = nuke.createNode("Scene", '', False)
    sw = scene.screenWidth()
    sh = scene.screenHeight()
    inImg = nuke.createNode("Input", '', False)
    inImg.setName("img");
    inImg.setXYpos(m + int(w*(numCameras-1)/2) - int(sw/2), y)
    out = nuke.createNode("Output", '', False)
    out.setXYpos(m + int(w*(numCameras-1)/2) - int(sw/2), y + 4*w)
    out.setInput(0, scene)
    scene.setXYpos(m + int(w*(numCameras-1)/2) - int(sw/2), y + 3*w)
  for i in range(numCameras):
    frame = solver.knob("camTranslate").getKeyTime(i)
    camera = nuke.createNode(CAMERA_CLASS, '', False)
    camera.setSelected(False)
    camera.setInput(0,inImg)
    camera.setXYpos(m + w*i - int(sw/2), y + 2*w)
    scene.setInput(i, camera)
    if link:
      camera.knob("focal").setExpression( exprStr + ".knob('focalLength').getValueAt(" + str(frame) + ")}]" )
      camera.knob("haperture").setExpression( exprStr + ".knob('aperture').getValueAt(" + str(frame) + ",0)}]" )
      camera.knob("vaperture").setExpression( exprStr + ".knob('aperture').getValueAt(" + str(frame) + ",1)}]" )
      camera.knob("translate").setExpression( exprStr + ".knob('camTranslate').getValueAt(" + str(frame) + ",0)}]",0 )
      camera.knob("translate").setExpression( exprStr + ".knob('camTranslate').getValueAt(" + str(frame) + ",1)}]",1 )
      camera.knob("translate").setExpression( exprStr + ".knob('camTranslate').getValueAt(" + str(frame) + ",2)}]",2 )
      camera.knob("rotate").setExpression( exprStr + ".knob('camRotate').getValueAt(" + str(frame) + ",0)}]",0 )
      camera.knob("rotate").setExpression( exprStr + ".knob('camRotate').getValueAt(" + str(frame) + ",1)}]",1 )
      camera.knob("rotate").setExpression( exprStr + ".knob('camRotate').getValueAt(" + str(frame) + ",2)}]",2 )
    else:
      camera.knob("focal").setValue( solver.knob("focalLength").getValueAt(frame) )
      camera.knob("haperture").setValue( solver.knob("aperture").getValueAt(frame,0) )
      camera.knob("vaperture").setValue( solver.knob("aperture").getValueAt(frame,1) )
      camera.knob("translate").setValue( solver.knob("camTranslate").getValueAt(frame) )
      camera.knob("rotate").setValue( solver.knob("camRotate").getValueAt(frame) )
  group.end()
  group.setInput(0,solver)
  return group

def createScene(cameraTracker):
  """Create a Scene with a Camera and PointCloud for the camera solve."""
  scene = nuke.createNode('Scene', '', False)
  camera = nuke.createNode(CAMERA_CLASS, '', False)
  pointCloud = nuke.createNode('CameraTrackerPointCloud', '', False)
  sw = scene.screenWidth()
  sh = scene.screenHeight()
  x = cameraTracker.xpos()
  y = cameraTracker.ypos()
  w = cameraTracker.screenWidth()
  h = cameraTracker.screenHeight()
  m = int(x + w/2)
  camera.setXYpos(m + w, y + w + int((h-sh)/2))
  pointCloud.setXYpos(m - int(pointCloud.screenWidth()/2), y + w)
  scene.setXYpos(m - int(sw/2), y + w*2 - int((sh-h)/2))
  camera.setInput(0,None)
  pointCloud.setInput(0,cameraTracker)
  scene.setInput(0,camera)
  scene.setInput(1,pointCloud)
  numviews = len( nuke.views() )
  link = False
  linkKnob = cameraTracker.knob("linkOutput")
  if linkKnob:
    link = bool(linkKnob.getValue())
  if link:
    camera.knob("focal").setExpression(cameraTracker.name() + ".focalLength")
    camera.knob("haperture").setExpression(cameraTracker.name() + ".aperture.x")
    camera.knob("vaperture").setExpression(cameraTracker.name() + ".aperture.y")
    camera.knob("translate").setExpression(cameraTracker.name() + ".camTranslate")
    camera.knob("rotate").setExpression(cameraTracker.name() + ".camRotate")
    camera.knob("win_translate").setExpression(cameraTracker.name() + ".windowTranslate")
    camera.knob("win_scale").setExpression(cameraTracker.name() + ".windowScale")
  else:
    camera.knob("focal").fromScript(cameraTracker.knob("focalLength").toScript(False))
    camera.knob("translate").fromScript(cameraTracker.knob("camTranslate").toScript(False))
    camera.knob("rotate").fromScript(cameraTracker.knob("camRotate").toScript(False))
    camera.knob("win_translate").fromScript(cameraTracker.knob("windowTranslate").toScript(False))
    camera.knob("win_scale").fromScript(cameraTracker.knob("windowScale").toScript(False))
    for i in range(numviews):
      camera.knob("haperture").setValue(cameraTracker.knob("aperture").getValue(0,i+1),0,0,i+1)
      camera.knob("vaperture").setValue(cameraTracker.knob("aperture").getValue(1,i+1),0,0,i+1)
  return [scene, camera, pointCloud]


def createEverything(cameraTracker):
  """Create a Scene with a Camera, PointCloud, ScanlineRender, and LensDistortion (Undistort) node."""
  [scene, camera, pointCloud] = createScene(cameraTracker);
  lensDistort = createUndistortion(cameraTracker)
  scanline = nuke.createNode('ScanlineRender', '', False)
  # need to create a dummy camera here, as there seems to be a bug where calling
  # .screenWidth() on the scene or camera objects always returns 0.
  dummyCamera = nuke.createNode(CAMERA_CLASS, '', False)
  # creating our 4 dots
  cameraToSceneDot = nuke.createNode('Dot', '', False)
  cameraToScanlineRenderDot = nuke.createNode('Dot', '', False)
  lensToScanlineDot = nuke.createNode('Dot', '', False)
  # setting up widths & heights
  sw = dummyCamera.screenWidth()
  sh = dummyCamera.screenHeight()
  x = cameraTracker.xpos()
  y = cameraTracker.ypos()
  w = cameraTracker.screenWidth()
  h = cameraTracker.screenHeight()
  # have to hard-code our dot size because of the the
  # .screenWidth()/Height() always returning 0 bug.
  dw = 12
  dh = 12
  m = int(x + w/2)
  hspacing = int(w*1.5)
  vspacing = w
  # deleting our dummy camera
  nuke.delete(dummyCamera);
  # setting the node positions
  camera.setXYpos(      m - hspacing - int(sw/2), y +   vspacing + int((h-sh)/2))
  pointCloud.setXYpos(  m - int(w/2), y +   vspacing)
  lensDistort.setXYpos( m + hspacing - int(w/2),  y +   vspacing)
  scene.setXYpos(       m - int(sw/2),  y + 2*vspacing + int((h-sh)/2))
  scanline.setXYpos(    m - int(w/2), y + 3*vspacing)
  # setting dot positions
  cameraToSceneDot.setXYpos(          m - hspacing - int(dw/2), y + 2*vspacing + int((h-dh)/2) )
  cameraToScanlineRenderDot.setXYpos( m - hspacing - int(dw/2), y + 3*vspacing + int((h-dh)/2) )
  lensToScanlineDot.setXYpos(         m + hspacing - int(dw/2), y + 3*vspacing + int((h-dh)/2) )
  # setting dot connections
  cameraToSceneDot.setInput(0, camera)
  cameraToScanlineRenderDot.setInput(0, cameraToSceneDot)
  lensToScanlineDot.setInput(0, lensDistort)
  # setting node connections
  camera.setInput(0,None)
  pointCloud.setInput(0,cameraTracker)
  # try set the lens distortion input to the CT's input if possible, otherwise ensure it's
  # disconnected.
  if cameraTracker.inputs() > 0 and cameraTracker.input(0) != None:
    lensDistort.setInput(0, cameraTracker.input(0))
  else:
    lensDistort.setInput(0, None)
  scene.setInput(0,cameraToSceneDot)
  scene.setInput(1,pointCloud)
  scanline.setInput(0, lensToScanlineDot)
  scanline.setInput(1, scene)
  scanline.setInput(2, cameraToScanlineRenderDot)


def createPointCloud(cameraTracker):
  """Create a CameraTrackerPointCloud node."""
  _clearSelection()
  cameraTracker.setSelected(True)
  pointCloud = nuke.createNode('CameraTrackerPointCloud', '', False)


def createLensDistortion(cameraTracker):
  return _createLensDistortionNode(cameraTracker, False)


def createUndistortion(cameraTracker):
  return _createLensDistortionNode(cameraTracker, True)


def _createLensDistortionNode(cameraTracker, invertDistortion):
  """Create a LensDistortion node which matches the settings calculated by the CameraTracker."""
  _clearSelection()

  lensDistort = nuke.createNode('LensDistortion2', '', False)
  lensDistort.setInput(0, cameraTracker.input(0))
  link = cameraTracker["linkOutput"].getValue()
  _copyKnob(cameraTracker, "lensType",                lensDistort, "lensType",                 link)
  _copyKnob(cameraTracker, "distortion1",             lensDistort, "distortionDenominator0",   link)
  _copyKnob(cameraTracker, "distortion2",             lensDistort, "distortionDenominator1",   link)
  _copyKnob(cameraTracker, "distortionCenter",        lensDistort, "centre",                   link)
  _copyKnob(cameraTracker, "anamorphicSqueeze",       lensDistort, "anamorphicSqueeze",        link)
  _copyKnobIdx(cameraTracker, "asymmetricDistortion", 0, lensDistort, "distortionDenominatorX00", 0, link)
  _copyKnobIdx(cameraTracker, "asymmetricDistortion", 1, lensDistort, "distortionDenominatorY00", 0, link)

  if invertDistortion:
    lensDistort['output'].setValue('Undistort')
  else:
    lensDistort['output'].setValue('Redistort')

  lensDistort['projection'].setValue('Rectilinear')
  lensDistort['distortionModelPreset'].setValue('NukeX Classic')

  lensDistort.selectOnly()

  return lensDistort


def createCards(solver):
  numCameras = solver["camTranslate"].getNumKeys()

  if numCameras >= 100:
    ok = nuke.ask("This will create %d cards, which may take some time.\nAre you sure?" % numCameras)
    if not ok:
      return

  if numCameras == 0:
    nuke.message("You can only create a card set when you have solved cameras.")
    return

  x = solver.xpos()
  y = solver.ypos()
  w = solver.screenWidth()
  h = solver.screenHeight()
  m = int(x + w*2)
  link = False
  linkKnob = solver.knob("linkOutput")
  if linkKnob:
    link = bool(linkKnob.getValue())
  exprStr = "[python {nuke.toNode('" + solver.fullName() +"')"

  group = nuke.createNode("Group", '', False)
  group.begin()
  group.setName("Cards")
  group.setXYpos(m + w, y + w)
  if numCameras>0:
    scene = nuke.createNode("Scene", '', False)
    sw = scene.screenWidth()
    sh = scene.screenHeight()
    inImg = nuke.createNode("Input", '', False)
    inImg.setName("img");
    inImg.setXYpos(m + int(w*(numCameras-1)/2) - int(sw/2), y)
    out = nuke.createNode("Output", '', False)
    out.setXYpos(m + int(w*(numCameras-1)/2) - int(sw/2), y + 5*w)
    out.setInput(0, scene)
    group.addKnob(nuke.Tab_Knob('cards','Cards'))
    zDistKnob = nuke.Double_Knob('z','z')
    zDistKnob.setRange(0,100)
    zDistKnob.setTooltip("Cards are placed this far from origin. Use this to make a pan & tile dome of this radius.")
    zDistKnob.setDefaultValue([1])
    group.addKnob(zDistKnob)
  for i in range(numCameras):
    frame = solver.knob("camTranslate").getKeyTime(i)
    hold = nuke.createNode("FrameHold", '', False)
    hold.setInput(0, inImg)
    hold.knob("first_frame").setValue(frame)
    hold.setXYpos(m + w*i - int(w/2), y + w)
    camera = nuke.createNode(CAMERA_CLASS, '', False)
    camera.setInput(0,None)
    if link:
      camera.knob("focal").setExpression( exprStr + ".knob('focalLength').getValueAt(" + str(frame) + ")}]" )
      camera.knob("haperture").setExpression( exprStr + ".knob('aperture').getValueAt(" + str(frame) + ",0)}]" )
      camera.knob("vaperture").setExpression( exprStr + ".knob('aperture').getValueAt(" + str(frame) + ",1)}]" )
      camera.knob("translate").setExpression( exprStr + ".knob('camTranslate').getValueAt(" + str(frame) + ",0)}]",0 )
      camera.knob("translate").setExpression( exprStr + ".knob('camTranslate').getValueAt(" + str(frame) + ",1)}]",1 )
      camera.knob("translate").setExpression( exprStr + ".knob('camTranslate').getValueAt(" + str(frame) + ",2)}]",2 )
      camera.knob("rotate").setExpression( exprStr + ".knob('camRotate').getValueAt(" + str(frame) + ",0)}]",0 )
      camera.knob("rotate").setExpression( exprStr + ".knob('camRotate').getValueAt(" + str(frame) + ",1)}]",1 )
      camera.knob("rotate").setExpression( exprStr + ".knob('camRotate').getValueAt(" + str(frame) + ",2)}]",2 )
    else:
      camera.knob("focal").setValue( solver.knob("focalLength").getValueAt(frame) )
      camera.knob("haperture").setValue( solver.knob("aperture").getValueAt(frame,0) )
      camera.knob("vaperture").setValue( solver.knob("aperture").getValueAt(frame,1) )
      camera.knob("translate").setValue( solver.knob("camTranslate").getValueAt(frame) )
      camera.knob("rotate").setValue( solver.knob("camRotate").getValueAt(frame) )
    camera.setXYpos(m + w*i - int(sw/2), y + 3*w)
    card = nuke.createNode("Card", '', False)
    card.setSelected(False)
    card.knob("lens_in_focal").setExpression( camera.name() + ".focal" )
    card.knob("lens_in_haperture").setExpression( camera.name() + ".haperture" )
    card.knob("translate").setExpression( camera.name() + ".translate" )
    card.knob("rotate").setExpression( camera.name() + ".rotate" )
    card.knob("z").setExpression( "parent.z" )
    card.setInput(0, hold)
    card.setXYpos(m + w*i - int(w/2), y + 2*w)
    scene.setInput(i*2,camera)
    scene.setInput(i*2+1,card)
    scene.setXYpos(m + int(w*(numCameras-1)/2) - int(sw/2), y + 4*w)
  group.end()
  group.setInput(0,solver)
  return group


def _copyKnob(fromNode, fromKnobName, toNode, toKnobName, link):
  fromKnob = fromNode[fromKnobName]
  toKnob = toNode[toKnobName]
  if link:
    toKnob.setExpression(fromKnob.fullyQualifiedName())
  else:
    toKnob.fromScript(fromKnob.toScript(False))

def _copyKnobIdx(fromNode, fromKnobName, fromKnobIdx, toNode, toKnobName, toKnobIdx, link):
  fromKnob = fromNode[fromKnobName]
  toKnob = toNode[toKnobName]
  if link:
    toKnob.setExpression(fromKnob.fullyQualifiedName() + "." + str(fromKnobIdx), toKnobIdx)
  else:
    if fromKnob.isAnimated(fromKnobIdx):
      if fromKnob.hasExpression(fromKnobIdx):
        toKnob.setExpression(fromKnob.animation(fromKnobIdx).expression(), toKnobIdx)
      else:
        toKnob.copyAnimation(toKnobIdx, fromKnob.animation(fromKnobIdx))
    else:
      toKnob.setValue(fromKnob.getValue(fromKnobIdx), toKnobIdx)


def _clearSelection():
  nuke.selectAll()
  nuke.invertSelection()


#
# Camera Film Back Preset Functions
#

def setKnobToPreset(cameraTracker, selectedPresetIdx):
  """Finds the index of the preset knob and sets the film back size knob accordingly."""
  filmbackSizeKnob  = cameraTracker['filmBackSize']
  selectedFilmbackSize = nukescripts.camerapresets.getFilmBackSize(selectedPresetIdx)
  filmbackSizeKnob.setValue( selectedFilmbackSize[0], 0 )
  filmbackSizeKnob.setValue( selectedFilmbackSize[1], 1 )

  # Making sure the film back units are set to 'mm'
  filmBackUnits = cameraTracker['filmBackUnits']
  filmBackUnits.setValue(0)


#
# Callbacks
#

def cameratrackerCreateCallback():
  populateExportMenu(nuke.thisNode())
  populateFilmBackPresets(nuke.thisNode())


if not nuke.env['assist']:
  nuke.addOnCreate(cameratrackerCreateCallback, nodeClass='CameraTracker')
  nuke.addOnCreate(cameratrackerCreateCallback, nodeClass='CameraTracker1_0')

#
# Track import and export functions
#

class LinkableImportPanel( nukescripts.PythonPanel ):
  """
    Modal dialog for selecting a Linkable node in the script.

    The following class creates a modal dialog with one UI element: an enum of nodes
    that derive from the LinkableI class. (The LinkableI interface allows us to easily query and import
    2D data from a variety of sources, particularly the Tracker node.) The user then selects their source node
    to import the data from. Once Ok'ed, the code below creates a new user track for each LinkableInfo object
    returned in the node.linkableKnobs() function with an XY co-ordinate, and then copies each animation curve
    entry.
    """

  def __init__( self ):
    nukescripts.PythonPanel.__init__( self, "Select Tracker to Import From", "uk.co.thefoundry.FramePanel" )
    # Show a list of trackers in the project.
    self._trackers = [n.name() for n in nuke.allNodes() if n.linkableKnobs(nuke.KnobType.eXYKnob)]
    self._tracker = nuke.Enumeration_Knob( "trackers", "tracker node", self._trackers )
    self._tracker.setTooltip( "The Tracker node to import from." )
    self.addKnob( self._tracker )


  def showModalDialog( self, dstNode ):
    result = nukescripts.PythonPanel.showModalDialog( self )
    if result:
      srcNode = self._tracker.value()
      return srcNode
    return None

def _copyLinkableXYAnimCurve(linkableSrc, linkableDst):
  """Copies the x, y animation curves from one XYKnob linkable object to another."""
  linkKnobSrc = linkableSrc.knob()
  linkKnobDst = linkableDst.knob()
  linkableSrcIndices = linkableSrc.indices()
  linkableDstIndices = linkableDst.indices()

  # Setting enabled
  linkKnobDst.setValue(linkableSrc.enabled(), 0)

  # Clearing the animation curves of the locatior x and y curve
  linkKnobDst.clearAnimated(int(linkableDstIndices[0]))
  linkKnobDst.clearAnimated(int(linkableDstIndices[1]))

  # Now setting x and y positions
  for i in range(0, linkKnobSrc.getNumKeys(int(linkableSrcIndices[0]))):
    t = linkKnobSrc.getKeyTime(i, int(linkableSrcIndices[0]))

    # Because of a bug in the tableknob, before setting the first key/value, we need to re-enable setAnimated.
    # See below for more details.
    if i == 0:
      linkKnobDst.setAnimated(int(linkableDstIndices[0]))
      linkKnobDst.setAnimated(int(linkableDstIndices[1]))

    # Finally setting the key/values
    linkKnobDst.setValueAt( linkKnobSrc.getValueAt(t, int(linkableSrcIndices[0])), t, int(linkableDstIndices[0]) )
    linkKnobDst.setValueAt( linkKnobSrc.getValueAt(t, int(linkableSrcIndices[1])), t, int(linkableDstIndices[1]) )

    # Because of the setAnimation bug which always creates a key at 0, we need to explicitly check and remove it.
    if i == 0 and t != 0:
      linkKnobDst.removeKeyAt(0, int(linkableDstIndices[0]))
      linkKnobDst.removeKeyAt(0, int(linkableDstIndices[1]))


def importTracker(cameraTracker):
  """Import data from a Tracker node into the CameraTracker node."""
  # This is the entry point where we bring up our modal dialog.
  strSrcNode = LinkableImportPanel().showModalDialog(cameraTracker)
  if not strSrcNode:
    return

  # First we start by getting the nodes.
  srcNode = nuke.toNode(strSrcNode)
  # And from the nodes, we get our LinkableInfo objects.
  linkablesSrc = srcNode.linkableKnobs(nuke.KnobType.eXYKnob)
  linkablesDst = cameraTracker.linkableKnobs(nuke.KnobType.eXYKnob)

  # The following 'startIndex' is used to determine the index of the newly
  # created user track below. For example, if there are already 10 user tracks, the
  # next index of the user track we create will be at 10.
  startIndex = len(linkablesDst)

  # First create new user track for each valid track
  numValidTracks = 0

  for linkableSrc in linkablesSrc:
    linkableSrcIndices = linkableSrc.indices()

    # Make sure our source linkable has two indices, one for each co-ordinate.
    if len(linkableSrcIndices) != 2:
      continue

    # Here we're manually executing a button, when really
    # we should be using the 'createLinkable' function in the NDK.
    # When this code is made into a NukeScript file, we should really just add
    # 'createLinkable' to PythonObject.
    cameraTracker['addUserTrack'].execute()

    # We now grab our destination LinkableInfo, our new user track and copy the anims.
    linkablesDst = cameraTracker.linkableKnobs(nuke.KnobType.eXYKnob)

    if startIndex >= len(linkablesDst):
      continue;

    linkableDst = linkablesDst[startIndex]

    _copyLinkableXYAnimCurve(linkableSrc, linkableDst)

    # Incrementing the startIndex to say where to find the next user track.
    startIndex = startIndex + 1

    # Lastly, copying the 'enabled' status of the track.
    trackEnabled = linkableSrc.enabled()
    cameraTrackKnob = linkableDst.knob()
    cameraTrackIndices = linkableDst.indices()
    if len(cameraTrackIndices) != 2:
      continue

    # The following line derives the 'enabled' column index. Until the TableKnob
    # has proper Python bindings we must hardcode these index offsets.
    cameraTrackEnabledIdx = cameraTrackIndices[0] - 2
    cameraTrackKnob.setValue( trackEnabled, int(cameraTrackEnabledIdx) )

def exportTracker(cameraTracker):
  """Export data from the CameraTracker node into a Tracker node."""
  tracker = nuke.createNode('Tracker4', '', True)
  x = cameraTracker.xpos()
  y = cameraTracker.ypos()
  w = cameraTracker.screenWidth()
  h = cameraTracker.screenHeight()
  m = int(x + w/2)
  tracker.setXYpos(m - int(tracker.screenWidth()/2), y + w)

  # And from the nodes, we get our LinkableInfo objects.
  linkablesSrc = cameraTracker.linkableKnobs(nuke.KnobType.eXYKnob)
  linkablesDst = tracker.linkableKnobs(nuke.KnobType.eXYKnob)

  # The following 'startIndex' is used to determine the index of the newly
  # created user track below. For example, if there are already 10 user tracks, the
  # next index of the user track we create will be at 10.
  startIndex = len(linkablesDst)
  # First create new track for each valid user track
  numValidTracks = 0
  # Create an empty dict
  trackEnabledDict = {}
  for linkableSrc in linkablesSrc:
    linkableSrcIndices = linkableSrc.indices()

    # Make sure our source linkable has two indices, one for each co-ordinate.
    if len(linkableSrcIndices) < 2:
      continue

    # Here we're manually executing a button, when really
    # we should be using the 'createLinkable' function in the NDK.
    # When this code is made into a NukeScript file, we should really just add
    # 'createLinkable' to PythonObject.
    tracker['add_track'].execute()
    # We now grab our destination LinkableInfo, our new user track and copy the anims.
    linkablesDst = tracker.linkableKnobs(nuke.KnobType.eXYKnob)

    if startIndex >= len(linkablesDst):
      continue;

    linkableDst = linkablesDst[startIndex]

    _copyLinkableXYAnimCurve(linkableSrc, linkableDst)

    # Adding to the dict for later table manipulation.
    trackEnabledDict[linkableDst] = linkableSrc.enabled()

    # Incrementing the startIndex to say where to find the next user track.
    startIndex = startIndex + 1

  # We need to do a bit more to make the exported tracks nicer. In particular,
  # the enabled flags between user and exported tracks must be respected,
  # and the target offset_x and offset_y fields must not be keyed. This has
  # to be done as a separate loop as there may be sync issues.
  for linkableDst, userTrackEnabled in trackEnabledDict.items():
    trackKnob = linkableDst.knob()
    trackIndices = linkableDst.indices()
    if len(trackIndices) != 2:
      continue

    # The following three lines are deriving the indices of the 'enabled' and
    # the 'offset_x' and 'offset_y' columns in the Tracker. Until the TableKnob
    # has proper Python bindings we must hardcode these index offsets.
    trackEnabledIdx = trackIndices[0] - 2
    trackOffsetXIdx = trackIndices[1] + 1
    trackOffsetYIdx = trackIndices[1] + 2
    trackKnob.clearAnimated( int(trackOffsetXIdx) )
    trackKnob.clearAnimated( int(trackOffsetYIdx) )
    trackKnob.clearAnimated( int(trackEnabledIdx) )
    trackKnob.setValue( userTrackEnabled, int(trackEnabledIdx) )
    # A second clearAnimated is needed as the above setValue seems to create a key.
    trackKnob.clearAnimated( int(trackEnabledIdx) )


def importTracks(cameraTracker):
  """Utility function that collects the filename to be used in importing tracks from a Shake formatted file."""
  filename = nuke.getClipname("Import File")
  if filename is None:
    filename = ""

  cameraTracker.knob("tracksFile").fromScript( filename )


def exportTracks(cameraTracker):
  """Utility function that collects the filename to be used in exporting tracks from a Shake formatted file."""
  filename = nuke.getClipname("Export File")
  if filename is None:
    filename = ""

  cameraTracker.knob("tracksFile").fromScript( filename )
