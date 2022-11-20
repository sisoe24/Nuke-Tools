# -*- coding: utf-8 -*-

"""
Python code to be executed after a Studio project is loaded. Currently this
is just used to fix up deprecated reformatting options for track items on a
sequence.
"""

import hiero.core
import _nuke
from . events import (registerInterest, EventType)
from hiero.core.FnEffectHelpers import (calculateReformat)

def shiftLinkedSubTrackItems(trackItem):
  """ Move a track item's linked sub-track items up to the next sub-track so new
  effects can be inserted at the bottom.
  """
  track = trackItem.parentTrack()
  subTrackItems = [ i for i in trackItem.linkedItems() if isinstance(i, hiero.core.SubTrackItem) ]
  # Sort in descending order so they can be shifted up
  subTrackItems.sort(cmp=lambda x, y: -cmp(x.subTrackIndex(), y.subTrackIndex()))
  for subTrackItem in subTrackItems:
    index = subTrackItem.subTrackIndex() + 1
    # Default remove behaviour is to remove all linked items and to remove empty
    # sub-tracks. Stop it from doing that.
    flags = hiero.core.TrackBase.eDontRemoveLinkedItems | hiero.core.TrackBase.eDontCollapseSubTracks
    track.removeSubTrackItem(subTrackItem, flags)
    track.addSubTrackItem(subTrackItem, index)


def fixDeprecatedReformatStateProperties(project):
  """ Find track items in the project which are set to reformat in a way which
  is now invalid. Creates soft effect items which are equivalent to the old
  behavior.
  """
  undo = _nuke.Undo()
  migrated = False
  try:
    undo.disable()
    trackItems = hiero.core.findItemsInProject(project, hiero.core.TrackItem)
    for item in trackItems:
      reformatState = item.reformatState()

      # If this is an audio track item, reformatState will be null
      if not reformatState:
        continue

      track = item.parentTrack()
      seq = item.parentSequence()
      seqFormat = seq.format()

      if reformatState.originalType() in [hiero.core.nuke.ReformatNode.kToFormat, hiero.core.nuke.ReformatNode.kToScale]:
        # Reformatting options center, flip, flop, turn may be enabled with type to format / to scale,
        # so we may need to create soft effects for them

        # Turn
        ######

        if reformatState.originalResizeTurn():
          seqWidth = seqFormat.width()
          seqHeight = seqFormat.height()
          sourceFormat = item.source().format()
          sourceWidth = sourceFormat.width()
          sourceHeight = sourceFormat.height()
          resizeType = reformatState.resizeType() if reformatState.originalType() == hiero.core.nuke.ReformatNode.kToFormat else "scale"
          center = reformatState.resizeCenter()
          scale = reformatState.scale()

          # Obtain the location of the sourceFormat within the sequence format
          (x, y, w, h) = calculateReformat(sourceFormat, seqFormat, resizeType, center, scale)

          if resizeType == "width":
            scalex = scaley = w / float(h)

          elif resizeType == "height":
            scalex = scaley = h / float(w)

          elif resizeType == "fit":
            if sourceHeight < sourceWidth:
              scalex = scaley = seqHeight / float(w)
            else:
              scalex = scaley = seqWidth / float(h)

          elif resizeType == "fill":
            if sourceHeight < sourceWidth:
              scalex = scaley = seqWidth / float(h)
            else:
              scalex = scaley = seqHeight / float(w)

          elif resizeType == "distort":
            scalex = seqHeight / float(seqWidth)
            scaley = 1 / scalex

          else:
            scalex = scaley = 1

          # If we're centreing, rotate about the sequence centre. If we're not centring,
          # rotate about the origin and translate across the x-axis to shift it back into position.
          # We could instead choose a different centre point to rotate about, with no translate,
          # but the maths is less clear to follow, as the centre point then depends on the
          # resize type.
          if center:
            centerx = seqWidth / 2.0
            centery = seqHeight / 2.0
            transx = 0
            transy = 0
          else:
            centerx = 0
            centery = 0
            transx = h * scaley
            transy = 0

          shiftLinkedSubTrackItems(item)
          turnEffect = track.createEffect(effectType="Transform",
                                        trackItem=item,
                                        subTrackIndex=0)
          migrated = True
          turnEffect.setName("Turn")
          turnNode = turnEffect.node()

          turnNode["center"].fromScript("%s %s" % (centerx, centery))
          turnNode["rotate"].setValue(90)

          if scalex == scaley:
            turnNode["scale"].setValue(scalex)
          else:
            scaleKnob = turnNode.knobs()["scale"]
            scaleKnob.setSingleValue(False)
            scaleKnob.setValue(scalex, 0)
            scaleKnob.setValue(scaley, 1)

          translateKnob = turnNode["translate"]
          translateKnob.setValue(transx, 0)
          translateKnob.setValue(transy, 1)

        # Flip / Flop
        #############

        if reformatState.originalResizeFlip() or reformatState.originalResizeFlop():
          resizeType = reformatState.resizeType() if reformatState.originalType() == hiero.core.nuke.ReformatNode.kToFormat else "scale"
          sourceFormat = item.source().format()
          center = reformatState.resizeCenter()
          scale = reformatState.scale()

          # Obtain the location of the sourceFormat within the sequence format
          (x, y, w, h) = calculateReformat(sourceFormat, seqFormat, resizeType, center, scale)

          # Flip/flop either about the centre of the sequence, or the centre of the clip,
          # depending on whether or not we're centreing
          if center:
            centerx = seqFormat.width() / 2.0
            centery = seqFormat.height() / 2.0
          else:
            centerx = x + w / 2.0
            centery = y + h / 2.0

          shiftLinkedSubTrackItems(item)
          flipFlopEffect = track.createEffect(effectType="Transform",
                                              trackItem=item,
                                              subTrackIndex=0)
          migrated = True
          flipFlopEffect.setName("Flip_and_flop")
          transformNode = flipFlopEffect.node()
          scaleKnob = transformNode.knobs()["scale"]
          scaleKnob.setSingleValue(False)

          scaleKnob.setValue(-1 if reformatState.originalResizeFlop() else 1, 0)
          scaleKnob.setValue(-1 if reformatState.originalResizeFlip() else 1, 1)

          transformNode["center"].fromScript("%s %s" % (centerx, centery))
          transformNode["rotate"].setValue(0)

          # Flip/flop never require a translate, as long as we choose the centre point
          # carefully, as above.
          transx = transy = 0
          translateKnob = transformNode["translate"]
          translateKnob.setValue(transx, 0)
          translateKnob.setValue(transy, 1)

      # Scale
      #######

      if reformatState.originalType() == hiero.core.nuke.ReformatNode.kToScale:
        scale = reformatState.scale()
        shiftLinkedSubTrackItems(item)
        scaleEffect = track.createEffect(effectType="Transform",
                                         trackItem=item,
                                         subTrackIndex=0)
        migrated = True
        scaleNode = scaleEffect.node()
        # Note: the center knob needs to be set here because there is a bug when
        # constructing soft effects through Python where the initial knob values
        # don't get set correctly.
        if reformatState.resizeCenter():
          scaleNode["center"].fromScript("%s %s" % (seqFormat.width()/2, seqFormat.height()/2))
        else:
          clipFormat = item.source().format()
          xOffset = (clipFormat.width()-seqFormat.width())/2
          yOffset = (clipFormat.height()-seqFormat.height())/2
          scaleNode["center"].fromScript("%s %s" % (-xOffset,-yOffset))
          scaleNode["translate"].fromScript("%s %s" % (xOffset,yOffset))

        scaleNode["scale"].setValue(scale)


  finally:
    if migrated:
      project.setHasMigratedSequenceProperties()

    undo.enable()

def onProjectLoaded(event):
  """ Callback after a project is loaded. """
  project = event.sender
  fixDeprecatedReformatStateProperties(project)


registerInterest(EventType.kAfterProjectLoad, onProjectLoaded)
