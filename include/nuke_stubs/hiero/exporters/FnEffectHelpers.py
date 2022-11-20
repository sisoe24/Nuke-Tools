import hiero.core
import itertools


def testTimelineIntersection(item, intersectItems):
  """ Test if a track item intersects with any of a list of items on the
  timeline. Note that we're using timelineIn() + duration() rather than timelineOut().
  Otherwise the test fails for 1 frame long items, where timelineIn() and
  timelineOut() are the same.
  """
  itemIn = item.timelineIn()
  itemOut = itemIn + item.duration()
  for intersectItem in intersectItems:
    intersectItemIn = intersectItem.timelineIn()
    intersectItemOut = intersectItemIn + intersectItem.duration()
    if intersectItemIn < itemOut and  intersectItemOut > itemIn:
      return True
  return False


def findEffectsAnnotationsForTrackItems(trackItems):
  """ Find applicable soft effects and annotations for a list of track items.
  This includes any effects with an intersecting timeline range, and which are
  on tracks above which do not contain any other items. Effects linked to the
  track items are not included. Assumes that all items are on the  same
  sequence, which they should be when exporting. """
  effects = []
  annotations = []

  if not trackItems:
    return effects, annotations

  views = set()
  views.add('') #Include tracks with no view set
  for item in trackItems:
    try:
      # This will throw an exception if it's an audio track, can swallow it
      trackView = item.parentTrack().view()
      if trackView:
        views.add(trackView)
    except:
      pass

  sequence = trackItems[0].parentTrack().parent()
  hitItemTrack = False
  for track in sequence.videoTracks():
    if not track.view() in views:
      continue

    # Test if we've found the first track containing any of the selected items
    if  not hitItemTrack and [i for i in trackItems if i.parentTrack() == track]:
      hitItemTrack = True

    # Once the first track containing one of the selected items has been hit,
    # start including effects and annotations. Effects are only included if
    # they're on a track with no items (since we don't want ones which are
    # linked to track items). Currently all annotations will be included in the
    # list
    if hitItemTrack:
      useEffectsFromTrack = len(list(track.items())) == 0
      useAnnotationsFromTrack = True

      # Loop over all the subtrack items, testing if they intersect any of the
      # track items on the timeline and are valid for inclusion
      for subTrackItem in itertools.chain(*track.subTrackItems()):
        if testTimelineIntersection(subTrackItem, trackItems):
          if isinstance(subTrackItem, hiero.core.EffectTrackItem) and useEffectsFromTrack and subTrackItem.isValid():
            effects.append(subTrackItem)
          elif isinstance(subTrackItem, hiero.core.Annotation) and useAnnotationsFromTrack:
            annotations.append(subTrackItem)
  
  return effects, annotations


def ensureEffectsNodesCreated(sequence):
  """ Find all the EffectTrackItems on a sequence or clip, and force creation of
  their nodes. The node creation is done lazily, but it must happen on the main
  thread, so for exports this can be called to force it to be done at a point
  when we know the code is running on the main thread. This also calls isValid()
  to make sure that the linking of effects and track items is correct.
  """
  if isinstance(sequence, hiero.core.Sequence):
    for track in sequence.videoTracks():
      for subTrackItem in itertools.chain(*track.subTrackItems()):
        if isinstance(subTrackItem, hiero.core.EffectTrackItem):
          subTrackItem.node()
          subTrackItem.isValid()
  elif isinstance(sequence, hiero.core.Clip):
    for subTrackItem in itertools.chain( *itertools.chain(*sequence.subTrackItems()) ):
      if isinstance(subTrackItem, hiero.core.EffectTrackItem):
        subTrackItem.node()
        subTrackItem.isValid()
  else:
    raise AssertionError("Unexpected argument type %s" % type(sequence))



