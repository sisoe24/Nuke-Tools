import copy
import traceback
import hiero.ui
import hiero.core
import hiero.core.util

from hiero.ui.BuildExternalMediaTrack import *
from hiero.core.VersionScanner import VersionScanner

class HieroMediaDescriptor:
  kClip         = "clip"
  kClipGUID     = "clip_guid"
  kShot         = "shot"
  kShotGUID     = "shot_guid"
  kShotTagGUID  = "shot_tag_guid"
  kTrack        = "track"
  kTrackGUID    = "track_guid"
  kSequence     = "sequence"
  kSequenceGUID = "sequence_guid"
  kProject      = "project"
  kProjectGUID  = "project_guid"
  
  def __init__( self, **kwargs  ):
    def tryGet( kwargs, key ):
      if key in kwargs:
        return kwargs[key]
      return None
    self._clip          = tryGet( kwargs, HieroMediaDescriptor.kClip )
    self._clip_guid     = tryGet( kwargs, HieroMediaDescriptor.kClipGUID )
    self._shot          = tryGet( kwargs, HieroMediaDescriptor.kShot )
    self._shot_guid     = tryGet( kwargs, HieroMediaDescriptor.kShotGUID )
    self._shot_tag_guid = tryGet( kwargs, HieroMediaDescriptor.kShotTagGUID )
    self._track         = tryGet( kwargs, HieroMediaDescriptor.kTrack )
    self._track_guid    = tryGet( kwargs, HieroMediaDescriptor.kTrackGUID )
    self._sequence      = tryGet( kwargs, HieroMediaDescriptor.kSequence )
    self._sequence_guid = tryGet( kwargs, HieroMediaDescriptor.kSequenceGUID )
    self._project       = tryGet( kwargs, HieroMediaDescriptor.kProject )
    self._project_guid  = tryGet( kwargs, HieroMediaDescriptor.kProjectGUID )
    
  @staticmethod
  def build(trackitem):
    sequence, track, clip = trackitem.parentSequence(), trackitem.parentTrack(), trackitem.source()
    project = sequence.project()
    mediaDesc = {'clip':clip.name(), 'clip_guid':clip.guid(), 'shot':trackitem.name(), 'shot_guid':trackitem.guid(), 
                 'track':track.name(), 'track_guid':track.guid(), 'sequence':sequence.name(), 'sequence_guid':sequence.guid(),
                 'project':project.name(), 'project_guid':project.guid()}
    return mediaDesc
    
    
  def __repr__(self):
    return   str({  HieroMediaDescriptor.kClip         : self._clip,
                    HieroMediaDescriptor.kClipGUID     : self._clip_guid,    
                    HieroMediaDescriptor.kShot         : self._shot,
                    HieroMediaDescriptor.kShotGUID     : self._shot_guid,
                    HieroMediaDescriptor.kShotTagGUID  : self._shot_tag_guid,
                    HieroMediaDescriptor.kTrack        : self._track,
                    HieroMediaDescriptor.kTrackGUID    : self._track_guid,
                    HieroMediaDescriptor.kSequence     : self._sequence,  
                    HieroMediaDescriptor.kSequenceGUID : self._sequence_guid,
                    HieroMediaDescriptor.kProject      : self._project,       
                    HieroMediaDescriptor.kProjectGUID  : self._project_guid })
    
  def clip(self):
    return self._clip
  def clip_guid(self):
    return self._clip_guid
  def shot(self):
    return self._shot
  def shot_guid(self):
    return self._shot_guid
  def shot_tag_guid(self):
    return self._shot_tag_guid
  def track(self):
    return self._track
  def track_guid(self):
    return self._track_guid
  def sequence(self):
    return self._sequence
  def sequence_guid(self):
    return self._sequence_guid
  def project(self):
    return self._project
  def project_guid(self):
    return self._project_guid 

class HieroState:
  def __init__(self):
    self._trackItems = {}
    self._originalTrackItems = {}
    self._clips = {}
    
  def _nukeBin(self):
    # find the Nuke bin if it's in there
    # create it if it's not
    pass

  def _createClip(self, mediaPath):
    if hiero.core.projects():
      # find the nuke bin
      bin = BuildTrack.FindOrCreateBin(hiero.core.projects()[-1], "Nuke")
    
      # check if it's got a clip with our media path already
      clips = bin.clips()
      for clip in clips:
        if clip.activeItem().mediaSource().filename() == mediaPath:
          self._clips[mediaPath] = clip.activeItem()
          clip.activeItem().refresh()
          return clip
    
      # we didn't find it, so create it
      newSource = hiero.core.MediaSource(mediaPath)
      clip = hiero.core.Clip(newSource)
      bin.addItem(hiero.core.BinItem(clip))
      return clip
    
  def addTrackItem(self, newTrackItem, originalTrackItem, mediaPath):
    self._trackItems[mediaPath] = newTrackItem
    self._originalTrackItems[newTrackItem] = originalTrackItem
  
  def _createSingleFilePath(self, path):
    
    path = path.replace('#', '0')
    
    try:
      if '%' in path:
        path = path % 0
    except:
      pass
      
    return path
  
  def _findNewVersion(self, lastMediaPath, mediaPath):
    scanner = VersionScanner()
    
    # get rid of any %d's or hashes right away, because they screw up the scanner
    lastMediaPath = self._createSingleFilePath(lastMediaPath)
    mediaPath = self._createSingleFilePath(mediaPath)

    hiero.core.log.debug("scanner._visitedClips:", scanner._visitedClips)
    return scanner.checkNewVersion(lastMediaPath, mediaPath)
  
  def _setVersion(self, trackItem, newVersionPath):
    trackItem.source().refresh() # First rescan the current clip
    
    version = trackItem.currentVersion()
    binitem = version.parent()

    hiero.core.log.debug("Creating and setting Version; scan successful; should set media / do a rescan of the clip.")
    
    # This ensures the new version is inserted at the right position
    scanner = VersionScanner()
    insertedVersions = scanner.insertVersions(binitem, [newVersionPath])
    if len(insertedVersions) == 0:
      hiero.core.log.debug("New Version was not inserted")
      return
    
    # Retrieve inserted version and make the trackItem point to it  
    newVersion = insertedVersions[0]
    trackItem.setCurrentVersion(newVersion)
    
  def _scanAndBump(self, trackItem, mediaPath, lastMediaPath):
    try:
      # check if it is a version
      if not self._findNewVersion(lastMediaPath, mediaPath):
        hiero.core.log.debug("Bad Version filename - lastMediaPath:", lastMediaPath, "mediaPath:", mediaPath)
        return
    
      # set the version
      self._setVersion(trackItem, mediaPath)
    
      # store this here so that we don't scan again next time
      self._trackItems[mediaPath] = trackItem
    except Exception as e:
      print("Exception: " + str(e))

  def _findTrackItem(self, mediaDesc):

    # Walk all open projects
    for project in hiero.core.projects():
      if not mediaDesc.project_guid() or project.guid() == mediaDesc.project_guid():

        for sequence in project.sequences():
          if sequence.guid() == mediaDesc.sequence_guid():

            for track in sequence.videoTracks():
              #if track.guid() == mediaDesc.track_guid(): # don't check the track, as the user may drag track items onto different tracks
              for trackItem in track:
                if trackItem.guid() == mediaDesc.shot_guid():
                  hiero.core.log.debug("shot guid matched")
                  mediaSource = trackItem.source().mediaSource()
                  return trackItem, mediaSource.firstpath()
                    
            hiero.core.log.debug("shot guid and trackitem guid mismatch %s" % (mediaDesc.shot_guid()))
            return None, None
            #print "track guid not found %s" % (mediaDesc.track_guid())
            #return None, None
            
        hiero.core.log.debug("Sequence guid not found %s" % (mediaDesc.sequence_guid()))
        return None, None
        
    hiero.core.log.debug("Project guid not found [%s not in %s]" % (mediaDesc.project_guid(), ", ".join([project.guid() for project in hiero.core.projects()])))
    return None, None

  

  def _findTrackItemFromTag(self, mediaDesc):

    # Find Track Item referenced by MediaDescriptor
    trackItem, mediaPath = self._findTrackItem(mediaDesc)
    if trackItem:
      # Walk each tag to match tag guid
      for tag in trackItem.tags():
        if tag.guid() == mediaDesc.shot_tag_guid():
          metadata = tag.metadata()

          # Make a copy of the Media Descripto and 
          cloneMediaDesc =  copy.deepcopy(mediaDesc)
          if "tag.track" in metadata and "tag.trackItem" in metadata:
            cloneMediaDesc._track_guid = metadata["tag.track"]
            cloneMediaDesc._shot_guid = metadata["tag.trackItem"]
            hiero.core.log.debug("Cloned TrackItem matched")
            return self._findTrackItem(cloneMediaDesc)
          hiero.core.log.debug("Tag Found, metadata keys missing")
          return None, None

      print("Export Tag not found - %s" % mediaDesc.shot_tag_guid())
      return None, None
      
    return None, None


  def _findTrackItemFromTable(self, mediaDesc):      
    if (not mediaDesc.shot()) and (not mediaDesc.clip()):
      print("no clip or shot")
      return (None, None)
          
    for oldMediaPath in self._trackItems:
      trackItem = self._trackItems[oldMediaPath]
      
      if not mediaDesc.shot():
        try:
          if (mediaDesc.clip() != self._originalTrackItems[trackItem].source().name()):
            hiero.core.log.debug("Clip name and source mismatch %s - %s" % (mediaDesc.clip(), self._originalTrackItems[trackItem].source().name()))
            continue
        except:
          continue
      elif mediaDesc.shot() != trackItem.name():
        hiero.core.log.debug("Shot name and TrackItem name mismatch %s - %s" % (mediaDesc.shot(), trackItem.name()))
        continue
        
      if mediaDesc.project() and (trackItem.project().name() != mediaDesc.project()):
        hiero.core.log.debug("Project name mismatch")
        continue
        
      if mediaDesc.track() and (mediaDesc.track() != self._originalTrackItems[trackItem].parentTrack().name()):
        hiero.core.log.debug("Track name mismatch %s - %s" % (mediaDesc.track(), self._originalTrackItems[trackItem].parentTrack().name()))
        continue
        
      if mediaDesc.sequence() and (mediaDesc.sequence() != self._originalTrackItems[trackItem].parentSequence().name()):
        hiero.core.log.debug("Sequence name mismatch %s - %s" % (mediaDesc.sequence(), self._originalTrackItems[trackItem].parentSequence().name()))
        continue
        
      hiero.core.log.debug("Found TrackItem")
      return (trackItem, oldMediaPath)
    
    hiero.core.log.debug("Did not find TrackItem")
    return (None, None)
    
  def updateMediaFrame(self, mediaPath, **kwargs):
    pass

  # Generator method which iterates over all the Clips
  # open in Hiero and returns ones which point to mediaPath
  def _findClipsForPath(self, mediaPath):
    mediaPath = hiero.core.util.SequenceifyFilename(mediaPath, False) # Try to normalise paths with SequenceifyFilename
    for project in hiero.core.projects():
      for clip in project.clips():
        clipPath = hiero.core.util.SequenceifyFilename(clip.mediaSource().fileinfos()[0].filename(), False)
        if clipPath.startswith(mediaPath): # Use startswith because there might be trailing frame number specifications in clipPath if it's an image sequence
          yield clip
    
  def mediaRendered(self, mediaPath, **kwargs):

    try:
      
      mediaDesc = HieroMediaDescriptor(**kwargs)

      # look up if we have any track items that map to this media path
      if mediaPath in self._trackItems:
        #print "refreshing from media Path"
        trackItem = self._trackItems[mediaPath]
        
        # there's no rescan of track items, so set the version on the track item to the current to
        # force a rescan.
        trackItem.source().refresh() # First rescan the current clip
        trackItem.setCurrentVersion(trackItem.currentVersion())
        return
      else:
        #print "not refreshing from mediaPath"
        # Walks project using guids to match against trackitem
        # If trackItem tag references a new vfx trackitem, return that
        refreshedClip = None
        (trackItem, lastMediaPath) = self._findTrackItemFromTag(mediaDesc)
        if trackItem:
          refreshedClip = trackItem.source()
          refreshedClip.refresh()
          #print "scan and bump version"
          # scan for new versions
          self._scanAndBump(trackItem, mediaPath, lastMediaPath)

        # Refresh any other clips pointing to the rendered media
        for clip in self._findClipsForPath(mediaPath):
          if clip != refreshedClip:
            clip.refresh()
      
      # don't do anything else; this is a frame by frame update
      #self._createClip(mediaPath)
    except Exception as e:
      print(str(e))
      print(traceback.format_exc())

  def updateScriptName(self, newNukeScriptPath, **kwargs):
    try:
      mediaDesc = HieroMediaDescriptor(**kwargs)
      
      trackItem, mediaPath = self._findTrackItem(mediaDesc)
      if trackItem:
        # Walk each tag to match tag guid
        for tag in trackItem.tags():
          if tag.guid() == mediaDesc.shot_tag_guid():
            metadata = tag.metadata()
            
            # update the script path
            metadata.setValue("tag.script", newNukeScriptPath)
            return
      
    except Exception as e:
      print(str(e))
      print(traceback.format_exc())
