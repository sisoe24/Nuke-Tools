#####
##
##  Bookmarks
#


import nuke

quickSaves = {}

def jumpTo( nodeName ):
  node = nuke.toNode( nodeName )
  for s in nuke.selectedNodes():
    s['selected'].setValue( False )

  node['selected'].setValue( True )
  nuke.zoomToFitSelected()

def quickSave( slot ):
  z = nuke.zoom()
  x = nuke.center()[0]
  y = nuke.center()[1]
  quickSaves[slot] = [z,x,y]


def quickRestore( slot ):
  try:
    nuke.zoom( quickSaves[slot][0], [ quickSaves[slot][1], quickSaves[slot][2] ] )
  except:
    return

