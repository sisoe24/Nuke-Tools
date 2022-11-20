import os.path
import hiero.core
import hiero.core.log
import hiero.core.util
import hiero.core.VersionScanner
import hiero.ui
import glob
import re
import math
import collections
import functools
from PySide2 import (QtCore, QtGui, QtWidgets)
import foundry.ui

class TrackFinderByNameWithDialog(object):
  """ Find or create tracks to build on based on the track name.  Also checks for collisions and shows a dialog
      if there are any so the user can choose what to do. """

  def __init__(self, trackBuilder):
     # Reference back the track builder, for access to the getTimelineRange method
    self.trackBuilder = trackBuilder


  def findOrCreateTrackByName(self, sequence, trackName):
    """ Searches the sequence for a track with the given name.  If none are found,
        creates a new one. """
    #a track always has to have a name
    if not trackName or not sequence:
      raise RuntimeError("Invalid arguments")

    track = None
    isNewTrack = False
    # Look for existing track
    for existingtrack in sequence.videoTracks():
      if existingtrack.trackName() == trackName:
        # hiero.core.log.debug( "Track Already Exists  : " + trackName )
        track = existingtrack

    # No existing track. Create new video track
    if track is None:
      # hiero.core.log.debug( "Track Created : " + trackName )
      track = hiero.core.VideoTrack(str(trackName))
      sequence.addTrack(track)
      track.addTag(hiero.core.Tag(trackName, "icons:NukeVFX.png"))
      isNewTrack = True
    return track, isNewTrack


  def checkTrackItemCollisionsShowDialog(self, selection, track):
    """ Check for collisions with items on the destination track.  If there are any, shows a TrackItemCollisionDialog. """
    srcCollisions = []
    dstCollisions = set()

    for item in selection:
      if isinstance(item, hiero.core.TrackItem):
        collidedItems = set()
        collidedTransitions = set() # Should we be doing something with transitions?

        timelineIn, timelineOut = self.trackBuilder.getTimelineRange(item)

        BuildTrack.CheckForTrackItemCollisions(timelineIn, timelineOut, track, False, collidedItems, collidedTransitions)
        if len(collidedItems) > 0:
          dstCollisions.update( collidedItems )
          srcCollisions.append( item )

    if len(srcCollisions) > 0:
      sequence = track.parent()
      uniqueTrackName = track.name()
      if sequence:
        trackNames = [t.name() for t in sequence.videoTracks() + sequence.audioTracks()]
        uniqueTrackName = hiero.core.util.uniqueKey(track.name(), trackNames)

      dialog = TrackItemCollisionDialog(len(srcCollisions), track, uniqueTrackName)

      if dialog.exec_():
        selectedAction = dialog.selectedAction()

        if selectedAction is TrackItemCollisionDialog.kMakeNewTrack :
          #Return empty selection and new track name
          newTrackName = str(dialog._newTrackName.text())
          if len(newTrackName) == 0 :
            newTrackName = "Untitled"
          return None, newTrackName

        elif selectedAction is TrackItemCollisionDialog.kDeleteDestCollisions:
          # Remove colliding track items from the destination track
          for item in dstCollisions:
            # If the clip for the deleted item is offline, and not just a media source, then delete it.
            if not item.isMediaPresent() and hasattr(item.source(), "binItem"):
              binItem = item.source().binItem()
              if binItem and binItem.parentBin():
                binItem.parentBin().removeItem(binItem)

            track.removeItem(item)
          return selection, track


        else:
          # Refresh colliding track items
          if selectedAction is TrackItemCollisionDialog.kRefreshDestCollisions:
            for item in dstCollisions:
              BuildTrackActionBase.updateVersions(item)

          # Remove selected track items which collide with ones on the destination track.


          return [ item for item in selection if not item in srcCollisions ], track
      else:
        # User cancelled
        return [], None
    else:
      return selection, track


  def findTrack(self, name, selection, sequence):
    """ Find or create a track to build on for the given selection, and with name. """
    track = None
    trackName = name
    readyToBuild = 0
    while readyToBuild == 0 :
      #Get the destination track
      track, isNewTrack = self.findOrCreateTrackByName(sequence, trackName)

      if not isNewTrack :

        #Look for collisions
        newSelection, returnedTrack = self.checkTrackItemCollisionsShowDialog(selection, track)

        #Check if the user cancelled
        if returnedTrack == None:
          return False

        #If user choose to deal with collisions then we do build
        if newSelection != None :
          selection = newSelection
          track = returnedTrack
          readyToBuild = 1

        #Else user wants to make a new track
        else :
          trackName = returnedTrack
          readyToBuild = 0

      else :
        readyToBuild = 1
    return track, selection



class TrackFinderByTag(object):
  """ Find or create tracks to build based on a tag name.  Searches for tracks above the selected items
      which have the expected tag and have no colliding items, otherwise creates a new one. """

  def __init__(self, trackBuilder):
    # Reference back the track builder, for access to the getTimelineRange method
    self.trackBuilder = trackBuilder


  @staticmethod
  def FindOrCreateTrackFromIndex(startIndex, sequence, tagName):
    ''' Finds the next track in sequence above startIndex which has the tag tagName.
        If no track exists, one will be created.
        Returns the track, whether the track is new and the index of te track. '''
    numVideoTracks = sequence.numVideoTracks()
    track = None
    currentTrackIndex = startIndex # Initialise in case the range is invalid.
    for currentTrackIndex in range(startIndex, numVideoTracks):
      if track is None:
        currentTrack = sequence.videoTrack(currentTrackIndex)
        # Check each track for the correct tag
        for tag in currentTrack.tags():
          if tag.name() == tagName:
            track = currentTrack
            break
      else:
        break

    isNewTrack = False
    if track is None:
      # create new track
      numberTaggedTracks = TrackFinderByTag.NumberTaggedTracks(sequence, tagName)
      track = hiero.core.VideoTrack(str('{0} {1}'.format(tagName, numberTaggedTracks + 1 )))
      track.addTag(hiero.core.Tag(tagName, "icons:NukeVFX.png", False))
      sequence.addTrack(track)
      isNewTrack = True

    return track, isNewTrack, currentTrackIndex


  @staticmethod
  def NumberTaggedTracks(sequence, tagName):
    ''' Find the nuber of Tracks with the tag tagName '''
    numVideoTracks = sequence.numVideoTracks()
    numTaggedTracks = 0
    for currentTrackIndex in range(numVideoTracks):
      currentTrack = sequence.videoTrack(currentTrackIndex)
      # Check each track for the correct tag
      for tag in currentTrack.tags():
        if tag.name() == tagName:
          numTaggedTracks = numTaggedTracks + 1
    return numTaggedTracks


  @staticmethod
  def GetTopmostSelectedItem(selection):
    ''' find the index fo the topmost seleted track '''
    topmostSelectedTrackIndex = -1;
    for originalTrackItem in selection:
      if isinstance(originalTrackItem, hiero.core.TrackItem):
        parentTrack = originalTrackItem.parentTrack()
        trackIndex = parentTrack.trackIndex()
        if trackIndex > topmostSelectedTrackIndex:
          topmostSelectedTrackIndex = trackIndex
    return topmostSelectedTrackIndex


  def checkTrackItemCollisions(self, selection, track):
    """ Check for selected track items which collide with those on the destination track.
        Returns true if there were collisions, else returns false. """
    srcCollisions = []

    for item in selection:
      if isinstance(item, hiero.core.TrackItem):
        collidedItems = set()
        collidedTransitions = set() # Should we be doing something with transitions?

        timelineIn, timelineOut = self.trackBuilder.getTimelineRange(item)

        BuildTrack.CheckForTrackItemCollisions(timelineIn, timelineOut, track, False, collidedItems, collidedTransitions)
        if len(collidedItems) > 0:
          srcCollisions.append( item )

    return len(srcCollisions) > 0


  def findTrack(self, name, selection, sequence):
    """ Find or create a track to build on for the given selection, and with tag matching name. """
    # We always want to add the new track above the current selection
    topmostSelecetdItem = TrackFinderByTag.GetTopmostSelectedItem(selection)
    startItem = topmostSelecetdItem
    track = None
    readyToBuild = 0
    while readyToBuild == 0 :
      track, isNewTrack, lastCheckedTrackIndex = TrackFinderByTag.FindOrCreateTrackFromIndex(startItem, sequence, name)
      if not isNewTrack and self.checkTrackItemCollisions(selection, track):
        # Track has a collision, keep searching from the next index
        startItem = lastCheckedTrackIndex + 1
      else:
        # We have a valid track!
        readyToBuild = 1
    return track, selection




class BuildTrack(QtWidgets.QMenu):

  def __init__(self):
    QtWidgets.QMenu.__init__(self, "Build Track", None)

    hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.eventHandler)

    self._actionStructure = BuildExternalMediaTrackAction()
    self._actionTag = BuildTrackFromExportTagAction()

    self.addAction(self._actionStructure)
    self.addAction(self._actionTag)

  def eventHandler(self, event):
    # Check if this actions are not to be enabled
    restricted = []
    if hasattr(event, 'restricted'):
      restricted = getattr(event, 'restricted');
    if "buildExternalMediaTrack" in restricted:
      return

    if not hasattr(event.sender, 'selection'):
      # Something has gone wrong, we shouldn't only be here if raised
      # by the timeline view which will give a selection.
      return

    selection = event.sender.selection()

    # We don't need this action if a user has right-clicked on a Track header
    trackSelection = [item for item in selection if isinstance(item, (hiero.core.VideoTrack,hiero.core.AudioTrack))]
    if len(trackSelection)>0:
      return

    #filter out the Audio Tracks
    selection = [ item for item in selection if isinstance(item.parent(), hiero.core.VideoTrack) ]

    if selection is None:
      selection = () # We disable on empty selection.
    self.setEnabled(len(selection)>0)

    # Disable Build Track From Export Tag action if there are no tags
    tags = []
    for item in selection:
      if hasattr(item, 'tags'):
        for tag in item.tags():
          tags.append(tag)

    self._actionTag.setEnabled(len(tags) > 0)

    event.menu.addMenu(self)


  @staticmethod
  def ProjectTrackNameDefault(selection):
    project = None
    # Find parent project
    for item in selection:
      if hasattr(item, "project"):
        project = item.project()
        break

    if project:
      return project.buildTrackName()

  @staticmethod
  def FindOrCreateBin(project, binName):
    # If the bin does not exist within the project, create it
    for bin in project.bins():
      if binName == bin.name():
        return bin
    bin = hiero.core.Bin(binName)
    project.clipsBin().addItem(bin)
    return bin

  @staticmethod
  def FindOrCreateClip(mediaSource, destBin, project):
    ''' Try to find an existing Clip which uses mediaSource.  If not found, creates a new clip and adds it to destBin.
        Returns the found or created clip. '''
    for clip in project.clips():
      if clip.mediaSource() == mediaSource:
        return clip
    clip = hiero.core.Clip( mediaSource )
    destBin.addItem( hiero.core.BinItem(clip) )
    return clip

  @staticmethod
  def CheckForTrackItemCollisions(timelineIn, timelineOut, track, isNewTrack, collidedItems, collidedTransitions):

    # Check for collisions
    if not isNewTrack:
      # Check trackitems, remove any items overlapping with originalTrackItem
      trackItems = list(track.items())
      for item in trackItems:
        if timelineOut < item.timelineIn():
          break
        elif timelineIn > item.timelineOut():
          continue
        else:
          collidedItems.add(item)
      # Check transitions, remove only items completely hidden by originalTrackItem
      transitions = track.transitions()
      for item in transitions:
        if timelineOut < item.timelineIn():
          break
        elif timelineIn <= item.timelineIn() and item.timelineOut() <= timelineOut:
          collidedTransitions.add(item)

  @staticmethod
  def CheckForTransitionCollisions(originalTrackItem, track, collidedTransitions):
    # Check for collisions
    transitions = track.transitions()
    for item in transitions:
      if originalTrackItem.timelineOut() < item.timelineIn():
        break
      elif originalTrackItem.timelineIn() > item.timelineOut():
        continue
      else:
        # track.removeTransition(item)
        collidedTransitions.add(item)


  @staticmethod
  def CopyTimingFrom( toTrackItem, fromTrackItem, expectedHandles=None ):
    """ Copy timing information between track items.  If expectedHandles are given, tries to use them to
        set the source in/out of the track item, otherwise calculates handles based on the frame range of
        toTrackItem's media source.

        Note that this function does not deal well with cases where the expected handles are incorrect, or there are retimes involved.
        BuildTrackFromExportTagAction no longer uses it.
        """
    if isinstance(toTrackItem, hiero.core.TrackItem) and isinstance(fromTrackItem, hiero.core.TrackItem):
      
      toTrackItem.setTimelineIn( fromTrackItem.timelineIn() )
      toTrackItem.setTimelineOut( fromTrackItem.timelineOut() )

      toClip = toTrackItem.source()
      fromClip = fromTrackItem.source()
      toSource = toClip.mediaSource()
      fromSource = fromClip.mediaSource()


      # Debug printing
      hiero.core.log.debug( "TrackItem Duration A:%i, B:%i" % (toTrackItem.duration(), fromTrackItem.duration()) )
      hiero.core.log.debug( "Clip Duration A:%i, B:%i" % (toClip.duration(), fromClip.duration()) )
      hiero.core.log.debug( "Source Duration A:%i, B:%i" % (toSource.duration(), fromSource.duration()) )

      if toSource.duration() == fromSource.duration():
        # If source durations match, then the whole clip was exported
        # hiero.core.log.debug( "source durations match, then the whole clip was exported" )
        # Copy Source Times
        toTrackItem.setSourceIn( fromTrackItem.sourceIn() )
        toTrackItem.setSourceOut( fromTrackItem.sourceOut() )
      elif toSource.duration() == fromTrackItem.duration():
        # If cut durations match, then the cut was exported
        # hiero.core.log.debug( "cut durations match, then the cut was exported" )
        toTrackItem.setSourceIn( 0 )
        toTrackItem.setSourceOut( fromTrackItem.duration() - 1 )
      else:
        # Otherwise, cut was exported with handles
        # hiero.core.log.debug( "cut was exported with handles" )
        # TODO: Use timecode if possible to set handles properly
        # Total frames assigned for handles

        # If expected handles are given, use them, otherwise try to determine them
        if expectedHandles:
          inHandle, outHandle = expectedHandles
        else:
          # Get the available handles in the to item's media source
          handles = (toSource.duration() - toTrackItem.duration())

          # Check for transitions, to allow handles for their length
          inTransLength, outTransLength = BuildTrack.CalcTransitionExtraLengths(fromTrackItem)

          if inTransLength + outTransLength == handles:
            # Transitions length match the exported handles
            inHandle = inTransLength
            outHandle = outTransLength
          elif inTransLength + outTransLength < handles:
            # Transitions length does not match exported handles, but we have enough frames for them
            remainder = handles - (inTransLength + outTransLength);
            inHandle = inTransLength + int(math.floor(remainder * 0.5))
            outHandle = handles - inHandle
          else:
            # No transitions or transitions length does not match exported handles, and we do not have enough frames for them
            # Divide the available handles on each side
            inHandle = int(math.floor(handles * 0.5))
            outHandle = handles - inHandle

        toTrackItem.setSourceIn( inHandle )
        toTrackItem.setSourceOut( (toSource.duration() - 1) - outHandle )


  @staticmethod
  def CalcTransitionExtraLengths(trackItem):
    inTransition = trackItem.inTransition()
    outTransition = trackItem.outTransition()

    # For a dissolve, the trackitem needs extra handles depending on the position of the transition.
    # For a fade in/out, the trackitem needs no handles.
    # Empty transitions (NULL) have alignment Unknown.
    if inTransition:
      if inTransition.alignment() == hiero.core.Transition.Alignments.kDissolve:
        inLength = trackItem.timelineIn() - inTransition.timelineIn()
      elif inTransition.alignment() in [hiero.core.Transition.Alignments.kFadeIn, hiero.core.Transition.Alignments.kFadeOut]:
        inLength = 0
      elif inTransition.alignment() == hiero.core.Transition.Alignments.kUnknown:
        inLength = 0
    else:
      # TODO raise error/exception here?
      inLength = 0

    if outTransition:
      if outTransition.alignment() == hiero.core.Transition.Alignments.kDissolve:
        outLength = outTransition.timelineOut() - trackItem.timelineOut()
      elif outTransition.alignment() in [hiero.core.Transition.Alignments.kFadeIn, hiero.core.Transition.Alignments.kFadeOut]:
        outLength = 0
      elif outTransition.alignment() == hiero.core.Transition.Alignments.kUnknown:
        outLength = 0
    else:
      # TODO raise error/exception here?
      outLength = 0

    return (inLength, outLength)


  @staticmethod
  def SetTrackItemReformatState(originalTrackItem, trackItem):
    """ Set the reformat state of the created track item based on that of the
    original so they look the same on the timeline.
    """
    # Copy all the relevant properties from the original
    originalReformatState = originalTrackItem.reformatState()
    reformatState = trackItem.reformatState()
    reformatState.setType(originalReformatState.type())
    reformatState.setResizeType(originalReformatState.resizeType())
    reformatState.setResizeCenter(originalReformatState.resizeCenter())


  @staticmethod
  def GetTagIdentifier(tag):
    """ Get an identifier for the tag.  Just tag.name() is not reliable, since
        tasks which are part of the same export can have the same name.  Combine it
        with the output path, if that is present in the tag metadata. """
    metadata = tag.metadata()
    if metadata.hasKey("pathtemplate"):
      return tag.name() + " " + metadata.value("pathtemplate")
    else:
      return tag.name()



class TrackItemCollisionDialog(QtWidgets.QDialog):
  kMakeNewTrack = 0
  kDeleteDestCollisions = 1
  kRefreshDestCollisions = 2
  kSkipSrcCollisions = 3

  def __init__(self, numCollisions, track, uniqueTrackName, labelText=None, parent=None, enableDeleteButton=True, enableRefreshButton=True):
    if not parent:
      parent = hiero.ui.mainWindow()
    super(TrackItemCollisionDialog, self).__init__(parent)

    self.setWindowTitle("Build Track")
    layout = QtWidgets.QVBoxLayout()
    self.setLayout(layout)

    if not labelText:
      labelText = "The track '%s' already exists.  What would you like to do?\n" % (track.name())

    label = QtWidgets.QLabel(labelText)
    layout.addWidget(label)

    self._newTrackButton = QtWidgets.QRadioButton("Choose a different destination track.")
    self._newTrackButton.setChecked(True)
    self._newTrackButton.toggled.connect(self.optionChanged)
    layout.addWidget( self._newTrackButton )

    self._newTrackNameLayout = QtWidgets.QHBoxLayout()
    self._newTrackLabel = QtWidgets.QLabel("Track Name :")
    self._newTrackName = QtWidgets.QLineEdit()
    self._newTrackName.setText(uniqueTrackName)
    self._newTrackNameLayout.addWidget(self._newTrackLabel)
    self._newTrackNameLayout.addWidget(self._newTrackName)
    layout.addLayout( self._newTrackNameLayout )

    if enableDeleteButton:
      self._deleteButton = QtWidgets.QRadioButton("Overwrite the %s colliding items found on the track." % numCollisions)
      self._deleteButton.toggled.connect(self.optionChanged)
      layout.addWidget( self._deleteButton )
    else:
      self._deleteButton = None

    if enableRefreshButton:
      self._findVersionsButton = QtWidgets.QRadioButton("Refresh the %s colliding items' source clips." % numCollisions)
      self._findVersionsButton.toggled.connect(self.optionChanged)
      layout.addWidget( self._findVersionsButton )
    else:
      self._findVersionsButton = None

    self._skipButton = QtWidgets.QRadioButton("Skip the %s colliding items." % numCollisions)
    self._skipButton.toggled.connect(self.optionChanged)
    layout.addWidget( self._skipButton )

    buttonBox = QtWidgets.QDialogButtonBox( QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel )
    buttonBox.accepted.connect( self.accept )
    buttonBox.rejected.connect( self.reject )
    layout.addWidget( buttonBox )

  def optionChanged(self) :
    if self._newTrackButton.isChecked() :
      self._newTrackName.setEnabled(True)
      self._newTrackLabel.setEnabled(True)
    else :
      self._newTrackName.setEnabled(False)
      self._newTrackLabel.setEnabled(False)

  def selectedAction(self):
    if self._newTrackButton.isChecked():
      return TrackItemCollisionDialog.kMakeNewTrack
    elif self._deleteButton and self._deleteButton.isChecked():
      return TrackItemCollisionDialog.kDeleteDestCollisions
    elif self._findVersionsButton and self._findVersionsButton.isChecked():
      return TrackItemCollisionDialog.kRefreshDestCollisions
    else:
      return TrackItemCollisionDialog.kSkipSrcCollisions

class BuildTrackActionBase(QtWidgets.QAction):
  def __init__(self, name):
    QtWidgets.QAction.__init__(self, name, None)

    self.trackFinder = TrackFinderByNameWithDialog(self)

    # Qt seems to barf connecting this signal occasionally
    # I suspect it's because doit can be overridden in sub classes and the function isn't fully defined or something
    # by the time this constructor is called. So to work around it, I just connect the signal to this local function that calls
    # into the derived function
    def localDoit():
      self.doit()
    self.triggered.connect(localDoit)

    self._processorPreset = None
    self._errors = []
    self._useMaxVersions = True # Auto-scan to max version of imported/existing clips.

  def configure(self, project, selection):
    return False

  def trackName(self):
    return ''

  @staticmethod
  def updateVersions(trackItem):
    """ Scan for versions on a track item and change to the highest available """
    trackItem.source().rescan() # First rescan the current clip
    if trackItem.isMediaPresent():
      version = trackItem.currentVersion()
      scanner = hiero.core.VersionScanner.VersionScanner() # Scan for new versions
      scanner.doScan(version)
      # Put the track item and the clip bin item on the max version
      trackItem.maxVersion()
      trackItem.source().binItem().maxVersion()



  def trackItemAdded(self, newTrackItem, track, originalTrackItem):
    """ Method called when a new TrackItem is called while building a track.  The default implementation
        does nothing but can be implemented by sub-classes which need to customize the behavior. """
    pass


  def buildShotFromFiles(self, files, name, sequence, track, bin, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle, expectedEndHandle, expectedOffset):
    if files:
      clip = None

      # Try to find an existing clip in the bin so we don't end up with duplicates
      normPathFiles = [os.path.abspath(file) for file in files]
      for existingClip in bin.clips():
        existingSource = existingClip.activeItem().mediaSource()
        if os.path.abspath(existingSource.firstpath()) in normPathFiles:
          if self._useMaxVersions:
            scanner = hiero.core.VersionScanner.VersionScanner()
            scanner.doScan( existingClip.activeVersion() )
            existingClip.maxVersion()

          clip = existingClip.activeItem()
          clip.rescan()
          break

      # Create a new clip and add it to the bin
      if not clip:
        # Select the last file in the list so we (hopefully) get the highest version.  What we would like to do at this point
        # is scan for new versions, but this isn't possible due to issues with the undo system.
        file = hiero.core.util.SequenceifyFilename(files[-1], False)

        # If it is a sequence, add the frame range specified, but not if we're building from an external render, when the range is unknown.
        # Due to a quirk in the way MediaSources are handled, this can end up with the MediaSource having a logical frame range which is the union
        # of the range actually on disk and the one specified here.  See Bug 45955.
        if file != files[-1] and not self.buildingFromExternalRender():
          file = file + ' ' + str(expectedStartTime) + '-' + str(expectedStartTime+expectedDuration-1)

        # Replace version wildcard with version information from preset
        if self._processorPreset:
          versionIndex, versionPadding = self._processorPreset.properties()["versionIndex"], self._processorPreset.properties()["versionPadding"]
          file = file.replace("v*", "v%s" % format(versionIndex, "0%id" % int(versionPadding)))

        
        # Movie files are indexed from zero so ignore expected start time 
        if hiero.core.isVideoFileExtension(os.path.splitext(file)[1].lower()):
          expectedStartTime = 0
          
        # If the media is offline, try to create a media source with the correct properties.  Depending on the file format,
        # start time and timecode might not be correct, but it should be updated when the clip is refreshed.
        oldSource = originalTrackItem.source().mediaSource()
        startTimecode = oldSource.timecodeStart() + expectedStartTime - oldSource.startTime()
          
        try:
          expectedFormat = self.getExpectedFormat(originalTrackItem)

          newSource = hiero.core.MediaSource.createOfflineVideoMediaSource( file, expectedStartTime, expectedDuration, sequence.framerate(), startTimecode )
          clip = BuildTrack.FindOrCreateClip( newSource, bin, sequence.project() )

          if not newSource.isMediaPresent():
            clip.setFormat(expectedFormat)

          # Force a rescan.  Various factors can cause it to not be update even if we've created a new clip.  We might not have the correct frame range.
          # The media source might have already existed but been offline, in which case it needs to be refreshed.
          if clip:
            clip.rescan()

          # read metadata if its a nk script
          try:
            clipMediaSourceMeta = clip.mediaSource().metadata()
            filename = clipMediaSourceMeta.value("media.nk.writepath")

            newOutputSource = hiero.core.MediaSource.createOfflineVideoMediaSource( filename, expectedStartTime, expectedDuration, sequence.framerate(), startTimecode )
            outputClip = BuildTrack.FindOrCreateClip( newOutputSource, bin, sequence.project() )
            if not newOutputSource.isMediaPresent():
              outputClip.setFormat(expectedFormat)

            if outputClip:
              outputClip.rescan()

          except:
            pass # ignore if no nk metadata

        # Catch errors creating the media source.  Since we should be able to open anything that Nuke can render,
        # the most likely reason for failure is that it's a movie format and rendering isn't finished.
        except:
          self._errors.append( "Could not create clip for %s.  Check that the file has finished rendering." % file )
          return

      trackItem = self._buildTrackItem(name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle, expectedEndHandle, expectedOffset )

      BuildTrack.SetTrackItemReformatState(originalTrackItem, trackItem)

      # Set the new track item's version linking property to match the project setting
      trackItem.setVersionLinkedToBin(clip.project().trackItemVersionsLinkedToBin())

      # Add to track
      track.addTrackItem(trackItem)

      # Tell anything listening
      self.trackItemAdded(trackItem, track, originalTrackItem)

  def getExternalFilePaths(self, trackItem):
    return ''

  def getExpectedRange(self, trackItem):
    """ Get range information.  Returns a tuple containing the values: (start, duration, starthandle, endhandle, offset) """
    return 0, 0, None, None, 0


  def getTimelineRange(self, trackItem):
    """ Get the (timelineIn, timelineOut) for items being built from trackItem.  The default behaviour
        is to return trackItem's timeline range. """
    return (trackItem.timelineIn(), trackItem.timelineOut())


  def buildingFromExternalRender(self):
    """ Check if the the track is being built from external render tasks.  The behaviour needs to be different in this case because
        the frame range of those renders may not be what is expected. """
    return False


  def getExpectedFormat(self, trackItem):
    """ Get the expected format from the original track item.  The default implementation 
        returns the parent sequence format. """
    return trackItem.parentSequence().format()


  # Get a list of existing files for the given paths, handling padding for image sequences.  If
  # no files were found, returns the input paths.
  @staticmethod
  def findFiles(paths):
    files = []

    if paths:
      
      pathexts = [ os.path.splitext(path)[1] for path in paths ]
      for path in paths:
        # Try to match files for different versions
        versionScanner = hiero.core.VersionScanner.VersionScanner()
        path = versionScanner.getGlobExpression(path)

        # Strip padding out of single file types
        if hiero.core.isVideoFileExtension(os.path.splitext(path)[1].lower()):
          path = re.sub(r'.[#]+', '', path)
          path = re.sub(r'.%[\d]+d', '', path)
        path = path.replace('#', '*')

        hiero.core.log.info("Scanning: %s" % path)

        globbed = glob.glob(path)
        files += globbed

      # No existing files found, return the original paths
      if len(files) is 0:
        hiero.core.log.info( "No files found; adding paths in. %s" % str(paths) )
        files = paths
      else:
        hiero.core.log.info("found %s" % str(paths))

      # Custom sort function which proitises a particular file extension over everything else
      def extpriority ( file1, file2 ):

        file1 = os.path.splitext(file1)
        file2 = os.path.splitext(file2)
        file1match = file1[1] in pathexts
        file2match = file2[1] in pathexts

        # If either file has desired extension, move towards end of list
        if file1match != file2match:
          if file1match:
            return 1
          elif file2match:
            return -1

        # Otherwise sort based on filebase
        if file1[0] < file2[0]:
            return -1
        elif file1[0] > file2[0]:
            return 1
        else:
            return 0

      # Sort the list.  This is a hacky way of trying to make sure we can pick the highest version
      # by selecting the last file in the list.
      # Custom sort function to prioritise the format we were expecting
      files = sorted( files, key=functools.cmp_to_key(extpriority) )

    return files

  def getTrackItems(self):
    if not hasattr(hiero.ui.activeView(), 'selection'):
      # Something has gone wrong, we shouldn't only be here if raised
      # by the timeline view which will give a selection.
      return

    # Filter out audio
    selection = [ item for item in hiero.ui.activeView().selection() if isinstance(item.parent(), hiero.core.VideoTrack) ]
    return selection

  def doit(self):
    selection = self.getTrackItems()

    sequence = hiero.ui.activeView().sequence()
    project = sequence.project()

    if not self.configure(project, selection):
      return

    self._buildTrack(selection, sequence, project)

    if self._errors:
      msgBox = QtWidgets.QMessageBox(hiero.ui.mainWindow())
      msgBox.setWindowTitle("Build Media Track")
      msgBox.setText("There were problems building the track.")
      msgBox.setDetailedText( '\n'.join(self._errors) )
      msgBox.exec_()
      self._errors = []


  def _buildTrack(self, selection, sequence, project):
    """ Build the VFX track from the original items.  selection may contain TrackItems and Transitions, which are duplicated to the VFX track. """

    # Begin undo group
    project.beginUndo("Build external media track")

    try:
      # Get the track to build on.  findTrack() may filter items out of the selection if they collide with items on
      # the target track, so use the returned selection
      track, selection = self.trackFinder.findTrack(self.trackName(), selection, sequence)

      #If there's nothing to do, stop doing things.
      if len(selection) == 0 :
        project.endUndo()
        return True

      # TODO: Allow the user to choose a destination in the bin
      bin = BuildTrack.FindOrCreateBin(project, track.name())

      # Collision handling: store collided items in sets, to be removed at the end (preventing from removing the same item twice)
      collidedTransitions = set()

      task = foundry.ui.ProgressTask("Building track")
      newItems = len(selection)
      currentItem = 0
      
      for originalTrackItem in selection:
        currentItem += 1
        task.setProgress(int(100.0*(float(currentItem)/float(newItems))))
        
        # TrackItems
        if isinstance(originalTrackItem, hiero.core.TrackItem):
          if isinstance(originalTrackItem.source(), hiero.core.Clip):

            files = self.getExternalFilePaths(originalTrackItem)
            if self._useMaxVersions:
              files = BuildTrackActionBase.findFiles( files )
            start, duration, starthandle, endhandle, offset = self.getExpectedRange( originalTrackItem )
            self.buildShotFromFiles(files, originalTrackItem.name(), sequence, track, bin, originalTrackItem, start, duration, starthandle, endhandle, offset)
        elif isinstance(originalTrackItem, hiero.core.Transition):
          # Check for colliding transitions
          BuildTrack.CheckForTransitionCollisions(originalTrackItem, track, collidedTransitions)
          track.addTransition(originalTrackItem.copy())

      # Remove collided transitions
      for item in collidedTransitions:
        track.removeTransition(item)

      return True
    # Ensure the undo gets closed even if there's an exception
    finally:
      # End undo group (this does the actual editing, hence BEFORE sequence.editFinished())
      project.endUndo()
      # Send signal to update viewers (TimelineEditor, SpreadsheetView, Viewer)
      sequence.editFinished(selection)

  def _buildTrackItem(self, name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle, expectedEndHandle, expectedOffset):
    # Create track item
    trackItem = hiero.core.TrackItem(name, hiero.core.TrackItem.kVideo)
    # hiero.core.log.debug( "TrackItem Created : " + originalTrackItem.name() )
    # hiero.core.log.debug( "Clip Created : " + file )

    expectedHandles = None
    if (expectedStartHandle is not None) and (expectedEndHandle is not None):
      expectedHandles = (expectedStartHandle, expectedEndHandle)

    # Assign our new clip
    trackItem.setSource(clip)
    # Copy timings from source track item
    BuildTrack.CopyTimingFrom(trackItem, originalTrackItem, expectedHandles)
    return trackItem



class BuildTrackFromExportTagDialog(QtWidgets.QDialog):
  """ Dialog for configuring a Build Track/From Export Tag action. """

  def __init__(self, selection, createCompClips,  parent=None):
    if not parent:
      parent = hiero.ui.mainWindow()
    super(BuildTrackFromExportTagDialog, self).__init__(parent)
    self.setWindowTitle("Build Track From Export Tag")
    self.setSizeGripEnabled(True)

    self._tagIdentifier = None

    layout = QtWidgets.QVBoxLayout()
    formLayout = QtWidgets.QFormLayout()
    formLayout.setRowWrapPolicy(QtWidgets.QFormLayout.WrapAllRows)
    self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
    self._tracknameField.setToolTip("Name of new track")
    validator = hiero.ui.trackNameValidator()
    self._tracknameField.setValidator(validator)

    formLayout.addRow("Track Name:", self._tracknameField)

    # Use an OrderedDict so the tags are displayed in creation order
    self._tagData = collections.OrderedDict()

    for item in selection:
      if hasattr(item, 'tags'):
        for tag in item.tags():
          tagMetadata = tag.metadata()
          if tagMetadata.hasKey("path"):
            identifier = BuildTrack.GetTagIdentifier(tag)
            data = self._tagData.get(identifier, dict())
            if not data:
              data["icon"] = tag.icon()
              data["tagname"] = tag.name()
              if tagMetadata.hasKey("description"):
                data["description"] = tagMetadata.value("description")
              if tagMetadata.hasKey("pathtemplate"):
                data["pathtemplate"] = tagMetadata.value("pathtemplate")
              data["itemnames"] = []
              self._tagData[identifier] = data
            data["itemnames"].append( item.name() )

    self._notesView = QtWidgets.QTextEdit()
    self._notesView.setReadOnly(True)

    # List box for track selection
    self._tagListModel = QtGui.QStandardItemModel()
    self._tagListView = QtWidgets.QListView()
    self._tagListView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
    self._tagListView.setModel(self._tagListModel)
    for tagIdentifier, tagData in self._tagData.items():
      item = QtGui.QStandardItem(tagData["tagname"])
      item.setData(tagIdentifier)
      item.setEditable(False)
      itemlist = tagData["itemnames"]
      item.setToolTip("%i Items with this tag: \n%s" % (len(itemlist), "\n".join(itemlist)))
      item.setIcon(QtGui.QIcon(tagData["icon"]))
      self._tagListModel.appendRow(item)

    tagListSelectionModel = self._tagListView.selectionModel()
    tagListSelectionModel.selectionChanged.connect(self.tagSelectionChanged)

    # Start with the last tag selected
    tagListSelectionModel.select( self._tagListModel.index(self._tagListModel.rowCount()-1, 0), QtCore.QItemSelectionModel.Select )

    tagLayout = QtWidgets.QHBoxLayout()
    tagLayout.addWidget(self._tagListView)
    tagLayout.addWidget(self._notesView)

    formLayout.addRow("Select Export Tag:", tagLayout)

    createCompClipsCheckBox = QtWidgets.QCheckBox("Create Comp Clips")
    createCompClipsCheckBox.setToolTip("When building from a Nuke Project export, this controls whether the created clips reference the exported nk script or the render output.")
    createCompClipsCheckBox.setChecked(createCompClips)
    formLayout.addRow(createCompClipsCheckBox)
    self._createCompClipsCheckBox = createCompClipsCheckBox

    layout.addLayout(formLayout)

    # Add the standard ok/cancel buttons, default to ok.
    self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Build")
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setToolTip("Resolves the exported item from the selected export tags.")
    self._buttonbox.accepted.connect(self.acceptTest)
    self._buttonbox.rejected.connect(self.reject)
    layout.addWidget(self._buttonbox)

    self.setLayout(layout)


  def acceptTest(self):
    if self.tagIdentifier() and self.trackName():
      self.accept()
    else:
      QtWidgets.QMessageBox.warning(self, "Build Media Track", "Please set track name and export tag.", QtWidgets.QMessageBox.Ok)


  def tagSelectionChanged(self, selection):
    item = self._tagListModel.itemFromIndex(selection.indexes()[0])
    self._tagIdentifier = item.data()
    tagData = self._tagData.get(self._tagIdentifier)
    if tagData:
      itemlist = tagData["itemnames"]
      notes = ""
      if "description" in tagData:
        notes = "Description:\n" + tagData["description"] + "\n\n"

      if "pathtemplate" in tagData:
        notes = notes + "Path:\n" + tagData["pathtemplate"] + "\n\n"

      notes = notes + "%i Shots with this Tag:\n%s" % (len(itemlist), ", ".join(itemlist))
      self._notesView.setText(notes)


  def trackName(self):
    return str(self._tracknameField.text())


  def tagIdentifier(self):
    return str(self._tagIdentifier)


  def createCompClips(self):
    return self._createCompClipsCheckBox.isChecked()



class BuildTrackFromExportTagAction(BuildTrackActionBase):
  """ Action for the Build Track/From Export Tag functionality. """

  # Key for storing the createCompClips flag in the preferences
  kCreateCompClipsPreferenceKey = "buildtrack/createcompclips"

  def __init__(self):
    super(BuildTrackFromExportTagAction, self).__init__("From Export Tag")


  def buildTrackFromParams(self, trackItems, tag, trackName, createCompClips):
    """ Perform the action with the parameters configured programatically rather
    than through the UI. This is to facilitate auto-testing.

    @param trackItems: list of track items to build from
    @param tag: the export tag to build from
    @param trackName: name of the track to put built items on
    @param createCompClips: control whether the built items reference the comp
    or rendered files
    """

    self._trackName = trackName
    self._tagIdentifier = BuildTrack.GetTagIdentifier(tag)
    self._createCompClips = createCompClips
    sequence = trackItems[0].parentSequence()
    project = sequence.project()
    self._buildTrack(trackItems, sequence, project)


  def configure(self, project, selection):

    # Check the preferences for whether the built clips should be comp clips in the
    # case that the export being built from was a Nuke Shot export.
    settings = hiero.core.ApplicationSettings()
    createCompClips = settings.boolValue(self.kCreateCompClipsPreferenceKey, False)

    dialog = BuildTrackFromExportTagDialog(selection, createCompClips)
    if dialog.exec_():
      self._trackName = dialog.trackName()
      self._tagIdentifier = dialog.tagIdentifier()
      self._createCompClips = dialog.createCompClips()

      # Write the create comp clips choice to the preferences
      settings.setBoolValue(self.kCreateCompClipsPreferenceKey, self._createCompClips)

      return True
    else:
      return False

  def trackName(self):
    return self._trackName


  def _setMetadataValue(self, metadata, name, value):
    """ Helper function for setting values on metadata, first checking
        if the value is already set. """
    if metadata.hasKey(name) and (metadata.value(name) == value):
      return

    metadata.setValue(name, value)


  def findTag(self, trackItem):
    for tag in trackItem.tags():
      if BuildTrack.GetTagIdentifier(tag) == self._tagIdentifier:
        return tag
    return None


  def trackItemAdded(self, newTrackItem, track, originalTrackItem):
    """ Reimplementation.  Adds a tag to the new track item, and copies any retime effects if necessary. """
    # Find export tag on the original track item
    tag = self.findTag(originalTrackItem)
    if tag:
      # Add metadata referencing the newly created copied track item
      metadata = tag.metadata()

      # call setMetadataValue so that we only trigger something that's
      # undo/redo able if we need to
      self._setMetadataValue(metadata, "tag.track", track.guid())
      self._setMetadataValue(metadata, "tag.trackItem", newTrackItem.guid())

      # Tag the new track item to give it an icon.  Add a reference to the original
      # in the tag metadata.  This is used for re-export, so only add it if the original tag
      # has a presetid which could be re-exported from.
      if metadata.hasKey("tag.presetid"):
        newTag = hiero.core.Tag("VFX", "icons:NukeVFX.png", False)
        newTag.metadata().setValue("tag.originaltrackitem", originalTrackItem.guid())
        newTag.setVisible( False )
        newTrackItem.addTag(newTag)

      # If retimes were not applied as part of the export, check for linked effects on the original track item, and
      # copy them to the new track.
      if not self.retimesAppliedInExport(tag):
        linkedRetimeEffects = [ item for item in originalTrackItem.linkedItems() if isinstance(item, hiero.core.EffectTrackItem) and item.isRetimeEffect() ]
        for effect in linkedRetimeEffects:
          effectCopy = track.createEffect(copyFrom=effect, trackItem=newTrackItem)
          effectCopy.setEnabled(effect.isEnabled())


  def _findTagWithMetadataKeys(self, trackItem, keys):
    """ Try to find a tag which has all the given set of metadata keys. """
    for tag in reversed(trackItem.tags()):
      metadata = tag.metadata()
      keysFound = True
      for key in keys:
        if not metadata.hasKey(key):
          keysFound = False
      if keysFound:
        return tag
    return None

  def findShotExporterTag(self, trackItem):
    """ Try to find a tag added by the Nuke Shot Exporter by checking it has the expected metadata keys. """
    return self._findTagWithMetadataKeys(trackItem, ("tag.presetid", "tag.path", "tag.script"))


  def getExternalFilePaths(self, trackItem):

    ## see if this is an nk export first - if so add that
    if self._createCompClips:
      tag = self.findShotExporterTag(trackItem)
      if tag and tag.metadata().hasKey("script"):
        return tag.metadata().value("script").split(';')

    ## otherwise add the destination path ( eg a dpx )
    tag = self.findTag(trackItem)
    if tag and tag.metadata().hasKey("path"):
      return tag.metadata().value("path").split(";")
    else:
      return None


  def getExpectedRange(self, trackItem):
    tag = self.findTag(trackItem)
    start, duration, starthandle, endhandle, offset = 0, 0, 0, 0, 0
    if tag and tag.metadata().hasKey("startframe") and tag.metadata().hasKey("duration"):
      start = int(math.floor(float(tag.metadata().value("startframe"))))

      # There was a bug in NukeShotExporter where the duration would be written as negative if the
      # original track item was negatively retimed.  Get the abs value just in case.
      duration = abs(int(math.floor(float(tag.metadata().value("duration")))))

      if tag.metadata().hasKey("sourceoffset"):
        offset = int(tag.metadata().value("sourceoffset"))
    else:
      start, duration, starthandle, endhandle, offset = BuildTrackActionBase.getExpectedRange(self, trackItem)

    if tag and tag.metadata().hasKey("starthandle"):
      starthandle = int(math.floor(float(tag.metadata().value("starthandle"))))
    if tag and tag.metadata().hasKey("endhandle"):
      endhandle = int(math.floor(float(tag.metadata().value("endhandle"))))

    # This is no longer added, as the exporters now use the separate start and end handle keys above.  But older projects
    # might still contain it.
    if tag and tag.metadata().hasKey("handles"):
      starthandle = endhandle = int(math.floor(float(tag.metadata().value("handles"))))

    return start, duration, starthandle, endhandle, offset


  def getTimelineRange(self, trackItem):
    """ Override.  The created track item is not necessarily the same length as the source, if multiple clips have been exported
        together (particularly with Create Comp).  Use the duration of the new source, minus handles. """
    start, duration, starthandle, endhandle, offset = self.getExpectedRange( trackItem )

    # Handles might be None (indicating that we don't know what handles to expect).  Use 0 in this case
    starthandle = 0 if starthandle is None else starthandle
    endhandle = 0 if endhandle is None else endhandle

    timelineIn = trackItem.timelineIn()
    timelineOut = timelineIn + duration - 1 - starthandle - endhandle

    inTransitionLength, outTransitionLength = BuildTrack.CalcTransitionExtraLengths(trackItem)
    timelineOut -= (inTransitionLength + outTransitionLength)
    return (timelineIn, timelineOut)


  def getExpectedFormat(self, trackItem):
    """ Reimplemented.  Tries to get the expected format from the tag metadata.
        If not present, returns the parent sequence format. """
    try:
      tag = self.findTag(trackItem)
      formats = tag.metadata().value("format").split(";")
      format = hiero.core.Format(formats[0])
      return format
    except:
      return trackItem.parentSequence().format()


  def retimesAppliedInExport(self, item):
    """ Look up whether retimes were applied in the export.  Item can either be a Tag or a TrackItem.  In the latter case,
        the tag is looked up using findTag() """
    if isinstance(item, hiero.core.Tag):
      tag = item
    else:
      tag = self.findTag(item)
    appliedRetimes = False
    if tag and tag.metadata().hasKey("appliedretimes"):
      appliedRetimes = int( tag.metadata().value("appliedretimes") )
    return appliedRetimes


  def _buildTrackItem(self, name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle, expectedEndHandle, expectedOffset):
    """ Create the new track item and set its in/out times.  Reimplemented here as the BuildTrackFromExportTagAction can be a bit cleverer about this,
        since all the relevant information should be stored in the tag metadata. """

    # Create the item
    trackItem = hiero.core.TrackItem(name, hiero.core.TrackItem.kVideo)
    trackItem.setSource(clip)

    # Copy the timeline in/out
    trackItem.setTimelineIn(originalTrackItem.timelineIn())
    trackItem.setTimelineOut(originalTrackItem.timelineOut())

    # Calculate the source in/out times.  Try to match frame numbers, compensating for handles etc.
    mediaSource = clip.mediaSource()

    originalClip = originalTrackItem.source()
    originalMediaSource = originalClip.mediaSource()

    appliedRetimes = self.retimesAppliedInExport(originalTrackItem)

    # If source durations match, and there were no retimes, then the whole clip was exported, and we should use the same source in/out
    # as the original.  The correct handles are not being stored in the tag in this case.
    fullClipExported = (originalMediaSource.duration() == mediaSource.duration()) and not appliedRetimes

    if fullClipExported:
      sourceIn = originalTrackItem.sourceIn()
      sourceOut = originalTrackItem.sourceOut()

    # Otherwise try to use the export handles and retime info to determine the correct source in/out
    else:
      # On the timeline, the first frame of video files is always 0.  Reset the start time
      isVideoFile = hiero.core.isVideoFileExtension(os.path.splitext(mediaSource.fileinfos()[0].filename())[1])
      if isVideoFile:
        expectedStartTime = 0

      sourceIn = expectedStartTime - mediaSource.startTime()
      if expectedStartHandle is not None:
        sourceIn += expectedStartHandle

      # If retimes were applied in the export, then the built item should not be retimed (since that was baked in).
      if appliedRetimes:
        sourceOut = sourceIn + originalTrackItem.duration() - 1
      # Otherwise it should have the same source duration as the original, and thus the same retime percentage.
      else:
        # First add the abs src duration to get the source out
        sourceOut = sourceIn + abs(originalTrackItem.sourceOut() - originalTrackItem.sourceIn())

        # Then, for a negative retime, src in/out need to be reversed
        if originalTrackItem.playbackSpeed() < 0.0:
          sourceIn, sourceOut = sourceOut, sourceIn

    trackItem.setSourceIn(sourceIn)
    trackItem.setSourceOut(sourceOut)
    return trackItem



class BuildExternalMediaTrackDialog(QtWidgets.QDialog):
  def __init__(self,  selection,  parent=None):
    if not parent:
      parent = hiero.ui.mainWindow()
    super(BuildExternalMediaTrackDialog, self).__init__(parent)
    self.setWindowTitle("Build Track From Export Structure")
    self.setSizeGripEnabled(True)

    self._exportTemplate = None
    self._selection = selection
    layout = QtWidgets.QVBoxLayout()
    formLayout = QtWidgets.QFormLayout()

    self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
    self._tracknameField.setToolTip("Name of new track")
    validator = hiero.ui.trackNameValidator()
    self._tracknameField.setValidator(validator)
    formLayout.addRow("Track Name:", self._tracknameField)

    project = None
    if self._selection:
      project = self.itemProject(self._selection[0])
    presetNames = [ preset.name() for preset in hiero.core.taskRegistry.localPresets() + hiero.core.taskRegistry.projectPresets(project) ]
    presetCombo = QtWidgets.QComboBox()
    for name in sorted(presetNames):
      presetCombo.addItem(name)
    presetCombo.currentIndexChanged.connect(self.presetChanged)
    self._presetCombo = presetCombo
    formLayout.addRow("Export Preset:", presetCombo)

    layout.addLayout(formLayout)

    self._exportTemplate = hiero.core.ExportStructure2()
    self._exportTemplateViewer = hiero.ui.ExportStructureViewer(self._exportTemplate, hiero.ui.ExportStructureViewer.ReadOnly)
    if project:
      self._exportTemplateViewer.setProject(project)

    layout.addWidget(self._exportTemplateViewer)

    # Add the standard ok/cancel buttons, default to ok.
    self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Build")
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDefault(True)
    self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setToolTip("Builds the selected entry in the export template. Only enabled if an entry is selected in the view above.")
    self._buttonbox.accepted.connect(self.acceptTest)
    self._buttonbox.rejected.connect(self.reject)
    layout.addWidget(self._buttonbox)

    if presetNames:
      self.presetChanged(presetNames[0])

    self.setLayout(layout)

  def itemProject(self, item):
    if hasattr(item, 'project'):
      return item.project()
    elif hasattr(item, 'parent'):
      return self.itemProject(item.parent())
    else:
      return None

  def acceptTest(self):
    validSelection = self._exportTemplateViewer.selection() is not None
    if not validSelection:
      QtWidgets.QMessageBox.warning(self, "Build External Media Track", "Please select an entry in the export template and press Build again.", QtWidgets.QMessageBox.Ok)
    elif not self.trackName():
      QtWidgets.QMessageBox.warning(self, "Build External Media Track", "Please set a track name", QtWidgets.QMessageBox.Ok)
    else :
      self.accept()


  def presetChanged(self, index):

    project = None
    if self._selection:
      project = self.itemProject(self._selection[0])
    presetsDict = dict([ (preset.name(), preset) for preset in hiero.core.taskRegistry.localPresets() + hiero.core.taskRegistry.projectPresets(project) ])

    value = self._presetCombo.currentText()
    if value in presetsDict:
      #self._exportTemplate = hiero.core.ExportStructure2()
      self._preset = presetsDict[value]
      self._exportTemplate.restore(self._preset._properties["exportTemplate"])
      if self._preset._properties["exportRoot"] != "None":
        self._exportTemplate.setExportRootPath(self._preset._properties["exportRoot"])
      self._exportTemplateViewer.setExportStructure(self._exportTemplate)
      self._resolver = self._preset.createResolver()
      self._resolver.addEntriesToExportStructureViewer(self._exportTemplateViewer)

      # force the first item to be selected, if there is only one
      self._exportTemplateViewer.selectFileIfOnlyOne()

  def trackName(self):
    return self._tracknameField.text()
 


class BuildExternalMediaTrackAction(BuildTrackActionBase):

  def __init__(self):
    super(BuildExternalMediaTrackAction, self).__init__("From Export Structure")

  def configure(self, project, selection):
    dialog = BuildExternalMediaTrackDialog(selection)
    if dialog.exec_():
      self._trackName = dialog.trackName()

      # Determine the exported file paths
      self._exportTemplate = dialog._exportTemplate
      structureElement = dialog._exportTemplateViewer.selection()
      self._processorPreset = dialog._preset
      if structureElement is not None:
        # Grab the elements relative path
        self._elementPath = structureElement.path()
        self._elementPreset = structureElement.preset()

        resolver = hiero.core.ResolveTable()
        resolver.merge(dialog._resolver)
        resolver.merge(self._elementPreset.createResolver())
        self._resolver = resolver

        self._project = project

        return True

    return False

  def trackName(self):
    return self._trackName

  def getExternalFilePaths(self, trackItem):
    # Instantiate a copy of the task in order to resolve the export path
    # replace the version string with "v*" so the glob matches all versions
    taskData = hiero.core.TaskData(self._elementPreset, trackItem, self._exportTemplate.exportRootPath(), self._elementPath, "v*", self._exportTemplate, project=self._project, resolver=self._resolver)
    task = hiero.core.taskRegistry.createTaskFromPreset(self._elementPreset, taskData)
    return [task.resolvedExportPath()]

  def getExpectedRange(self, trackItem):
    """ Override. Get expected range based on the original track item. 
        Returns None for handles so that they are calculated based on the duration
        of the new media. """
    source = trackItem.source().mediaSource()
    start, duration = source.startTime(), source.duration()
    starthandle, endhandle = None, None
    offset = 0
    return (start, duration, starthandle, endhandle, offset)


  def buildingFromExternalRender(self):
    """ Override.  Check if the selected task preset is an External Render. """
    return self._elementPreset and ("ExternalRenderTask" in self._elementPreset.ident())



# Instantiate the action to get it to register itself.
if (not hiero.core.isHieroPlayer()) and QtCore.QCoreApplication.instance().inherits("QApplication"):
  buildExternalMediaTrackAction = BuildTrack()
