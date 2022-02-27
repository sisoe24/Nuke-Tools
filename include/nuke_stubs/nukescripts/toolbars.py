# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke
import nukescripts
import os, os.path

# Define the tool menus. This file is loaded by menu.py.
def setup_toolbars():
  # This is not currently used but when we support a text-only mode we'll need it.
  #size = nuke.numvalue("preferences.toolbarTextSize")

  # Use the following options to set the shortcut context in the call to menu addCommand.
  # Setting the shortcut context to a widget will mean the shortcut will only be triggered
  # if that widget (or it's children) has focus. If no shortcut context is specified the
  # default context is window context i.e. it can be triggered from anywhere in the window.
  # The enum is defined in nk_menu_python_add_item in PythonObject.cpp
  windowContext = 0
  applicationContext = 1
  dagContext = 2

  # Get the top-level toolbar
  toolbar = nuke.menu("Nodes")
  assist = nuke.env['assist']

  # The "Image" menu
  m = toolbar.addMenu("Image", "ToolbarImage.png")
  m.addCommand("Read", "nukescripts.create_read()", "r", icon="Read.png", shortcutContext=dagContext)
  m.addCommand("Write", "nuke.createNode(\"Write\")", "w", icon="Write.png", shortcutContext=dagContext)
  m.addCommand("Profile", "nuke.createNode(\"Profile\")", icon="Write.png", shortcutContext=dagContext)
  if not assist:
    m.addCommand("UDIM import", "nukescripts.udim_import()", "u", icon="Read.png", shortcutContext=dagContext)
  m.addCommand("Constant", "nuke.createNode(\"Constant\")", icon="Constant.png")
  m.addCommand("CheckerBoard", "nuke.createNode(\"CheckerBoard2\")", icon="CheckerBoard.png")
  m.addCommand("ColorBars", "nuke.createNode(\"ColorBars\")", icon="ColorBars.png")
  m.addCommand("ColorWheel", "nuke.createNode(\"ColorWheel\")", icon="ColorWheel.png")
  if not assist:
    m.addCommand("CurveTool", "nukescripts.createCurveTool()", icon="CurveTool.png")
  m.addCommand("Viewer", "nuke.createNode(\"Viewer\")", icon="Viewer.png")
  # m.addCommand("Proxy", "nuke.knob(\"root.proxy\", \"!root.proxy\")", icon="proxyfullres.png")

  # The "Draw" menu
  m = toolbar.addMenu("Draw", "ToolbarDraw.png")
  m.addCommand("Roto", '''nuke.createNode("Roto")''', "o", icon="Roto.png", shortcutContext=dagContext)
  m.addCommand("RotoPaint", "nuke.createNode(\"RotoPaint\")", "p", icon="RotoPaint.png", shortcutContext=dagContext)

  m.addCommand("@;RotoBranch", "nuke.createNode(\"Roto\")", "+o", shortcutContext=dagContext)
  m.addCommand("@;RotoPaintBranch", "nuke.createNode(\"RotoPaint\")", "+p", shortcutContext=dagContext)

  m.addCommand("Dither", "nuke.createNode(\"Dither\")", icon="Dither.png")
  m.addCommand("DustBust", "nuke.createNode(\"DustBust\")", icon="DustBust.png")
  m.addCommand("Grain", "nuke.createNode(\"Grain2\")", icon="Grain.png")
  m.addCommand("ScannedGrain", "nuke.createNode(\"ScannedGrain\")", icon="ScannedGrain.png")
  m.addCommand("Glint", "nuke.createNode(\"Glint\")", icon="Glint.png")
  m.addCommand("Grid", "nuke.createNode(\"Grid\")", icon="Grid.png")
  m.addCommand("Flare", "nuke.createNode(\"Flare\")", icon="Flare.png")
  m.addCommand("LightWrap", "nuke.createNode(\"LightWrap\")", icon="LightWrap.png")
  m.addCommand("MarkerRemoval", "nuke.createNode(\"MarkerRemoval\")", icon="MarkerRemoval.png")
  m.addCommand("Noise", "nuke.createNode(\"Noise\")", icon="Noise.png")
  m.addCommand("Radial", "nuke.createNode(\"Radial\")", icon="Radial.png")
  m.addCommand("Ramp", "nuke.createNode(\"Ramp\")", icon="Ramp.png")
  m.addCommand("Rectangle", "nuke.createNode(\"Rectangle\")", icon="Rectangle.png")
  m.addCommand("Sparkles", "nuke.createNode(\"Sparkles\")", icon="Sparkles.png")
  m.addCommand("Text", "nuke.createNode(\"Text2\")", icon="Text.png")

  m = toolbar.addMenu("Time", "ToolbarTime.png")
  m.addCommand("Add 3:2 pulldown", "nuke.createNode(\"add32p\")", icon="Add32.png")
  m.addCommand("Remove 3:2 pulldown", "nuke.createNode(\"remove32p\")", icon="Remove32.png")
  m.addCommand("AppendClip", "nuke.createNode(\"AppendClip\")", icon="AppendClip.png")
  m.addCommand("FrameBlend", "nuke.createNode(\"FrameBlend\")", icon="FrameBlend.png")
  m.addCommand("FrameHold", "nuke.createNode(\"FrameHold\")", icon="FrameHold.png")
  m.addCommand("FrameRange", "nuke.createNode(\"FrameRange\")", icon="FrameRange.png")
  if not assist:
    m.addCommand("Kronos", "nukescripts.createKronos()", icon="Oflow.png")
  m.addCommand("OFlow", "nukescripts.createOFlow()", icon="Oflow.png")
  m.addCommand("Retime", "nuke.createNode(\"Retime\")", icon="Retime.png")
  m.addCommand("TemporalMedian", "nuke.createNode(\"TemporalMedian\")", icon="TemporalMedian.png")
  m.addCommand("TimeBlur", "nuke.createNode(\"TimeBlur\")", icon="TimeBlur.png")
  m.addCommand("NoTimeBlur", "nuke.createNode(\"NoTimeBlur\")", icon="NoTimeBlur.png")
  m.addCommand("TimeEcho", "nuke.createNode(\"TimeEcho\")", icon="TimeEcho.png")
  m.addCommand("TimeOffset", "nuke.createNode(\"TimeOffset\")", icon="TimeOffset.png")

  if not assist:
    m.addCommand("TimeWarp", "nukescripts.create_time_warp()", icon="TimeWarp.png")
  m.addCommand("TimeClip")

  m.addCommand("SmartVector", "nuke.createNode(\"SmartVector\")", icon="SmartVector.png")
  m.addCommand("VectorToMotion", "nuke.createNode(\"VectorToMotion\")", icon="VectorToMotion.png")
  m.addCommand("VectorGenerator", "nuke.createNode(\"VectorGenerator\")")


  # The "Channel" menu
  m = toolbar.addMenu("Channel", "ToolbarChannel.png")
  m.addCommand("Shuffle", "nuke.createNode(\"Shuffle2\")", icon="Shuffle.png")
  m.addCommand("Copy", "nuke.createNode(\"Copy\")", "k", icon="CopyNode.png", shortcutContext=dagContext)
  m.addCommand("@;CopyBranch", "nuke.createNode(\"Copy\")", "+k", shortcutContext=dagContext)
  m.addCommand("ChannelMerge", "nuke.createNode(\"ChannelMerge\")", icon="ChannelMerge.png")
  m.addCommand("Add", "nuke.createNode(\"AddChannels\")", icon="Add.png")
  m.addCommand("Remove","nuke.createNode(\"Remove\")", icon="Remove.png")


  # The "Color" menu
  m = toolbar.addMenu("Color", "ToolbarColor.png")

  n = m.addMenu("Math", "ColorMath.png")
  n.addCommand("Add", "nuke.createNode(\"Add\")", icon="ColorAdd.png")
  n.addCommand("Multiply", "nuke.createNode(\"Multiply\")", icon="ColorMult.png")
  n.addCommand("Gamma", "nuke.createNode(\"Gamma\")", icon="ColorGamma.png")
  n.addCommand("ClipTest", "nuke.createNode(\"ClipTest\")", icon="ClipTest.png")
  n.addCommand("ColorMatrix", "nuke.createNode(\"ColorMatrix\")", icon="ColorMatrix.png")
  n.addCommand("Expression", "nuke.createNode(\"Expression\")", icon="Expression.png")

  n = m.addMenu("OCIO", "OCIO.png")
  n.addCommand("OCIO CDLTransform", "nuke.createNode(\"OCIOCDLTransform\")", icon="OCIO.png")
  n.addCommand("OCIO ColorSpace", "nuke.createNode(\"OCIOColorSpace\")", icon="OCIO.png")
  n.addCommand("OCIO Display", "nuke.createNode(\"OCIODisplay\")", icon="OCIO.png")
  n.addCommand("OCIO FileTransform", "nuke.createNode(\"OCIOFileTransform\")", icon="OCIO.png")
  n.addCommand("OCIO LogConvert", "nuke.createNode(\"OCIOLogConvert\")", icon="OCIO.png")
  n.addCommand("OCIO LookTransform", "nuke.createNode(\"OCIOLookTransform\")", icon="OCIO.png")

  n = m.addMenu("3D LUT", "Toolbar3DLUT.png")
  n.addCommand("CMSTestPattern", "nuke.createNode(\"CMSTestPattern\")", icon="CMSTestPattern.png")
  n.addCommand("GenerateLUT", "nuke.createNode(\"GenerateLUT\")", icon="GenerateLUT.png")
  n.addCommand("Vectorfield (Apply 3D LUT)", "nuke.createNode(\"Vectorfield\")", icon="Vectorfield.png")

  m.addCommand("Clamp", "nuke.createNode(\"Clamp\")", icon="Clamp.png")
  m.addCommand("ColorLookup", "nuke.createNode(\"ColorLookup\")", icon="ColorLookup.png")
  m.addCommand("Colorspace", "nuke.createNode(\"Colorspace\")", icon="ColorSpace.png")
  m.addCommand("ColorTransfer", "nuke.createNode(\"ColorTransfer\")", icon="ColorTransfer.png")
  m.addCommand("ColorCorrect", "nuke.createNode(\"ColorCorrect\")", "c", icon="ColorCorrect.png", shortcutContext=dagContext)
  m.addCommand("@;ColorCorrectBranch", "nuke.createNode(\"ColorCorrect\")", "+c")
  m.addCommand("Crosstalk", "nuke.createNode(\"CCrosstalk\")", icon="Crosstalk.png")
  m.addCommand("Exposure", "nuke.createNode(\"EXPTool\")", icon="Exposure.png")
  m.addCommand("Grade", "nuke.createNode(\"Grade\")", "g", icon="Grade.png", shortcutContext=dagContext)
  m.addCommand("@;GradeBranch", "nuke.createNode(\"Grade\")", "+g", shortcutContext=dagContext)
  m.addCommand("Histogram", "nuke.createNode(\"Histogram\")", icon="Histogram.png")
  m.addCommand("HistEQ", "nuke.createNode(\"HistEQ\")", icon="HistEQ.png")
  m.addCommand("HueCorrect", "nuke.createNode(\"HueCorrect\")", icon="HueCorrect.png")
  m.addCommand("HueShift", "nuke.createNode(\"HueShift\")", icon="HueShift.png")
  m.addCommand("HSVTool", "nuke.createNode(\"HSVTool\")", icon="HSVTool.png")
  m.addCommand("Invert", "nuke.createNode(\"Invert\")", icon="Invert.png")
  m.addCommand("Log2Lin", "nuke.createNode(\"Log2Lin\")", icon="Log2Lin.png")
  m.addCommand("PLogLin", "nuke.createNode(\"PLogLin\")", icon="Log2Lin.png")
  m.addCommand("MatchGrade", "nuke.createNode(\"MatchGrade\")", icon="MatchGrade.png")
  m.addCommand("MinColor", "nuke.createNode(\"MinColor\")", icon="MinColor.png")
  m.addCommand("Posterize", "nuke.createNode(\"Posterize\")", icon="Posterize.png")
  m.addCommand("RolloffContrast", "nuke.createNode(\"RolloffContrast\")", icon="RolloffContrast.png")
  m.addCommand("Saturation", "nuke.createNode(\"Saturation\")", icon="Saturation.png")
  m.addCommand("Sampler", "nuke.createNode(\"Sampler\")", icon="Sampler.png")
  m.addCommand("SoftClip", "nuke.createNode(\"SoftClip\")", icon="SoftClip.png")
  m.addCommand("Toe", "nuke.createNode(\"Toe2\")", icon="Toe.png" )


  # The "Filter" menu
  m = toolbar.addMenu("Filter", "ToolbarFilter.png")
  m.addCommand("Blur", "nuke.createNode(\"Blur\")", "b", icon="Blur.png", shortcutContext=dagContext)
  m.addCommand("@;BlurBranch", "nuke.createNode(\"Blur\")", "+b", shortcutContext=dagContext)
  m.addCommand("Bilateral", "nuke.createNode(\"Bilateral2\")", icon="Bilateral.png")
  m.addCommand("BumpBoss", "nuke.createNode(\"BumpBoss\")", icon="BumpBoss.png")
  m.addCommand("Convolve", "nuke.createNode(\"Convolve2\")", icon="Convolve.png")
  m.addCommand("Defocus", "nuke.createNode(\"Defocus\")", icon="Defocus.png")
  m.addCommand("DegrainBlue", "nuke.createNode(\"DegrainBlue\")", icon="DegrainBlue.png")
  m.addCommand("DegrainSimple", "nuke.createNode(\"DegrainSimple\")", icon="DegrainSimple.png")
  m.addCommand("Denoise", "nuke.createNode(\"Denoise2\")", icon="denoise.png")
  m.addCommand("DirBlur", "nuke.createNode(\"DirBlurWrapper\")", icon="DirBlur.png")
  m.addCommand("DropShadow", "nuke.createNode(\"DropShadow\")", icon="DropShadow.png")
  m.addCommand("EdgeBlur", "nuke.createNode(\"EdgeBlur\")", icon="EdgeBlur.png")
  m.addCommand("EdgeDetect", "nuke.createNode(\"EdgeDetectWrapper\")", icon="EdgeDetect.png")
  m.addCommand("EdgeExtend", "nuke.createNode(\"EdgeExtend\")", icon="EdgeExtend.png")
  m.addCommand("Emboss", "nuke.createNode(\"Emboss\")", icon="Emboss.png")
  m.addCommand("Erode (fast)", "nuke.createNode(\"Dilate\")", icon="ErodeFast.png")
  m.addCommand("Erode (filter)", "nuke.createNode(\"FilterErode\")", icon="FilterErode.png")
  m.addCommand("Erode (blur)", "nuke.createNode(\"Erode\")", icon="ErodeBlur.png")
  m.addCommand("Glow", "nuke.createNode(\"Glow2\")", icon="Glow.png")
  m.addCommand("GodRays", "nuke.createNode(\"GodRays\")", icon="GodRays.png")
  m.addCommand("Inpaint", "nuke.createNode(\"Inpaint2\")", icon="Inpaint.png")
  m.addCommand("Laplacian", "nuke.createNode(\"Laplacian\")", icon="Laplacian.png")
  m.addCommand("LevelSet", "nuke.createNode(\"LevelSet\")", icon="LevelSet.png")

  if not assist:
    m.addCommand("Matrix...", "nukescripts.create_matrix()", icon="Matrix.png")
  m.addCommand("Median", "nuke.createNode(\"Median\")", icon="Median.png")
  m.addCommand("MotionBlur", "nuke.createNode(\"MotionBlur\")", icon="MotionBlur2D.png")
  m.addCommand("MotionBlur2D", "nuke.createNode(\"MotionBlur2D\")", icon="MotionBlur2D.png")
  m.addCommand("MotionBlur3D", "nuke.createNode(\"MotionBlur3D\")", icon="MotionBlur3D.png")
  m.addCommand("Sharpen", "nuke.createNode(\"Sharpen\")", icon="Sharpen.png")
  m.addCommand("Soften", "nuke.createNode(\"Soften\")", icon="Soften.png")
  m.addCommand("VectorBlur", "nuke.createNode(\"VectorBlur2\")", icon="VectorBlur.png")
  m.addCommand("VolumeRays", "nuke.createNode(\"VolumeRays\")", icon="VolumeRays.png")
  m.addCommand("ZDefocus", "nuke.createNode(\"ZDefocus2\")", icon="ZBlur.png")
  m.addCommand("ZSlice", "nuke.createNode(\"ZSlice\")", icon="ZSlice.png")


  # The "Keyer" menu
  m = toolbar.addMenu("Keyer", "ToolbarKeyer.png")
  m.addCommand("ChromaKeyer", "nuke.createNode(\"ChromaKeyer\")", icon="ChromaKeyer.png")
  m.addCommand("Cryptomatte", "nuke.createNode(\"Cryptomatte\")", icon="Cryptomatte.png")
  m.addCommand("Difference", "nuke.createNode(\"Difference\")", icon="DifferenceKeyer.png")
  m.addCommand("HueKeyer", "nuke.createNode(\"HueKeyer\")", icon="HueKeyer.png")
  if not assist:
    m.addCommand("IBKColour", "nuke.tcl(\"IBKColourV3\")", icon="IBKColour.png")
    m.addCommand("IBKGizmo", "nuke.tcl(\"IBKGizmoV3\")", icon="IBKGizmo.png")
  m.addCommand("Keyer", "nuke.createNode(\"Keyer\")", icon="Keyer.png")
  m.addCommand("Keylight", 'nuke.createNode("OFXuk.co.thefoundry.keylight.keylight_v201")', icon="Keylight.png")
  m.addCommand("Primatte", "nuke.createNode(\"Primatte3\")", icon="Primatte.png")
  m.addCommand("Ultimatte", "nuke.createNode(\"Ultimatte\")", icon="Ultimatte.png")


  # The "Merge" menu
  m = toolbar.addMenu("Merge", "ToolbarMerge.png")
  m.addCommand("AddMix", "nuke.createNode(\"AddMix\")", "+a", icon="AddMix.png", shortcutContext=dagContext)
  m.addCommand("KeyMix", "nuke.createNode(\"Keymix\")", icon="Keymix.png")
  m.addCommand("ContactSheet", "nuke.createNode(\"ContactSheet\")", icon="ContactSheet.png")
  m.addCommand("CopyBBox", "nuke.createNode(\"CopyBBox\")", icon="CopyBBox.png")
  m.addCommand("CopyRectangle", "nuke.createNode(\"CopyRectangle\")", icon="CopyRectangle.png")
  m.addCommand("Dissolve", "nuke.createNode(\"Dissolve\")", icon="Dissolve.png")
  m.addCommand("LayerContactSheet", "nuke.createNode(\"LayerContactSheet\")", icon="LayerContactSheet.png")
  m.addCommand("Merge", "nuke.createNode(\"Merge2\")", "m", icon="Merge.png", shortcutContext=dagContext)
  m.addCommand("@;MergeBranch", "nuke.createNode(\"Merge2\")", "+m", shortcutContext=dagContext)

  n = m.addMenu("Merges", "Merge.png")
  if not assist:
    n.addCommand("Plus", "nuke.createNode(\"Merge2\", \"operation plus name Plus\", False)", icon="MergePlus.png")
    n.addCommand("Matte", "nuke.createNode(\"Merge2\", \"operation matte name Matte\", False)", icon="MergeMatte.png")
    n.addCommand("Multiply", "nuke.createNode(\"Merge2\", \"operation multiply name Multiply\", False)", icon="MergeMultiply.png")
    n.addCommand("In", "nuke.createNode(\"Merge2\", \"operation in name In\", False)", icon="MergeIn.png")
    n.addCommand("Out", "nuke.createNode(\"Merge2\", \"operation out name Out\", False)", icon="MergeOut.png")
    n.addCommand("Screen", "nuke.createNode(\"Merge2\", \"operation screen name Scrn\", False)", icon="MergeScreen.png")
    n.addCommand("Max", "nuke.createNode(\"Merge2\", \"operation max name Max\", False)", icon="MergeMax.png")
    n.addCommand("Min", "nuke.createNode(\"Merge2\", \"operation min name Min\", False)", icon="MergeMin.png")
    n.addCommand("Absminus", "nuke.createNode(\"Merge2\", \"operation difference name Difference\", False)", icon="MergeDifference.png")
    m.addCommand("MergeExpression", "nuke.createNode(\"MergeExpression\")", icon="MergeExpression.png")
  m.addCommand("Switch", "nuke.createNode(\"Switch\")", icon="Switch.png")
  if not assist:
    m.addCommand("TimeDissolve", "nuke.createNode(\"TimeDissolve\")", icon="TimeDissolve.png")
  m.addCommand("Premult", "nuke.createNode(\"Premult\")", icon="Premult.png")
  m.addCommand("Unpremult", "nuke.createNode(\"Unpremult\")", icon="Unpremult.png")
  if not assist:
    m.addCommand("Blend", "nuke.createNode(\"Blend\")", icon="Blend.png")
    m.addCommand("ZMerge", "nuke.createNode(\"ZMerge\")", icon="ZMerge.png")


  # The "Transform" menu
  m = toolbar.addMenu("Transform", "ToolbarTransform.png")
  m.addCommand("Transform", "nuke.createNode(\"Transform\")", "t", icon="2D.png", shortcutContext=dagContext)
  m.addCommand("@;Transform Branch", "nuke.createNode(\"Transform\")", "+t", shortcutContext=dagContext)
  m.addCommand("TransformMasked", "nuke.createNode(\"TransformMasked\")", icon="2DMasked.png")
  m.addCommand("Card3D", "nuke.createNode(\"Card3D\")", icon="3D.png")
  m.addCommand("AdjustBBox", "nuke.createNode(\"AdjBBox\")", icon="AdjBBox.png")
  m.addCommand("BlackOutside", "nuke.createNode(\"BlackOutside\")", icon="BlackOutside.png")
  m.addCommand("CameraShake", "nuke.createNode(\"CameraShake3\")", icon="CameraShake.png")
  m.addCommand("Crop", "nuke.createNode(\"Crop\")", icon="Crop.png")
  m.addCommand("CornerPin", "nuke.createNode(\"CornerPin2D\")", icon="CornerPin.png")
  m.addCommand("VectorCornerPin", "nuke.createNode(\"VectorCornerPin\")", icon="VectorCornerPin.png")
  m.addCommand("SphericalTransform", "nuke.createNode(\"SphericalTransform2\")", icon="EnvironMaps.png")
  m.addCommand("IDistort", "nuke.createNode(\"IDistort\")", icon="IDistort.png")
  m.addCommand("VectorDistort", "nuke.createNode(\"VectorDistort\")", icon="VectorDistort.png")
  m.addCommand("LensDistortion", "nuke.createNode(\"LensDistortion2\")", icon="LensDistort.png")
  m.addCommand("Mirror", "nuke.createNode(\"Mirror2\")", icon="Mirror.png")
  m.addCommand("Position", "nuke.createNode(\"Position\")", icon="Position.png")
  m.addCommand("Reformat", "nuke.createNode(\"Reformat\")", icon="Reformat.png")
  m.addCommand("Reconcile3D", "nuke.createNode(\"Reconcile3D\")", icon="Reconcile3D.png")
  m.addCommand("PointsTo3D", "nuke.createNode(\"PointsTo3D\")", icon="PointsTo3D.png")
  m.addCommand("PlanarTracker", "nukescripts.createPlanartracker()", icon="planar_tracker.png")
  m.addCommand("Tracker", "nuke.createNode(\"Tracker4\")", icon="Tracker.png")
  m.addCommand("TVIScale", "nuke.createNode(\"TVIscale\")", icon="TVIScale.png")
  m.addCommand("GridWarp", "nuke.createNode(\"GridWarp3\")", icon="GridWarp.png")
  m.addCommand("GridWarpTracker", "nuke.createNode(\"GridWarpTracker\")", icon="GridWarpTracker.png")
  m.addCommand("SplineWarp", "nuke.createNode(\"SplineWarp3\")", icon="SplineWarp.png")
  m.addCommand("Stabilize", "nuke.createNode(\"Stabilize2D\")", icon="Stabilize.png")  
  m.addCommand("STMap", "nuke.createNode(\"STMap\")", icon="STMap.png")
  m.addCommand("Tile", "nuke.createNode(\"Tile\")", icon="Tile.png")

  #m.addCommand("AutoCrop", "nukescripts.autocrop()", icon="AutoCrop.png")


  # The "3D" menu
  m = toolbar.addMenu("3D", "Cube.png")

  m.addCommand("Axis", "nuke.createNode(\"Axis3\")", icon="Axis.png")

  n = m.addMenu("Geometry", "Geometry.png")
  n.addCommand("Card", "nuke.createNode(\"Card2\")", icon="Card.png")
  n.addCommand("Cube", "nuke.createNode(\"Cube\")", icon="Cube.png")
  n.addCommand("Cylinder", "nuke.createNode(\"Cylinder\")", icon="Cylinder.png")
  n.addCommand("DepthToPoints", "nuke.createNode(\"DepthToPoints\")", icon="DepthToPoints.png")
  #n.addCommand("Modeler", "nuke.createNode(\"Modeler\")", icon="Modeler.png")
  n.addCommand("ModelBuilder", "nuke.createNode(\"ModelBuilder\")", icon="Modeler.png")
  n.addCommand("PointCloudGenerator", "nuke.createNode(\"PointCloudGenerator\")", icon="PointCloudGenerator.png")
  n.addCommand("PositionToPoints", "nuke.createNode(\"PositionToPoints2\")", icon="PositionToPoints.png")
  n.addCommand("PoissonMesh", "nuke.createNode(\"PoissonMesh\")", icon="PoissonMesh.png")
  n.addCommand("Sphere", "nuke.createNode(\"Sphere\")", icon="Sphere.png")
  n.addCommand("ReadGeo", "nuke.createNode(\"ReadGeo2\")", icon="ReadGeo.png")
  n.addCommand("WriteGeo", "nuke.createNode(\"WriteGeo\")", icon="WriteGeo.png")

  n = m.addMenu("Lights", "Toolbar3DLights.png")
  n.addCommand("Light", "nuke.createNode(\"Light3\")", icon="PointLight.png")
  n.addCommand("Point", "nuke.createNode(\"Light\")", icon="PointLight.png")
  n.addCommand("Direct", "nuke.createNode(\"DirectLight\")", icon="DirectLight.png")
  n.addCommand("Spot", "nuke.createNode(\"Spotlight\")", icon="SpotLight.png")
  n.addCommand("Environment", "nuke.createNode(\"Environment\")", icon="Environment.png")
  n.addCommand("Relight", "nuke.createNode(\"ReLight\")", icon="ReLight.png")

  n = m.addMenu("Modify", "Modify.png")
  n.addCommand("TransformGeo", "nuke.createNode(\"TransformGeo\")", icon="Modify.png")
  n.addCommand("MergeGeo", "nuke.createNode(\"MergeGeo\")", icon="Modify.png")
  n.addCommand("CrosstalkGeo", "nuke.createNode(\"CrosstalkGeo\")", icon="Modify.png")
  #n.addCommand("Connect Points", "nuke.createNode(\"ConnectPointsGeo\")", icon="Modify.png")
  n.addCommand("DisplaceGeo", "nuke.createNode(\"DisplaceGeo\")", icon="Modify.png")
  n.addCommand("EditGeo", "nuke.createNode(\"EditGeo\")", icon="Modify.png")
  n.addCommand("GeoSelect", """nuke.createNode("GeoSelect")""", icon="Modify.png")
  n.addCommand("LookupGeo", "nuke.createNode(\"LookupGeo\")", icon="Modify.png")
  n.addCommand("LogGeo", "nuke.createNode(\"LogGeo\")", icon="Modify.png")
  n.addCommand("Normals", "nuke.createNode(\"Normals\")", icon="Modify.png")
  n.addCommand("ProceduralNoise", "nuke.createNode(\"ProcGeo\")", icon="Modify.png")
  n.addCommand("RadialDistort", "nuke.createNode(\"RadialDistort\")", icon="Modify.png")
  n.addCommand("Trilinear", "nuke.createNode(\"Trilinear\")", icon="Modify.png")
  n.addCommand("UVProject", "nuke.createNode(\"UVProject\")", icon="Modify.png")
  #n.addCommand("VectorfieldGeo", "nuke.createNode(\"VectorfieldGeo\")", icon="Modify.png")
  #n.addCommand("Vectorfield Create", "nuke.createNode(\"VectorfieldCreateGeo\")", icon="Modify.png")
  n = n.addMenu("RenderMan", "Modify.png")
  n.addCommand("ModifyRIB", "nuke.createNode(\"ModifyRIB\")", icon="Modify.png")

  n = m.addMenu("Shader", "Shaders.png")
  n.addCommand("AmbientOcclusion", "nuke.createNode(\"AmbientOcclusion\")", icon="Shader.png")
  n.addCommand("ApplyMaterial", "nuke.createNode(\"ApplyMaterial\")", icon="Shader.png")
  n.addCommand("BasicMaterial", "nuke.createNode(\"BasicMaterial\")", icon="Shader.png")
  n.addCommand("FillMat", "nuke.createNode(\"FillMat\")", icon="Shader.png")
  n.addCommand("MergeMat", "nuke.createNode(\"MergeMat\")", icon="Shader.png")
  n.addCommand("BlendMat", "nuke.createNode(\"BlendMat\")", icon="Shader.png")
  n.addCommand("Project3D", "nuke.createNode(\"Project3D2\")", icon="Shader.png")
  n.addCommand("Diffuse", "nuke.createNode(\"Diffuse\")", icon="Shader.png")
  n.addCommand("Emission", "nuke.createNode(\"Emission\")", icon="Shader.png")
  n.addCommand("Phong", "nuke.createNode(\"Phong\")", icon="Shader.png")
  n.addCommand("Specular", "nuke.createNode(\"Specular\")", icon="Shader.png")
  n.addCommand("Displacement", "nuke.createNode(\"Displacement\")", icon="Shader.png")
  if not assist:
    n.addCommand("UVTile", "nukescripts.createUVTile()", icon="Shader.png")
  n.addCommand("Wireframe", "nuke.createNode(\"Wireframe\")", icon="Shader.png")
  n.addCommand("Transmission", "nuke.createNode(\"Transmission\")", icon="Shader.png")
  n = n.addMenu("RenderMan", "Shaders.png")
  n.addCommand("Reflection", "nuke.createNode(\"Reflection\")", icon="Shader.png")
  n.addCommand("Refraction", "nuke.createNode(\"Refraction\")", icon="Shader.png")

  m.addCommand("Camera", "nuke.createNode(\"Camera3\")", icon="Camera.png")
  m.addCommand("CameraTracker", "nuke.createNode(\"CameraTracker\")", icon="CameraTracker.png")
  m.addCommand("DepthGenerator", "nuke.createNode(\"DepthGenerator\")", icon="DepthGenerator.png")
  m.addCommand("DepthToPosition", "nuke.createNode(\"DepthToPosition\")", icon="DepthToPosition.png")
  m.addCommand("Scene", "nuke.createNode(\"Scene\")", icon="Scene.png")
  m.addCommand("ScanlineRender", "nuke.createNode(\"ScanlineRender\")", icon="Render.png")
  m.addCommand("RayRender", "nuke.createNode(\"RayRender\")", icon="Render.png")

  if not assist:
    m = m.addMenu("RenderMan", "Toolbar3D.png")
    m.addCommand("PrmanRender","nukescripts.createPrmanRender()", icon="Render.png")

  # particles menu
  m = toolbar.addMenu("Particles", "ToolbarParticles.png")
  m.addCommand("ParticleEmitter")

  m.addCommand("ParticleBounce")
  m.addCommand("ParticleCache", icon="ParticleCache.png")
  m.addCommand("ParticleCurve")
  m.addCommand("ParticleDirectionalForce")
  m.addCommand("ParticleDrag", "nuke.createNode('ParticleDrag2')", icon="ParticleDrag.png")
  m.addCommand("ParticleExpression")
  m.addCommand("ParticleMerge")
  m.addCommand("ParticleMotionAlign")
  m.addCommand("ParticleGravity")

  #Disable ParticleLineForce for now as it is not ready for being included in the bundle - Bug 30000
  # m.addCommand("ParticleLineForce")

  m.addCommand("ParticleLookAt")
  m.addCommand("ParticlePointForce")
  m.addCommand("ParticleSpeedLimit")
  m.addCommand("ParticleSpawn")
  m.addCommand("ParticleTurbulence")
  m.addCommand("ParticleVortex")
  m.addCommand("ParticleWind")

  m.addCommand("ParticleSettings", icon="particle_settings.png")

  m.addCommand("ParticleToGeo")

  m.addCommand("ParticleBlinkScript", icon="ParticleBlinkScript.png")

  n = m.addMenu("ParticleBlinkScript Gizmos", "ParticleBlinkScript.png")
  n.addCommand("ParticleColorByAge", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleKill", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleProjectDisplace", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleProjectImage", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleGrid", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleDirection", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleFuse", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleDistributeSphere", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleCylinderFlow", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleConstrainToSphere", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleFlock", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleAttractToSphere", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleHelixFlow", icon="ParticleBlinkScript.png")
  n.addCommand("ParticleShockWave", icon="ParticleBlinkScript.png")

  m.addCommand("ParticleInfo", icon="ParticleInfo.png")

  # deep menu
  m = toolbar.addMenu("Deep", "ToolbarDeep.png")
  m.addCommand("DeepColorCorrect", "nuke.createNode('DeepColorCorrect2')" )
  m.addCommand("DeepCrop")
  m.addCommand("DeepExpression")
  m.addCommand("DeepFromFrames")
  m.addCommand("DeepFromImage")
  m.addCommand("DeepMerge", "nuke.createNode('DeepMerge2')")
  if not assist:
    m.addCommand("DeepRead", '''nukescripts.create_read("DeepRead")''')
  m.addCommand("DeepRecolor")
  m.addCommand("DeepReformat")
  m.addCommand("DeepSample")
  m.addCommand("DeepToImage")
  m.addCommand("DeepToImage", "nuke.createNode('DeepToImage2')")
  m.addCommand("DeepToPoints")
  m.addCommand("DeepTransform")
  m.addCommand("DeepWrite")

  # Views menu
  m = toolbar.addMenu("Views", "ToolbarViews.png")
  n = m.addMenu("Stereo", "ToolbarStereo.png")
  n.addCommand("Anaglyph", "nuke.createNode(\"Anaglyph\")", icon="Anaglyph.png")
  n.addCommand("MixViews", "nuke.createNode(\"MixViews\")", icon="MixViews.png")
  n.addCommand("SideBySide", "nuke.createNode(\"SideBySide\")", icon="SideBySide.png")
  n.addCommand("ReConverge", "nuke.createNode(\"ReConverge\")", icon="ReConverge.png")

  m.addCommand("JoinViews", "nuke.createNode(\"JoinViews\")", icon="JoinViews.png")
  m.addCommand("OneView", "nuke.createNode(\"OneView\")", icon="OneView.png")
  m.addCommand("ShuffleViews", "nuke.createNode(\"ShuffleViews\")", icon="ShuffleViews.png")
  m.addCommand("Split and Join", "nukescripts.create_viewsplitjoin()", icon="SplitAndJoin.png")

  m = toolbar.addMenu("MetaData", "MetaData.png")
  m.addCommand("ViewMetaData", "nuke.createNode(\"ViewMetaData\")", icon="ViewMetaData.png")
  m.addCommand("CompareMetaData", "nuke.createNode(\"CompareMetaData\")", icon="CompareMetaData.png")
  m.addCommand("ModifyMetaData", "nuke.createNode(\"ModifyMetaData\")", icon="ModifyMetaData.png")
  m.addCommand("CopyMetaData", "nuke.createNode(\"CopyMetaData\")", icon="CopyMetaData.png")
  m.addCommand("AddTimeCode", "nuke.createNode(\"AddTimeCode\")", icon="AddTimeCode.png")

  import nukescripts.toolsets
  nukescripts.toolsets.createToolsetsMenu(toolbar)
  nukescripts.createNodePresetsMenu()


  # The "Other" menu
  m = toolbar.addMenu("Other", "ToolbarOther.png")
  m.addCommand("AudioRead", "nuke.createNode(\"AudioRead\")", icon="Read.png")
  m.addCommand("Assert", "nuke.createNode(\"Assert\")", icon="Assert.png")
  m.addCommand("Backdrop", "nukescripts.autoBackdrop()", icon="Backdrop.png")
  m.addCommand("BlinkScript", "nuke.createNode(\"BlinkScript\")", icon="BlinkScript.png")
  m.addCommand("DiskCache", "nuke.createNode(\"DiskCache\")", ".", icon="DiskCache.png", shortcutContext=dagContext)
  m.addCommand("Dot", "nuke.createNode(\"Dot\", inpanel=False)", ".", icon="Dot.png", shortcutContext=dagContext)
  m.addCommand("Input", "nuke.createNode(\"Input\")", icon="Input.png")
  m.addCommand("Output", "nuke.createNode(\"Output\")", icon="Output.png")
  m.addCommand("NoOp", "nuke.createNode(\"NoOp\")", icon="NoOp.png")
  m.addCommand("PostageStamp", "nuke.createNode(\"PostageStamp\")", icon="PostageStamp.png")
  m.addCommand("Group", "nuke.collapseToGroup()", icon="Group.png")
  if not assist:
    m.addCommand("Precomp", "nukescripts.precomp_selected()","^+p", icon="Precomp.png", shortcutContext=dagContext)
    m.addCommand("LiveGroup", "nuke.collapseToLiveGroup()", icon="Group.png")
    m.addCommand("LiveInput", "nuke.createLiveInput()", icon="Input.png")

  m.addCommand("StickyNote", "nukescripts.toolbar_sticky_note()", "#n", icon="StickyNote.png", shortcutContext=dagContext)
  n = m.addMenu("All plugins", "AllPlugins.png")
  n.addCommand("Update", "nukescripts.update_plugin_menu(\"All plugins\")")

  # The OFX plugins menus
  nuke.ofxMenu("")

  # Have to remove some of the furnace core nodes that get added automatically in nuke.ofxMenu()
  m = toolbar.menu("FurnaceCore")
  if (m != None):
    m.removeItem("F_DeGrain")
    m.removeItem("F_DeNoise")
    m.removeItem("F_Kronos")
    m.removeItem("F_MotionBlur")
    m.removeItem("F_VectorGenerator")
    m.removeItem("F_MatchGrade")

  # Denoise2 needs to be added after the OFX plugins menus
  m = toolbar.menu( 'Filter' )
  if m == None or not hasattr(m, 'addCommand'):
    # If the Filter menu is empty, eg no whitelisted filter plugins in Nuke Assist,
    # we must create the menu afresh, as it will not exist
    m = toolbar.addMenu("Filter", "ToolbarFilter.png")
  if m != None and hasattr(m, 'addCommand'):
    m.addCommand("Denoise", "nuke.createNode(\"Denoise2\")", icon="denoise.png")

  # OFlow needs to be added after the OFX plugins menus
  m = toolbar.menu( 'Time' )
  if m == None or not hasattr(m, 'addCommand'):
    # If the Filter menu is empty, eg no whitelisted filter plugins in Nuke Assist,
    # we must create the menu afresh, as it will not exist
    m = toolbar.addMenu("Time", "ToolbarTime.png")
  if m != None and hasattr(m, 'addCommand'):
    m.addCommand("OFlow", "nukescripts.createOFlow()", icon="Oflow.png")

  # AIR plugins menu
  m = toolbar.addMenu("AIR", "ToolbarAIR.png")
  m.addCommand("CopyCat", "nuke.createNode(\"CopyCat\")", icon="CopyCat.png")
  m.addCommand("Inference", "nuke.createNode(\"Inference\")", icon="Inference.png")
  m.addCommand("Deblur", "nuke.createNode(\"Deblur\")", icon="Deblur.png")
  m.addCommand("Upscale", "nuke.createNode(\"Upscale\")", icon="Upscale.png")

  m = None
  n = None

def createCurveTool():
  n = nuke.createNode( 'CurveTool' )
  if n.input(0):
    n['resetROI'].execute()

def createKronos():
  n = nuke.createNode( 'Kronos' )
  if n.input(0):
    n['resetInputRange'].execute()

def createOFlow():
  n = nuke.createNode('OFlow2');
  if n.input(0):
    n['resetInputRange'].execute()

# Some helper functions that we can call from the toolbar items.

def create_time_warp():
  t = nuke.createNode("TimeWarp")
  a = nuke.value(t.name()+".first_frame")
  e = nuke.value(t.name()+".last_frame")
  if float(e)<=float(a):
    a = nuke.value("root.first_frame")
    e = nuke.value("root.last_frame")
  cmd = "{curve C x"+a+" "+a+" x"+e+" "+e+"}"
  t.knob("lookup").fromScript(cmd)


def create_matrix():
  p = nuke.Panel("Enter desired matrix size:")
  p.addSingleLineInput("width", 3)
  p.addSingleLineInput("height", 3)
  ret = p.show()
  if ret == 1:
    wdt = p.value("width")
    hgt = p.value("height")
    a = " { "+" 0 "*int(wdt)+" } "
    a = "{ " + a*int(hgt) + " }"
    nuke.createNode("Matrix", "matrix "+a)


def toolbar_sticky_note():
  sticky = nuke.createNode("StickyNote")
  sticky.knob("label").setValue("type note here")
  sticky.knob("selected").setValue(False)

def createPrmanRender():
  try:
    nuke.createNode( "PrmanRender" )
  except:
    msg = "Could not create PrmanRender node.\n\nThis is usually because the library search path environment variable is not set correctly so Nuke can't link with the prman libraries.\n"
    if 'RMANTREE' not in os.environ:
      msg = msg + "\nAlso, the RMANTREE environment variable is not set.\n"

    if  nuke.env['MACOS']:
      msg = msg + "\nIf you are launching Nuke from an icon on Mac OSX you may need to add environment variable settings to your environment plist file (~/.MacOSX/environment.plist).\n"
    msg = msg + "\nCheck your Pixar Photorealistic Renderman documentation section \"RenderMan Pro Server > Administration > Installation\" for platform-specific installation instructions."

    nuke.message( msg )

def createUVTile():
  uvtile_node = nuke.createNode("UVTile2")
  n = uvtile_node.input(0)

  if n != None and n.Class() == 'Read':
    filename = n['file'].getValue()
    udim = nukescripts.parseUdimFile(filename)
    if udim != None:
      uvtile_node['udim_enable'].setValue(True)
      uvtile_node['udim'].setValue(udim)

def createPlanartracker():

  rotoNode = nuke.createNode("Roto", "output {rgba.alpha none none mask_planartrack.a}", False)
  rotoLayerId = 1
  rotoLayerName = "PlanarTrackLayer"+str(rotoLayerId)

  rotoTrackLayer = rotoNode.name() + "." + str(rotoLayerId) + "." + rotoLayerName

  rotoCurves = rotoNode["curves"]
  rotoCurveRoot = rotoCurves.rootLayer
  planarLayer = nuke.rotopaint.Layer(rotoCurves)
  rotoCurveRoot.append(planarLayer)
  atr = planarLayer.getAttributes()
  planarLayer.name = rotoLayerName
  planarLayer.getAttributes().set(nuke.rotopaint.AnimAttributes.kPlanarTrackLayerAttribute,rotoLayerId)

  rotoNode.showControlPanel()
  planarLayer.setFlag(nuke.rotopaint.FlagType.eSelectedFlag, 1)
  rotoCurves.changed()
  rotoNode["toolbox"].setValue(4)
