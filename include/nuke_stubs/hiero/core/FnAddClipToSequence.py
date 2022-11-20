import core

def _addClip(self, clip, time, videoTrackIndex=0, audioTrackIndex=-1):
  """
  Add a clip to a sequence, creating a TrackItem for each video/audio channel in the clip,
  adding them to the appropriate tracks and linking them together.  This has the same effect
  as dragging a clip from the Bin View to the Timeline View in the Hiero UI.

  @param clip: the clip to add
  @param time: the in time for created track items
  @param videoTrackIndex: index of the video track to add items to if the clip has video
  @param audioTrackIndex: index of the audio track to start adding items to if the clip has audio
  @return: list of created hiero.core.TrackItems
  """
  trackItems = []
  source = clip.mediaSource()

  # Add video track item
  if source.hasVideo():
    # Find or create the video track to add to
    videoTracks = self.videoTracks()
    if videoTrackIndex < len(videoTracks): # Track already exists
      videoTrack = videoTracks[videoTrackIndex]
    else: # Track not found, create it, adding empty tracks up to the requested index if needed
      for index in range(len(videoTracks), videoTrackIndex+1):
        videoTrack = core.VideoTrack("Video %s" % (index+1))
        self.addTrack( videoTrack )
    trackItems.append( videoTrack.addTrackItem(clip, time) ) # Create track item

  # Add audio track items
  if source.hasAudio():
    # If the audio track index was left at the default, then try to match the UI behaviour
    if audioTrackIndex < 0:
      if source.hasVideo():
        # If there was video, we add audio starting at the video track index * 2, so if you
        # have video on Video 2 (index 1) audio would start on Audio 3 (index 2).  This is the same
        # as dragging clips onto the Timeline View in the UI.
        audioTrackIndex = videoTrackIndex * 2
      else:
        audioTrackIndex = 0

    # Add items on a different track for each audio channel, creating
    # new tracks if necessary, and adding empty tracks up to the requested index if needed
    audioTracks = self.audioTracks()
    numChannels = source.numChannels(core.MediaSource.kAudio)
    highestTrackIndex = audioTrackIndex + numChannels - 1
    if highestTrackIndex >= len(audioTracks):
      for index in range(len(audioTracks), highestTrackIndex+1):
        track = core.AudioTrack('Audio %s' % (index+1))
        self.addTrack( track )
    audioTracks = self.audioTracks()

    # Create track items for each channel, placing them on ascending tracks
    for channel in range(numChannels):
      track = audioTracks[audioTrackIndex]
      trackItems.append( track.addTrackItem(clip, channel, time) )
      audioTrackIndex = audioTrackIndex + 1

  # Link track items together
  linkTrackItem = None
  for trackItem in trackItems:
    if linkTrackItem:
      linkTrackItem.link(trackItem)
    else:
      linkTrackItem = trackItem

  # Return the created track items
  return trackItems

core.Sequence.addClip = _addClip
