# Copyright (c) 2010 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

def setViewsForStereo():
  nuke.root().knob('views').fromScript( '\n'.join( ('left #ff0000', 'right #00ff00') ) )

def setViewsForMono():
  nuke.root().knob('views').fromScript('main #ffffff')

def setViewsForStereoOrMono():
  """ If there is only one view, set stereo, otherwise set to a single main view. """
  numViews = len(nuke.views())
  if numViews == 1:
    setViewsForStereo()
  else:
    setViewsForMono()
