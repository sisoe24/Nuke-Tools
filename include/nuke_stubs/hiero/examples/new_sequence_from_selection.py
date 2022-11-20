# Context menu option to create new sequences from selected Clips in the Bin View.
# If Clips are named as Stereo left and right then one sequence will be created with left and right tagged tracks.

import hiero.core
from PySide2 import QtWidgets
from PySide2.QtWidgets import QSizePolicy, QDialogButtonBox
import re
import os
import trace

class NewSequenceFromSelectionAction(QtWidgets.QAction):

  class NewSequenceFromSelection(QtWidgets.QDialog):

    def __init__(self,  trackItem,  parent=None):
      super(NewSequenceFromSelectionAction.NewSequenceFromSelection, self).__init__(parent)
      self.setWindowTitle("New Sequence")
      self.setSizeGripEnabled(False)
      self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      self.setContentsMargins(15, 10, 10, 0)
      self.layout = QtWidgets.QVBoxLayout()
      self.layout.setContentsMargins(20, 20, 20, 20)

      self.groupBox = QtWidgets.QGroupBox()
      self.groupLayout = QtWidgets.QFormLayout()
      self.groupBox.setLayout(self.groupLayout)

      self.radioSingle = QtWidgets.QRadioButton("Single Sequence", self.groupBox)
      self.radioSingle.setToolTip("Create a single sequence.\
                                  \nAll clips will be stacked on separate layers starting at frame 0\
                                  \nunless Sequential Layers is checked.")
      self.radioSingle.setChecked(True)
      self.radioMultiple = QtWidgets.QRadioButton("Multiple Sequences", self.groupBox)
      self.radioMultiple.setToolTip("Create multiple sequences, one for each clip.\
                                    \nIf 'Use Timecode' is checked each sequence will start at the clip timecode.\
                                    \nOtherwise each sequence will start at the default sequence start.")
      self.groupLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.radioSingle)
      self.groupLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.radioMultiple)

      self.spacerItem = QtWidgets.QSpacerItem(15, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
      self.groupLayout.setItem(2, QtWidgets.QFormLayout.LabelRole, self.spacerItem)

      self.sequenceLayers = QtWidgets.QCheckBox("Sequential Layers", self.groupBox)
      self.sequenceLayers.setChecked(True)
      self.sequenceLayers.setToolTip("Place the selected items on one track back to back if Single Sequence is selected.\nOtherwise items are stacked on separate tracks.")
      self.groupLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.sequenceLayers)

      self.includeAudio = QtWidgets.QCheckBox("Include Audio", self.groupBox)
      self.includeAudio.setChecked(True)
      self.includeAudio.setToolTip("Include Audio Tracks from clips containing audio (R3D, QuickTime).")
      self.groupLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.includeAudio)

      self.useTimecode = QtWidgets.QCheckBox("Use Timecode", self.groupBox)
      self.useTimecode.setChecked(False)
      self.useTimecode.setToolTip("Place clips on the timeline using timecode from the clip's metadata.")
      self.useTimecode.clicked.connect(self.useTimecodeChanged)
      self.groupLayout.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.useTimecode)

      self.timecodeHorizontalLayout = QtWidgets.QHBoxLayout()
      self.timecodeHorizontalLayout.setSpacing(-1)
      self.timecodeHorizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
      self.timecodeHorizontalLayout.setObjectName("timecodeHorizontalLayout")

      self.TCspacerItem = QtWidgets.QSpacerItem(15, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
      self.groupLayout.setItem(5, QtWidgets.QFormLayout.LabelRole, self.TCspacerItem)

      self.timecodeOptionsLabel = QtWidgets.QLabel()
      self.timecodeOptionsLabel.setText("Clips Without Timecode:")
      self.timecodeOptionsLabel.setToolTip("Choose how to handle clips with no inherent timecode.")
      self.timecodeOptionsLabel.setEnabled(self.useTimecode.isChecked() & self.radioSingle.isChecked())

      self.timecodeHorizontalLayout.addWidget(self.timecodeOptionsLabel)
      self.timecodeHorizontalLayout.setStretch(1, 40)
      self.timecodeOptions = QtWidgets.QComboBox()
      self.timecodeOptions.setToolTip("Choose how to handle clips with no inherent timecode:\
                                       \n-Add Stacked will create new tracks for each clip.\
                                       \n-Add To Single Track will lay each clip back to back on one track.\
                                       \n-Ignore will ignore these clips")

      self.timecodeOptions.currentIndexChanged.connect(self.timecodeOptionsChanged)
      self.groupLayout.setWidget(5, QtWidgets.QFormLayout.SpanningRole, self.timecodeOptions)
      self.timecodeOptions.addItem("Add Stacked")
      self.timecodeOptions.addItem("Add To Single Track")
      self.timecodeOptions.addItem("Ignore")
      self.timecodeOptions.setEnabled(self.useTimecode.isChecked() & self.radioSingle.isChecked())
      self.timecodeHorizontalLayout.addWidget(self.timecodeOptions)

      self.groupLayout.setLayout(5, QtWidgets.QFormLayout.SpanningRole, self.timecodeHorizontalLayout)

      self.dividerline1 = QtWidgets.QFrame()
      self.dividerline1.setFrameShape(QtWidgets.QFrame.HLine)
      self.dividerline1.setFrameShadow(QtWidgets.QFrame.Sunken)
      self.groupLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.dividerline1)

      self.horizontalLayout = QtWidgets.QHBoxLayout()
      self.horizontalLayout.setSpacing(-1)
      self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
      self.horizontalLayout.setObjectName("formatHorizontalLayout")
      self.formatLabel = QtWidgets.QLabel()
      self.formatLabel.setText("Format:")
      self.horizontalLayout.addWidget(self.formatLabel)
      self.formatChooser = hiero.ui.FormatChooser()
      self.formatChooser.setToolTip("Choose the format for a New Sequence created from Multiple Selections.")
      self.formatChooser.formatChanged.connect(self.formatChanged)
      self.horizontalLayout.addWidget(self.formatChooser)
      self.horizontalLayout.setStretch(1, 40)
      self.groupLayout.setLayout(7, QtWidgets.QFormLayout.SpanningRole, self.horizontalLayout)

      self.horizontalLayout2 = QtWidgets.QHBoxLayout()
      self.horizontalLayout2.setSpacing(-1)
      self.horizontalLayout2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
      self.horizontalLayout2.setObjectName("framerateHorizontalLayout")
      self.framerateLabel = QtWidgets.QLabel()
      self.framerateLabel.setText("Frame Rate:")
      self.horizontalLayout2.addWidget(self.framerateLabel)
      self.fpsChooser = QtWidgets.QComboBox()
      self.fpsChooser.setToolTip("Choose the framerate for a New Sequence created from Multiple Selections.")
      self.fpsChooser.currentIndexChanged.connect(self.fpsChanged)
      self.horizontalLayout2.addWidget(self.fpsChooser)
      self.horizontalLayout2.setStretch(1, 40)
      self.spacerItem2 = QtWidgets.QSpacerItem(175, 20, QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
      self.horizontalLayout2.addItem(self.spacerItem2)
      self.groupLayout.setLayout(8, QtWidgets.QFormLayout.SpanningRole, self.horizontalLayout2)

      self.dividerline2 = QtWidgets.QFrame()
      self.dividerline2.setFrameShape(QtWidgets.QFrame.HLine)
      self.dividerline2.setFrameShadow(QtWidgets.QFrame.Sunken)
      self.groupLayout.setWidget(9, QtWidgets.QFormLayout.SpanningRole, self.dividerline2)

      for fps in hiero.core.defaultFrameRates():
        if fps.is_integer():
          self.fpsChooser.addItem(str(int(fps)))
        else:
          self.fpsChooser.addItem(str(fps))

      # Add the standard ok/cancel buttons, default to ok.
      self.buttonBox = QtWidgets.QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Ok")
      self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
      self.buttonBox.accepted.connect(self.accept)
      self.buttonBox.rejected.connect(self.reject)
      self.groupLayout.addWidget(self.buttonBox)

      self.setLayout(self.groupLayout)
      self.layout.addWidget(self.groupBox)

      self.radioMultiple.clicked.connect(self.sequenceOptionChanged)
      self.radioSingle.clicked.connect(self.sequenceOptionChanged)

      firstclip = hiero.ui.activeView().selection()[0]
      try:
        format = firstclip.activeItem().format()
        self.formatChooser.setCurrentFormat(format)
      except:
        print("Could not set format")

      try:
        fps = firstclip.activeItem().framerate()
        for i in range(self.fpsChooser.count()):
          if str(self.fpsChooser.itemText(i)) == str(fps):
            self.fpsChooser.setCurrentIndex(i)
      except:
        self.fpsChooser.setCurrentIndex(6)
        print("Could not set framerate")

    def formatChanged(self):
      format = self.formatChooser.currentFormat()

    def fpsChanged(self):
      fps = self.fpsChooser.currentText()

    def sequenceOptionChanged(self):
      if self.radioMultiple.isChecked():
        self.sequenceLayers.setEnabled(False)
        self.formatChooser.setEnabled(False)
        self.fpsChooser.setEnabled(False)
        self.formatLabel.setEnabled(False)
        self.framerateLabel.setEnabled(False)
      if self.radioSingle.isChecked():
        self.sequenceLayers.setEnabled(True)
        if self.formatChooser.count() > 0:
          self.formatChooser.setEnabled(True)
          self.fpsChooser.setEnabled(True)
          self.formatLabel.setEnabled(True)
          self.framerateLabel.setEnabled(True)
      self.useTimecodeChanged()

    def useTimecodeChanged(self):
      if self.useTimecode.isChecked() and self.radioSingle.isChecked():
        self.timecodeOptions.setEnabled(True)
        self.timecodeOptionsLabel.setEnabled(True)
      else:
        self.timecodeOptions.setEnabled(False)
        self.timecodeOptionsLabel.setEnabled(False)

    def timecodeOptionsChanged(self):
      timecodeOption = self.timecodeOptions.currentText()
      if timecodeOption == "Ignore":
        self.ignoreZeroStart = True
        self.singleTrackZero = False
      if timecodeOption == "Add Stacked":
        self.ignoreZeroStart = False
        self.singleTrackZero = False
      if timecodeOption == "Add To Single Track":
        self.singleTrackZero = True

  def __init__(self):
      QtWidgets.QAction.__init__(self, "New Sequence from Selection", None)
      self.triggered.connect(self.doit)
      hiero.core.events.registerInterest((hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kBin), self.eventHandler)
      hiero.core.events.registerInterest(hiero.core.events.EventType.kSelectionChanged, self.eventHandler)

  def addClipToSequence(self, sequence, clip, start, trackindex, useTimecode=True, includeAudio=True):
    '''Add a clip to a sequence on track number @trackindex starting at frame @start.
       Optionally add linked audio if it exists (i.e. QuickTime or R3D).
    '''
    if useTimecode:
      if clip.mediaSource().hasVideo():
        clipfps = clip.framerate()
        sequencefps = sequence.framerate()
        if clipfps.toInt() != sequencefps.toInt():
          clipStart = self.convertStartTimecode(clip.timecodeStart(), clipfps.toInt(), sequencefps.toInt())
          if clipStart < sequence.timecodeStart():
            start = sequence.timecodeStart() - clipStart
          else:
            start = clipStart - sequence.timecodeStart()
        else:
          if clip.timecodeStart() < sequence.timecodeStart():
            start = sequence.timecodeStart() - clip.timecodeStart()
          else:
            start = clip.timecodeStart() - sequence.timecodeStart()
      else:
        videoClip = None

      if clip.mediaSource().hasAudio() and includeAudio:
        linkedItems = []
        for i in range(clip.numAudioTracks()):
          audioTrackName = "Audio " + str(i+1)
          if not self.trackExists(sequence, audioTrackName):
            newAudioTrack = sequence.addTrack(hiero.core.AudioTrack(audioTrackName))
          else:
            newAudioTrack = self.trackExists(sequence, audioTrackName)
          audioClip = newAudioTrack.addTrackItem(clip, i, start)
          linkedItems.append(audioClip)
          if videoClip:
            audioClip.link(videoClip)
          else:
            if len(linkedItems) > 0:
              audioClip.link(linkedItems[0])
    else:
      try:
        if trackindex == len(sequence.videoTracks()):
          sequence.addTrack(hiero.core.VideoTrack("Video " + str(trackindex+1)))
        videoClip = sequence.videoTrack(trackindex).addTrackItem(clip, start)
      except:
        print("Failed to add clip")

  def newSequence(self, selection):
    '''Create a new sequence from a selection of clips
       @return hiero.core.Sequence, hiero.core.Bin
    '''
    if isinstance(selection[0], hiero.core.BinItem):
      clip = selection[0].activeItem()
    elif isinstance(selection[0], hiero.core.Clip):
      clip = selection[0]

    bin = clip.binItem().parentBin()
    sequence = hiero.core.Sequence(selection[0].name())

    if clip.mediaSource().hasVideo():
      if clip.mediaSource().metadata()["foundry.source.framerate"]:
        fps = clip.mediaSource().metadata()["foundry.source.framerate"]
      else:
        fps = clip.framerate()
      sequence.setFramerate(hiero.core.TimeBase.fromString(str(fps)))
      sequence.setFormat(clip.format())

      for i in range(clip.numVideoTracks()):
        sequence.addTrack(hiero.core.VideoTrack("Video " + str(i+1)))
        try:
          videoClip = sequence.videoTrack(i).addTrackItem(clip, 0)
        except:
          print("Failed to add clip")
    else:
      videoClip = None

    if clip.mediaSource().hasAudio():
      linkItems = []
      for i in range(clip.numAudioTracks()):
        audioTrackName = "Audio " + str( i+1 )
        if not self.trackNameExists(sequence, audioTrackName):
          newAudioTrack = sequence.addTrack(hiero.core.AudioTrack(audioTrackName))
        else:
          newAudioTrack = self.trackNameExists(sequence, audioTrackName)
        audioClip = newAudioTrack.addTrackItem(clip, i, 0)
        linkItems.append(audioClip)
        if videoClip:
          audioClip.link(videoClip)
        else:
          if len(linkItems) > 0:
            audioClip.link(linkItems[0])

    return sequence, bin

  def newStereoSequence(self, leftClip, rightClip, baseName, useTimecode):
    '''Create a stereo sequence with Left/Right tagged tracks.
       Eventually when full stereo support is implemented this can be changed.
       @return hiero.core.Sequence
    '''
    bin = leftClip.binItem().parentBin()
    fps = leftClip.framerate()
    sequence = hiero.core.Sequence(baseName)
    sequence.setFramerate(hiero.core.TimeBase.fromString(str(fps)))
    sequence.setFormat(leftClip.format())
    trackLeft = hiero.core.VideoTrack("Left")
    trackRight = hiero.core.VideoTrack("Right")
    sequence.addTrack(trackLeft)
    sequence.addTrack(trackRight)

    if useTimecode:
      start = leftClip.timecodeStart()
    else:
      start = 0

    videoLeft = trackLeft.addTrackItem(leftClip, start)
    videoRight = trackRight.addTrackItem(rightClip, start)

    newStartTC = self.earliestTimecode(sequence)
    sequence.setTimecodeStart(newStartTC)
    sequence.clearRange(0, newStartTC-1, True)

    leftTag = hiero.core.findProjectTags(hiero.core.projects(hiero.core.Project.kStartupProjects)[0], "Left")
    rightTag = hiero.core.findProjectTags(hiero.core.projects(hiero.core.Project.kStartupProjects)[0], "Right")
    trackLeft.addTag(leftTag[0])
    trackRight.addTag(rightTag[0])

    return sequence

  def findStereoPairs(self, selection):
    ''' Look for matching stereo pairs in the selection and return a list.
        Also return the remaining unpaired clips as a list.
        @return list, list
    '''
    stereoPairs = []
    singleFiles = []
    leftrx = re.compile("(.*)(_L(eft)?)$", re.IGNORECASE)
    rightrx = re.compile("(.*)(_R(ight)?)$", re.IGNORECASE)

    for item in selection:
      clip = item.activeItem()

      if not leftrx.match(clip.name()) and not rightrx.match(clip.name()):
        singleFiles.append(clip)

      if leftrx.match(clip.name()):
        baseName = leftrx.match(clip.name()).groups()[0]
        if len(stereoPairs) == 0:
          stereoPairs.append([clip])
        else:
          pairMatch = False
          for i in range(len(stereoPairs)):
            for item in stereoPairs[i]:
              if baseName in item.name():
                stereoPairs[i].append(clip)
                pairMatch = True
                break
          if not pairMatch:
            stereoPairs.append([clip])

      if rightrx.match(clip.name()):
        baseName = rightrx.match(clip.name()).groups()[0]
        if len(stereoPairs) == 0:
          stereoPairs.append([clip])
        else:
          pairMatch = False
          for i in range(len(stereoPairs)):
            for item in stereoPairs[i]:
              if baseName in item.name():
                stereoPairs[i].append(clip)
                pairMatch = True
                break
          if not pairMatch:
            stereoPairs.append([clip])

    # Python doesn't like you to remove things from a list while iterating
    # over that same list so we add those items to a new list and then remove
    unmatchedPairs = []

    for pair in stereoPairs:
      if len(pair) == 1:
        unmatchedPairs.append(pair)

    for pair in unmatchedPairs:
      singleFiles.append(pair[0])
      stereoPairs.remove(pair)

    return stereoPairs, singleFiles

  def earliestTimecode(self, sequence):
    '''Find the earliest timeline timecode used in a sequence.
       @return long
    '''
    sequenceTimecodes = []
    for track in sequence:
      for item in track:
        sequenceTimecodes.append(item.timelineIn())

    earliest = sorted(sequenceTimecodes)[0]
    return earliest

  def convertStartTimecode(self, start, sourcerate, destrate):
    '''Convert Start Timecode from @sourcerate to @destrate
       @return destination start timecode in frames
    '''
    # hiero.core.TimeBase.convert should do this, but it doesn't do it correctly
    # so we do it manually here
    startHMSF = hiero.core.Timecode.framesToHMSF(start, sourcerate, False)
    destFrames = hiero.core.Timecode.HMSFToFrames(destrate, False, int(startHMSF[0]), int(startHMSF[1]), int(startHMSF[2]), int(startHMSF[3]))
    return destFrames

  def clipInfo(self, clip, fps):
    '''Get a clip object and framerange
       @return dict
    '''
    if clip.activeItem().mediaSource().hasVideo():
      start = self.convertStartTimecode(clip.activeItem().timecodeStart(), clip.activeItem().framerate().toInt(), fps.toInt())
      end = start + clip.activeItem().duration() - 1
    else:
      # Clip only contains audio and probably no inherent framerate
      start = clip.activeItem().timecodeStart()
      end = start + clip.activeItem().duration() - 1

    clipInfo = {}
    clipInfo['clip'] = {}
    clipInfo['clip']['src'] = clip
    clipInfo['clip']['framerange'] = list(range(start, end))

    return clipInfo

  def buildTracksFromTimecode(self, selection, siftedselection, fps, tracks, trackindex=0, ignoreZeroStart=False, singleTrackZero=False):
    '''Create a dictionary of tracks using clip timecode to check for overlaps.
       If timecode overlaps the clip is placed on a new track.
       @selection: the clips selected
       @siftedselection: list of items without timecode (or starting at 00:00:00:00 which is usually the same thing)
       @fps: framerate
       @tracks: empty dict we fill in using @selection
       @trackindex: the current track index
       @ignoreZeroStart: flag to ignore clips that start with timecode 00:00:00:00
       @singleTrackZero: flag to indicate we want to add clips with start timecode 00:00:00:00 to a single track (True) or stacked (False)
       @return dict of tracks, list of clips with
    '''
    for clip in selection:
      try:
        # check if the track has been initialized
        tracks[trackindex]
      except:
        # track hasn't been initialized yet so do it here
        tracks[trackindex] = []

      clipInfo = self.clipInfo(clip, fps)
      cliprange = clipInfo['clip']['framerange']

      # if the current track is not empty we need to check if the clip conflicts with
      # existing track items before we can add it
      if len(tracks[trackindex]) > 0:
        for i in tracks:
          if clip in tracks[i]:
            clipexists = True
            break
          else:
            clipexists = False

        # we didn't find the clip already on a track so we are ready to add it
        if not clipexists:
          overlap = False
          for item in tracks[trackindex]:
            iteminfo = self.clipInfo(item, fps)
            itemrange = iteminfo['clip']['framerange']
            # If the ranges overlap we will get a list by adding sets (i.e. set(A) & set(B)).
            # If there is no overlap the list will be empty.
            if list(set(cliprange) & set(itemrange)):
              # clips overlap so try to add the clip to the next track
              overlap = True
              break

          if overlap:
            # conflict was found so increment the current track by 1 and try again
            self.buildTracksFromTimecode([clip], siftedselection, fps, tracks, trackindex=trackindex+1, ignoreZeroStart=ignoreZeroStart, singleTrackZero=singleTrackZero)
          else:
            # no conflict on this track so add the clip
            tracks[trackindex].append(clip)
      else:
        for i in tracks:
          if clip in tracks[i]:
            clipexists = True
            break
          else:
            clipexists = False
        if not clipexists:
          tracks[trackindex].append(clip)

    return tracks, siftedselection

  def trackNameExists(self, sequence, trackName):
    for track in sequence:
      if track.name() == trackName:
        return track
    return None

  def recursiveClips(self, selection, clips):
    for s in selection:
      if isinstance(s, hiero.core.Bin):
        for item in list(s.items()):
          if isinstance(item, hiero.core.BinItem) and hasattr(item, "activeItem"):
            if isinstance(item.activeItem(), hiero.core.Clip):
              clips.append(item)
          elif isinstance(item, hiero.core.Bin):
              self.recursiveClips([item], clips)
      elif isinstance(s, hiero.core.BinItem) and hasattr(s, "activeItem"):
        if isinstance(s.activeItem(), hiero.core.Clip):
          clips.append(s)

    return clips

# Change doit to reallydoit to get a trace for debugging.
#   def doit(self):
#     tracer = trace.Trace( count=False, trace=True )
#     tracer.runfunc( NewSequenceFromSelectionAction.reallydoit, self )

  def doit(self):
    selection = list(hiero.ui.activeView().selection())
    ignoredItems = []
    for selected in selection:
      if isinstance(selected, hiero.core.BinItem) and hasattr(selected, "activeItem"):
        if isinstance(selected.activeItem(), hiero.core.Sequence):
          ignoredItems.append(selected)

    if ignoredItems:
      for item in ignoredItems:
        selection.remove(item)

    isStereo = False

    if len(selection) == 1 and isinstance(selection[0], hiero.core.Bin):
      clips = []
      selection = self.recursiveClips(selection, clips)

    # if only one item is selected and it's a clip, not a bin
    if len(selection) == 1:
      if isinstance(selection[0], hiero.core.BinItem) or isinstance(selection[0], hiero.core.Clip):
        sequence, bin = self.newSequence(selection)
        bin.addItem(hiero.core.BinItem(sequence))
        sequence.editFinished()

    # If exactly 2 items are selected we check to see if they are a stereo pair
    # If yes then create a stereo sequence. Otherwise treat them as 2 normal clips
    if len(selection) == 2:
      hiero.core.projects()[-1].beginUndo("New Stereo Sequence")
      leftrx = re.compile("(.*)(_L(eft)?)$", re.IGNORECASE)
      rightrx = re.compile("(.*)(_R(ight)?)$", re.IGNORECASE)
      stereoPairs, singleFiles = self.findStereoPairs(selection)

      if stereoPairs:
        isStereo = True
        for pair in stereoPairs:

          if len(pair) == 2:
            if leftrx.match(pair[0].name()) and rightrx.match(pair[1].name()):
              leftClip = pair[0]
              rightClip = pair[1]
            else:
              leftClip = pair[1]
              rightClip = pair[0]
            try:
              newName = leftrx.match(leftClip.name()).groups()[0]
              sequence = self.newStereoSequence(leftClip, rightClip, newName, False)
              bin = leftClip.binItem().parentBin()
              if sequence:
                bin.addItem(hiero.core.BinItem(sequence))
                sequence.editFinished()
            except:
              print("Error creating Stereo Sequence")
      hiero.core.projects()[-1].endUndo()

    # If multiple clips are selected and we want a Single Sequence
    if len(selection) > 1 and isStereo == False:
      dialog = self.NewSequenceFromSelection(selection)
      if dialog.exec_():
        if dialog.radioSingle.isChecked() == True:
          hiero.core.projects()[-1].beginUndo("New Sequence From Selection")
          newFPS = hiero.core.TimeBase.fromString(str(dialog.fpsChooser.currentText()))
          newResolution = dialog.formatChooser.currentFormat()

          # If we want to stack clips on separate layers
          if dialog.sequenceLayers.isChecked() == False:
            clip = selection[0].activeItem()
            bin = clip.binItem().parentBin()
            sequence = hiero.core.Sequence(selection[0].name())

            if clip.mediaSource().hasVideo():
              if clip.mediaSource().metadata()["foundry.source.framerate"]:
                fps = clip.mediaSource().metadata()["foundry.source.framerate"]
              else:
                fps = clip.framerate()
              sequence.setFramerate(newFPS)
              sequence.setFormat(newResolution)
            else:
              videoClip = None

            k = 0
            j = 0
            for item in selection:
              clip = item.activeItem()
              if clip.mediaSource().hasVideo():
                for i in range(clip.numVideoTracks()):
                  newVideoTrack = sequence.addTrack(hiero.core.VideoTrack("Video " + str(k+1)))
                  try:
                    videoClip = newVideoTrack.addTrackItem(clip, 0)
                  except:
                    print("Failed to add clip")
              else:
                videoClip = None
              k+=1

              if clip.mediaSource().hasAudio() and dialog.includeAudio.isChecked():
                linkedItems = []
                for i in range(clip.numAudioTracks()):
                  newAudioTrack = sequence.addTrack(hiero.core.AudioTrack("Audio " + str(j+i+1) ))
                  audioClip = newAudioTrack.addTrackItem(clip, i, 0)
                  linkedItems.append(audioClip)
                  if videoClip:
                    audioClip.link(videoClip)
                  else:
                    if len(linkedItems) > 0:
                      audioClip.link(linkedItems[0])
                  j+=1

            bin.addItem(hiero.core.BinItem(sequence))
            sequence.editFinished()
            hiero.core.projects()[-1].endUndo()

          # Add the clips to the sequence back to back on one video layer ignoring timecode
          if dialog.sequenceLayers.isChecked() == True:
            if not dialog.useTimecode.isChecked():
              clip = selection[0].activeItem()
              bin = clip.binItem().parentBin()
              sequence = hiero.core.Sequence(selection[0].name())

              if clip.mediaSource().hasVideo():
                if clip.mediaSource().metadata()["foundry.source.framerate"]:
                  fps = hiero.core.TimeBase(clip.mediaSource().metadata()["foundry.source.framerate"])
                else:
                  fps = clip.framerate()
                sequence.setFramerate(newFPS)
                sequence.setFormat(newResolution)
              else:
                videoClip = None
                fps = sequence.framerate()

              sequence.addTrack(hiero.core.VideoTrack("Video 1"))
              k = 0
              for item in selection:
                clip = item.activeItem()

                if clip.mediaSource().hasVideo():
                  for i in range(clip.numVideoTracks()):
                    try:
                      videoClip = sequence.videoTrack(0).addTrackItem(clip, k)
                    except:
                      print("Failed to add clip")
                    outTime = clip.duration() - 1
                else:
                  videoClip = None
                  outTime = None

                if clip.mediaSource().hasAudio() and dialog.includeAudio.isChecked():
                  linkedItems = []
                  for i in range(clip.numAudioTracks()):
                    audioTrackName = "Audio " + str( i+1 )
                    if not self.trackNameExists(sequence, audioTrackName):
                      newAudioTrack = sequence.addTrack(hiero.core.AudioTrack(audioTrackName))
                    else:
                      newAudioTrack = self.trackNameExists(sequence, audioTrackName)

                    audioClip = newAudioTrack.addTrackItem(clip, i, k)
                    linkedItems.append(audioClip)
                    if videoClip:
                      audioClip.link(videoClip)
                    else:
                      if len(linkedItems) > 0:
                        audioClip.link(linkedItems[0])
                        # Audio only duration is currently returned in samples so we need to convert to frames
                        outTime = ( float(clip.duration() / 48000) * fps.toFloat() ) - 1
                k += (outTime + 1)
              bin.addItem(hiero.core.BinItem(sequence))
              sequence.editFinished()
              hiero.core.projects()[-1].endUndo()
            else:
              # Build the sequence based on clip timecode.
              tracks = {}
              tracks[0] = []

              selection = list(selection)
              siftedselection = []

              for clip in selection:
                if clip.activeItem().timecodeStart() == 0:
                  if dialog.ignoreZeroStart or dialog.singleTrackZero:
                    siftedselection.append(clip)
              if siftedselection:
                for item in siftedselection:
                  selection.remove(item)

              if dialog.ignoreZeroStart:
                cliptracks, zeroStartClips = self.buildTracksFromTimecode(selection, siftedselection, newFPS, tracks, 0, True)
              elif not dialog.ignoreZeroStart and dialog.singleTrackZero:
                cliptracks, zeroStartClips = self.buildTracksFromTimecode(selection, siftedselection, newFPS, tracks, 0, False, True)
              else:
                cliptracks, zeroStartClips = self.buildTracksFromTimecode(selection, siftedselection, newFPS, tracks, 0, False)
              if cliptracks:
                clip1 = cliptracks[0][0]
                bin = clip1.parentBin()
                # Name the sequence based on the first clip in the selection
                sequence = hiero.core.Sequence(clip1.name())
                sequence.setFramerate(newFPS)
                sequence.setFormat(newResolution)
                # Set the start timecode to zero so everything is added correctly
                # If the default is set to 01:00:00:00 and we try to add clips with
                # timecode before hour 01 then it won't work so start with zero and
                # change it back later if necessary
                sequence.setTimecodeStart(0)

                for trackindex in range(len(cliptracks)):
                  sequence.addTrack(hiero.core.VideoTrack("Video %s" % (trackindex + 1)))

                  for item in cliptracks[trackindex]:
                    clip = item.activeItem()
                    if not clip.mediaSource().hasVideo():
                      videoClip = None
                      fps = sequence.framerate()

                    if clip.mediaSource().hasVideo():
                      for i in range(clip.numVideoTracks()):
                        clipfps = clip.framerate()
                        sequencefps = sequence.framerate()
                        if clipfps.toInt() != sequencefps.toInt():
                          # Convert start timecodes to the destination fps
                          # This will ensure that the first frame of each clip with a different timebase
                          # is still at the correct timecode
                          clipStart = self.convertStartTimecode(clip.timecodeStart(), clipfps.toInt(), sequencefps.toInt())
                          if clipStart < sequence.timecodeStart():
                            sequence.setTimecodeStart(clipStart)
                            start = sequence.timecodeStart() - clipStart
                          else:
                            start = clipStart - sequence.timecodeStart()
                        else:
                          if clip.timecodeStart() < sequence.timecodeStart():
                            sequence.setTimecodeStart(clip.timecodeStart())
                            start = sequence.timecodeStart() - clip.timecodeStart()
                          else:
                            start = clip.timecodeStart() - sequence.timecodeStart()
                        try:
                          videoClip = sequence.videoTrack(trackindex).addTrackItem(clip, start)
                        except:
                          print("Failed to add clip")
                    else:
                      videoClip = None

                    if clip.mediaSource().hasAudio() and dialog.includeAudio.isChecked():
                      linkedItems = []
                      for i in range(clip.numAudioTracks()):
                        print("Source track Num", i)
                        print("Trackindex", trackindex)
                        try:
                          newAudioTrack = sequence.audioTrack(trackindex + i)
                        except:
                          newAudioTrack = sequence.addTrack(hiero.core.AudioTrack("Audio %s" % (trackindex + i + 1)))
                        audioClip = newAudioTrack.addTrackItem(clip, i, start)
                        linkedItems.append(audioClip)
                        if videoClip:
                          audioClip.link(videoClip)
                        else:
                          if len(linkedItems) > 0:
                            audioClip.link(linkedItems[0])

              if siftedselection and dialog.singleTrackZero:
                # len will give us current track count (len([0,1]) = 2 so 2 is the next trackindex)
                trackindex = len(cliptracks)
                start = 0
                for selection in siftedselection:
                  clip = selection.activeItem()
                  self.addClipToSequence(sequence, clip, start, trackindex, False, False)
                  start += clip.duration()
              bin.addItem(hiero.core.BinItem(sequence))
              # Set the start timecode to the earliest clip start time in the sequence
              # and then remove anything between 0 and the first clip.
              newStartTC = self.earliestTimecode(sequence)
              sequence.setTimecodeStart(newStartTC)
              sequence.clearRange(0, newStartTC-1, True)
              sequence.editFinished()
              hiero.core.projects()[-1].endUndo()

        # Multiple Sequences from selection
        if dialog.radioMultiple.isChecked():
          hiero.core.projects()[-1].beginUndo("Multiple Sequences From Selection")
          leftrx = re.compile("(.*)(_L(eft)?)$", re.IGNORECASE)
          rightrx = re.compile("(.*)(_R(ight)?)$", re.IGNORECASE)

          stereoPairs, singleFiles = self.findStereoPairs(selection)

          for pair in stereoPairs:

            if len(pair) == 2:
              if leftrx.match(pair[0].name()) and rightrx.match(pair[1].name()):
                leftClip = pair[0]
                rightClip = pair[1]
              else:
                leftClip = pair[1]
                rightClip = pair[0]

              try:
                newName = leftrx.match(leftClip.name()).groups()[0]
                sequence = self.newStereoSequence(leftClip, rightClip, newName, dialog.useTimecode.isChecked())
                bin = leftClip.binItem().parentBin()
                if sequence:
                  bin.addItem(hiero.core.BinItem(sequence))
                  sequence.editFinished()
              except:
                print("Error creating Stereo Sequence")

          for clip in singleFiles:

            bin = clip.binItem().parentBin()
            sequence = hiero.core.Sequence(clip.name())

            if clip.mediaSource().hasVideo():
              if clip.mediaSource().metadata()["foundry.source.framerate"]:
                fps = clip.mediaSource().metadata()["foundry.source.framerate"]
              else:
                fps = clip.framerate()
              sequence.setFramerate(hiero.core.TimeBase.fromString(str(fps)))
              sequence.setFormat(clip.format())

              if dialog.useTimecode.isChecked():
                start = clip.timecodeStart()
                sequence.setTimecodeStart(0)
              else:
                start = 0
              for i in range(clip.numVideoTracks()):
                sequence.addTrack(hiero.core.VideoTrack("Video " + str(i+1)))
                try:
                  videoClip = sequence.videoTrack(i).addTrackItem(clip, start)
                except:
                  print("Failed to add clip")
                  videoClip = None
            else:
              videoClip = None

            if clip.mediaSource().hasAudio() and dialog.includeAudio.isChecked():
              linkedItems = []

              if dialog.useTimecode.isChecked():
                start = clip.timecodeStart()
                sequence.setTimecodeStart(0)
              else:
                start = 0

              for i in range(clip.numAudioTracks()):
                audioTrackName = "Audio " + str( i+1 )
                if not self.trackNameExists(sequence, audioTrackName):
                  newAudioTrack = sequence.addTrack(hiero.core.AudioTrack(audioTrackName))
                else:
                  newAudioTrack = self.trackNameExists(sequence, audioTrackName)
                audioClip = newAudioTrack.addTrackItem(clip, i, start)
                linkedItems.append(audioClip)
                if videoClip:
                  audioClip.link(videoClip)
                else:
                  if len(linkedItems) > 0:
                    audioClip.link(linkedItems[0])

            bin.addItem(hiero.core.BinItem(sequence))
            sequence.editFinished()
          hiero.core.projects()[-1].endUndo()

  def eventHandler(self, event):
    if not hasattr(event.sender, 'selection'):
      return

    # Disable if nothing is selected
    selection = event.sender.selection()

    if selection is None:
      selection = ()

    title = "New Sequence from Selection"
    self.setText(title)
    self.setEnabled( len(selection) > 0 )
    if hasattr(event, "menu"):
      event.menu.addAction(self)

action = NewSequenceFromSelectionAction()
