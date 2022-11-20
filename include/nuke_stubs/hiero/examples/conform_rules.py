import re
import os.path
from hiero.core import ConformRule
from hiero.core import Keys
from hiero.core import conformer

#------------------------------------------------------------------------------
class UmidConformRule(ConformRule):
  """Match Umid."""
  def __init__(self):
    ConformRule.__init__(self, "Umids")
	
  def compare( self, media, candidateMedia ):
    try:
      mediaUmid = media.value(Keys.kMediaUmid)
      candidateUmid = candidateMedia.value(Keys.kMediaUmid)
	
      return mediaUmid == candidateUmid
    except:
      return False

#------------------------------------------------------------------------------
class TapeNameConformRule(ConformRule):
  """Match tape names."""
  def __init__(self):
    ConformRule.__init__(self, "TapeName")
  
  def compare( self, media, candidateMedia ):
    try:
      tapeName = media[ Keys.kMediaTapeName ].lower()
      candidateName = candidateMedia[ Keys.kMediaTapeName ].lower()
      
      return tapeName == candidateName
    except KeyError:
      return False

#------------------------------------------------------------------------------
class NameConformRule(ConformRule):
  """Match media filenames."""
  def __init__(self):
    ConformRule.__init__(self, "Name")
  
  def compare( self, media, candidateMedia ):
    try:
      sourceName = media[ Keys.kMediaName ].lower()
      candidateName = candidateMedia[ Keys.kMediaName ].lower()
      
      return sourceName == candidateName
    
    except KeyError:
      return False

#------------------------------------------------------------------------------
class PartialNameConformRule(ConformRule):
  """Match partial media filenames."""
  def __init__(self):
    ConformRule.__init__(self, "PartialName")
  
  def compare( self, media, candidateMedia ):
    try:
      (sourcePath, sourceName ) = os.path.split( media[ Keys.kMediaName ].lower() )
      (candidatePath, candidateName ) = os.path.split( candidateMedia[ Keys.kMediaName ].lower() )
      (sourceRoot, sourceExt) = os.path.splitext( sourceName )
      (candidateRoot, candidateExt) = os.path.splitext( candidateName )
      
      # Peel off space, dot, or _ separated words from end of source looking for a
      # candidate that starts with that shortened source name.
      # There is probably some way of doing this with regex engine but I am keeping it like the C++ code
      lastSep = len( sourceRoot )
      candidateLen = len( candidateRoot )
      
      while (lastSep > 0 and lastSep >= candidateLen and lastSep != -1):
        sourceHead = sourceRoot[0:lastSep];
        if (candidateRoot.find(sourceHead, None, None) != -1):
          return True
        spaceSep = sourceRoot.rfind(" ", lastSep-1)
        dotSep = sourceRoot.rfind(".", lastSep-1)
        scoreSep = sourceRoot.rfind("_", lastSep-1)
        lastSep = max( spaceSep, dotSep, scoreSep )
      
      return False
    
    except KeyError:
      return False

#------------------------------------------------------------------------------
class TimecodeConformRule(ConformRule):
  """Match timecode values."""
  def __init__(self):
    ConformRule.__init__(self, "Timecode")
  
  def compare( self, media, candidateMedia ):
    try:
      mediaStartTimeValue = media[ Keys.kMediaStartTime ]
      mediaDurationValue = media[ Keys.kMediaDuration ]
      mediaTypeValue = media[ Keys.kMediaMasterMediaType ]
      candidateMediaStartTimeValue = candidateMedia[ Keys.kMediaStartTime ]
      candidateMediaDurationValue = candidateMedia[ Keys.kMediaDuration ]
      candidateMediaTypeValue = candidateMedia[ Keys.kMediaMasterMediaType ]
  
      if (mediaTypeValue == candidateMediaTypeValue):
        mediaStartTime = int(mediaStartTimeValue)
        mediaDuration = int(mediaDurationValue)
        candidateMediaStartTime = int(candidateMediaStartTimeValue)
        candidateMediaDuration = int(candidateMediaDurationValue)
        
        return (mediaStartTime >= candidateMediaStartTime and mediaStartTime + mediaDuration <= candidateMediaStartTime + candidateMediaDuration)
  
      return False
  
    except KeyError:
      return False

#------------------------------------------------------------------------------

# Construct instances of the rules to register them with Hiero.
umidRule = UmidConformRule()
nameRule = NameConformRule()
tapeNameRule = TapeNameConformRule()
partialNameRule = PartialNameConformRule()
timecodeRule = TimecodeConformRule()

# To turn off a rule:
# nameRule.deactivate()

# To return a tuple of the active conform rules:
activeRules = conformer().pythonRuleNames()
print(activeRules)
