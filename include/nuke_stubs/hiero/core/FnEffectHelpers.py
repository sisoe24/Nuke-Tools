#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
from hiero.core import (EffectTrackItem,
                        TrackItem,
                        ReformatState,
                        formats)
from _nuke import Undo


class EffectTransform(object):
  """ Class for handling scale and translation of effect knob values. """
  def __init__(self, scaleX=1.0, scaleY=1.0, translateX=0.0, translateY=0.0):
    self._scaleX = scaleX
    self._scaleY = scaleY
    self._translateX = translateX
    self._translateY = translateY

  def setScale(self, scaleX, scaleY):
    self._scaleX = scaleX
    self._scaleY = scaleY

  def getScale(self):
    return self._scaleX, self._scaleY

  def setTranslate(self, translateX, translateY):
    self._translateX = translateX
    self._translateY = translateY

  def scaleX(self, value):
    return value * self._scaleX

  def scaleY(self, value):
    return value * self._scaleY

  def translateAndScaleX(self, value):
    return value * self._scaleX + self._translateX

  def translateAndScaleY(self, value):
    return value * self._scaleY + self._translateY

  def __str__(self):
    return ("EffectTransform(scaleX=%s, scaleY=%s, translateX=%s translateY=%s)"
            % (self._scaleX, self._scaleY, self._translateX, self._translateY))


def _transformKnobValue(knob, transform, errorCallback):
  """ Apply a transform function to a knob, taking account of animations. """
  if knob.hasExpression():
    errorCallback("Could not transform expression on node '%s' knob '%s'" %
                    (knob.node().name(), knob.name()))
  elif knob.isAnimated():
    for anim in knob.animations():
      for key in list(anim.keys()):
        oldValue = key.y
        newValue = transform(key.y)
        key.y = newValue
  else:
    newValue = transform(knob.getValue())
    knob.setValue(newValue)

def _transformArrayKnobValueFromKnob(knob, index, transform, knobDep, indexDep, errorCallback):
  """ Apply a transformation to the given index in an array knob that depends on another array Knob """
  #knobDep will be use to transform the knob
  if knob.hasExpression(index) or knobDep.hasExpression(indexDep):
    errorCallback("Could not transform expression on node '%s' knob '%s' in terms of knob '%s'" %
                    (knob.node().name(), knob.name(), knobDep.name()))
  elif not knob.isAnimated(index) and not knobDep.isAnimated(indexDep):
    #none of the knobs are animated, transform it
    newValue = transform( knob.getValue(index), knobDep.getValue(indexDep))
    knob.setValue(newValue, index)
  elif knob.isAnimated(index) and not knobDep.isAnimated(indexDep):
    #only for each key on
    knobDepValue = knobDep.getValue(indexDep)
    anim = knob.animation(index)
    for key in list(anim.keys()):
      newValue = transform(key.y, knobDepValue )
      knob.setValueAt(newValue,key.x,index)
    anim.fixSlopes()
  elif not knob.isAnimated(index) and knobDep.isAnimated(indexDep):
    #knob is not animated, add a keyframe for each keyframe in knobDep
    anim = knobDep.animation(indexDep)
    knobValue = knob.getValue(index)
    knob.setAnimated(index)
    for key in list(anim.keys()):
      newValue = transform(knobValue, knobDep.getValueAt(key.x,indexDep))
      knob.setValueAt(newValue, key.x, index)
    anim.fixSlopes()
  else:
    #both animated, add all missing keyframes on knob and transform them all
    anim = knob.animation(index)
    animDep = knobDep.animation(indexDep)
    #get the union of the keyframes in both knobs
    keyFrames = set(key.x for key in list(anim.keys()))
    keyFrames.update(key.x for key in list(animDep.keys()))
    keyFrameList = list(keyFrames)
    keyFrameList.sort()
    #get a copy of the values to transform them
    originalValueList = [knob.getValueAt( keyFrame, index ) for keyFrame in keyFrameList]
    for (frame, originalValue) in zip(keyFrameList, originalValueList):
      newValue = transform(originalValue, knobDep.getValueAt( frame, indexDep ))
      knob.setValueAt(newValue, frame, index)
    anim.fixSlopes()


def _transformArrayKnobValue(knob, index, transform, errorCallback):
  "Apply a transformation to the given index in an array knob. """
  if knob.hasExpression(index):
    errorCallback("Could not transform expression on node '%s' knob '%s'" %
                    (knob.node().name(), knob.name()))
  elif knob.isAnimated(index):
    anim = knob.animation(index)
    for key in list(anim.keys()):
      newValue = transform(key.y)
      knob.setValueAt( newValue, key.x, index)
    anim.fixSlopes()
  else:
    newValue = transform( knob.getValue(index) )
    knob.setValue(newValue, index)



def _transformCropEffect(node, formatChange, errorCallback):
  # Transform the crop box
  transform = formatChange.getTransformForFormat()
  transformXFunc = transform.translateAndScaleX
  transformYFunc = transform.translateAndScaleY
  boxKnob = node["box"]
  for i in (0, 2):
    _transformArrayKnobValue(boxKnob, i, transformXFunc, errorCallback)
  for i in (1, 3):
    _transformArrayKnobValue(boxKnob, i, transformYFunc, errorCallback)


def _transformTransformEffect(node, formatChange, errorCallback):
  # If the transform is not linked to a clip, or is linked to one that is
  # scaling to the output format, transform the translate and center knobs so it
  # fits the new format.
  # If it's linked to a clip that isn't being scaled, then just the center point
  # needs to be offset to handle the clip being centered in the new format
  if not formatChange.hasUnscaledClip():
    transform = formatChange.getTransformForFormat()

    knob = node["translate"]
    scaleXFunc = transform.scaleX
    scaleYFunc = transform.scaleY
    _transformArrayKnobValue(knob, 0, scaleXFunc, errorCallback)
    _transformArrayKnobValue(knob, 1, scaleYFunc, errorCallback)

    knob = node["center"]
    translateAndScaleXFunc = transform.translateAndScaleX
    translateAndScaleYFunc = transform.translateAndScaleY
    _transformArrayKnobValue(knob, 0, translateAndScaleXFunc, errorCallback)
    _transformArrayKnobValue(knob, 1, translateAndScaleYFunc, errorCallback)
  else:
    transform = formatChange.getTransformOffsetUnscaledClip()
    translateXFunc = transform.translateAndScaleX
    translateYFunc = transform.translateAndScaleY
    centerKnob = node["center"]
    _transformArrayKnobValue(centerKnob, 0, translateXFunc, errorCallback)
    _transformArrayKnobValue(centerKnob, 1, translateYFunc, errorCallback)


def _transformTextEffect(node, formatChange, errorCallback):
  reformatState = formatChange.reformatState
  scaledToFormat = not reformatState or (formatChange.reformatStateType() == "to format" and
                                         formatChange.reformatStateResizeType() != "none")
  if scaledToFormat:
    if formatChange.reformatState:
      transform = formatChange.getTransformForReformatState()
    else:
      transform = formatChange.getTransformForFormat()

    transformXFunc = transform.translateAndScaleX
    transformYFunc = transform.translateAndScaleY
    scaleXFunc = transform.scaleX
    scaleYFunc = transform.scaleY

    autofit = node["autofit_bbox"]
    autofit.setValue(False)

    transformKnob = node["animation_layers"]
    boxKnob = node["box"]
    boxXFunc = lambda x, t: x+transformXFunc(t)-t
    boxYFunc = lambda y, t: y+transformYFunc(t)-t
    #transform the box in terms of the center knob
    for i in (0, 2):
      _transformArrayKnobValueFromKnob(boxKnob, i, boxXFunc, transformKnob, 2, errorCallback)
    for i in (1, 3):
      _transformArrayKnobValueFromKnob(boxKnob, i, boxYFunc, transformKnob, 3, errorCallback)

    _transformArrayKnobValue(transformKnob, 2, transformXFunc, errorCallback)#center
    _transformArrayKnobValue(transformKnob, 3, transformYFunc, errorCallback)#center

    _transformArrayKnobValue(transformKnob, 6, scaleXFunc, errorCallback)#scalex
    _transformArrayKnobValue(transformKnob, 7, scaleYFunc, errorCallback)#scaley

    _transformArrayKnobValue(transformKnob, 4, scaleXFunc, errorCallback)#translate
    _transformArrayKnobValue(transformKnob, 5, scaleYFunc, errorCallback)#translate

  else:
    transform = formatChange.getTransformOffsetUnscaledClip()
    transformXFunc = transform.translateAndScaleX
    transformYFunc = transform.translateAndScaleY
    centerKnob = node["animation_layers"]
    _transformArrayKnobValue(centerKnob, 4, transformXFunc, errorCallback)#translate
    _transformArrayKnobValue(centerKnob, 5, transformYFunc, errorCallback)#translate


def _transformBurnInEffect(node, formatChange, errorCallback):
  # For the burn-in, there's not much to be done. Just choose a scale factor
  # and apply that to the border padding and the text scaling.
  transform = formatChange.getTransformForFormatNoReformatState()
  knobs = ("burnIn_xPadding",
           "burnIn_yPadding",
           "burnIn_textScale")
  for knob in knobs:
    _transformKnobValue(node[knob], transform.scaleX, errorCallback)



EffectTransforms = { "Crop" : _transformCropEffect,
                     "Transform" : _transformTransformEffect,
                     "Text2" : _transformTextEffect,
                     "BurnIn" : _transformBurnInEffect }


def iterSequenceEffects(sequence):
  """ Generator for iteration over the EffectTrackItems in a sequence. """
  for track in sequence.videoTracks():
    for subTrackItem in itertools.chain(*track.subTrackItems()):
      if isinstance(subTrackItem, EffectTrackItem):
        yield subTrackItem


def _calculateScaleHelper(inFormat, outFormat, resizeType, scale):
  """ Helper function for calculating the scaling between two formats for a
  given resize type. Maths copied from Reformat.cpp
  """
  hxscale = float(outFormat.width()) / float(inFormat.width())
  hyscale = hxscale * outFormat.pixelAspect() / inFormat.pixelAspect()
  vyscale = float(outFormat.height()) / float(inFormat.height())
  vxscale = vyscale * inFormat.pixelAspect() / outFormat.pixelAspect()
  if resizeType == "none":
    return (1.0, 1.0)
  elif resizeType == "fit":
    return (hxscale, hyscale) if (hxscale <= vxscale) else (vxscale, vyscale)
  elif resizeType == "fill":
    return (hxscale, hyscale) if (hxscale >= vxscale) else (vxscale, vyscale)
  elif resizeType == "width":
    return (hxscale, hyscale)
  elif resizeType == "height":
    return (vxscale, vyscale)
  elif resizeType == "distort":
    return (hxscale, vyscale)
  elif resizeType == "scale":
    return (scale, scale)
  else:
    raise RuntimeError("unhandled resize type %s",resizeType)


class FormatChange(object):
  """ Helper class for calculating the changes between two formats. """
  def __init__(self, newFormat, oldFormat, clipFormat=None, reformatState=None):
    self.newFormat = newFormat
    self.oldFormat = oldFormat
    self.clipFormat = clipFormat

    # Allow reformatState to be either a hiero.core.ReformatState object or a
    # dict. If it's the former, put it into a dict.
    if isinstance(reformatState, ReformatState):
      self.reformatState = {"type":reformatState.type(),
                            "resizeType":reformatState.resizeType(),
                            "resizeCenter":reformatState.resizeCenter()}
    else:
      self.reformatState = reformatState

  def reformatStateType(self):
    return self.reformatState["type"] if self.reformatState else None

  def reformatStateResizeType(self):
    return self.reformatState["resizeType"] if self.reformatState else None

  def reformatStateResizeCenter(self):
    return self.reformatState["resizeCenter"] if self.reformatState else None

  def newWidth(self):
    return float(self.newFormat.width())

  def newHeight(self):
    return float(self.newFormat.height())

  def oldWidth(self):
    return float(self.oldFormat.width())

  def oldHeight(self):
    return float(self.oldFormat.height())

  def widthRatio(self):
    return self.newWidth() / self.oldWidth()

  def heightRatio(self):
    return self.newHeight() / self.oldHeight()

  def calculateCenterOffset(self, transform):
    """ Add translation required to center the image for the scale in the
    given transform.
    """
    scaleX, scaleY = transform.getScale()
    transform.setTranslate( (self.newWidth() - (self.oldWidth() * scaleX)) / 2.0,
                            (self.newHeight() - (self.oldHeight() * scaleY)) / 2.0 )

  def calculateScale(self, resizeType):
    """ Calculate the scaling from the old format to the new format for the given
    resize type.
    """

    # Note, we use a scale value of 1 (corresponding to the Scale knob on the reformat),
    # since it doesn't matter - we only return the ratio of new/old scale, and so any
    # contribution from the scale knob would be cancelled out
    oldScaleX, oldScaleY = _calculateScaleHelper(self.clipFormat, self.oldFormat, resizeType, 1)
    newScaleX, newScaleY = _calculateScaleHelper(self.clipFormat, self.newFormat, resizeType, 1)
    return (newScaleX / oldScaleX, newScaleY / oldScaleY)

  def getTransformForReformatState(self):
    """ Calculate the transform for a format change, taking into account the
    reformat settings on a track item.
    """
    #disabled, to scale 1 and resize type none should be the same result
    reformatType = self.reformatStateType()
    transform = EffectTransform()
    if reformatType == "to format":
      resizeType = self.reformatStateResizeType()
      transform.setScale(*self.calculateScale(resizeType))
    elif reformatType in ("disabled", "scale"):
      # This doesn't need to do anything apart from offsetting for the
      # centering, which is handled below
      pass
    else:
      raise RuntimeError("unhandled reformatType %s",reformatType)

    if self.isClipReformatCentered():
      self.calculateCenterOffset(transform)

    return transform

  def getTransformForFormatNoReformatState(self):
    """ Calculate the transform for a format change. This just scales by the ratio
    of the width/height of the old to new format. """
    return EffectTransform(self.widthRatio(), self.heightRatio(), 0, 0)

  def getTransformForFormat(self):
    """ Get the transform to shift to the new format, taking into account the
    clip reformat state.
    """
    if self.reformatState:
      return self.getTransformForReformatState()
    else:
      return self.getTransformForFormatNoReformatState()

  def getTransformOffsetUnscaledClip(self):
    """ If clips are not scaled to sequence format, when the format changes
    transforms should just be offset to compensate for the centering of the clip
    in the new format.
    """
    transform = EffectTransform()
    if self.isClipReformatCentered():
      of, nf, cf = self.oldFormat, self.newFormat, self.clipFormat
      transform.setTranslate( (nf.width()-cf.width())/2 - (of.width()-cf.width())/2,
                              (nf.height()-cf.height())/2 - (of.height()-cf.height())/2 )
    return transform

  def isClipReformatCentered(self):
    """ Check if the clip is centered in the sequence format. This is always
    true if set to 'disabled'.
    """
    return self.reformatStateType() == "disabled" or self.reformatStateResizeCenter()

  def hasUnscaledClip(self):
    return (self.reformatState and (self.reformatStateType() != "to format" or
                                        self.reformatStateResizeType() == "none"))



def findLinkedTrackItem(effectItem):
  """ Find the main video track item linked to an effect. """
  track = effectItem.parentTrack()
  for item in effectItem.linkedItems():
    if isinstance(item, TrackItem) and item.parentTrack() == track:
      return item
  return None


def transformNodeToFormatChange(node, formatChange, errorCallback):
  transformFunc = EffectTransforms.get(node.Class(), None)
  if transformFunc:
    transformFunc(node, formatChange, errorCallback)


def transformEffectToFormat(effectItem, format, oldFormat, errorCallback):
  trackItem = findLinkedTrackItem(effectItem)
  if trackItem:
    formatChange = FormatChange(format, oldFormat, trackItem.source().format(), trackItem.reformatState())
  else:
    formatChange = FormatChange(format, oldFormat)
  node = effectItem.node()
  transformNodeToFormatChange(node, formatChange, errorCallback)


def transformSequenceEffectsToFormat(sequence, format, oldFormat, errorCallback):
  for effectItem in iterSequenceEffects(sequence):
    transformEffectToFormat(effectItem, format, oldFormat, errorCallback)


def calculateReformat(inFormat, outFormat, resizeType, center, scale):
  """ Converts from inFormat to outFormat using the specified resizeType and
  center to determine how the reformat should happen.  Returns a tuple
  (x, y, w, h) providing the format's coordinates within the new format space.
  The logic of this function comes from the Reformat node, but ommitting
  flip, flop and turn.
  """
  (sx, sy) = _calculateScaleHelper(inFormat, outFormat, resizeType, scale)

  iw = inFormat.width()
  ih = inFormat.height()

  x = y = 0
  if (center):
    ow = outFormat.width()
    oh = outFormat.height()
    x = int((ow - iw) / 2.0) if sx ==1 else (ow - iw * sx) / 2.0
    y = int((oh - ih) / 2.0) if sy ==1 else (oh - ih * sy) / 2.0

  x *= sx
  y *= sy
  w = iw * sx
  h = ih * sy

  return (x, y, w, h)


