# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import os
import sys
from . import FnAudioConstants
from . import FnAudioHelper

from hiero.core import TaskBase
from hiero.core import TaskPresetBase
from hiero.core import taskRegistry
from hiero.core import Sequence
from hiero.core import TrackItem
from hiero.core import Clip
from . FnExportUtil import writeSequenceAudioWithHandles
from collections import OrderedDict

class AudioExportTask(TaskBase):
  def __init__( self, initDict ):
    """Initialize"""
    TaskBase.__init__( self, initDict )


  def startTask(self):
    TaskBase.startTask(self)

    pass

  def sequenceInOutPoints(self, sequence, indefault, outdefault):
    """Return tuple (start, end) of in/out points. If either in/out is not set, return in/outdefault in its place."""
    inTime, outTime = indefault, outdefault
    try:
      inTime = sequence.inTime()
    except:
      pass

    try:
      outTime = sequence.outTime()
    except:
      pass
    return inTime, outTime

  def taskStep(self):
    # Write out the audio bounce down
    if isinstance(self._item, (Sequence, TrackItem)):
      if self._sequenceHasAudio(self._sequence):
        self.setExportSettings()

        if isinstance(self._item, Sequence):
          start, end = self.sequenceInOutPoints(self._item, 0, self._item.duration() - 1)

          # If sequence, write out full length
          self._item.writeAudioToFile(self._audioFile,
                                      start,
                                      end,
                                      self._outputChannels,
                                      self._sampleRate,
                                      self._bitDepth,
                                      self._bitRate)

        elif isinstance(self._item, TrackItem):
          # Write out the audio covering the range of the track item,
          # including handles
          handles = self._cutHandles if self._cutHandles is not None else 0
          writeSequenceAudioWithHandles(self._audioFile,
                                        self._sequence,
                                        self._item.timelineIn(),
                                        self._item.timelineOut(),
                                        handles,
                                        handles,
                                        self._outputChannels,
                                        self._sampleRate,
                                        self._bitDepth,
                                        self._bitRate)

    elif isinstance(self._item, Clip):
      # If item is clip, we're writing out the clip audio not the whole sequence
      if self._item.mediaSource().hasAudio():
        self.setExportSettings()

        # If sequence or clip, write out full length
        self._item.writeAudioToFile(self._audioFile, 
                                    self._outputChannels, 
                                    self._sampleRate, 
                                    self._bitDepth, 
                                    self._bitRate)


    self._finished = True

    return False

  def setExportSettings(self):
    self._audioFile = self.resolvedExportPath()

    extension = FnAudioConstants.kCodecs[self._preset.properties()[FnAudioConstants.kCodecKey]]

    filename, ext = os.path.splitext(self._audioFile)
    if ext.lower() != extension:
      self._audioFile = filename + extension

    FnAudioHelper.setAudioExportSettings(self)
    

class AudioExportPreset(TaskPresetBase):
  def __init__(self, name, properties):
    TaskPresetBase.__init__(self, AudioExportTask, name)
    # Set any preset defaults here
    # self._properties["SomeProperty"] = "SomeValue"
    FnAudioHelper.defineExportPresetProperties(self)

    # Update preset with loaded data
    self.properties().update(properties)

  def supportedItems(self):
    return TaskPresetBase.kAllItems | TaskPresetBase.kAudioTrackItem

taskRegistry.registerTask(AudioExportPreset, AudioExportTask)
