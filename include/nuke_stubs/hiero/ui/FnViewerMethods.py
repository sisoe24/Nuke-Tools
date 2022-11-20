""" Extra method to hiero.ui.Viewer class
"""

import ui
import hiero.core

def _goToTag(self, tag):
  """
  Move playhead to Tag.
  If Tag (Tag Object or Tag name) does not exists on the Viewer's Sequence/Clip
  a KeyError is raised.

  @param tag: a Tag object or the name of the desired tag.
  """
  sequence = self.player().sequence()
  if sequence:
    tags = sequence.tags()
    tags = [ t for t in tags if t.outTime() >= 0 ]
    tagName = tag
    if isinstance(tag, hiero.core.Tag):
      tagName = tag.name()
    desiredTags = [t for t in tags if t.name() == tagName]
    numTagsFound = len(desiredTags)
    if numTagsFound:
      self.setTime(desiredTags[0].inTime())
      if numTagsFound > 1:
        tagsTimes = [ t.inTime() for t in desiredTags]
        print('Tag appears on frames: %s . Playhead moved to first instance' % tagsTimes)
    else:
      raise KeyError("Tag with name '%s' not found." % tagName)
  else:
    raise RuntimeError("Viewer does not have a sequence")


def _goToInTime(self):
  """
  Move playhead to In point
  """
  sequence = self.player().sequence()
  if sequence:
    self.setTime(sequence.inTime())
  else:
    raise RuntimeError("Viewer does not have a sequence")


def _goToOutTime(self):
  """
  Move playhead to Out point
  """
  sequence = self.player().sequence()
  if sequence:
    self.setTime(sequence.outTime())
  else:
    raise RuntimeError("Viewer does not have a sequence")



def _goToPosInTrackItem(viewer, trackItem, trackItemTimeMethod ):
  """ Helper method to move the playhead to a position of the trackItem
  according to trackItemTimeMethod
  @param viewer: hiero.ui.Viewer object
  @param trackItem: hiero.core.TrackItem object
  @param trackItemTimeMethod: method to get the desired time from the track
  item
  """

  if not isinstance(trackItem, hiero.core.TrackItem):
    raise RuntimeError("'%s' must be a hiero.core.TrackItem object", trackItem)

  sequence = viewer.player().sequence()
  if not sequence:
    raise RuntimeError("Viewer does not have a sequence")

  sequenceTrackItems = []
  for vt in sequence.videoTracks():
    sequenceTrackItems.extend( list(vt.items()) )

  if trackItem not in sequenceTrackItems:
    RuntimeError("%s is not in %s" % (trackItem, sequence))

  time = trackItemTimeMethod(trackItem)
  viewer.setTime(time)


def _goToTrackItemStart(self, trackItem):
  """
  Move playhead to start of the trackItem.

  @param trackItem: sequence's track item.
  """
  def _getTimelineIn(ti):
    return ti.timelineIn()
  _goToPosInTrackItem(self, trackItem, _getTimelineIn)


def _goToTrackItemEnd(self, trackItem):
  """
  Move playhead to end of the trackItem.

  @param trackItem: sequence's track item.
  """
  def _getTimelineOut(ti):
    return ti.timelineOut()
  _goToPosInTrackItem(self, trackItem, _getTimelineOut)


def _goToTrackItemMiddle(self, trackItem):
  """
  Move playhead to middle of the trackItem.

  @param trackItem: sequence's track item.
  """
  def _getTimelineIn(ti):
    inTime = ti.timelineIn()
    outTime = ti.timelineOut()
    middleTime = (inTime + outTime) / 2
    return middleTime
  _goToPosInTrackItem(self, trackItem, _getTimelineIn)


ui.Viewer.goToTag = _goToTag
ui.Viewer.goToInTime = _goToInTime
ui.Viewer.goToOutTime = _goToOutTime

ui.Viewer.goToTrackItemStart = _goToTrackItemStart
ui.Viewer.goToTrackItemEnd = _goToTrackItemEnd
ui.Viewer.goToTrackItemMiddle =_goToTrackItemMiddle

