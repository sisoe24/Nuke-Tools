# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import re
import os
import os.path

import hiero.core

from hiero.core import FnResolveTable
from hiero.core import log
from hiero.core import Keys
from hiero.core import Transition
from hiero.core import util
from hiero.importers.FnEdlStructures import *
from hiero.core.FnExporterBase import mediaSourceExportReadPath, mediaSourceExportFileHead
from . FnExportKeywords import kFileBaseKeyword, kFileHeadKeyword, KeywordTooltips


class EDLExportAudioTrackTask:
  def __init__(self, parent, tracks):
    self._parent = parent
    self._tracks = tracks
    self._trackItems = []
    self._trackItemIndex = 0
    self._fps = parent._fps
    self._preset = parent._preset
    self._eventIndex = 1
    self._edits = []
    self.filterTrackItems()

  def edits(self):
    return self._edits

  # Filter out track items which represent different channels for the same audio source.  We only want the first one for EDL export.
  def filterTrackItems(self):
    addedItems = set()
    trackIndex = 0
    for track in self._tracks:
      trackIndex += 1
      for trackItem in track:
        # If the track items are just different channels then source, sourceIn, sourceOut, timelineIn and timelineOut should be the same.
        data = (trackItem.source(), trackItem.sourceIn(), trackItem.sourceOut(), trackItem.timelineIn(), trackItem.timelineOut())
        if not data in addedItems:
          self._trackItems.append( (trackItem, trackIndex) )
          addedItems.add( data )

  def taskStep(self):
    if len(self._trackItems) == 0:
      return False
    trackItem, trackIndex = self._trackItems[self._trackItemIndex]
    channels = None
    metadata = trackItem.source().mediaSource().metadata()
    numChannels = int(metadata.value(Keys.kSourceNumAudioChannels)) if metadata.hasKey(Keys.kSourceNumAudioChannels) else 1
    if numChannels == 1:
      channels = [str(trackIndex)]
    else:
      channels = [str(trackIndex), str(trackIndex+1)]
    
    mode = None
    #If we're not on track 1, leave the mode as NONE, and write the AUD line instead
    if trackIndex == 1:
      mode = ModeField(True, False, channels)
    else:
      mode = ModeField(False, False, [])
    effect = EffectField(EffectField.CUT, 0)
    clip = None
    dropFrame = False
    sourceIn = trackItem.sourceIn()
    sourceOut = trackItem.sourceOut()

    # Source times are in frame numbers from the start of the clip.
    # Offset them by the clip's timecodeStart to get the timecode at that frame.
    if isinstance(trackItem.source(), hiero.core.Clip):
      clip = trackItem.source()
      sourceIn += clip.timecodeStart()
      sourceOut += clip.timecodeStart()

    timecodeStart = self._parent._sequence.timecodeStart()

    # TODO: Is the src framerate the same as the dst framerate?
    # Note EDLs use traditional tape-style outpoints of the frame where the video is completely out
    # not NLE style outpoints that are the last used frame, so we need to add 1 to the outpoint.
    # Note by Anton: using +1 is not corrects for source times when under a retime. Use durations instead.  
    srcEntry = TimeCode.createFromFrames(sourceIn, self._fps, dropFrame)
    srcExit = TimeCode.createFromFrames(sourceIn + trackItem.sourceDuration(), self._fps, dropFrame)
    syncEntry = TimeCode.createFromFrames(timecodeStart + trackItem.timelineIn(), self._fps, dropFrame)
    syncExit = TimeCode.createFromFrames(timecodeStart + trackItem.timelineIn() + trackItem.duration(), self._fps, dropFrame)

    editName = self._parent.trackItemEditName(trackItem)

    # Build an edit decision object.
    edit = EditDecision(self._eventIndex, editName, mode, effect, srcEntry, srcExit, syncEntry, syncExit)

    # if there is a source with a filename, add it as a 'from clip' element
    if clip is not None and clip.mediaSource() is not None and clip.mediaSource().fileinfos() is not None:
      fileinfo = clip.mediaSource().fileinfos()[0]
      if fileinfo is not None:
        filename = fileinfo.filename()
        if not self._preset.properties()["abspath"]:
          filename = os.path.basename(filename)
      edit.addElement(NamedElement("* FROM CLIP NAME:", filename))

    if trackIndex != 1:
      edit.addElement( NamedElement("AUD", "  ".join(channels)) )

    self._edits.append(edit)
    
    log.debug( ">>>> EDLExportTask generated:" )
    log.debug( str(edit) + '\n' )

    # add the dump from the edit object to a string and add
    # another CRLF to leave a blank line between entries.
    self._eventIndex += 1
    self._trackItemIndex += 1
    
    return self._trackItemIndex < len(self._trackItems)


class CompoundEditDecision:
  def __init__(self):
    self._edits = []
  
  def __repr__(self):
    string = ""
    for edit in self._edits:
      string += str(edit)
    return string

  def append(self, edit):
    self._edits.append(edit)

  def syncEntry(self):
    return self._edits[0].syncEntry()

  def setEditId(self, editId):
    for edit in self._edits:
      edit.setEditId(editId)
    

class EDLExportTrackTask:
  def __init__(self, parent, track, trackItems):
    self._parent = parent
    self._track = track
    self._trackItems = trackItems
    self._trackItemIndex = 0
    # Note EDL event indexes start at 1. In the future we may want to skip some track items so
    # keeping these counters separate to make sure EDL events will still increment sequentially.
    self._eventIndex = 1
    self._fps = parent._fps
    self._preset = parent._preset
    self._edits = []
    self._dropFrame = False

  def edits(self):
    return self._edits

  # Create a basic EDL cut
  def createCut(self, trackItem):
    srcEntry, srcExit, syncEntry, syncExit = self.trackItemTimes(trackItem)

    mode = ModeField(False, True, [])
    effect = EffectField(EffectField.CUT, 0)
    editName = self._parent.trackItemEditName(trackItem)

    # Build an edit decision object.
    edit = EditDecision(self._eventIndex, editName, mode, effect, srcEntry, srcExit, syncEntry, syncExit)
    
    # If the fromClip text resolves to something, add it as a 'from clip' element.
    fromClip = self._parent.resolveFromTrackItem(trackItem, 'fromClip')
    if fromClip:
      edit.addElement(NamedElement("* FROM CLIP NAME:", fromClip))
    
    speed = trackItem.playbackSpeed()
    if speed != 1:
      retime = speed * self._fps # M2 Retimes must be expressed in fps
      edit.setRetime(retime, srcEntry)

    self._edits.append( edit )
    
    log.debug( ">>>> EDLExportTask generated:" )
    log.debug( str(edit) + '\n' )

  # Create a fade in event
  def createFadeIn(self, trackItem):
    transition = trackItem.inTransition()

    edits = CompoundEditDecision()

    srcEntry, srcExit, syncEntry, syncExit = self.trackItemTimes(trackItem)

    # If the track item has an out transition, we need to run this event until the transition start time.
    outTransition = trackItem.outTransition()
    if outTransition:
      outDuration = outTransition.timelineOut() - outTransition.timelineIn() + 1
      outOffset = outDuration
      if outTransition.alignment() == Transition.kDissolve:
        outOffset = outOffset / 2
      srcExit = srcExit.addFrames( -outOffset, self._fps )
      syncExit = syncExit.addFrames( -outOffset, self._fps )
    
    mode = ModeField(False, True, [])
    effect = EffectField(EffectField.CUT, 0)
    zeroTime = TimeCode.createFromFrames(0, self._fps, self._dropFrame)
    blankEdit = EditDecision(self._eventIndex, "BL", mode, EffectField(EffectField.CUT, 0), zeroTime, zeroTime, syncEntry, syncEntry)
    edits.append(blankEdit)
    transitionDuration = transition.timelineOut() - transition.timelineIn() + 1
    effect = EffectField(EffectField.DISSOLVE, transitionDuration)

    editName = self._parent.trackItemEditName(trackItem)

    # Build an edit decision object.
    edit = EditDecision(self._eventIndex, editName, mode, effect, srcEntry, srcExit, syncEntry, syncExit)
    
    # Do we want comments for the effects?  This seems to be from FCP
    #toEdit.addElement( NamedElement("* EFFECT NAME:", "FADE IN FADE OUT DISSOLVE") )

    # If the fromClip text resolves to something, add it as a 'to clip' element.
    fromClip = self._parent.resolveFromTrackItem(trackItem, 'fromClip')
    if fromClip:
      edit.addElement(NamedElement("* TO CLIP NAME:", fromClip))
    
    edits.append(edit)

    self._edits.append( edits )
    
    log.debug( ">>>> EDLExportTask generated:" )
    log.debug( str(edit) + '\n' )

  def createFadeOut(self, trackItem):
    transition = trackItem.outTransition()

    edits = CompoundEditDecision()

    srcEntry, srcExit, syncEntry, syncExit = self.trackItemTimes(trackItem)

    transitionDuration = transition.timelineOut() - transition.timelineIn() + 1
    transitionStart = syncExit.addFrames(-transitionDuration, self._fps)

    # If the track item has an in transition, we should have a 0-length clip at the
    # start of the transition
    if trackItem.inTransition():
      srcEntry = srcExit
      syncEntry = transitionStart

    editName = self._parent.trackItemEditName(trackItem)
    
    mode = ModeField(False, True, [])
    effect = EffectField(EffectField.CUT, 0)
    clipEdit = EditDecision(self._eventIndex, editName, mode, effect, srcEntry, srcExit, syncEntry, transitionStart)

    effect = EffectField(EffectField.DISSOLVE, transitionDuration)
    transitionSrcStart = TimeCode.createFromFrames(0, self._fps, self._dropFrame)
    transitionSrcEnd = TimeCode.createFromFrames(transitionDuration, self._fps, self._dropFrame)
    transitionEdit = EditDecision(self._eventIndex, "BL", mode, effect, transitionSrcStart, transitionSrcEnd, transitionStart, syncExit)
    #toEdit.addElement( NamedElement("* EFFECT NAME:", "FADE IN FADE OUT DISSOLVE") )
    # If the fromClip text resolves to something, add it as a 'from clip' element.
    fromClip = self._parent.resolveFromTrackItem(trackItem, 'fromClip')
    if fromClip:
      transitionEdit.addElement(NamedElement("* FROM CLIP NAME:", fromClip))
    
    edits.append( clipEdit )
    edits.append(transitionEdit)

    self._edits.append( edits )
    
    log.debug( "EDLExportTask.createFadeOut generated:" )
    log.debug( str(edits) + '\n' )

  def createTransitionTo(self, trackItem, nextTrackItem):
    outTransition = trackItem.outTransition()
    edits = CompoundEditDecision()
    
    srcEntry, srcExit, syncEntry, syncExit = self.trackItemTimes(trackItem)
    transitionDuration = outTransition.timelineOut() - outTransition.timelineIn() + 1
    transitionOffset = transitionDuration / 2
    transitionStart = syncExit.addFrames(-transitionOffset, self._fps)
    srcExit = srcExit.addFrames(-transitionOffset, self._fps)
    syncExit = transitionStart
    
    # If the track item has an in transition, we should have a 0-length clip at the
    # start of the transition
    if trackItem.inTransition():
      srcEntry = srcExit
      syncEntry = transitionStart
    
    mode = ModeField(False, True, [])
    effect = EffectField(EffectField.CUT, 0)
    fromEdit = EditDecision(self._eventIndex, self._parent.trackItemEditName(trackItem), mode, effect, srcEntry, srcExit, syncEntry, syncExit)
    edits.append( fromEdit )

    toSrcEntry, toSrcExit, toSyncEntry, toSyncExit = self.trackItemTimes(nextTrackItem)
    toSrcEntry = toSrcEntry.addFrames(-transitionOffset, self._fps)
    toSyncEntry = transitionStart

    # If the next track has an out transition, end the clip at the start of that transition
    nextOutTransition = nextTrackItem.outTransition()
    if nextOutTransition:
      offset = (nextOutTransition.timelineOut() - nextOutTransition.timelineIn() + 1)
      if nextOutTransition.alignment() == Transition.kDissolve:
        offset = offset / 2
      toSrcExit = toSrcExit.addFrames(-offset, self._fps)
      toSyncExit = toSyncExit.addFrames(-offset, self._fps)

    effect = EffectField(EffectField.DISSOLVE, transitionDuration)
    toEdit = EditDecision(self._eventIndex, self._parent.trackItemEditName(nextTrackItem), mode, effect, toSrcEntry, toSrcExit, toSyncEntry, toSyncExit)

    #toEdit.addElement( NamedElement("* EFFECT NAME:", "CROSS DISSOLVE") )

    # If the fromClip text resolves to something, add it as a 'from clip' element.
    fromClip = self._parent.resolveFromTrackItem(trackItem, 'fromClip')
    if fromClip:
      toEdit.addElement( NamedElement("* FROM CLIP NAME:", fromClip))

    # If the fromClip text resolves to something for the next TrackItem, add that as the 'to clip' element.
    fromClip = self._parent.resolveFromTrackItem(nextTrackItem, 'fromClip')
    if fromClip:
      toEdit.addElement( NamedElement("* TO CLIP NAME:", fromClip))

    edits.append(toEdit)

    self._edits.append(edits)

  def trackItemTimes(self, trackItem):
    sourceIn = trackItem.sourceIn()
    sourceOut = trackItem.sourceOut()

    #Include source start time for clips
    if isinstance(trackItem.source(), hiero.core.Clip):
      clip = trackItem.source()
      sourceIn += clip.timecodeStart()
      sourceOut += clip.timecodeStart()

    timecodeStart = self._parent._sequence.timecodeStart()

    # TODO: Is the src framerate the same as the dst framerate?
    # Note EDLs use traditional tape-style outpoints of the frame where the video is completely out
    # not NLE style outpoints that are the last used frame, so we need to add 1 to the outpoint.
     # Note by Anton: using +1 is not corrects for source times when under a retime. Use durations instead.  
    srcEntry = TimeCode.createFromFrames(sourceIn, self._fps, self._dropFrame)
    srcExit = TimeCode.createFromFrames(sourceIn + trackItem.sourceDuration(), self._fps, self._dropFrame)
    syncEntry = TimeCode.createFromFrames(timecodeStart + trackItem.timelineIn(), self._fps, self._dropFrame)
    syncExit = TimeCode.createFromFrames(timecodeStart + trackItem.timelineIn() + trackItem.duration(), self._fps, self._dropFrame)
    return (srcEntry, srcExit, syncEntry, syncExit)

  def taskStep(self):
    if len(self._trackItems) == 0:
      return False
    trackItem = self._trackItems[self._trackItemIndex]

    inTransition = trackItem.inTransition()
    outTransition = trackItem.outTransition()

    log.debug( "EDLExportTask.taskStep: " + str(trackItem) + " in transition: " + str(inTransition) + " out transition: " + str(outTransition) )
    if (not inTransition) and (not outTransition):
      self.createCut(trackItem)
    else:
      if inTransition:
        if inTransition.alignment() is Transition.kFadeIn:
          self.createFadeIn(trackItem)
      if outTransition:
        if outTransition.alignment() is Transition.kFadeOut:
          self.createFadeOut(trackItem)
        else:
          nextTrackItem = self._trackItems[self._trackItemIndex+1]
          self.createTransitionTo(trackItem, nextTrackItem)

    self._eventIndex += 1
    self._trackItemIndex += 1
    
    return self._trackItemIndex < len(self._trackItems)

class EDLFileWriter:
  def __init__(self, parent):
    self._parent = parent

    self._edits = []

  def addEdits(self, edits):
    self._edits += edits

  def write(self, filePath):

    edlString = "TITLE: " + os.path.splitext(os.path.basename(filePath))[0] + CRLF
    # For now, always create non-drop frame edl files
    # TODO: Query timeline is drop frame
    edlString += "FCM: NON-DROP FRAME" + CRLF + CRLF

    # Sort our edits by sequence in time
    edits = sorted(self._edits, key=lambda edit: str(edit.syncEntry()))

    eventIndex = 1
    for edit in edits:
      edit.setEditId(eventIndex)
      edlString += str(edit) + CRLF
      eventIndex += 1

    try:
      # check export root exists
      dir = os.path.dirname(filePath)
      util.filesystem.makeDirs(dir)
      file = util.filesystem.openFile(filePath, 'w')
      file.write(edlString)
      file.close()
    except IOError:
      log.error( "EDLFileWriter.write failed %s" % exportPath )
      raise


# Some helpers for the per-shot token resolution.
def _filenameFromTrackItem(trackItem, absPath):
  filename = mediaSourceExportReadPath(trackItem.source().mediaSource(), False)
  if not absPath:
    filename = os.path.basename(filename)
  return filename


def _filebaseFromTrackItem(trackItem):
  filename = _filenameFromTrackItem(trackItem, False)
  filebase, fileext = os.path.splitext(filename)
  return filebase


def _fileheadFromTrackItem(trackItem):
  source = trackItem.source().mediaSource()
  return mediaSourceExportFileHead(source)


def _fileextFromTrackItem(trackItem):
  filename = _filenameFromTrackItem(trackItem, False)
  filebase, fileext = os.path.splitext(filename)
  return fileext


class EDLExportTask(hiero.core.TaskBase):
  
  def __init__(self, initDict):
    """Initialize"""
    self._currentTrack = None
    hiero.core.TaskBase.__init__(self, initDict)
    self._fps = self._sequence.framerate().toInt()
    self._trackTasks = []
    self._trackTaskIndex = 0
    self._audioTask = None

    self._stepTotal = 0
    self._stepCount = 0

  def currentTrackName(self):
    if self._currentTrack:
      return self._currentTrack.name()
    else:
      return self._sequence.videoTracks()[0].name()
    
  def resolveFromTrackItem(self, trackItem, presetName):
    resolvedString = None
    propertyString = self._preset.properties()[presetName]
    resolver = EDLExportTask.ShotResolveTable(trackItem, self._preset.properties()["abspath"])
    try:
      resolvedString = resolver.resolve(propertyString)
    except Exception as e:
      error = "EDLExportTask failed to resolve '{0}' value: '{1}'\n".format(presetName, propertyString)
      error = error + "\nValid tokens are: " + str(resolver.entries()) + "\n"
      error = error + str(e)
      log.error( error )
      self.setError( error )
      raise
    return resolvedString

  def trackItemEditName(self, trackItem):
    # If the user set the reelname to something in the export setup, then it will come back resolved.
    # If not, it will be blank so we use the reel name from the clip. The option's default is an
    # empty string so unless they explicitly specify otherwise, we use the clip reel name.
    # If both of those are empty, we fall back on the track item name.
    editName = self.resolveFromTrackItem(trackItem, 'reelName')
    if not editName:
      clip = trackItem.source()
      if clip:
        source = clip.mediaSource()
        if source and hiero.core.Keys.kSourceReelId in source.metadata():
          editName = source.metadata()[hiero.core.Keys.kSourceReelId]
    if not editName:
      editName = trackItem.name()
    editName = re.sub(r'[\W_]+', '', editName) # make it legal
    if self._preset.properties()["truncate"]:
      editName = editName[:8]
    return editName

  def startTask (self):
    try:
      if self._preset.supportsAudio():
        audioTracks = []
        for track in self._sequence.audioTracks():
          audioTracks.append( track )
        self._audioTask = EDLExportAudioTrackTask(self, audioTracks)
        while self._audioTask.taskStep():
          pass

      # Build list of items from sequence to be added added to the EDL
      for track in self._sequence.videoTracks():
        trackItems = []
        for trackitem in track:
          trackItems.append(trackitem)
          self._stepTotal += 1

        # We shouldn't get passed any empty tracks but if we do, don't create a task for them
        if trackItems:
          task = EDLExportTrackTask(self, track, trackItems)
          self._trackTasks.append( task )
    except Exception as e:
      self.setError( str(e) )
      log.exception(e)

  def exportFilePath(self):
    exportPath = self.resolvedExportPath()
    # Check file extension
    if not exportPath.lower().endswith(".edl"):
      exportPath += ".edl"
    return exportPath

  def taskStep(self):
    try:
      trackTask = self._trackTasks[self._trackTaskIndex]
      self._currentTrack = trackTask._track
      
      if not trackTask.taskStep():
        path = self.exportFilePath()

        fileWriter = EDLFileWriter(self)
        fileWriter.addEdits( trackTask.edits() )

        if self._audioTask:
          fileWriter.addEdits( self._audioTask.edits() )
          self._audioTask = None

        fileWriter.write( path )
        self._trackTaskIndex += 1

      self._stepCount += 1
      return self._stepCount < self._stepTotal
    except Exception as e:
      self.setError( str(e) )
      log.exception(e)
      return False
  
  def finishTask(self):
    hiero.core.TaskBase.finishTask(self)

  def progress(self):
    if self._stepTotal == 0:
      return 0.0
    else:
      return float(self._stepCount / self._stepTotal)

  # Keyword resolver for tokens relevant to shots.
  # This is a bit of a hack, using the genericness of the ResolveTable to eval using functions on TrackItems.
  # Keep this in the EDLExportTask for now but it might be good to move to FnResolveTable for general use.
  # This abspath option should go away and we should have a token for the filename with full path vs. without
  # but keeping it for now for backwards compatibility with pre-existing EDLExportTask presets.
  class ShotResolveTable(FnResolveTable.ResolveTable):
    def __init__(self, trackItem, absPath):
      FnResolveTable.ResolveTable.__init__(self)
      self._trackItem = trackItem
      
      # Some shots may not have a Clip, so just return None to let the resolver base handle it as it does with any other.
      # If this list is changed, be sure to update the text for the tooltips on fromClip and reelName QLineEdit widgets in FnEDLExportUI.py.
      self.addResolver( "{shot}", "Name of the TrackItem being processed", lambda keyword, trackItem: trackItem.name() )
      self.addResolver( "{clip}", "Name of the source Media clip being processed", lambda keyword, trackItem: trackItem.source().name() if trackItem.source() else None )
      self.addResolver( "{track}", "Name of the track being processed", lambda keyword, trackItem: trackItem.parent().name() if trackItem.parent() else None )
      self.addResolver( "{sequence}", "Name of the Sequence being processed", lambda keyword, trackItem: trackItem.parent().parent().name() if trackItem.parent().parent() else None )
      self.addResolver( "{event}", "Event Number of the shot being processed", lambda keyword, trackItem: str(trackItem.eventNumber()) )
      self.addResolver( "{fps}", "Frame rate of the Sequence", lambda keyword, trackItem: str(trackItem.parent().parent().framerate()) if trackItem.parent().parent() else None )
      self.addResolver( "{filename}", "File name part of the TrackItem's Source file.", lambda keyword, trackItem: _filenameFromTrackItem(trackItem, absPath) )
      self.addResolver( kFileBaseKeyword, KeywordTooltips[kFileBaseKeyword], lambda keyword, trackItem: _filebaseFromTrackItem(trackItem) )
      self.addResolver( "{fileext}", "File name extension of the TrackItem's Source file.", lambda keyword, trackItem: _fileextFromTrackItem(trackItem) )
      self.addResolver( kFileHeadKeyword, KeywordTooltips[kFileHeadKeyword], lambda keyword, trackItem: _fileheadFromTrackItem(trackItem) )
      
    def resolve(self, value):
      return FnResolveTable.ResolveTable.resolve(self, self._trackItem, value)
  
  

class EDLExportPreset(hiero.core.TaskPresetBase):
  def __init__(self, name, properties):
    """Initialise presets to default values"""
    hiero.core.TaskPresetBase.__init__(self, EDLExportTask, name)
    
    # Set any preset defaults here
    self.properties()["abspath"] = False
    self.properties()["truncate"] = False
    self.properties()["fromClip"] = "{filename}"
    self.properties()["reelName"] = ""
    
    # Update preset with loaded data
    self.properties().update(properties)

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kSequence
    
  def addCustomResolveEntries(self, resolver):
    resolver.addResolver("{ext}", "Extension of the file to be output", lambda keyword, task: "edl")
    resolver.addResolver("{track}", "Name of the track being processed", lambda keyword, task: task.currentTrackName())

  def supportsAudio(self):
    return True

    
log.debug( "Registering EDLExportTask" )
hiero.core.taskRegistry.registerTask(EDLExportPreset, EDLExportTask)

  
