
#   Register this event handler to get callbacks from viewer when playhead is either at the beginning or at the end of the playback

from datetime import datetime
from hiero.core.events import *

class PlaybackEventsHandler:
  startTime = datetime.now()
  
  def __init__(self):
    registerInterest((EventType.kPlayheadAtStart, EventType.kPlayback), self.playheadAtStartHandler)
    registerInterest((EventType.kPlayheadAtEnd, EventType.kPlayback), self.playheadAtEndHandler)
      
  def playheadAtStartHandler(self, event):
    self.startTime = datetime.now()
    print("Playhead at start")
      
  def playheadAtEndHandler(self, event):
    print("Playhead at end")
    print("Time spent = " + str((datetime.now() - self.startTime)))
      
  def unregister(self):
    unregisterInterest((EventType.kPlayheadAtStart, EventType.kPlayback), self.playheadAtStartHandler)
    unregisterInterest((EventType.kPlayheadAtEnd, EventType.kPlayback), self.playheadAtEndHandler)

playbackHandler = PlaybackEventsHandler()