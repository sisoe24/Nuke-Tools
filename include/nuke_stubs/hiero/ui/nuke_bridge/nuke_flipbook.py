# Copyright (c) 2010 The Foundry Visionmongers Ltd.  All Rights Reserved.
import platform
import sys
import os.path
import re
import _thread
import nuke_internal as nuke
import subprocess
import nukescripts
import nukescripts.flipbooking as flipbooking
import time
import ocionuke

import hiero.ui
import hiero.core
from hiero.core import log
from hiero.core import util
from hiero.ui import findMenuAction
from hiero.ui import menuBar

from . flipbook_common import (getColorspaceFromNode,
                               getIsUsingNukeColorspaces,
                               getRawViewerLUT,
                               mapViewerLUTString,
                               getOCIOConfigPath,
                               kNukeFlipbookCapabilities)

gFlipbookViewer = None

################################################################################
# The Nuke flipbook
################################################################################


#TODO move these classes into their own module. Currently not possible
# without adding a circular dependency or duplicating getColorspaceFromNode
class LUTCorrection(object):
  '''
  Base class for objects which correct the LUT of a flipbook render.
  '''
  def __init__(self, manager):
    self._manager = manager


class CustomLUTCorrection(LUTCorrection):
  '''
  LUT correction for when when using a custom OCIO config is being used.
  '''
  def applyLUT(self, videoTrack, first, last, inColorspace):
    
    # An empty string is passed in when the viewer colorspace is burnt into intermediate renders.
    if not inColorspace:
      return
  
    rootNode = nuke.root()
    
    # We should only be applying the LUT correction at timeline render time if we're NOT using Nuke color
    # management, since that requires intermediate renders (as we know we're not using the nuke-default config),
    # see isLUTAvailableForNode.
    if not getIsUsingNukeColorspaces(rootNode):
      
      addColorspace = False
      
      workingSpace = ""
      if rootNode:

        # Firstly obtain the ocio config
        ocioconfig = ocionuke.config.getOCIOConfig()

        # If the colour space is a role then the knob should be set directly
        if ocioconfig.hasRole(inColorspace):
          addColorspace = True
        else:
          # OCIOColorSpace currently requires us to prepend the colorspace name with the family, if there is one.
          try:
            family = rootNode.getOCIOColorspaceFamily(inColorspace)
            addColorspace = True  # family may actually be legitimately empty
            if family:
              inColorspace = ("Colorspaces/%s/%s") % (family, inColorspace)
          except ValueError:
            print("  Error: inColorspace '" + str(inColorspace) + "' not found in config's colorspaces")
          except:
            print("  Error finding colorspace family")
        
        # We'll ensure the output colorspace OCIOColorSpace is the working space, as that's what the timeline
        # viewer expects.
        workingSpaceKnob = rootNode.knob("workingSpaceLUT")
        if workingSpaceKnob:
          workingSpace = workingSpaceKnob.value()

          # If the colour space is a role then the knob should be set directly
          if ocioconfig.hasRole(workingSpace):
            pass
          else:
            # As above, need to prepend the family if there is one.
            try:
              family = rootNode.getOCIOColorspaceFamily(workingSpace)
              if family:
                workingSpace = ("Colorspaces/%s/%s") % (family, workingSpace)
            except ValueError:
              print("  Error: working space '" + str(workingSpace) + "' not found in config's colorspaces")
            except:
              print("  Error finding working space family")

      if addColorspace:
        colorspaceEffect = self._manager.createEffectItem('OCIOColorSpace', first, last)
        colorspaceNode = colorspaceEffect.node()
        log.debug("Setting in_colorspace to %s" % inColorspace)
        colorspaceNode['in_colorspace'].setValue( inColorspace )
        if workingSpace:
          log.debug("Setting out_colorspace to %s" % workingSpace)
          colorspaceNode['out_colorspace'].setValue(workingSpace)
        
        videoTrack.addSubTrackItem( colorspaceEffect, 0 )


  def isLUTAvailableForNode(self, node):
  
    ret = True
    if node.Class() == "Read" or node.Class() == "Write":
    
      nodeColorspace = getColorspaceFromNode( node )
      rootNode = nuke.root()
      
      if getIsUsingNukeColorspaces(rootNode):
        # If the Read/Write nodes are using built-in Nuke colorspaces then even if we could happen to get a
        # match for nodeColorspace in the current config (which, remember, we know won't be nuke-default) there's
        # no guarantee it'll actually correspond to the right conversion.
        ret = False
      else:
        # Since OCIO color management is being used, the colorspace of the Read/Write node must be available in
        # the current config.
        ret = True

    return ret

class NukeDefaultLUTCorrection(LUTCorrection):
  '''
  LUT correction for when the default Nuke OCIO config is used.
  '''
  def applyLUT(self, videoTrack, first, last, inColorspace):
  
    shouldApplyColorTranform = inColorspace != "" and inColorspace != "linear"
    if shouldApplyColorTranform:
      colorspaceEffect = self._manager.createEffectItem('OCIOColorSpace', first, last)
      colorspaceNode = colorspaceEffect.node()
      colorspaceNode['in_colorspace'].setValue( inColorspace )

      # Ensure the output gets set to the current working space, as that's what the timeline viewer expects.
      rootNode = nuke.root()
      if rootNode:
        workingSpaceKnob = rootNode.knob("workingSpaceLUT")
        if workingSpaceKnob:
          workingSpace = workingSpaceKnob.value()
          colorspaceNode['out_colorspace'].setValue(workingSpace)

      videoTrack.addSubTrackItem( colorspaceEffect, 0 )


  def isLUTAvailableForNode(self, node):
    # The nuke-default config supports all the colourspace options availble in the
    # the read and write nodes.
    assert(node.Class() == "Read" or node.Class() == "Write")
    return True


class FlipbookNuke(flipbooking.FlipbookApplication):
  """The Nuke built in flipbook"""
  
  # Delimeter used to separate the input and output colorspace names when they're both stored in the
  # lut option (strictly speaking, the latter has the dislay and view, rather than the corresponding colorspace).
  # This is a deliberately verbose string to make it extremely unlikely it appears in an OCIO name (the
  # original code used '-' which happens to appear extensively in the ACES 1.0.1 config).
  # TODO This could be avoided by just storing them in separate fields in the options
  LUT_OUT_DELIM = "[Flipbook lut out]"
  
  def __init__(self):
    self._manager = hiero.core.FlipbookManager()

  def _createLUTCorrection(self):
    root = nuke.root()
    ocioConfigKnob = root.knob("OCIO_config")
    usingNukeDefault = ocioConfigKnob.value() == "nuke-default"
    return NukeDefaultLUTCorrection(self._manager) if usingNukeDefault else CustomLUTCorrection(self._manager)

  def isLUTAvailableForNode(self, node):
    # Since a single FlipbookNuke object is created and reused we can't just create/store a lutCorrection object in the __init__
    # as it'll be out of date if the user changes the config being used.
    lutCorrection = self._createLUTCorrection()
    return lutCorrection.isLUTAvailableForNode(node)

  def name(self):
    return 'Flipbook Viewer'

  def path(self):
    return nuke.env['ExecutablePath']

  def cacheDir(self):
    return nuke.value("preferences.DiskCachePath")
  
  def _updateWorkingSpace(self):
    """Helper to set the Flipbook's working space to match that of the root node."""
    rootNode = nuke.root()
    if rootNode:
      workingSpaceKnob = rootNode.knob("workingSpaceLUT")
      if workingSpaceKnob:
        self._manager.setWorkingSpace(workingSpaceKnob.value())

  def runFromNode(self, nodeToFlipbook, frameRanges, views, options):
    """ Execute the fipbook on a node.
    If the node is a AppendClip and all the inputs are Read nodes, the flipbook
    will be executed directly with the inputs filenames  instead of rendering 
    everything.
    """

    isAppendClipNode = nodeToFlipbook.Class() == 'AppendClip'
    if isAppendClipNode:
      # create a list of tuples with ( clip, inputColorspace )
      # the input colorspace is used to add a softeffect to
      # transform the colorspace of the correspongin file to
      # linear.
    
      self._manager.updateOCIOConfig( getOCIOConfigPath() )
      self._updateWorkingSpace()
      
      videoClips = []
      for index in range( nodeToFlipbook.inputs() ):
        inputNode = nodeToFlipbook.input( index )
        
        inputFilename = nuke.filename( inputNode )
        if inputFilename is None or inputFilename == "":
          raise RuntimeError("Cannot run a flipbook on '%s', expected to find a filename for input %d and there was none." % (nodeToFlipbook.fullName(), index))
        
        inputClip = self._manager.createClip(inputFilename) 
        inputColorspace = getColorspaceFromNode( inputNode )
        videoClips.append( (inputClip , inputColorspace ) )

      audioClip = self._getAudioClip( options )

      first = frameRanges.minFrame()
      last = frameRanges.maxFrame()
    
      self.flipbook( videoClips , audioClip , first , last , views, options )

    else:
      filename = nuke.filename(nodeToFlipbook)
      self.run(filename, frameRanges, views, options)


  def run(self, filename, frameRanges, views, options):
    if filename is None or filename == "":
      raise RuntimeError("Cannot run a flipbook on '%s', expected to find a filename and there was none." % (nodeToFlipbook.fullName(),))
    
    self._manager.updateOCIOConfig( getOCIOConfigPath() )
    self._updateWorkingSpace()

    audioClip = self._getAudioClip( options )

    videoClip = self._manager.createClip(filename) 
    videoClips = [ ( videoClip , self._getInputColorspace(options) ) , ]
    
    first = frameRanges.minFrame()
    last = frameRanges.maxFrame()

    self.flipbook( videoClips , audioClip , first , last , views, options )


  def flipbook(self, videoClips, audioClip, first, last, views, options):
    """ Flipbook a set of video clips.
    This method creates a sequence with all the video clips and the audio clip and plays it
    from first to last.
    @param videoClips: a list of tuples with ( clip, inputColorspace). The input colorspace
    for each clip is used to add a softeffect to correct the clip colorspace to linear to be
    @param audioClip: a audio clip to be added to the sequence
    @param first: defines the In position
    @param last: defines the Out position
    @param options: A dictionary of options to use.
    """

    if not self._clipsAreValid(videoClips, views, first, last):
      return

    name = options.get('nodeName', 'Flipbook' )

    log.debug("FlipbookNuke.flipbook", videoClips, audioClip, first, last)
    log.debug("FlipbookNuke.flipbook", "options = %s" % options )

    # figure out our options
    burnIn = options.get("burnIn",False)

    viewerLUT = self._getViewerLUT( options )

    # get first clip format to define the sequence's format.
    # In NC When creating a hiero.core.Format higher than HD
    # a ValueError exception will be raised.
    outputFormat = videoClips[0][0].format()

    buffer = 0
    if options.get('wipe', 'A') == "B":
      buffer = 1

    inputIsRaw = options.get("raw", False) 

    try:

      # Build and configure a new sequence
      newSequence = self._manager.createSequence( nuke.Root().fps() , outputFormat, views)

      startAtTime = 1 # nuke start at 1 so default value is 1
      # define clip start time if it is defined
      try:
        startAtTime = int(options['start_at'])
      except:
        # if start_at is not defined use the clip source start value
        singleClip = videoClips[0][0]
        startAtTime = singleClip.sourceIn() if singleClip.duration() > 1 else 1

      clipInitTime = startAtTime
      sequenceEndTime = 0
      for videoClip, inColorspace in videoClips:
        newSequence.addClip( videoClip , clipInitTime,  0 )
        
        sequenceEndTime = clipInitTime + videoClip.duration()
        
        log.debug("FlipbookNuke.flipbook clip %s added from %d to %d " % ( videoClip, clipInitTime, sequenceEndTime ) )

        clipInitTime = sequenceEndTime
     
      if audioClip:
        newSequence.addClip( audioClip, startAtTime )

      # define in and out points
      newSequence.setInTime( first )
      # trim out point
      # the - 1 is needed because to match nuke time the clip starts at frame 1
      # instead of frame 0 as usual hiero does.
      last = min( last , newSequence.duration() - 1 )
      newSequence.setOutTime( last )

      newSequence.setInOutEnabled( True )

      # add dissolve transition
      dissolveTime = options.get( 'crossDissolve' , 0 )
      self._addDissolveTransition( newSequence , dissolveTime )

      # add fadeIn/fadeOut Transitions
      fadeInTime = options.get( 'fadeIn' , 0 )
      fadeOutTime = options.get( 'fadeOut' , 0 )
      self._addFadeInFadeOutTransitions( newSequence , fadeInTime , fadeOutTime )

      if not inputIsRaw:
        self._applyLutCorrectionFromSequence( newSequence, videoClips )

     
      # show flipbook
      cv = hiero.ui.getFlipbook()

      # Make sure the flipbook is stopped before we do anything else.  There are some problems in the viewer API if it 
      # was already playing, which can lead to it either getting stopped when we want it to play, or increasing the playback speed.
      cv.stop()

      p = cv.player(buffer)
     
      wm = hiero.ui.windowManager()
      cv.setSequence( newSequence, buffer )  # Flipbook sequences are a special case that don't need adding to a bin/project before setting on a player.

      if buffer > 0:
        cv.wipeTool().setActive( True )

      log.debug("FlipbookNuke.flipbook set sequence", p.sequence())

      if burnIn:
        # We're burning the viewer transform into the render so we want to initialise the flipbook to apply a 'raw'
        # transform - it doesn't make sense to apply the view transform twice (the user can subsequently change the
        # viewer setting if they want).
        p.setLUT(getRawViewerLUT())
      elif viewerLUT:
        p.setLUT( viewerLUT )

      log.debug("FlipbookNuke.flipbook playing", p.sequence())
      wm.showWindow( cv.window() )

      nukeViewer = nuke.activeViewer()
      displayTimecode = False
      if nukeViewer:
        viewerNode = nukeViewer.node()
        if viewerNode:
          displayTimecode = viewerNode['show_timecode'].value()
      cv.setDisplayTimecode(displayTimecode)

      cv.setTime( first )
      cv.play()

    except Exception as e:
      log.debug("FlipbookNuke.flipbook caught exception:")
      import traceback
      traceback.print_exc()


  def _clipsAreValid(self, videoClips, views, first, last):
    """Check if clips' media are valid. If any clip's media isn't present a
    message box will appear asking if the user wants to continue or not"""
    
    offlineMediaSource = []
    for clip, colorspace in videoClips:
      mediaSource = clip.mediaSource()
      if not mediaSource.isMediaPresent():
        fileInfo = mediaSource.fileinfos()[0]
        # TODO Temporary workaround to deal with MediaSource not being aware of
        # the %V notation for specifiying separate view files.
        if not self._hasSeparateViewFiles(fileInfo.filename(), views, first, last):
          offlineMediaSource.append( fileInfo.filename() )

    if len( offlineMediaSource ) > 0:
      offlineClipsList = '\n'.join( offlineMediaSource )
      message = 'The following file(s):\n%s\ncould not be found.' % offlineClipsList
      nuke.message( message )
      return False
    else:
      return True

  def _hasSeparateViewFiles(self, path, views, first, last):
    """Iterates from first to last and for each frame checks that a file exists
    for each view name by replacing %V and %v occurances in path. Returns True
    if all files exist and False otherwise."""
    for i in range (first, last):
      for view in views:
        # Replace %V with the view name
        fileName = path.replace("%V", view)
        # Replace %v with the view short name (first letter)
        fileName = fileName.replace("%v", view[0])
        # Insert the frame number
        fileName = fileName % i
        if not util.filesystem.exists(fileName):
          return False
    return True

  def _applyLutCorrectionFromSequence(self, sequence, videoClips):
    """Applies the color transform for each clip according
    the input colorspace"""

    videoTracks = sequence.videoTracks()
    if len(videoTracks) > 0:
      videoTrack = videoTracks[0]

      trackItems = list(videoTrack.items())
      for trackItem in trackItems:
        inColorspace = ''
        clipSource = trackItem.source()
        for videoClip , videoClipColorspace in videoClips:
          if videoClip == clipSource:
            inColorspace = videoClipColorspace
            break
        
        clipIn = trackItem.timelineIn()
        clipOut = trackItem.timelineOut()
        self._applyLutCorrection( videoTrack , clipIn , clipOut  , inColorspace )



  def _applyLutCorrection( self, videoTrack, first, last , inColorspace):
    """Apply the Lut color correction to the data if the input colorspace is not linear"""
    # This is a hack to the fact that the sequence can't apply the inverse lut transform
    # without a project.


    # if burnIs is enable inColorspace is empty. and in this case we don't
    # need to apply any color correction
    lutCorrection = self._createLUTCorrection()
    lutCorrection.applyLUT(videoTrack, first, last, inColorspace)


  def _getAudioClip( self, options ):
    """ Returns the audio clip for the file defined in the options dictionary,
    or None if no file was defined"""

    audioFile = options.get("audio" )
    audioClip = None
    if audioFile:
      audioClip = self._manager.createClip(audioFile) 
    return audioClip


  def _getViewerLUT( self, options ):
    """ Returns a string with the viewer LUT"""

    # Split on the delimiter for in/viewer LUT
    lut = options.get("lut", "")
    luts = lut.split(self.LUT_OUT_DELIM)

    if len(luts) > 1:
      # second if the viewer lut
      lut = luts[1]
    return mapViewerLUTString(lut)


  def _getInputColorspace( self, options ):
    """Returns the input color space defined in the options dictionary"""

    lut = options.get("lut", "")
    
    # gets the input colorspace. If the lut option contains the LUT_OUT_DELIM marker that precedes the output
    # colorspace (more strictly, display and view) then we only want what's before it, otherwise use the whole thing.
    delimIndex = lut.find(self.LUT_OUT_DELIM)
    if delimIndex >= 0:
      inColorspace = lut[ 0 : delimIndex ]
    else:
      inColorspace = lut

    return inColorspace


  def _addFadeInFadeOutTransitions( self , sequence , fadeInTime , fadeOutTime ):
    """Adds FadeIn and FadeOut transitions.
    If fadeInTime/fadeOutTime are bigger than the first/last sub track item durantion
    these values will be trimmed to the corresponding sub track duration"""

    videoTracks = sequence.videoTracks()
    if len(videoTracks) > 0:
      videoTrack = videoTracks[0]
      subTrackIn = videoTrack[0]
      subTrackOut = videoTrack[-1]
      fadeInTime = min( fadeInTime , subTrackIn.duration() )
      fadeOutTime = min( fadeOutTime , subTrackOut.duration() )
      if fadeInTime > 0:
        fadeInTransition = hiero.core.Transition.createFadeInTransition( subTrackIn , fadeInTime )
        videoTrack.addTransition( fadeInTransition )

      if fadeOutTime > 0:
        fadeOutTransition = hiero.core.Transition.createFadeOutTransition( subTrackOut , fadeOutTime)
        videoTrack.addTransition( fadeOutTransition )


  def _addDissolveTransition( self , sequence , dissolveTime ):
    """Add dissolve transition. If the video track only has one sub item nothing is done.
    If dissolveTime if bigger than any sub track item duration it will be trimmed to the smallest
    duration of the 2 sub items for that dissolve transition."""

    videoTracks = sequence.videoTracks()
    if len(videoTracks) > 0 and dissolveTime > 0:
      videoTrack = videoTracks[0]

      for index in range( len(list(videoTrack.items())) - 1 ):
          trackItemIn = videoTrack[ index ]
          trackItemOut = videoTrack[ index + 1 ]
          
          tempDissolveTime = min( dissolveTime , trackItemIn.duration() , trackItemOut.duration() )

          trackItemIn.setTimelineOut( trackItemIn.timelineOut() - tempDissolveTime )
          trackItemIn.setSourceOut( trackItemIn.sourceOut() - tempDissolveTime )
          trackItemOut.setSourceIn( trackItemOut.sourceIn() + tempDissolveTime )
          offset = trackItemIn.timelineOut() - trackItemOut.timelineIn() + 1
          trackItemOut.setTimelineIn( trackItemOut.timelineIn() + offset )
          trackItemOut.setTimelineOut( trackItemOut.timelineOut() + offset )

          dissolveTransition = hiero.core.Transition.createDissolveTransition( trackItemIn, trackItemOut, tempDissolveTime, tempDissolveTime )

          videoTrack.addTransition( dissolveTransition )


  def dialogKnobs(self, parent):
    parent._wipeEnum = nuke.Enumeration_Knob( "wipe", "Buffer", ["A", "B" ] )
    parent._wipeEnum.setTooltip("Select Buffer for Flipbook viewer")
    parent._state.setKnob(parent._wipeEnum, "A")
    parent.addKnob( parent._wipeEnum )

  def capabilities(self):
    return kNukeFlipbookCapabilities

  def getExtraOptions(self, flipbookDialog, nodeToFlipbook):
    """ Implements FlipbookApplication.getExtraOptions"""

    options = {
    }

    try:
      options['pixelAspect'] = float(nuke.value(nodeToFlipbook.name()+".pixel_aspect"))
    except:
      pass

    try:
      f = nodeToFlipbook.format()
      options['dimensions'] = { 'width' : f.width(), 'height' : f.height() }
    except:
      pass

    # LUT
    if not flipbookDialog._burnInLUT.value():
      inputColourspace = getColorspaceFromNode( flipbookDialog._node )

      # Check our output
      outputColourspace = flipbookDialog._getLUT()

      if inputColourspace == outputColourspace:
        options["lut"] = inputColourspace
      else:
        options["lut"] = inputColourspace + self.LUT_OUT_DELIM + outputColourspace

      # check if raw is selected
      if flipbookDialog._node.Class() == "Read" and flipbookDialog._node.knob("raw"):
        options["raw"] = flipbookDialog._node.knob("raw").value()
      else:
        options["raw"] = False

    # AUDIO
    audioTrack = flipbookDialog._getAudio()
    if audioTrack != "":
      options["audio"] = audioTrack

    # ROI
    if flipbookDialog._useRoi.value():
      roi = flipbookDialog._roi.toDict()
      if (roi["r"] - roi["x"] > 0) and (roi["t"] - roi["y"] > 0):
        options["roi"] = bboxToTopLeft(int(nuke.value(nodeToFlipbook.name()+".actual_format.height")), roi)

    # Burn in the LUT option
    if flipbookDialog._burnInLUT.value():
      options["burnIn"] = flipbookDialog._burnInLUT.value()

    try:
      wipeNum = flipbookDialog._wipeEnum.value()
      options['wipe'] = wipeNum
    except:
      pass

    # FIXME: uncomment this for fadeIn/fadeOut and dissovle support dirrectly on the sequence
    # once it is working
    #
    # get fadeIn and fadeOut from node
    #try:
    #  options['fadeIn'] = int( nuke.value( nodeToFlipbook.name() + ".fadeIn" ) )
    #  options['fadeOut'] = int( nuke.value( nodeToFlipbook.name() + ".fadeOut" ) )
    #except:
    #  pass

    #try:
    #  options['crossDissolve'] = int( nuke.value( nodeToFlipbook.name() + ".dissolve" ) )
    #except:
    #  pass

    # get start at frame number
    if flipbookDialog._node.Class() == "Read":
      try:
        hasStartAtDefined = flipbookDialog._node['frame_mode'].value() == "start at"
        if hasStartAtDefined:
          # 'frame_mode' knob is a string knob, so '20.0' will raise an exception
          # if converted directly to integer
          options['start_at'] = int( float( flipbookDialog._node['frame'].value() ) )
      except:
        pass
    elif flipbookDialog._node.Class() == "AppendClip":
      try:
        options['start_at'] = int( float( flipbookDialog._node['firstFrame'].value() ) )
      except:
        pass

    nodeName = nodeToFlipbook.name()
    if nodeName == "Flipbook":
      nodeName = nodeToFlipbook.input(0).name()

    options['nodeName'] = nodeName

    return options


flipbooking.register(FlipbookNuke())

from nukescripts.renderdialog import *

# This overrides Nuke's default renderdialog.py, without having to modify the Nuke install.
def _getIntermediatePath(self):
  """Get the path for the temporary files. May be filled in using printf syntax."""
  flipbooktmp=""
  if flipbooktmp == "":
    try:
      flipbooktmp = self._selectedFlipbook().cacheDir()
    except:
      try:
        flipbooktmp = os.environ["NUKE_DISK_CACHE"]
      except:
        flipbooktmp = nuke.value("preferences.DiskCachePath")

  # exr files can be written as stereo exrs so only write to
  # separate files if we are not writting to exr
  fileType = self._getIntermediateFileType()
  if len(self._selectedViews()) > 1 and fileType is not "exr":
    flipbookFileNameTemp = "nuke_tmp_flip.%04d.%V." + fileType
  else:
    # Here, we're replacing the 'nuke_tmp_flip' string which is used by FrameCycler. We want unique render names.
    flipbookFileNameTemp = "%s_flip_%i.%s." % (self._node.name(),int(time.time()),'%04d') + fileType
  flipbooktmpdir = os.path.join(flipbooktmp, "flipbook")
  if not util.filesystem.exists(flipbooktmpdir):
    util.filesystem.makeDirs(flipbooktmpdir)

  if not os.path.isdir(util.asUnicode(flipbooktmpdir)):
    raise RuntimeError("%s already exists and is not a directory, please delete before flipbooking again" % flipbooktmpdir)
  flipbooktmp = os.path.join(flipbooktmpdir, flipbookFileNameTemp)

  if nuke.env['WIN32']:
    flipbooktmp = re.sub(r"\\", "/", str(flipbooktmp))
  return flipbooktmp



# Insert unique flipbook image path methods for Hiero
FlipbookDialog._getIntermediatePath = _getIntermediatePath

# Fix audio read node selection in the flipbook dialog
def fixedAudioFlipbookDialogPostKnobs(self):

  # get the old method to do all the heavy lifting
  oldPostKnobs(self)

  # make audio reads select themselves in the item list
  if self._node.Class() == "AudioRead":
    index = 0
    for a in list(self._audioSource.values()):
      if a == self._node.name():
        self._audioSource.setValue(index)
        break
      index += 1

oldPostKnobs = FlipbookDialog._addPostKnobs
FlipbookDialog._addPostKnobs = fixedAudioFlipbookDialogPostKnobs


# save original _requireIntermediateNode to test if the Read nodes in the
# AppendClip input are valid
flipbookDialogRequiredIntermediateNode = FlipbookDialog._requireIntermediateNode

def _requireIntermediateNodeNew(self, nodeToTest):
  # hack to check if the selected node is a AppendClip or not.
  # This only works for this flipbook application, otherwise it will fallback to the _requireIntermediateNode
  # method defined in the FlipbookDialog class
  
  flipbookToRun = flipbooking.gFlipbookFactory.getApplication(self._flipbookEnum.value())
  if isinstance(flipbookToRun, FlipbookNuke):
    if nodeToTest.Class() == 'Read' or nodeToTest.Class() == 'Write':
      if not flipbookToRun.isLUTAvailableForNode( nodeToTest ):
        return True
    elif nodeToTest.Class() == 'AppendClip':
      allInputNodesAreRead = True
      for index in range( nodeToTest.inputs() ):
        inputNode = nodeToTest.input(index)
        isValidReadNode = inputNode.Class() == 'Read' and not flipbookDialogRequiredIntermediateNode(self, inputNode)
        allInputNodesAreRead = allInputNodesAreRead and isValidReadNode and flipbookToRun.isLUTAvailableForNode( inputNode )
    
      # FIXME:
      # fadeIn/fadeOut/dissolve transitions are not working at the moment
      # If any of this settings is defined in the AppendClip node
      # everything will be render out. Once the transitions are working
      # they can be set directly on the timeline. Uncomment code in _getOptions
      # to save the fadeIn/fadeOut/dissolve values
      if allInputNodesAreRead:
        fadeInIsZero = not int( nuke.value( nodeToTest.name() + ".fadeIn" ) ) > 0
        fadeOutIsZero = not int( nuke.value( nodeToTest.name() + ".fadeOut" ) ) > 0
        dissolveIsZero = not int( nuke.value( nodeToTest.name() + ".dissolve" ) ) > 0
        allInputNodesAreRead = allInputNodesAreRead and fadeInIsZero and fadeOutIsZero and dissolveIsZero

      return not allInputNodesAreRead
        
  return flipbookDialogRequiredIntermediateNode(self, nodeToTest)

FlipbookDialog._requireIntermediateNode = _requireIntermediateNodeNew


### event handler that is loaded in Nuke mode to enable/disable menu items for the flipbook

def recursiveSetActionVisibility(action, visible):
  action.setVisible(visible)
  menu = action.menu()
  if menu:
    actions = menu.actions()
    for a in actions:
      recursiveSetActionVisibility(a, visible)

class FlipbookEventHandler:
  def __init__(self):

    # Connect kContextChanged callback for automatically hiding/showing the view menu options
    hiero.core.events.registerInterest(hiero.core.events.EventType.kContextChanged, self.onContextChanged)


  def onContextChanged(self, event):
    """ Notification that keyboard focus has changed. """

    focusInNuke = event.focusInNuke

    ## if focus in Nuke hide the 'View' menu otherwise show it
    action = findMenuAction("foundry.menu.viewer")
    if action:
      recursiveSetActionVisibility(action, not focusInNuke)

    # Hide the nuke Viewer menu to prevent ambiguous shortcuts when the
    # flipbook has focus
    nukeMenuBar = nuke.menu('Nuke')
    nukeViewerViewerItem = nukeMenuBar.menu("Viewer")
    nukeViewerMenuAction = nukeViewerViewerItem.action()
    if nukeViewerMenuAction:
      recursiveSetActionVisibility(nukeViewerMenuAction, focusInNuke)

if not nuke.env['studio']:
  ## event handler needed in nuke mode only
  # in studio the switching is handled in nukestudio.py

  flipbookEventHandler = FlipbookEventHandler()

  ## move the 'view' menu next to the 'Layout' menu

  nukeEditMenu = findMenuAction( "Workspace" )
  hieroViewMenu = findMenuAction( "foundry.menu.viewer" )
  recursiveSetActionVisibility( hieroViewMenu, False )

  menuBar().insertMenu( nukeEditMenu, hieroViewMenu.menu() )

