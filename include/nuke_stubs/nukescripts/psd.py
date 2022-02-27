#####
##
##  Uses meta-data from the incoming image stream to break a PSD files into layers
#
#   Each layer is combined together with a PSDMerge node which emulates the blending modes
#


import nuke
import random
import math
import threading


class Layer():
  def __init__(self):
    self.attrs = {}

def getLayers(metadata):
  layers = []

  for key in metadata:
    if key.startswith( 'input/psd/layers/' ):
      splitKey = key.split( '/' )
      num = int( splitKey[3] )
      attr = splitKey[4]
      try:
        attr += '/' + splitKey[5]
      except:
        pass

      while ( len(layers) <= num ):
        layers.append( Layer() )
      layers[num].attrs[ attr ] = metadata[key]


  return layers

def breakoutLayers( node, sRGB = True ):

  if not node:
    return

  nuke.Undo().begin()

  blendMap = {}
  blendMap['norm'] = "normal"
  blendMap['scrn'] = "screen"
  blendMap['div '] = "color dodge"
  blendMap['over'] = "overlay"
  blendMap['mul '] = "multiply"
  blendMap['dark'] = "darken"
  blendMap['idiv'] = "color burn"
  blendMap['lbrn'] = "linear burn"
  blendMap['lite'] = "lighten"
  blendMap['lddg'] = "linear dodge"
  blendMap['lgCl'] = "lighter color"
  blendMap['sLit'] = "soft light"
  blendMap['hLit'] = "hard light"
  blendMap['lLit'] = "linear light"
  blendMap['vLit'] = "vivid light"
  blendMap['pLit'] = "pin light"
  blendMap['hMix'] = "hard mix"
  blendMap['diff'] = "difference"
  blendMap['smud'] = "exclusion"
  blendMap['fsub'] = "subtract"
  blendMap['fdiv'] = "divide"
  blendMap['hue '] = "hue"
  blendMap['sat '] = "saturation"
  blendMap['colr'] = "color"
  blendMap['lum '] = "luminosity"

  metaData = node.metadata()
  layers = getLayers(metaData)

  xspacing = 80

  dotXfudge = 34
  dotYfudge = 4

  backdropXfudge = -( xspacing/2 ) + 10
  backdropYfudge = -40

  spacing = 70

  x = node.xpos()
  y = node.ypos()
  curY = y + spacing * 2

  if not sRGB:
    colorSpace = nuke.nodes.Colorspace()
    colorSpace['channels'].setValue( 'all' )
    colorSpace['colorspace_out'].setValue( 'sRGB')
    colorSpace.setInput(0, node )
    colorSpace.setXYpos( x, curY )

    inputNode = colorSpace
  else:
    inputNode = node

  curX = x
  curY = y + spacing * 2
  topY  = curY

  lastLayer = None
  background = None

  i = 0

  for l in layers:

    try:
      if l.attrs['divider/type'] > 0: ## hidden divider or start of group
        continue
    except:
      pass

    i = i + 1
    if i > 100:
      nuke.message( "Too many layers, stopping at layer 100." )
      break;

    name = l.attrs['nukeName']

    curY = topY

    if i % 2 :
      tileColor = 2829621248
    else:
      tileColor = 1751668736

    backdrop = nuke.nodes.BackdropNode(tile_color = tileColor, note_font_size=18)
    backdrop.setXYpos( curX + backdropXfudge, curY + backdropYfudge )

    curY += spacing/2

    dot = nuke.nodes.Dot()
    dot.setInput( 0, inputNode )
    dot.setXYpos( curX + dotXfudge , curY + dotYfudge)
    curY += spacing

    inputNode = dot

    shuffle = nuke.nodes.Shuffle()
    shuffle['label'].setValue( name )
    shuffle['in'].setValue( name )
    shuffle['in2'].setValue( 'none' )

    shuffle['red'].setValue( 'red' )
    shuffle['green'].setValue( 'green' )
    shuffle['blue'].setValue( 'blue' )
    shuffle['alpha'].setValue( 'alpha' )

    ## if no 'alpha' assume alpha of 1
    alphaChan = name + ".alpha"
    if not alphaChan in inputNode.channels():
      shuffle['alpha'].setValue( 'white' )

    shuffle['black'].setValue( 'red2' )
    shuffle['white'].setValue( 'green2' )
    shuffle['red2'].setValue( 'blue2' )
    shuffle['green2'].setValue( 'alpha2' )

    shuffle['out'].setValue( 'rgba' )
    shuffle['out2'].setValue( 'none' )

    shuffle.setInput(0, inputNode )
    shuffle.setXYpos( curX, curY )

    curY += spacing

    crop = nuke.nodes.Crop()
    crop['box'].setValue( l.attrs['x'], 0 )
    crop['box'].setValue( l.attrs['y'], 1 )
    crop['box'].setValue( l.attrs['r'], 2 )
    crop['box'].setValue( l.attrs['t'], 3 )

    crop.setInput(0, shuffle )
    crop.setXYpos( curX, curY )

    curY += spacing * 2

    layer = crop
    merge = None

    try:
      operation = blendMap[ l.attrs['blendmode'] ]
    except:
      print("unknown blending mode " + l.attrs['blendmode'])
      operation = "normal"

    if lastLayer:
      psdMerge = nuke.nodes.PSDMerge()
      psdMerge['operation'].setValue( operation )

      psdMerge.setInput(0, lastLayer )
      psdMerge.setInput(1, layer )
      psdMerge.setXYpos( curX, curY )
      psdMerge['sRGB'].setValue( sRGB )
      psdMerge['mix'].setValue( (l.attrs['opacity'] / 255.0) )
      try:
        if ( l.attrs['mask/disable'] != True ):
          psdMerge['maskChannelInput'].setValue( name + '.mask' )
          if ( l.attrs['mask/invert'] == True ) :
            psdMerge['invert_mask'].setValue( True )
      except:
        pass
      lastLayer = psdMerge
    else:
      dot = nuke.nodes.Dot()
      dot.setInput( 0, layer )
      dot.setXYpos( curX + dotXfudge, curY + dotYfudge )
      lastLayer = dot

    curY += spacing

    backdrop['bdwidth'].setValue( xspacing * 2 + backdropXfudge * 2 + 50)
    backdrop['bdheight'].setValue( ( curY - backdrop.ypos() ) - backdropYfudge -  50 )
    backdrop['label'].setValue( l.attrs['name'] )

    curY += spacing

    curX = curX + xspacing * 2 + backdropXfudge * 2 + 50


  if not sRGB:
    colorSpace2 = nuke.nodes.Colorspace()
    colorSpace2['channels'].setValue( 'all' )
    colorSpace2['colorspace_in'].setValue( 'sRGB')
    colorSpace2.setInput(0, lastLayer )
    colorSpace2.setXYpos( lastLayer.xpos(), lastLayer.ypos() + 2 * spacing )

  nuke.Undo().end()

class BreakoutThreadClass(threading.Thread):

  def __init__(self, node):
    threading.Thread.__init__(self)
    self.node = node

  def run(self):
    nuke.executeInMainThread( breakoutLayers, self.node )


def doReaderBreakout():
  ## horrible workaround for Bug 24578 that doesn't allow creating gizmos from a script button

  global readerBreakoutThread
  readerBreakoutThread = BreakoutThreadClass( nuke.thisNode() )
  readerBreakoutThread.start()



