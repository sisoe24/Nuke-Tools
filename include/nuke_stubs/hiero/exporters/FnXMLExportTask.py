# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os
import os.path
import math
import xml.etree.ElementTree as etree
from xml.sax.saxutils import escape
from urllib.parse import unquote_plus
import hiero.core

from hiero.core import Timecode
from hiero.core import TimeBase
from hiero.core import Keys
from hiero.core import Sequence
from hiero.core import Clip
from hiero.core.FnExporterBase import mediaSourceExportReadPath
from hiero.core import util


# ...because "etree.tostring(rootElem, pretty_print = True)" doesn't work!
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# TODO: For now we just replace spaces with %20, need a way of 
# doing this properly.  I tried using urllib, but importing
# it seemed to cause some problems.
def encodeUrl(url):
  encoded = url.replace(' ', '%20')
  return encoded

def getPathUrl(source):
  prefix = ''

  path = mediaSourceExportReadPath(source, True)
  
  if path.find('/') is not -1:
    prefix = 'file://localhost' if path.startswith('/') else 'file://localhost/'

  return prefix + encodeUrl(path)

def addBoolElement(parent, name, value):
  """ Create a child element of parent with name, and the text set to TRUE or FALSE. """
  elem = etree.SubElement(parent, name)
  elem.text = "TRUE" if value else "FALSE"
  return elem


class XMLExportTask(hiero.core.TaskBase):

  def __init__(self, initDict):
    """Initialize"""
    hiero.core.TaskBase.__init__(self, initDict)

    # only supported type!
    sequence = self._item

    # everything within a sequence has the same timebase
    self._framerate = sequence.framerate();

  def name(self):
    return str(type(self))

  # <rate>
  #   <ntsc>...</ntsc>
  #   <timebase>...</timebase>
  # </rate>
  def addRateElem(self, parentElem, timebase):
    rateElem = etree.SubElement(parentElem, "rate")
    addBoolElement(rateElem, "ntsc", timebase.isNTSC())
    etree.SubElement(rateElem, "timebase").text = str(timebase.toInt())

  # <timecode>
  #   <rate>...</rate>
  #   <string>...</string>
  #   <frame>...</frame>
  #   <displayformat>...</displayformat>
  #   <reel><name>...</name></reel>
  # </timecode>
  def addTimecodeElem(self, parentElem, timeBase, timecodeStart, reel=None):
    timecodeElem = etree.SubElement(parentElem, "timecode")
    self.addRateElem(timecodeElem, timeBase)

    etree.SubElement(timecodeElem, "frame").text = str(timecodeStart)
    etree.SubElement(timecodeElem, "displayformat").text = "NDF"
    etree.SubElement(timecodeElem, "string").text = hiero.core.Timecode.timeToString(timecodeStart, timeBase, hiero.core.Timecode.kDisplayTimecode)

    if reel:
      reelElem = etree.SubElement(timecodeElem, "reel")
      etree.SubElement(reelElem, "name").text = reel

  def addElementFromMetadata(self, parentElem, name, metadata, key):
    if metadata.hasKey(key):
      etree.SubElement(parentElem, name).text = metadata.value(key)

  # Hiero puts source times in samples for wav files, convert to frames
  # for export.
  def hasTimesInSamples(self, source):
    fileName = source.filename().lower()
    return fileName.endswith(".wav")

  def samplesToFrames(self, source, samples):
		# If the media hasn't been conformed, it may not have the sample rate metadata set
    sampleRate = hiero.core.TimeBase.fromString(source.metadata().value(Keys.kSourceSamplerate)).toFloat()
    return int(float(samples) / sampleRate * self._framerate.toFloat()) if sampleRate > 0. else samples

  def sourceTime(self, source, time):
    return self.samplesToFrames(source, time) if self.hasTimesInSamples(source) else time

  def addFileMediaElement(self, parentElem, source):
    metadata = source.metadata()
    
    mediaElem = etree.SubElement(parentElem, "media")

    if source.hasVideo():
      videoElem = etree.SubElement(mediaElem, "video")
      etree.SubElement(videoElem, "duration").text = str(self.sourceTime(source, source.duration()))
      sampleCharacteristicsElem = etree.SubElement(videoElem, "samplecharacteristics")
      etree.SubElement(sampleCharacteristicsElem, "width").text = str(source.width())
      etree.SubElement(sampleCharacteristicsElem, "height").text = str(source.height())
    
    if source.hasAudio():
      audioElem = etree.SubElement(mediaElem, "audio")
      self.addElementFromMetadata(audioElem, "channelcount", metadata, Keys.kSourceNumAudioChannels)
      sampleCharacteristicsElem = etree.SubElement(audioElem, "samplecharacteristics")
      self.addElementFromMetadata(sampleCharacteristicsElem, "depth", metadata, Keys.kSourceAudioBitDepth)
      self.addElementFromMetadata(sampleCharacteristicsElem, "samplerate", metadata, Keys.kSourceSamplerate)

  # <file id="...">
  #   <name>...</name>
  #   <pathurl>...</pathurl>
  #   <duration>...</duration>
  #   <rate>...</rate>
  #   <width>...</width>
  #   <height>...</height>
  # </file>
  def addFileElem(self, parentElem, source, clip):
    frameRate = clip.framerate()

    fileElem = etree.SubElement( parentElem, "file", id=clip.name() )
    etree.SubElement(fileElem, "name").text = clip.name()
    if source.isMediaPresent():
      etree.SubElement(fileElem, "pathurl").text = getPathUrl(source)
    etree.SubElement(fileElem, "duration").text = str(self.sourceTime(source, source.duration()))
    self.addRateElem(fileElem, frameRate)
    if source.isMediaPresent():
      if source.hasVideo():
        etree.SubElement(fileElem, "width").text = str(source.width())
        etree.SubElement(fileElem, "height").text = str(source.height())
      self.addFileMediaElement(fileElem, source)

    reel = None
    if hiero.core.Keys.kSourceReelId in source.metadata():
      reel = source.metadata()[hiero.core.Keys.kSourceReelId]

    self.addTimecodeElem( fileElem, frameRate, source.timecodeStart(), reel )

  #	<filter>
  #		<effect>
  #			<name>Time Remap</name>
  #			<effectid>timeremap</effectid>
  #			<effectcategory>motion</effectcategory>
  #			<effecttype>motion</effecttype>
  #			<mediatype>video</mediatype>
  #			<parameter>
  #				<parameterid>speed</parameterid>
  #				<name>speed</name>
  #				<value>...</value>
  #			</parameter>
  #		</effect>
  #	</filter>
  def addRetime(self, parentElem, retimeFactor):

    # For some reason, FCP ignores a retime of exactly -1
    # This is a clumsy workaround which will cause a frame slip after
    # 10^10 frames (around 12 years of footage).
    if retimeFactor == -1:
      retimeFactor = -1.0000000001

    filterElem = etree.SubElement(parentElem, "filter")
    effectElem = etree.SubElement(filterElem, "effect")

    etree.SubElement(effectElem, "name").text = "Time Remap"
    etree.SubElement(effectElem, "effectid").text = "timeremap"
    etree.SubElement(effectElem, "effectcategory").text = "motion"
    etree.SubElement(effectElem, "effecttype").text = "motion"
    etree.SubElement(effectElem, "mediatype").text = "video"

    parameterElem = etree.SubElement(effectElem, "parameter")
    etree.SubElement(parameterElem, "name").text = "speed"
    etree.SubElement(parameterElem, "parameterid").text = "speed"
    etree.SubElement(parameterElem, "value").text = str(abs(retimeFactor)*100)

    if retimeFactor < 0:
      parameterElem = etree.SubElement(effectElem, "parameter")
      etree.SubElement(parameterElem, "parameterid").text = "reverse"
      etree.SubElement(parameterElem, "name").text = "reverse"
      etree.SubElement(parameterElem, "value").text = "TRUE"


  # <effect>
  #   <name>...</effectid>
  #   <effectid>...</effectid>
  #   <effectcategory>...</effectcategory>
  #   <effecttype>...</effecttype>
  #   <mediatype>...</mediatype>
  #   <wipecode>...</wipecode>
  #   <wipeaccuracy>...</wipeaccuracy>
  #   <startratio>...</startratio>
  #   <endratio>...</endratio>
  #   <reverse>...</reverse>
  # </effect>
  def addEffectElem(self, parentElem, transition):
    effectElem = etree.SubElement(parentElem, "effect")
    etree.SubElement(effectElem, "name").text = "Cross Disolve"
    etree.SubElement(effectElem, "effectid").text = "Cross Dissolve"
    etree.SubElement(effectElem, "effectcategory").text = "Dissolve"
    etree.SubElement(effectElem, "effecttype").text = "transition"
    etree.SubElement(effectElem, "mediatype").text = "video"
    etree.SubElement(effectElem, "wipecode").text = "0"
    etree.SubElement(effectElem, "wipeaccuracy").text = "100"
    etree.SubElement(effectElem, "startratio").text = "0"
    etree.SubElement(effectElem, "endratio").text = "1"
    etree.SubElement(effectElem, "reverse").text = "FALSE"

  # <transitionitem>
  #		<rate>...</rate>
  #		<start>...</start>
  #		<end>...</end>
  #		<alignment>...</alignment>
  #		<effect>...</effect>
  #	</transitionitem>
  def addDissolve(self, parentElem, transition):
    transitionElem = etree.SubElement(parentElem, "transitionitem")
    self.addRateElem(transitionElem, self._framerate)
    etree.SubElement(transitionElem, "start").text = str(transition.timelineIn())
    etree.SubElement(transitionElem, "end").text = str(transition.timelineOut()+1)
    etree.SubElement(transitionElem, "alignment").text = "center"
    self.addEffectElem(transitionElem, transition)

  def addFadeIn(self, parentElem, transition):
    transitionElem = etree.SubElement(parentElem, "transitionitem")
    etree.SubElement(transitionElem, "start").text = str(transition.timelineIn())
    etree.SubElement(transitionElem, "end").text = str(transition.timelineOut()+1)
    etree.SubElement(transitionElem, "alignment").text = "start"
    self.addEffectElem(transitionElem, transition)

  def addFadeOut(self, parentElem, transition):
    transitionElem = etree.SubElement(parentElem, "transitionitem")
    etree.SubElement(transitionElem, "start").text = str(transition.timelineIn())
    etree.SubElement(transitionElem, "end").text = str(transition.timelineOut()+1)
    etree.SubElement(transitionElem, "alignment").text = "end"
    self.addEffectElem(transitionElem, transition)

  # does transition cross over time?
  def isTransitionCrossing(self, transition, time):
    if not transition:
      return False
    if transition.timelineIn() < time and transition.timelineOut()+1 > time:
      return True
    return False

  # <clipitem>
  #   <name>...</name>
  #   <duration>...</duration>
  #   <rate>...</rate>
  #   <in>...</in>
  #   <out>...</out>
  #   <start>...</start>
  #   <end>...</end>
  #   [<file>...</file>]
  # </clipitem>
  def addClipItemElem(self, parentElem, trackitem):
    clip = trackitem.source()

    timelineOffset = self._sequence.timelineOffset()

    playbackSpeed = trackitem.playbackSpeed()
    # Retimes may not be less than 0.25% in FCP
    # An alternative must be provided for freeze frames of more than 16 seconds.
    if (abs(playbackSpeed) < 0.0025):
      playbackSpeed = 0.0025 if playbackSpeed >= 0 else -0.0025
    inTrans = trackitem.inTransition()
    outTrans = trackitem.outTransition()

    inDissolve = False
    outDissolve = False

    if outTrans:
      if self.isTransitionCrossing(outTrans, trackitem.timelineOut() + 1):
        outDissolve = True

    if inTrans:
      if self.isTransitionCrossing(inTrans, trackitem.timelineIn()):
        inDissolve = True

        # xml abuse - element order matters! transitionitems must be before/after relevant clipitems
        self.addDissolve(parentElem, inTrans)
      else:
        self.addFadeIn(parentElem, inTrans)

    clipElem = etree.SubElement(parentElem, "clipitem")

    clipDuration = self.sourceTime(clip.mediaSource(), clip.duration())

    # Duration is the full length of the retimed source clip
    duration = clipDuration
    duration /= abs(playbackSpeed)
    # FCP requires integer values
    # If the duration runs over by a partial frame then the frame is available
    # to display.
    duration = math.ceil(duration)

    etree.SubElement(clipElem, "name").text = clip.name()
    etree.SubElement(clipElem, "duration").text = str(duration)
    self.addRateElem(clipElem, self._framerate)
    addBoolElement(clipElem, "enabled", trackitem.isEnabled())

    # trackitem.sourceIn() is the number of frames into the source at which
    # this track item starts.  FCP treats the whole clip as being run at
    # playback speed, and records the number of frames into the retimed clip at
    # which the track item starts.  The number of frames into the retimed clip
    # is the number of frames into the source clip divided by the playback speed.
    srcIn = trackitem.sourceIn()

    # If the clip is reversed then the frame number is relative to the end of
    # the clip. clipDuration is the duration of the whole clip.  For instance,
    # a clip of frames from 0 to 59 will have duration 60.  When the clip is
    # reversed frame 0 will become frame 59, frame 1 will become frame 58, etc.
    srcIn /= abs(playbackSpeed)
    if playbackSpeed < 0.0:
      retimedClipDuration = clipDuration/ abs(playbackSpeed)
      srcIn = (retimedClipDuration-1) - srcIn
    if srcIn < 0:
        srcIn = 0.0
    srcOut = srcIn + trackitem.duration()

    # FCP requires integer values
    # TODO: This code chooses which frame is the frame to display.  Because FCP
    # considers all frames to be relative to a complete retimed source, the
    # point at which frames change may still be incorrect.  We need to add
    # some kind of anchor point so that these values become exact frames in the
    # retimed source.
    # For the moment, I think that this is most likely to select the correct frame.
    srcIn = round(srcIn)
    srcOut = round(srcOut)

    dstIn = timelineOffset + trackitem.timelineIn()
    dstOut = dstIn + trackitem.duration()

    # offset source in and outs to match fcp convention
    if outDissolve and inDissolve:
      srcIn = srcOut - (dstOut - inTrans.timelineIn())
      srcOut = srcIn + (1 + outTrans.timelineOut() - inTrans.timelineIn())
    elif outDissolve:
      srcOut = srcIn + (outTrans.timelineOut() + 1 - dstIn)
    elif inDissolve:
      srcIn = srcOut - (dstOut - inTrans.timelineIn())

    # fcp uses -1 to mean matched against a transition
    # sequence times are inferred from transition times and source in/out time range
    if outTrans:
      dstOut = -1
    if inTrans:
      dstIn = -1

    etree.SubElement(clipElem, "in").text =     str(srcIn)
    etree.SubElement(clipElem, "out").text =    str(srcOut)
    etree.SubElement(clipElem, "start").text =  str(dstIn)
    etree.SubElement(clipElem, "end").text =    str(dstOut)

    source = trackitem.source().mediaSource()
    if source is not None and len(source.firstpath()) > 0:
      self.addFileElem(clipElem, source, clip)

    if self._preset.properties()["includeMarkers"]:
      markers = [tag for tag in clip.tags() if tag.visible()]
      for marker in markers:
        markerElem = etree.SubElement(clipElem, "marker")
        self.addMarker(markerElem, marker)      

    if playbackSpeed != 1.0:
      self.addRetime(clipElem, playbackSpeed)

    # xml abuse - element order matters! if out transition is a fade-out, add it to the parent element
    if outTrans and trackitem.timelineOut() == outTrans.timelineOut():
      self.addFadeOut(parentElem, outTrans)

  # current nesting assumption: sub-sequences are clips (ie. limited to a single track with a single source trackitem)
  def addSubSequence(self, parentElem, sequence):
    for track in sequence.videoTracks():
      for trackitem in track:
        self.addTrackItem(parentElem, trackitem)

  # current nesting assumption: sub-sequences are clips (ie. limited to a single track with a single source trackitem)
  def addTrackItem(self, parentElem, trackitem):
    if isinstance(trackitem.source(), hiero.core.Sequence):
      self.addSubSequence(parentElem, trackitem.source())
    elif isinstance(trackitem.source(), hiero.core.Clip):
      self.addClipItemElem(parentElem, trackitem)

  # <track>
  #   <name>...</name>
  #   [<clipitem>...</clipitem>]*
  # </track>
  def addVideoTracks(self, parentElem, sequence):
    for track in sequence.videoTracks():
      trackElem = etree.SubElement(parentElem, "track")
      etree.SubElement(trackElem, "name").text = track.name()
      for trackitem in track:
        self.addTrackItem(trackElem, trackitem)

  # TODO We need to include information about audio channels,
  # but Hiero doesn't yet deal with that properly
  def addAudioTracks(self, parentElem, sequence):
    for track in sequence.audioTracks():
      trackElem = etree.SubElement(parentElem, "track")
      etree.SubElement(trackElem, "name").text = track.name()
      for trackitem in track:
        self.addTrackItem(trackElem, trackitem)

  # Add format element for audio.  The depth and samplerate are currently hardcoded.
  # <format>
  #   <samplecharacteristics>
  #     <depth>..</depth>
  #     <samplerate>..</samplerate>
  #   </samplecharacteristics>
  # </format>
  def addAudioFormat(self, parentElem, sequence):
    formatElem = etree.SubElement(parentElem, "format")
    scElem = etree.SubElement(formatElem, "samplecharacteristics")
    etree.SubElement(scElem, "depth").text = "16"
    etree.SubElement(scElem, "samplerate").text = "48000"

  def addVideoFormat(self, parentElem, sequence):
    formatElem = etree.SubElement(parentElem, "format")
    scElem = etree.SubElement(formatElem, "samplecharacteristics")
    format = sequence.format()
    etree.SubElement(scElem, "width").text = str(format.width())
    etree.SubElement(scElem, "height").text = str(format.height())
    self.addRateElem(scElem, sequence.framerate())

  #    <marker>
  #      <comment>This is shot10</comment>
  #      <name>shot10</name>
  #      <in>24</in>
  #      <out>-1</out>
  #    </marker>    
  def addMarker(self, parentElem, marker):
    # unicode(unquote_plus(escape(str(marker.name()))).decode('utf8'))
    comment = str(unquote_plus(escape(str(marker.note()))).decode('utf8'))
    name = str(unquote_plus(escape(str(marker.name()))).decode('utf8'))

    if len(comment)>0:
      etree.SubElement(parentElem, "comment").text = comment

    if len(name)>0:
      etree.SubElement(parentElem, "name").text = name

    etree.SubElement(parentElem, "in").text = str(int(marker.inTime()))
    etree.SubElement(parentElem, "out").text = str(int(marker.outTime()))    

  # <sequence>
  #   <name>...</name>
  #   <duration>...</duration>
  #   <rate>...</rate>
  #   <timecode>...</timecode>
  #   <media>
  #     <video>...</video>
  #   </media>
  # </sequence>
  def addSequenceElem(self, parentElem, sequence):
    sequenceElem = etree.SubElement(parentElem, "sequence", id=sequence.name())
    etree.SubElement(sequenceElem, "name").text = sequence.name()
    etree.SubElement(sequenceElem, "duration").text = str(sequence.duration())
    self.addRateElem( sequenceElem, self._framerate )
    self.addTimecodeElem( sequenceElem, self._framerate, self._sequence.timecodeStart() )
    mediaElem = etree.SubElement(sequenceElem, "media")
    videoElem = etree.SubElement(mediaElem, "video")
    self.addVideoFormat( videoElem, sequence )
    self.addVideoTracks( videoElem, sequence )

    if self._preset.supportsAudio():
      audioElem = etree.SubElement(mediaElem, "audio")
      self.addAudioFormat( audioElem, sequence )
      self.addAudioTracks( audioElem, sequence )

    if self._preset.properties()["includeMarkers"]:
      markers = [tag for tag in sequence.tags() if tag.visible() and tag.outTime()>-1]
      for marker in markers:
        markerElem = etree.SubElement(sequenceElem, "marker")
        self.addMarker(markerElem, marker)

  # <xmeml version="5">
  #   <sequence>...</sequence>
  # </xmeml>
  def createXMEML(self):
    self._rootElem = etree.Element("xmeml", version="5")
    self.addSequenceElem(self._rootElem, self._sequence)

  def startTask(self):
    self.createXMEML()

  def taskStep(self):
    return False

  def finishTask(self):
    # Open file and write xml string
    try:
      exportPath = self.resolvedExportPath()
      # Check file extension
      if not exportPath.lower().endswith(".xml"):
        exportPath += ".xml"

      indent( self._rootElem )

      # check export root exists
      dir = os.path.dirname(exportPath)
      util.filesystem.makeDirs(dir)

      # open and write to file
      with util.filesystem.openFile(exportPath, 'wb') as file:
        docType = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE xmeml>\n"
        file.write(docType)
        xml = etree.tostring(self._rootElem, encoding="UTF-8")
        file.write(xml)

    # Catch all exceptions and log error
    except Exception as e:
      self.setError( "failed to write file %s\n%s" % (exportPath, e) )

    hiero.core.TaskBase.finishTask(self)

  def forcedAbort(self):
    pass

class XMLExportPreset(hiero.core.TaskPresetBase):
  def __init__(self, name, properties):
    """Initialise presets to default values"""
    hiero.core.TaskPresetBase.__init__(self, XMLExportTask, name)

    self.properties()["includeMarkers"] = False
    self.properties().update(properties)

  def supportedItems(self):
    return hiero.core.TaskPresetBase.kSequence
    
  def addCustomResolveEntries(self, resolver):
    resolver.addResolver("{ext}", "Extension of the file to be output", lambda keyword, task: "xml")

  def supportsAudio(self):
    return True

hiero.core.taskRegistry.registerTask(XMLExportPreset, XMLExportTask)


