# This module creates the default set of viewer guides for Hiero

import hiero.ui
import foundry.ui

# Possible coordinate system constants:
kGuideSequence = 0 # Use the sequence's output format
kGuideMasked = 1   # Use the sequence output format after any mask has been applied

class SimpleGuide(foundry.ui.Drawing):
  def __init__(self, name, r, g, b, amount, coords = kGuideSequence, aspect = 0.0, crosshairs = True):
    foundry.ui.Drawing.__init__(self, name)
    self.setCoordinateSystem(coords, 0.0, 0.0, 1.0, 1.0, aspect)
    self.setPen(r, g, b)
    self.drawRectangle(amount, amount, 1.0-2*amount, 1.0-2*amount)
    if crosshairs:
      self.drawCrossHairs(amount, amount, 1.0-2*amount, 1.0-2*amount)
    self.aspect = aspect
    self.name = name

class MaskGuide(foundry.ui.Drawing):
  def __init__(self, name, aspect):
    foundry.ui.Drawing.__init__(self, name)
    self.setCoordinateSystem(kGuideSequence, 0.0, 0.0, 1.0, 1.0, aspect)
    self.drawOutsideRectangle(0, 0, 1, 1)
    self.aspect = aspect
    self.name = name
