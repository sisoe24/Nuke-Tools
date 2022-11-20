# Shows how to create a new project, add clips, and create a sequence

from hiero.core import (newProject, BinItem, Bin, Sequence, VideoTrack)
import os
import sys

# create a new project
myProject = newProject()

# create some bins for it
bin1 = Bin("Bin 1")
bin2 = Bin("Bin 2")
bin3 = Bin("Bin 3")

# make bin2 a sub bin of bin1
bin1.addItem(bin2)

# attach the bins to the project
clipsBin = myProject.clipsBin()
clipsBin.addItem(bin1)
clipsBin.addItem(bin3)

def findResourcePath():
  try:
    devGuidePath = os.environ["HIERO_PYTHON_DEV_GUIDE"]
  except KeyError:
    raise RuntimeError("Cannot find resource files, please set the HIERO_PYTHON_DEV_GUIDE environment variable")
  resourcesPath = os.path.abspath(os.path.join(devGuidePath, "Resources"))
  return resourcesPath

# find the path to the resources that ship with Hiero
resourcesPath = findResourcePath()

# make some clips
clip1 = clipsBin.createClip(os.path.join(resourcesPath, "blue_green_checkerboard.mov"))
clip2 = bin1.createClip(os.path.join(resourcesPath, "red_black_checkerboard.mov"))
clip3 = bin2.createClip(os.path.join(resourcesPath, "colour_bars.mov"))
clip4 = bin3.createClip(os.path.join(resourcesPath, "colour_wheel.mov"))
clip5 = bin3.createClip(os.path.join(resourcesPath, "purple.######.dpx"))

# create a new sequence and attach it to the project
sequence = Sequence("NewSequence")
clipsBin.addItem(BinItem(sequence))

# helper method for creating track items from clips
def createTrackItem(track, trackItemName, sourceClip, lastTrackItem=None):
  # create the track item
  trackItem = track.createTrackItem(trackItemName)
  
  # set it's source
  trackItem.setSource(sourceClip)
  
  # set it's timeline in and timeline out values, offseting by the track item before if need be
  if lastTrackItem:
    trackItem.setTimelineIn(lastTrackItem.timelineOut() + 1)
    trackItem.setTimelineOut(lastTrackItem.timelineOut() + sourceClip.duration())
  else:
    trackItem.setTimelineIn(0)
    trackItem.setTimelineOut(trackItem.sourceDuration()-1)
  
  # add the item to the track
  track.addItem(trackItem)
  return trackItem

# create a track to add items/clips to
track = VideoTrack("VideoTrack")

# create the track items, each one offset from the one before it
trackItem1 = createTrackItem(track, "TrackItem1", clip1)
trackItem2 = createTrackItem(track, "TrackItem2", clip2, lastTrackItem=trackItem1)
trackItem3 = createTrackItem(track, "TrackItem3", clip3, lastTrackItem=trackItem2)
trackItem4 = createTrackItem(track, "TrackItem4", clip4, lastTrackItem=trackItem3)
trackItem5 = createTrackItem(track, "TrackItem5", clip5, lastTrackItem=trackItem4)

# add the track to the sequence now
sequence.addTrack(track)
