#! /usr/bin/python3

from hiero.core.log import info

# SMPTE 258M-2004 says an element is terminted by the ascii CR and LF characters
# so nake sure we always separate elements with exactly this, not randomly one or the other or both.
CRLF = '\r\n'

class TimeCode :
  """
  Represesents a TimeCode
  """
  def __init__(self, h, m, s, f, sf, dropFrame) :
    self.__hrs = h
    self.__mins = m
    self.__secs = s
    self.__frames = f
    self.__subfield = sf
    self.__dropFrame = dropFrame

  def __repr__(self):
    """
    return string representation of timecode
    """
    separator = ";" if self.isDropFrame() else ":"
    tc = "%02d%s%02d%s%02d%s%02d" % (self.__hrs, separator, self.__mins, separator, self.__secs, separator, self.__frames)
    if self.__subfield > 0:
      tc = tc + "%s%02d" % ("%", self.__subfield)
    return tc
    
  def hrs(self) :
    """
    Return Hours component of timecode
    """
    return self.__hrs

  def mins(self) : 
    """
    Return Minutes component of timecode
    """
    return self.__mins

  def secs(self) :
    """
    Return Seconds component of timecode
    """
    return self.__secs

  def frames(self) :
    """
    Return Frames component of timecode
    """
    return self.__frames

  def isDropFrame(self):
    """
    Return True if timecode is dropframe
    http://documentation.apple.com/en/finalcutpro/usermanual/index.html#chapter=D%26section=6%26tasks=true
    """
    return self.__dropFrame

  def toFrames(self, fps):
    """
    Return timecode as frame index given framerate
    """
    totalseconds = (self.hrs() * 60 * 60) + (self.mins() * 60) + (self.secs()) 
    if self.isDropFrame():
      totalmins = (60*self.hrs()) + self.mins()
      return (totalseconds * fps) + self.frames() - 2*(totalmins - totalmins%10)
    else:
      return (totalseconds * fps) + self.frames()

  @staticmethod
  def createFromFrames(time, fps, dropFrame):
    
    if dropFrame:
      d = time / 17982
      m = int(time % 17982)
      time +=  18 * d + 2 * ((m - 2) / 1798)
    
    frames = int(time % fps)
    time /= fps
    secs = int(time % 60)
    time /= 60
    mins = int(time % 60)
    time /= 60
    hrs = int(time % 24)
    return TimeCode(hrs, mins, secs, frames, 0, dropFrame)
  
  def fromFrames(self, time, fps, dropFrame):
    if dropFrame:
      d = time / 17982
      m = int(time % 17982)
      time +=  18 * d + 2 * ((m - 2) / 1798)
    
    self.__frames = int(time % fps)
    time /= fps
    self.__secs = int(time % 60)
    time /= 60
    self.__mins = int(time % 60)
    time /= 60
    self.__hrs = int(time % 24)
    
    self.__dropFrame = dropFrame

  def addFrames(self, time, fps):
    """
    Return a new TimeCode offset by a given number of frames.
    """
    return TimeCode.createFromFrames( self.toFrames(fps) + time, fps, self.__dropFrame )
    

  def isEqual(self, rhs):
    """
    Compare two time code objects
    """
    return self.hrs() == rhs.hrs() and \
           self.mins() == rhs.mins() and \
           self.secs() == rhs.secs() and \
           self.frames() == rhs.frames()

  def __lt__(self, other):
    return self.hrs() < other.hrs() and \
           self.mins() < other.mins() and \
           self.secs() < other.secs() and \
           self.frames() < other.frames()

  def __le__(self, other):
    return self.hrs() <= other.hrs() and \
           self.mins() <= other.mins() and \
           self.secs() <= other.secs() and \
           self.frames() <= other.frames()

  def __gt__(self, other):
    return self.hrs() > other.hrs() and \
           self.mins() > other.mins() and \
           self.secs() > other.secs() and \
           self.frames() > other.frames()
           
  def __ge__(self, other):
    return self.hrs() >= other.hrs() and \
           self.mins() >= other.mins() and \
           self.secs() >= other.secs() and \
           self.frames() >= other.frames()
  
  
    
class EffectField :
  """
  Represents the Effect Field of and EDL entry.
  The Effect Field describes the transition into the EDL entry.
  """

  CUT = 'C'
  DISSOLVE = 'D'
  KEY = 'K'
  KEY_BACKGROUND = 'B'

  def __init__ (self, effect, effectParameter):
    self.__effect = effect
    self.__effectParameter = effectParameter
  
    if self.__effect != self.CUT and self.__effect != self.DISSOLVE and self.__effect != self.KEY:
      info( "Warning : Unsupported effect field (" + self.__effect + ")" )

  def __repr__(self):
    """
    Returns a string representation of the EffectField.
    """
    if self.__effect == self.DISSOLVE or self.__effect == self.KEY :
      return str(self.__effect) + " " + str(self.__effectParameter)
    return str(self.__effect)

  def effect (self):
    return self.__effect

  def effectparameter (self):
    return self.__effectParameter

  def isKeyBackground(self):
    return self.__effect == self.KEY and self.__effectParameter == self.KEY_BACKGROUND

  def isKeyIn(self):
    return self.__effect == self.KEY and self.__effectParameter != self.KEY_BACKGROUND

class ModeField:
  """
  Represents the Mode field of an EDL entry.
  Audio, Video or Both. 
  """
  def __init__(self, audio, video, channels):

    self.__audio = audio
    self.__video = video
    self.__audiochannels = channels

    if self.hasAudio() and self.numAudioChannels() < 1:
      self.__audiochannels.append(1)
      

  def numAudioChannels(self):
    """
    Returns True if has one or more audio track
    """
    return len(self.__audiochannels)
  
  def hasAudio(self):
    return self.__audio
  def hasVideo(self):
    return self.__video
    
  def __repr__(self):
    """
    Return string representation of Mode Field
    """
    mode = ""
    if self.hasAudio() and self.hasVideo():
      mode = "B"
    elif self.hasAudio():
      mode = "A" if self.numAudioChannels() == 1 else "AA"
    elif self.hasVideo():
      mode = "V"
    else:
      mode = "NONE"

    return mode
   
class EditDecision :
  """
  Represents an entry in an Edit Decision list.
  Additional parameters are catalogued as key value pairs.
  """
   
  def __init__(self, editId, name, mode, effect, srcEntry, srcExit, syncEntry, syncExit):
    self.__editId = editId
    self.__name = name
    self.__mode = mode
    self.__effect = effect
    self.__srcEntry = srcEntry
    self.__srcExit = srcExit
    self.__syncEntry = syncEntry
    self.__syncExit = syncExit
    self.__elements = dict()
    self.__edlSource = ""
    self.__retime = None

  def __repr__(self):
    """
    Return a string representing the Edit Decision
    """
    editId = self.__editId
    if not type(editId) == str:
      editId = ("%03d " % self.__editId)
      
    event =  ' '.join( ( editId.ljust(6), str(self.__name).ljust(8), str(self.__mode).ljust(1), str(self.__effect).ljust(8),
                         str(self.__srcEntry), str(self.__srcExit), str(self.__syncEntry), str(self.__syncExit) ) )
    event += CRLF
    for key, values in self.__elements.items():
      for value in values:
        event += ' '.join( ( str(key), str(value) ) ) + CRLF
    
    if self.__retime:
      event += str(self.__retime) + CRLF 
    
    return event

  def addElement(self, element):
    """
    Add NamedElement object to list of key value pairs
    Values are stored in a list if duplicates are added 
    """
    if element.key() in self.__elements:
      self.__elements[element.key()].append(element.val())
    elif isinstance(element.val(), list):
      self.__elements.update({element.key() : element.val()})
    else:
      self.__elements.update({element.key() : [element.val()]})
      
  def removeElement(self, key):
    """
    Remove all elements with matching key in list of KVPs
    """
    if key in self.__elements:
      del self.__elements[key]
      
  def getElement(self, key):
    """
    Return list of values with matching key
    """
    return self.__elements[key]
  
  def hasElement(self, key):
    """
    Returns true if list of KVPs contains matching key
    """
    return key in self.__elements

  def setEditId(self, editId):
    """
    Set Edit index
    """
    self.__editId = editId

  def editId (self):
    """
    Return Edit index
    """
    return self.__editId
  def name (self):
    """
    Return tape name
    """
    return self.__name
  def mode (self):
    """
    Return mode field object
    """
    return self.__mode
  def effectfield (self):
    """
    Return effect field object
    """
    return self.__effect
  def srcEntry (self):
    """
    Return source in timecode obj
    """
    return self.__srcEntry
  def srcExit (self):
    """
    Return source out timecode obj
    """
    return self.__srcExit
  def syncEntry (self):
    """
    Return timeline in timecode obj
    """
    return self.__syncEntry
  def syncExit (self):
    """
    Return timeline out timecode obj
    """
    return self.__syncExit

  def isBlank (self):
    """
    Return true if tape name is BL or BLANK
    """
    name = self.__name.upper()
    return name == "BL" or name == "BLANK"

  def setSource(self, edlSource):
    self.__edlSource = edlSource

  def getSource(self):
    return self.__edlSource
  
  def conflicts(self, other):
    if other.syncEntry() <= self.syncEntry() and \
      other.syncExit() >= self.syncEntry():
      return True
    elif other.syncEntry() >= self.syncEntry() and \
      other.syncEntry() <= self.syncExit():
      return True
    return False
  
  def setRetime(self, fps, srcEntry=None):
    if srcEntry is None:
      self.__retime = RetimeElement(self.__name, fps, self.__srcEntry)
    else:
      self.__retime = RetimeElement(self.__name, fps, srcEntry)
    
  def retime(self):
    return self.__retime


class RetimeElement:
  """
  A class representing a retime directive  
  """
  def __init__(self, name, framerate, srcEntry=None):
    self.__name = name
    self.__framerate = framerate
    self.__srcEntry = srcEntry
    self.__edlSource = ""

  def name(self):
    """
    Return reel name for retime
    """
    return self.__name

  def framerate(self):
    """
    Return resulting framerate
    """
    return self.__framerate
  def srcEntry(self):
    """
    Return src entry timecode for retime. This can be None if a parsed EDL did not contain it.
    """
    return self.__srcEntry

  def setSrcEntry(self, srcEntry):
    """
    Set the src entry timecode value for this retime.
    """
    self.__srcEntry = srcEntry
  
  def matches(self, rhs):
    """
    Return True if rhs object has same name and timecode
    """
    return True if (self.name() == rhs.name() or self.name() == rhs.editId()) and self.srcEntry().isEqual(rhs.srcEntry()) else False

  def setSource(self, edlSource):
    self.__edlSource = edlSource

  def getSource(self):
    return self.__edlSource

  def __repr__(self):
    # This is the format expected in EDLs (note that speed is expressed in fps with up to one decimal position)
    return "M2    %s %.1f %s" % (self.__name, self.__framerate, self.__srcEntry)
  
class NamedElement:
  """
  Simple object containing key value pair
  This shouldnt be neccessary.
  """
  def __init__(self, field, value):      
    self.__field = field
    self.__value = value

  def __str__(self):
    return self.__repr__()
    
  def __repr__(self):
    # Use str() as join() will throw an exception if __value isn't a string, e.g., an integer.
    return "%s %s" % (str(self.__field), "".join(str(self.__value))) + CRLF
                    
  def key(self):
    return self.__field
                  
  def val(self):
    return self.__value
