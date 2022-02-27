# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import re
import nuke
import nukescripts

def render_panel(_list, exceptOnError = True, allowFrameServer = True):
  return nukescripts.showRenderDialog(_list, exceptOnError, allowFrameServer)


def cache_particles_panel(particleCacheNode):
  particleCacheNode.knobs()["particle_cache_render_in_progress"].setValue(True)
  try:
    nuke.Undo().disable()
    rootNode = nuke.root()
    firstFrame = rootNode['first_frame'].getValue()
    lastFrame = rootNode['last_frame'].getValue()
    # Extra frames added for motion blur
    padding = int(particleCacheNode['particle_cache_padding'].getValue())
    nuke.executeMultiple((particleCacheNode,), ([firstFrame - padding, lastFrame + padding, 1],))
  except RuntimeError as e:
    nuke.tprint(e)
    if e.args[0][0:9] != "Cancelled":   # TO DO: change this to an exception type
      raise
  finally:
    nuke.Undo().enable()

