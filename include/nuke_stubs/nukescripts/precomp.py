# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.
import nuke
import os, re, sys, math, time
from nukescripts import execute_panel
from nukescripts import panels

class PrecompOptionsDialog( panels.PythonPanel ):
  def __init__( self ):
    panels.PythonPanel.__init__( self, "Precomp Nodes", "uk.co.thefoundry.PrecompOptionsDialog" )
    self.scriptPath = nuke.File_Knob( "script", "Precomp script path " )
    self.renderPath = nuke.File_Knob( "render", "Precomp render path " )
    self.channels = nuke.Channel_Knob( "channels", "Channels " )
    self.origNodes = nuke.Enumeration_Knob( "orig", "Original nodes ", ["add backdrop", "delete", "no change" ] )
    self.addKnob ( self.scriptPath )
    self.addKnob ( self.renderPath )
    self.addKnob ( self.channels )
    self.addKnob ( self.origNodes )

    self.channels.setValue('all')

    defaultDir = nuke.Root()['name'].value()
    if defaultDir and defaultDir != "":
      defaultDir = os.path.dirname( defaultDir )
      if not defaultDir.endswith("/"):
        defaultDir += "/"
    else:
      defaultDir = ""

    basename = findNextName("Precomp")
    self.scriptPath.setValue( defaultDir + basename + "_v01.nk" )
    self.renderPath.setValue( defaultDir + basename + ".####.exr" )
    self.setMinimumSize( 420, 50 )

class PrecompOptions:
  def __init__(self):
    self.scriptPath = ""
    self.renderPath = ""
    self.channels = ""
    self.addBackdrop = False
    self.delete = False

  def askUserForOptions(self):
    p = PrecompOptionsDialog()
    result = p.showModalDialog()
    if result:
      self.scriptPath = p.scriptPath.value()
      self.renderPath = p.renderPath.value()
      self.channels = p.channels.value()
      if p.origNodes.value() == "delete":
        self.delete = True
      elif p.origNodes.value() == "add backdrop":
        self.addBackdrop = True

      if nuke.env['nc']:
        nukeExt = ".nknc"
      if nuke.env['indie']:
        nukeExt = ".nkind"
      else:
        nukeExt = ".nk"

      (root, ext) = os.path.splitext(self.scriptPath)
      if not ext:
        self.scriptPath += nukeExt
      elif ext == ".nk" and ext != nukeExt:
        self.scriptPath = self.scriptPath[0:-3] + nukeExt

      (root,ext) = os.path.splitext(self.renderPath)
      if not ext:
        self.renderPath += ".exr"

      if os.path.exists(self.scriptPath):
        if not nuke.ask("Overwrite existing " + self.scriptPath + " ?"):
          return False
      return True
    else:
      return False

def precomp_open(precomp):
  precomp.executePythonCallback(nuke.PRECOMP_CALLBACK_OPENED)
  nuke.Root().setModified( True )
  nuke.scriptOpen(precomp["file"].evaluate())

def precomp_render(precomp):
  reading = precomp["reading"].getValue()
  precomp["reading"].setValue( False )
  try:
    finalNode = None
    if precomp['useOutput'].value() == True:
      finalNode = nuke.toNode( precomp['output'].value() )
    else:
      if precomp.output() and precomp.output().input(0):
        finalNode = precomp.output().input(0)
    execute_panel( [ finalNode ] )
  except RuntimeError as e:
    if e.message[0:9] != "Cancelled":   # TO DO: change this to an exception type
      raise
    return
  precomp["reading"].setValue( True )

def findNextName(name):
  i = 1
  while nuke.toNode ( name + str(i) ) != None:
    i += 1

  return name + str(i)

def precomp_copyToGroup(precomp):

  ## group context is set to precomp, so back up one level.
  nuke.endGroup()

  g = nuke.nodes.Group()
  with precomp:
    nuke.selectAll()
    nuke.nodeCopy ( '%clipboard%' )

  with g:
    nuke.nodePaste( '%clipboard%' )

  for k in ['label', 'icon', 'indicators', 'tile_color', 'disable']:
    v =  precomp[k].value()
    if v:
      g[k].setValue( v )

  for k in precomp.allKnobs():
    if isinstance( k, nuke.Link_Knob ):
      lnk = nuke.Link_Knob( k.name() )
      lnk.setLink( k.getLink() )
      g.addKnob( lnk )

def precomp_selected():

  nodes = nuke.selectedNodes()
  if len(nodes) == 0:
    g = nuke.createNode( "Precomp" )
    return

  options = PrecompOptions()

  if not options.askUserForOptions():
    return False

  sel = nodes[0]

  ## select upstream nodes
  if len( nodes ) == 1:
    upstreamNodes = nuke.dependencies( nodes )
    while len ( upstreamNodes ) != 0:
      nodes += upstreamNodes
      upstreamNodes = nuke.dependencies( upstreamNodes )

  left = right = nodes[0].xpos()
  top = bottom = nodes[0].ypos()

  nodeSize = 100
  titleHeight = 50

  inputs = []

  for n in nodes:
    n["selected"].setValue ( True )
    if n.xpos() < left:
      left = n.xpos()

    if n.xpos() > right:
      right = n.xpos()

    if n.ypos() < top:
      top = n.ypos()

    if n.ypos() > bottom:
      bottom = n.ypos()

    for i in range( 0, n.inputs() ):
      if not n.input(i):
        continue

      if not n.input(i) in nodes:
        inputs.append( n.input(i) )

  ## find all the dependent nodes
  inputDeps = []
  expressionDeps = []

  for n in nodes:
    for d in nuke.dependentNodes( nuke.INPUTS, [n]):
      if d not in nodes:
        if d.Class() != 'Viewer':
          inputIndices = [i for i in range(d.inputs()) if d.input(i) == n]
          inputDeps.append( (d, inputIndices) )

    for d in nuke.dependencies( [n], nuke.EXPRESSIONS ):
      if d not in nodes:
        expressionDeps.append( d )

  if len(inputDeps) > 1:
    nuke.message( "You cannot precomp the selected nodes because there are multiple outputs." )
    return

  addLinkedExpressionNodes = False
  if len(expressionDeps) > 0:
    addLinkedExpressionNodes = nuke.ask( "Warning: The selected nodes have expressions to nodes outside the precomp. Do you want to copy these nodes to the precomp?" )

  ## make group and export
  if len( nodes ) == 1 and nodes[0].Class() == "Group":
    group = nodes[0]
  else:
    group = nuke.makeGroup( False )

  with group:
    outputInputs = []
    output = group.output()
    for i in range(0, output.inputs()):
      outputInputs.append( output.input(i) )

    ## insert write node or use existing one
    outInp = output.input(0)
    if outInp is None or outInp.Class() != "Write":
      w = nuke.createNode( "Write", inpanel = False)
      w.setInput( 0, None )
    else:
      w = outInp

    for i in range(0, len(outputInputs) ):
      w.setInput( i, outputInputs[i] )
      output.setInput(i, None )

    output.setInput(0, w )

    w.knob("file").setValue( options.renderPath )
    type = os.path.splitext( options.renderPath)[1][1:].lower()
    w.knob("file_type").setValue( type )
    w.knob("channels").setValue( options.channels )

    for n in nuke.allNodes():
      n['selected'].setValue( False )

  if addLinkedExpressionNodes:
    for n in nuke.allNodes():
      n['selected'].setValue( False )

    for n in expressionDeps:
      n['selected'].setValue( True )

    nuke.nodeCopy ( '%clipboard%' )

    with group:
      nuke.nodePaste( '%clipboard%' )

  writeOk = True
  with group:
    try:
      nuke.tcl("export_as_precomp",  options.scriptPath)
    except:
      nuke.message( "Could not write precomp script, permission denied, please specify a different \'script path\' and try again.")
      writeOk = False

    for n in nuke.selectedNodes():
      n['selected'].setValue( False )

  if group != nodes[0]:
    group['selected'].setValue( False )
    nuke.delete( group )

  if not writeOk:
    for n in nuke.selectedNodes():
      n['selected'].setValue( False )

    for n in nodes:
      n['selected'].setValue( True )

    return

  ## reload saved out script
  g = nuke.createNode( "Precomp" )
  g[ "file" ].setValue( options.scriptPath )

  #nuke.tprint( "Selected Node: " + sel.name() )

  for d in inputDeps:
    node = d[0]
    for inp in d[1]:
      #nuke.tprint ( "Reconnecting dep " + node.name() + " input " + str(inp) )
      node.setInput(inp, g)

  ## reconnect inputs, if any
  for i in range(0, len(inputs)):
    #nuke.tprint ( "Reconnecting input " + inputs[i].name() + " " + str(i) )
    g.setInput(i, inputs[i] )

  pad = 5

  if options.addBackdrop:
    b = nuke.createNode( "BackdropNode", inpanel = False )
    width = int(math.fabs(right - left)) + (pad * 2) + nodeSize
    height = int(math.fabs(bottom - top)) + ( pad * 2 ) + nodeSize + titleHeight
    b['label'].setValue( os.path.basename( options.scriptPath ) )
    b['note_font_size'].setValue( 18 )
    b.setXYpos( left - pad * 2, top - ( pad * 2) - titleHeight )
    b.knob( "bdwidth" ).setValue( width  )
    b.knob( "bdheight").setValue( height )
    b.knob( "z_order" ).setValue( 0 )
    b['selected'].setValue(False)
    g.setXYpos( b.xpos() + width/2 - nodeSize/2, b.ypos() + height + pad * 2 )
  elif options.delete:
    for n in nodes:
      nuke.delete( n )

  if len(inputs) > 0:
    nuke.message( "Warning: The precomp script requires inputs and may not render the same independent of its parent script." )

  return group
