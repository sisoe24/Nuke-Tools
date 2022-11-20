# Example shows how you can add custom viewer guides and masks via Python
# If you wish for this code to be run on startup, copy it to your <HIERO_PATH>/StartupUI directory.
# Run: help(hiero.ui.guides) for more info.

import hiero.ui.guides

# SimpleGuide( name, r, g, b, amount, coords = kGuideSequence, aspect = 0.0, crosshairs = True)
titleSafeGuide = hiero.ui.guides.SimpleGuide("Custom Title Safe", 0.0 , 1.0 , 0.1 , 1, hiero.ui.guides.kGuideMasked)
actionSafeGuide = hiero.ui.guides.SimpleGuide("Custom Action Safe", 1, 1, 1, 1, hiero.ui.guides.kGuideMasked, crosshairs = True)
sequenceFormatGuide = hiero.ui.guides.SimpleGuide("Custom Sequence Format", 1, 1, 0, 1, hiero.ui.guides.kGuideSequence, crosshairs = False)
viewer_guides = [titleSafeGuide, actionSafeGuide, sequenceFormatGuide]


# MaskGuide( name, aspect)
viewer_masks = [
  hiero.ui.guides.MaskGuide("NTSC", 0.91),
  hiero.ui.guides.MaskGuide("PAL", 1.09),
  hiero.ui.guides.MaskGuide("NTSC_16:9", 1.21),
  hiero.ui.guides.MaskGuide("PAL_16:9", 1.46),
  hiero.ui.guides.MaskGuide("Cinemascope 2:1", 2.0)  
]

for vg in viewer_guides:
  hiero.ui.viewer_guides.append(vg)

for vm in viewer_masks:
  hiero.ui.viewer_masks.append(vm)