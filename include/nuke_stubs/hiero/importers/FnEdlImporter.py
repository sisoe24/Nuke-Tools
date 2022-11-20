# from _fnpython import *

import sys
import traceback
import hiero.core
import hiero.core.util
import FnCyclone
import os.path
import ntpath
import posixpath
import re
import math

from hiero.core.log import debug, info

from .FnEdlDefinitions import *
from .yeanpypa import *
        
TOCLIPNAME = "TOCLIPNAME"
FROMCLIPNAME = "FROMCLIPNAME"
KEYCLIPNAME = "KEYCLIPNAME"
STARTTC = "STARTTC"

# Indices for referencing tracks
VIDEO1 = 0
VIDEO2 = 5
AUDIO1 = 1
AUDIO2 = 2
AUDIO3 = 3
AUDIO4 = 4

# Convert all line endings to CRLF
def fixLineEndings(text):
  return re.sub("\r(?!\n)|(?<!\r)\n", "\r\n" , text)

# Detect absolute paths in Windows or Unix format
def isAbsPath(path):
  return posixpath.isabs(path) or ntpath.isabs(path)

# Try and determine if the given string looks like a file name
def isFileName(name):
  # If it's an absolute path return true
  if isAbsPath(name):
    return True
  # If it has an extension of 3 or 4 characters (minus the period) return true
  ext = os.path.splitext(name)[1]
  if len(ext) in (4, 5):
    return True

  return False

# Try to clean up a filename, replacing invalid characters with _
# and stripping whitespace
def cleanupFileName(fileName):
  # Replace all backslashes.  This needs to be done even if it's a Windows path
  fileName = fileName.replace('\\', '/')

  # Get rid of slashes if it's not an absolute path, otherwise it might be interpreted as a
  # relative one.
  if not isAbsPath(fileName):
    fileName = fileName.replace('/', '_')

  # Remove trailing whitespace
  fileName = fileName.strip()

  return fileName


class track:
  def __init__(self, trackId, trackType, timelineId, name, filename):
    self.__trackId = trackId
    self.__trackType = trackType
    self.__timelineId = timelineId
    self.__name = name
    self.__filename = filename
    
  def getTrackId(self):
    if self.__trackId == -1:
      self.__trackId = FnCyclone.addTrack(parentTimeline = self.__timelineId, data = { FnCyclone.kTrackType :self.__trackType, FnCyclone.kTrackName: self.__name, FnCyclone.kTrackEdlName: self.__filename } )
    return self.__trackId
  
  def getTrackType(self):
    return self.__trackType

class EdlImporter:
  def __init__(self):
    """Initialize"""
    self.__title = None
    
  def displayName(self):  
    return "Foundry EDL Importer";

  __options = [ FnCyclone.kOptionFramerate, FnCyclone.kOptionFramerateIsNtsc, FnCyclone.kOptionDropFrame,
                FnCyclone.kOptionSamplerate, FnCyclone.kOptionEDLRetimeFromSourceDuration ]
    
  def isOptionRequired(self, option):
    return option in EdlImporter.__options
  
  def isValidFile(self, fileName):
    """Return true if file is of correct type"""
    debug( "isFileValid (" + fileName + ")" )
    
    if os.path.isfile(fileName):
      basename, extension = os.path.splitext(fileName)
      if extension.lower() == ".edl":
        return True    
    return False

  # Calculate the speed and duration for a track item based on the EDL data and
  # the options set.
  def getTrackItemSpeedAndDuration(self, edlElement):
    speed = 1.0
    fps = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerate)
    srcDuration = edlElement.srcExit().toFrames(fps)  - edlElement.srcEntry().toFrames(fps)
    timelineDuration = edlElement.syncExit().toFrames(fps) - edlElement.syncEntry().toFrames(fps)

    retimeFromSourceDuration = FnCyclone.getImportOption(name = FnCyclone.kOptionEDLRetimeFromSourceDuration)

    # First look for an M2 command
    retime = edlElement.retime()
    if retime:
      speed = retime.framerate() / fps
      debug("M2 command found: speed = " + str(retime.framerate()) + " fps")
    # Otherwise if the option was set use the ratio of the source and timeline durations
    elif retimeFromSourceDuration and srcDuration != timelineDuration:
      speed = float(srcDuration) / float(timelineDuration)
      debug("No M2 command found: speed = " + speed)

    srcDuration = math.ceil( timelineDuration * abs(speed) )
    # Add an extra frame for retimes for rounding issues
    #anton: -What??
    if speed != 1.0:
      srcDuration += 1

    return speed, srcDuration

  def getClipData(self, name, edlElement, speed, mediaType, startTC):
    fps = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerate)
    timelineDuration = (edlElement.syncExit().toFrames(fps) - edlElement.syncEntry().toFrames(fps))

    syncIn = edlElement.syncEntry().toFrames(fps)

    # Note that we don't use the src out on the clip except for the additional EDL metadata.  
    # The duration on the timeline is set with kClipDuration, and the src duration is calculated 
    # based on that and the retime (if present)

    srcIn = edlElement.srcEntry().toFrames(fps)
    srcOut = edlElement.srcExit().toFrames(fps)

    edlSource =  edlElement.getSource().strip() # take white spaces off the front and back 
    edlSource = fixLineEndings(edlSource)

    
    # If there is an M2 command, we ignore the edit's sourceIn to use the one specified here:
    sourceIn = srcIn
    retime = edlElement.retime()
    if retime:
      retimeSrcIn = retime.srcEntry()
      if retimeSrcIn is not None:
        sourceIn = retime.srcEntry().toFrames(fps)
      debug("M2 command found: sourceIn = " + str(sourceIn))

    data = {  FnCyclone.kClipName : name, 
              FnCyclone.kClipSourceIn : sourceIn,
              FnCyclone.kClipTimelineIn : syncIn,
              FnCyclone.kClipDuration : timelineDuration,
              FnCyclone.kClipRetime : speed,
              FnCyclone.kClipEdlEditString : edlSource,
              FnCyclone.kClipEdlEditNumber : edlElement.editId(),
              # MPLEC TODO: Need to deal with FINAL CUT PRO REEL: BR_005 REPLACED BY: BR005
              FnCyclone.kClipEdlSourceReel : edlElement.name(),
              FnCyclone.kClipEdlMode : str(edlElement.mode()),
              FnCyclone.kClipEdlEffect : str(edlElement.effectfield()),
              FnCyclone.kClipEdlTimelineIn : edlElement.syncEntry().toFrames(fps),
              FnCyclone.kClipEdlTimelineOut : edlElement.syncExit().toFrames(fps),
              FnCyclone.kClipEdlSrcIn : srcIn,
              FnCyclone.kClipEdlSrcOut : srcOut,
              FnCyclone.kClipEdlRetime : speed,
              FnCyclone.kMediaType : mediaType
          }
    
    # We only have an overriding start timecode if the file has a DLEDL START TC: entry.
    if startTC is not None:
      data[FnCyclone.kClipEdlSrcTimecode] = startTC

    # Read comments and add them as separate metadata
    edlComments = CRLF.join( [ line[1:].strip() for line in edlSource.splitlines() if line.startswith('*') ] ) # Extract comment lines
    if edlComments:
      data[FnCyclone.kClipEdlComments] = edlComments

    debug( "EdlImporter.getClipData: " + str(data) )

    return data
  
  def getMediaData(self, filename, edlElement, duration, startTC):

    fps = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerate)
    isNtsc = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerateIsNtsc)
    samplerate = FnCyclone.getImportOption(name = FnCyclone.kOptionSamplerate)

    if os.path.exists(filename):
      filename = hiero.core.util.SequenceifyFilename(filename, False)

    forceStartTimecode = False
    mediaStartTimecode = min ( edlElement.srcEntry().toFrames(fps), edlElement.srcExit().toFrames(fps) )
    if startTC is not None:
      mediaStartTimecode = startTC
      forceStartTimecode = True

    data = {  FnCyclone.kMediaUrl : filename, 
              FnCyclone.kMediaName : '', # Don't set the name here, it will be done automatically when the Sequence is created
              FnCyclone.kMediaTapeName : edlElement.name(), 
              FnCyclone.kMediaAudioChannels : "0",
              FnCyclone.kMediaStartTime : mediaStartTimecode,
              FnCyclone.kMediaTimecode : mediaStartTimecode,
              FnCyclone.kMediaForceTimecode : forceStartTimecode,
              FnCyclone.kMediaDuration : duration,
              FnCyclone.kMediaFramerate : fps,
              FnCyclone.kMediaFramerateIsNtsc : isNtsc,
              FnCyclone.kMediaSamplerate : samplerate }

    debug( "EdlImporter.getMediaData: " + str(data) )

    return data

  # Extract file names and possible clip name from an EDL event.
  # If we can't find a clip name it will be empty, and it will be
  # derived from the file name later on.
  def extractFilenamesAndClipName (self, element):
    filenames = list()
    clipname = ''
    
    # Build url from path and file name
    if element.hasElement("PATH") and element.hasElement("FILENAME"):
      # This also catches useful items in .dledl files like:
      # 001  mpc1     V    C         00:00:00:12 00:00:08:02 01:00:06:16 01:00:14:06
      # DLEDL: START TC: 00:00:00:04
      # DLEDL: PATH: /mpc/fcprepo-a/editors/conor-b/JCOM/forFinishSuite/conformed/SHOWREEL_JCOM_O_WA_109_0210_V45_COMPGRADED_QT98
      # DLEDL: EDIT:0 FILENAME: SHOWREEL_JCOM_O_WA_109_0210_V45_COMPGRADED_QT98.(1025@1222).dpx
      # but we may need to clean the filename up.
      filename = os.path.join(element.getElement("PATH")[0], element.getElement("FILENAME")[0])
      m = re.search("(.+\.)?\((\d+)\@(\d+)\)(.+)", filename)
      if len(m.groups()) == 4:
        # It looks like the digits are always assumed to be listed with padding.
        frames = '%%0%dd' % ( max(len(m.group(2)), len(m.group(3))), )
        if m.group(1) is None:
          # No filename part at head -- some names are just "(105@180).dpx".
          filename = frames + m.group(4)
        else:
          filename = m.group(1) + frames + m.group(4)
      filenames.append( filename )

    # Just the file name
    elif element.hasElement("FILENAME"):
      filenames.extend( element.getElement("FILENAME") )

    # We've seen some EDLs where the FROM CLIP NAME comment is just a name,
    # and the file is specified in SOURCE FILE.  In this case we want to treat
    # FROM CLIP NAME as the name for the track item.  For example:
    #
    # 017  A03514AT V     C        09:19:59:12 09:20:05:00 01:00:26:08 01:00:28:04
    # M2   A03514AT       075.0                09:19:59:12
    # * MOTION EFFECT AT SEQUENCE TC 01:00:26:08.
    # * FROM CLIP NAME:  B24A/1 (75.00 FPS)
    # * SOURCE FILE: A035_C001_0514AT
    elif element.hasElement(FROMCLIPNAME) and element.hasElement("SOURCEFILE"):
      clipname = element.getElement(FROMCLIPNAME)[0]
      filenames.extend( element.getElement("SOURCEFILE") )

    # FROM CLIP NAME isn't necessarily a file name, but we use it anyway
    elif element.hasElement(FROMCLIPNAME):     
      filenames.extend( element.getElement(FROMCLIPNAME) )

    elif element.hasElement('SOURCEFILE'):
      filenames.extend( element.getElement("SOURCEFILE") )
    elif element.hasElement(TOCLIPNAME):
      filenames.extend( element.getElement(TOCLIPNAME) )
    else:
      filenames.append(element.name())


    numtracks = 0
    if element.mode().hasVideo():
      numtracks += 1

    # The element can have audio in two ways, either with an explicit audio edit type (A, AA, etc) or
    # with the NONE edit type and the addition AUD entry  specifying 3 and/or 4. The latter case is
    # handled with an integer array in the optional AUD element.
    # The AUD element takes precedence.
    if element.hasElement("AUD"):
      numtracks += len(element.getElement("AUD"))
    elif element.mode().hasAudio():
      numtracks += element.mode().numAudioChannels()

    # If there was only a FROM CLIP NAME element, it might or might not be a file name.
    # If it's not, then set the clip name directly, otherwise it goes through the clip naming code,
    # which might do the wrong thing.  For example: '* FROM CLIP NAME: i_lx_110_bg_v1 (highlight 1)'
    # gets mangled.
    if not clipname and not isFileName(filenames[0]):
      clipname = filenames[0]
    # Strip whitespace
    if clipname:
      clipname = clipname.strip()

    # Clean up file names
    filenames = list(map( cleanupFileName, filenames ))

    while len(filenames) < numtracks:
      filenames.append(filenames[0])

    #debug( "FnEdlImporter.extractFilenames " + str(element) )
    #for filename in filenames:
    #  debug( "  file name: " + filename )

    return  filenames, clipname
  
    
  def createClipAndMedia(self, element, mediaDict, trackDict):
    fps = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerate)
    clipIds = list()
    clipId = None
    videoClipId = None

    # Initialise the first track index to 0 assuming a video track.
    index = VIDEO1

    # Use Video 2 for Key foreground elements
    if element.effectfield().isKeyIn():
      index = VIDEO2
    
    if not element.mode().hasVideo():
      # This isn't actually a video track so set the first track index to the appropriate value.
      # If there's an AUD element then we need to start at 3 or 4, depending on the 0th entry in the
      # list of channels. Otherwise we've got a regular mono or stereo track and should start at 1.
      if element.hasElement("AUD"):
        index = element.getElement("AUD")[0]
      else:
        index = 1
    
    #debug( "FnEdlImporter.createClipAndMedia " + str(element) + "index: " + str(index) )

    filenames, clipname = self.extractFilenamesAndClipName(element)

    # Extract any DLEDL START TC: element. This overrides the start timecode of the video clip. Looks like:
    # DLEDL; START TC: 00:00:00:04
    startTC = None
    if element.hasElement(STARTTC):
      startTC = element.getElement(STARTTC)[0].toFrames(fps)

    for filename in filenames:

      if not index < len(trackDict):
        debug( "FnEdlImporter.createClipAndMedia out of range index: " + str(index) + " " + str(len(trackDict)) )
        break

      # This assumes that filenames are ordered [video, audio, audio, audio]
      # This is a safe assumption for DLEDL.
      track = trackDict[index]
      trackId = track.getTrackId()

      #debug( "EdlImporter.createClipAndMedia index: " + str(index) + " track id: " + str(trackId) )

      speed, srcDuration = self.getTrackItemSpeedAndDuration( element )

      # Add new clip (track item)
      clipData = self.getClipData(clipname, element, speed, track.getTrackType(), startTC)
      clipId = FnCyclone.addClip(parentTrack = trackId, data = clipData )

      if index == VIDEO1:
        videoClipId = clipId

      clipIds.append(clipId)

      mediaidentifier = filename + str(element.srcEntry()) + str(element.srcExit()) + str(srcDuration)

      #debug( "FnEdlImporter.createClipAndMedia adding media: " + mediaidentifier )
      
      mediaId = -1      
      if mediaidentifier in mediaDict:
        # Media Already Exists
        mediaId = mediaDict[mediaidentifier]
        
      else:
        # New Media
        mediaId = mediaDict[mediaidentifier] = FnCyclone.addMedia(data = self.getMediaData(filename, element, srcDuration, startTC))
      
      # Pair the clip and the media
      FnCyclone.setClipMediaByTimecode(clip = clipId, media = mediaId)

      index += 1

    if len(clipIds) > 1:
      FnCyclone.addClipGroup(clipIds)

    return videoClipId
  
  def createTransition(self, prevelement, element, clipDict):
    fps = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerate)
    # Assuming this is a disolve, the effect paramter is the transition duration.    
    duration = element.effectfield().effectparameter()

    inClipId = FnCyclone.kClipInvalid
    outClipId = FnCyclone.kClipInvalid
    inDuration = 0
    outDuration = 0

    #debug( "createTransition" )
    #debug( "  prev: " + str(prevelement) )
    #debug( "  current: " + str(element) )

    # FROM Clip is blank    
    if not prevelement or prevelement.isBlank():
      outDuration = duration
      outClipId = clipDict[element]
      # Both Elements cannot be blank
      if element.isBlank():
        info("Error : Invalid Transition from %s to %s", prevelement.editId(), element.editId())
    # TO Clip is blank
    elif element.isBlank():
      inDuration = duration
      inClipId = clipDict[prevelement]
    else:
      outDuration = duration / 2
      outClipId = clipDict[element]
      inDuration = duration / 2
      inClipId = clipDict[prevelement]

    # EDL does not support asymetric transitions (AFAIK)
    data = { FnCyclone.kTransitionInDuration : inDuration , FnCyclone.kTransitionOutDuration : outDuration, FnCyclone.kTransitionExclusive : 1}
    FnCyclone.addTransition(inClip = inClipId, outClip = outClipId, data = data)

  @staticmethod
  def prepassCheckKeyEvent(element, eventElements):
    """
    Handle Key events.  For example:
    
    006  001      V     C        00:01:08:22 00:01:09:18 00:00:03:23 00:00:04:19
    006  001      V     K B      00:01:09:18 00:01:10:07 00:00:04:19 00:00:05:08
    006  001      V     K    000 00:01:08:22 00:01:09:11 00:00:04:19 00:00:05:08
    * FROM CLIP NAME: C003_007_3010_04.mov
    * KEY CLIP NAME: C003_007_3010_04.mov 
    
    The initial Cut line is optional.  The second line is the Key Background.  Third line is 
    the Key In element, which places a clip on a second track.

    We need to a) move FROMCLIPNAME from the Key In element to the background and cut elements, 
    b) rename KEYCLIPNAME to FROMCLIPNAME for the Key In element.
    """
    if element.effectfield().isKeyIn():

      # We must have a preceding Key Background event
      if not eventElements or not eventElements[-1].effectfield().isKeyBackground():
        raise Exception("EdlImporter.prepassCheckKeyEvent Key events in unexpected order!")

      # We must have a KEYCLIPNAME
      if not element.hasElement(KEYCLIPNAME):
        raise Exception("EdlImporter.prepassCheckKeyEvent key event missing KEY CLIP NAME!")

      # Move FROMCLIPNAME to previous elements
      if element.hasElement(FROMCLIPNAME):
        fromClip = element.getElement(FROMCLIPNAME)
        for e in eventElements:
          if not e.hasElement(FROMCLIPNAME):
            e.addElement( NamedElement(FROMCLIPNAME, fromClip) )
        element.removeElement(FROMCLIPNAME)

      # Rename KEYCLIPNAME to FROMCLIPNAME
      keyClip = element.getElement(KEYCLIPNAME)
      element.addElement( NamedElement(FROMCLIPNAME, keyClip) )


  def prepass(self, edl):
    prevelement = None
    eventcount = 0

    currentEventElements = []
        
    # Process elements
    for element in edl:
      if isinstance(element, NamedElement):
        # Look for the EDL title
        if element.key() == 'TITLE':
          self.__title = element.val()

      if isinstance(element, EditDecision):
        eventcount += 1

        #debug( "EdlImporter.prepass processing element: " + str(element) )

        # While modifying these elements, we need to check that we're not giving an
        # edit two FROMCLIPNAMEs.  There are some (seemingly malformed) EDLs which
        # cause problems here, but we need to make sure that a TrackItem can be created
        # if at all possible.

        # If an element has FROMCLIPNAME and TOCLIPNAME move the FROMCLIPNAME to the
        # previous element
        if element.hasElement(TOCLIPNAME) and element.hasElement(FROMCLIPNAME):        
          if prevelement:
            #debug( "reshuffling clip data" )
            fromclipvalues = element.getElement(FROMCLIPNAME)
            if not prevelement.hasElement(FROMCLIPNAME):
              prevelement.addElement( NamedElement(FROMCLIPNAME, fromclipvalues) )
            element.removeElement( FROMCLIPNAME )
        # If an element is blank but has a FROMCLIPNAME, it's a fade out. Move it to the previous element.
        elif element.isBlank() and element.hasElement(FROMCLIPNAME) and prevelement:
          if not prevelement.hasElement(FROMCLIPNAME):
            prevelement.addElement( NamedElement(FROMCLIPNAME, element.getElement(FROMCLIPNAME)) )
            element.removeElement(FROMCLIPNAME)
          else:
            # If we seem to have a FROMCLIPNAME for a blank edit, treat it as non-blank
            element.isBlank = (lambda: False) 
        else:
          EdlImporter.prepassCheckKeyEvent(element, currentEventElements)

        prevelement = element

        # Keep elements from the current event so we can handle Key events properly
        if not currentEventElements or currentEventElements[0].editId() == element.editId():
          currentEventElements.append(element)
        else:
          currentEventElements = [ element ]
        
    # Remove zero length elements
    removeList = []
    for listElement in edl:
      if isinstance(listElement, EditDecision):
        if listElement.srcEntry().isEqual(listElement.srcExit()):
          #debug( "LIST ELEMENT" )
          #debug( listElement )
          removeList.append(listElement)
    for removeElement in removeList:
      edl.remove(removeElement)        

    prevelement = None
    for element in reversed(edl):
      if isinstance(element, RetimeElement):
        debug( "prepass Found retime: " + str(element) )
        if prevelement:
          info( "Warning: M2 command not matched", prevelement.getSource() )
        prevelement = element

      if prevelement and isinstance(element, EditDecision):
        # Some EDLs do not have the source in on the M2 line, so patch in the element's source in.
        if prevelement.srcEntry() is None:
          prevelement.setSrcEntry(element.srcEntry())
        if prevelement.matches(element):
          debug( "prepass adding retime to element: " + str(element) )
          element.setRetime(prevelement.framerate(), prevelement.srcEntry())
          element.setSource(element.getSource() + prevelement.getSource())
          prevelement = None
        else:
          debug( "prepass retime doesn't match element" )

    if eventcount == 0:
      raise Exception("EdlImporter.prepass Invalid or Empty File")
  
  def importFile(self, fileName):
    """Return true if file is succesfully parsed"""
    #debug( "parseFile (" + fileName + ")\n" )

    fps = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerate)
    samplerate = FnCyclone.getImportOption(name = FnCyclone.kOptionSamplerate)
    isNtsc = FnCyclone.getImportOption(name = FnCyclone.kOptionFramerateIsNtsc)
    dropFrame = FnCyclone.getImportOption(name = FnCyclone.kOptionDropFrame)
    

    try:       
      edl = ParseEDL(fileName)
      
      self.prepass(edl)

      if not self.__title:
        self.__title = os.path.splitext(os.path.basename(fileName))[0]

      timelineProperties = { FnCyclone.kTimelineName : self.__title, 
                             FnCyclone.kTimelineFramerate : fps, 
                             FnCyclone.kTimelineFramerateIsNtsc : isNtsc,
                             FnCyclone.kTimelineSamplerate : samplerate,
                             FnCyclone.kTimelineDropFrameTimecode : dropFrame }

      timelineId = FnCyclone.addSequence(data = timelineProperties)

      # Keep a record of media added to avoid duplicates
      mediaDict = dict()
      clipDict = dict()
      
      trackDict = { VIDEO1 : track(-1, FnCyclone.kVideo, timelineId, self.__title + ' V1', fileName),
                    VIDEO2 : track(-1, FnCyclone.kVideo, timelineId, self.__title + ' V2', fileName),
                    AUDIO1 : track(-1, FnCyclone.kAudio, timelineId, self.__title + ' A1', fileName),
                    AUDIO2 : track(-1, FnCyclone.kAudio, timelineId, self.__title + ' A2', fileName),
                    AUDIO3 : track(-1, FnCyclone.kAudio, timelineId, self.__title + ' A3', fileName),
                    AUDIO4 : track(-1, FnCyclone.kAudio, timelineId, self.__title + ' A4', fileName) }

     
      previouselement = None
      for element in edl:
        try:
          if isinstance(element, EditDecision):
            #debug( "importFile element: " + str(element) + " isBlank: " + str(element.isBlank()) )
            if not element.isBlank():
              clipid = self.createClipAndMedia(element, mediaDict, trackDict)
              if clipid:
                clipDict[element] = clipid
            hasVideo = element.mode().hasVideo()
            if element.effectfield().effect() == EffectField.DISSOLVE and hasVideo:            
              self.createTransition(previouselement, element, clipDict)
            if hasVideo:
              previouselement = element
        except Exception as e:
          hiero.core.log.exception("Exception handling element\n", element.getSource(), '\n', e)
    except Exception as e:
      hiero.core.log.exception( e )
      raise e
    finally:
      sys.stdout.flush() # DM - On my system this seems to be necessary otherwise any output to console gets buffered indefinitely
    
    return True
