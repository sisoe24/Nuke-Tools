from hiero.core import AudioTrack, BinItem, Clip, Sequence, TrackItem, TrackItemBase, VideoTrack, Version

def deprecated(f, msg = None, funcName = None , deprecatedWarningMsg = None ):
  """ defines a new method and prints a message warning that the function is deprecated.
  @param f: method
  @param msg: Optional. Warning message to print.
  @param funcName: Optional. method name to appear in the warning message. If None f.__name__ will be used.
  @param deprecatedWarningMsg: Optional. Message that will appear after 'WARNING - DEPRECATED ( funcName ): '
  """
  if funcName is None:
    funcName = f.__name__
  warningMsg = "WARNING - DEPRECATED ( " + funcName + " ): "
  if deprecatedWarningMsg:
    warningMsg += deprecatedWarningMsg
  if msg:
    warningMsg += "\n" + msg
    
  def new(*args, **kwargs):
    print(warningMsg)
    return f(*args, **kwargs)

  new.__name__ = f.__name__
  new.__doc__ = f.__doc__ + "\n\n" + warningMsg

  return new


def markDeprecated():
  
  warningMsg = "This method is deprecated and will not be present in future versions of the Python API."

  BinItem.versionUp = deprecated(BinItem.versionUp, "Only available versions can now be obtained from BinItem. To find new versions, please use hiero.core.VersionScanner. To obtain the next version, please use BinItem.nextVersion().", deprecatedWarningMsg = warningMsg)
  BinItem.versionDown = deprecated(BinItem.versionDown, "Only available versions can now be obtained from BinItem. To find new versions, please use hiero.core.VersionScanner. To obtain the next version, please use BinItem.prevVersion().", deprecatedWarningMsg = warningMsg)
  BinItem.versionNextAvailable = deprecated(BinItem.versionNextAvailable, "Only available versions can now be obtained from BinItem. This method has been replaced by BinItem.nextVersion().", deprecatedWarningMsg = warningMsg)
  BinItem.versionPrevAvailable = deprecated(BinItem.versionPrevAvailable, "Only available versions can now be obtained from BinItem. This method has been replaced by BinItem.prevVersion().", deprecatedWarningMsg = warningMsg)
  BinItem.versionMaxAvailable = deprecated(BinItem.versionMaxAvailable, "Only available versions can now be obtained from BinItem. This method has been replaced by BinItem.maxVersion().", deprecatedWarningMsg = warningMsg)
  BinItem.versionMinAvailable = deprecated(BinItem.versionMinAvailable, "Only available versions can now be obtained from BinItem. This method has been replaced by BinItem.minVersion().", deprecatedWarningMsg = warningMsg)
  BinItem.setActiveVersionIndex = deprecated(BinItem.setActiveVersionIndex, "Version indices are no longer unique identifiers and should not be used as such. Please use BinItem.setActiveVersion() instead.", deprecatedWarningMsg = warningMsg)

  Version.versionIndex = deprecated(Version.versionIndex, "Version indices are no longer unique identifiers and should not be used as such.", deprecatedWarningMsg = warningMsg)
  
  TrackItem.versionUp = deprecated(TrackItem.versionUp, "Only available versions can now be obtained from TrackItem. To find new versions, please use hiero.core.VersionScanner. To obtain the next version, please use TrackItem.nextVersion().", deprecatedWarningMsg = warningMsg)
  TrackItem.versionDown = deprecated(TrackItem.versionDown, "Only available versions can now be obtained from TrackItem. To find new versions, please use hiero.core.VersionScanner. To obtain the next version, please use TrackItem.prevVersion().", deprecatedWarningMsg = warningMsg)
  TrackItem.versionNextAvailable = deprecated(TrackItem.versionNextAvailable, "Only available versions can now be obtained from TrackItem. This method has been replaced by TrackItem.nextVersion().", deprecatedWarningMsg = warningMsg)
  TrackItem.versionPrevAvailable = deprecated(TrackItem.versionPrevAvailable, "Only available versions can now be obtained from TrackItem. This method has been replaced by TrackItem.prevVersion().", deprecatedWarningMsg = warningMsg)
  TrackItem.versionMaxAvailable = deprecated(TrackItem.versionMaxAvailable, "Only available versions can now be obtained from TrackItem. This method has been replaced by TrackItem.maxVersion().", deprecatedWarningMsg = warningMsg)
  TrackItem.versionMinAvailable = deprecated(TrackItem.versionMinAvailable, "Only available versions can now be obtained from TrackItem. This method has been replaced by TrackItem.minVersion().", deprecatedWarningMsg = warningMsg)
  TrackItem.setCurrentVersionIndex = deprecated(TrackItem.setCurrentVersionIndex, "Version indices are no longer unique identifiers and should not be used as such. Please use TrackItem.setActiveVersion() instead.", deprecatedWarningMsg = warningMsg)
  
  # We're deprecating all Hiero's original clone() functions, replacing them with copy(). It's unfortunate that the Hiero C++ codebase and API
  # used 'clone' for copying while Nuke uses that term for node cloning in the sense of having multiple nodes sharing a single set of parameters
  # (i.e. knobs). We're be adding a clone() to EffectTrackItem (which wraps the soft effect track item class that owns a node) that will do
  # cloning in the Nuke sense.
  AudioTrack.clone = deprecated(AudioTrack.clone, "This method has been replaced by copy().", deprecatedWarningMsg = warningMsg)
  BinItem.clone = deprecated(BinItem.clone, "This method has been replaced by copy().", deprecatedWarningMsg = warningMsg)
  Clip.clone = deprecated(Clip.clone, "This method has been replaced by copy().", deprecatedWarningMsg = warningMsg)
  Sequence.clone = deprecated(Sequence.clone, "This method has been replaced by copy().", deprecatedWarningMsg = warningMsg)
  TrackItemBase.clone = deprecated(TrackItemBase.clone, "This method has been replaced by copy().", deprecatedWarningMsg = warningMsg)
  VideoTrack.clone = deprecated(VideoTrack.clone, "This method has been replaced by copy().", deprecatedWarningMsg = warningMsg)
