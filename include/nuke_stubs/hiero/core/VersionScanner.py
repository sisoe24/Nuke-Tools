# ScanForVersions is the action responsible for scanning for versions.
# This action is added to the BinView context menu.
# The code responsible for the scanning is located in hiero.core.VersionScanner

import hiero.core
from hiero.core import MediaSource
from hiero.core import Clip
from hiero.core import Version
from hiero.core import log
from hiero.core.log import *
from hiero.core.util import findViewInPath
from PySide2.QtCore import QDir
import os.path
import glob
import re


# WARNING: Modifying these regexes for "equivalent" ones might break code that depends on the grouping
#          (parentheses) in them for obtaining bits of data. Be extra-careful if you do so.
# NOTE: kRawSequenceRegex checks for preceding chars to distinguish from versions. This means it includes
#       exactly 2 chars in front of the actual frame number, that need to be trimmed to retrieve it.
_kVersionRegex = "([/._]v)(\\d+)" # e.g.: "_v1", ".v024", "/v13"
_kPaddedSequenceRegex = "%((\\d)*)(d)" # e.g.: "%01d", "%d"
_kRawSequenceRegex = "(.[^v0-9]|[^/._]v)(\\d+)(\\.[^\\.]+)$" # e.g.: "0001.dpx", "1.exr" - not preceded by "_v", ".v", "/v", or a digit

# Version Scanning preferences
# Here we can change how the version scanning detects version numbers. For example
# /dir_v1/file_v2.dpx
#
# kDetectVersionDirectoryOnly will get the version index from the directory, so v1
kDetectVersionDirectoryOnly = 0

# kDetectVersionFullPath will get the version index from the full path, so v2. Note we always find the version index looking from the right
kDetectVersionFullPath      = 1

# Default scanning method
DefaultVersionScanningIndexDetectionMethod = kDetectVersionFullPath

# Action to scan for new versions
class VersionScanner():

  def __init__(self):

    self._VersionScanningIndexDetectionMethod = DefaultVersionScanningIndexDetectionMethod

    # Optimisation: Cached regex matches (used by getMatches in checkNewVersion)
    self._regexMatches = None
    # Optimisation: Set of strings containing "file heads" for visited clips (used by isVisitedClip in checkNewVersion)
    self._visitedClips = set()

    # Path remaps that were applied to the clips being scanned. This will contain
    # tuples of (remapped path, original path)
    self._pathRemaps = set()

  def findVersionFiles(self, version):
    binitem = version.parent()

    origfilename = self.getFilename(version)
    self._origextension = os.path.splitext(origfilename)[1]

    foundVersions = self.findNewVersions(version)
   
    debug("ScanForVersions - Versions found for %s (before sorting/filtering): %s", version, foundVersions) 
    
    # Filter versions according to filterVersion
    foundVersions = [v for v in foundVersions if self.filterVersion(binitem, v)]
    # Sort versions according to sortVersions (uses versionLessThan)
    foundVersions = self.sortVersions(foundVersions)

    return foundVersions

  # Wrapping up the scanning process for purposes of testing
  def doScan(self, version):
    foundVersionFiles = self.findVersionFiles(version)
#    log.info("ScanForVersions - foundVersionFiles found for %s: %s", version, foundVersionFiles)

    binitem = version.parent()
      
    # Add versions to binitem, respecting the sorting
    newVersions = self.insertVersions(binitem, foundVersionFiles)
    log.info("ScanForVersions - Versions found for %s: %s", version, newVersions)
    
    return newVersions  

  def findNewVersions(self, version):
    """ Scan for files matching an existing Version. """
    return self.findNewVersionsInPath(self.getFilename(version))

  def findNewVersionsInPath(self, filename):
    """ Scan for files matching an existing path. Returns the matched files.
    Note this will include the files used by already added versions.
    """
    files = set()
    
    globex = self.getGlobExpression(filename)
    
    # If the path contains multi-view placeholders, first replace these with
    # wildcards in the glob expression so new versions with any views are found.
    isMultiViewPath = '%v' in filename or '%V' in filename
    if isMultiViewPath:
      globex = globex.replace('%v', '?').replace('%V', '*')

    foundFiles = [foundFile for foundFile in glob.iglob(globex)]
    foundFiles.sort()

    # If the original path was multi-view, ensure any matched versions also are
    # and contain the configured view names. In this case convert the matched 
    # files back to %v form.
    if isMultiViewPath:
      project = version.parent().project()
      views = project.views()
      foundMultiViewFiles = []
      for foundFile in foundFiles:
        result = findViewInPath(foundFile, views)
        if result and result[1] not in foundMultiViewFiles:
          foundMultiViewFiles.append( result[1] )
      foundFiles = foundMultiViewFiles
    
    for foundFile in foundFiles:
      foundFile = re.sub("\\\\", "/", foundFile)
      if self.checkNewVersion(filename, foundFile):
        files.add(foundFile)

    # Clear cache (it is only valid per Version object and needs clearing)
    self._regexMatches = None
    self._visitedClips.clear()

    return files


  def getFilename(self, version):
    """ Get the filename from a Version """
    assert isinstance(version, Version)
    clip = version.item()
    readNode = clip.readNode()
    
    # Normalize the original path and the remapped one to avoid issues with
    # backslashes etc. Note: using QDir.cleanPath() to do this because it
    # converts \ to / which is what is wanted here.
    filename = QDir.cleanPath(readNode['file'].getValue())

    # Filter through path remapping. If it was remapped, we want to look for files
    # in the remapped location but set the path on the new clips without the remapping,
    # so find the remapped part and store so the remapping be reversed when creating
    # the new clips
    remappedFilename = QDir.cleanPath(hiero.core.remapPath(filename))
    if filename != remappedFilename:
      for i in range(-1, 1-len(filename), -1):
        if filename[i] != remappedFilename[i]:
          self._pathRemaps.add( (remappedFilename[0:i+1], filename[0:i+1]) )
          break
    return remappedFilename


  # Get the active version index based upon the setting _VersionScanningIndexDetectionMethod as specified in __init__.py
  def getActiveIndexFromPath(self, filepath):
    (dirpath, filename) = os.path.split(filepath)
    
    if (self._VersionScanningIndexDetectionMethod is kDetectVersionDirectoryOnly):
      searchpath = dirpath
    elif (self._VersionScanningIndexDetectionMethod is kDetectVersionFullPath):
      searchpath = filepath

    # Replace version indices
    matches = [match for match in re.finditer(_kVersionRegex, searchpath, re.IGNORECASE)]
    if len(matches) > 0:
      # Obtain version index from the last version string, ignore the others
      match = matches[-1]
      versionIndex = int(match.group(2))
    return versionIndex
  
  # Find substrings representing sequence padding (_kPaddedSequenceRegex) and
  # version (_kVersionRegex) and replace them with suitable token strings in
  # 'glob' format.
  # e.g. "/files/clip_v13.%03d.dpx" -> "/files/clip_v***.*" 
  #      "/files/clip_v1.%01d.dpx" -> "/files/clip_v***.*" 
  #      "/files/v3/clip_v1.%01d.dpx" -> "/files/v3/clip_v***.*"
  def getGlobExpression(self, filename):
 
    # Replace version indices
    matches = [match for match in re.finditer(_kVersionRegex, filename, re.IGNORECASE)]
    if len(matches) > 0:
      
      # Obtain version index from the last version string, ignore the others
      match = matches[-1]

      # Get the version index from the file path
      versionIndex = self.getActiveIndexFromPath(filename)
  
      # Iterate through matches, if the version string equals versionIndex ("active one"), substitute
      # NB: Reverse iteration guarantees safety of modifying filename by splitting at given positions (match.start() / end())
      for match in reversed(matches):
        prefix = match.group(1)
        index = match.group(2)

        # #mat: This is where we're filtering ONLY on our active version index
        if int(index) == versionIndex:
          filename = filename[:match.start()] + prefix + "*" + filename[match.end():]
    
    # Replace sequence padding.    
    matches = [match for match in re.finditer(_kPaddedSequenceRegex, filename, re.IGNORECASE)]
    if len(matches) > 0:      
      # Iterate through matches, if the version string equals versionIndex ("active one"), substitute
      # NB: Reverse iteration guarantees safety of modifying filename by splitting at given positions (match.start() / end())
      for match in matches:
        pre = filename[:match.start() - 1] # -1 is to remove possibly leading '.' or similar before sequence padding
        post = filename[match.end():]
        filename = pre + "*" + post
    
    # Replace extension
    # NB: This also allows for sequence padding to appear before the extension, in case the original filename did not have a frame number
    filename = os.path.splitext(filename)[0] + "*.*"
    
    return filename
    
  # Check that newFile correctly matches a version of originalFile, where newFile is a real
  # filename and originalFile includes sequence padding tokens (e.g. "%03d").
  # Return the version index of the new file.
  def checkNewVersion(self, originalFile, newFile):
    if self.isVisitedClip(newFile):
      return False
      
    if newFile.endswith( '~' ) or newFile.endswith(".tmp") or newFile.endswith('.autosave'):  ## ignore backup, tmp and autosave files
      return False

    # Fetch regex matches from cache or compute if needed
    originalVersionMatches = self.getMatches(originalFile)
    
    # Retrieve original originalVersionString bit for originalFile and check it matches in newFile    
    if len(originalVersionMatches) > 0:
      originalVersionString = originalVersionMatches[-1].group(2)
      if not originalVersionString.isdigit():
        log.debug("checkNewVersion: originalVersionString is not digit %s", originalFile)
        return False
      originalVersionIndex = int(originalVersionString)
      
      # Retrieve version bit for this file
      newVersionMatches = [ match for match in re.finditer(_kVersionRegex, newFile, re.IGNORECASE) ]
      
      # If several matches, just look at the last one. Also check that we are looking at the right one
      # (same number of matches for original and new versions)        
      if len(newVersionMatches) != len(originalVersionMatches):
        log.debug("checkNewVersion: number of originalVersionString strings differ for original and new files %s, %s", originalFile, newFile)
        return False
      
      # Obtain new version index
      newVersionString = newVersionMatches[-1].group(2)
      if not newVersionString.isdigit():
        log.debug("checkNewVersion: new version is not digit %s", originalFile)   
        return False
      newVersionIndex = int(newVersionString)
      
      # Iterate through matches in the new file, comparing them to the matches in the old one
      for i in range(len(originalVersionMatches)):
        originalVersionIter = originalVersionMatches[i].group(2)
        newVersionIter = newVersionMatches[i].group(2)
        if not (originalVersionIter.isdigit() and newVersionIter.isdigit()):
          log.debug("checkNewVersion: version is not digit %s, %s", originalFile, newFile)
          return False
        originalVersionIndexIter = int(originalVersionIter)
        newVersionIndexIter = int(newVersionIter)
      
        # If this match contains the "active version" for the original file, we need to perform further tests,
        # but otherwise, the string should be the same since the globex replacement did not change it
        if originalVersionIndexIter == originalVersionIndex:
          if newVersionIndexIter != newVersionIndex:
            log.debug("checkNewVersion: found version string not updated to new version number %s, %s", originalFile, newFile)
            return False
      
      self.markVisitedClip(newFile)
      return True
    
    log.debug("checkNewVersion: No version found for original file %s, %s", originalFile, newFile)
    return False
  
  
  # Optimisation: When we get the glob results, we use regex to compare the original filename with the found files.
  #               Using _regexMatches, we ensure this regex matches are computed only once for each original filename.
  def getMatches(self, originalFile):
    if self._regexMatches == None:
      # Retrieve original version bit for originalFile and check it matches in newFile
      versionMatches = [ match for match in re.finditer(_kVersionRegex, originalFile, re.IGNORECASE) ]
      self._regexMatches = versionMatches
      return versionMatches
    
    return self._regexMatches
    
  
  # Optimisation: When we get the glob results, we look in the found files for discovering new versions..
  #               Using _visitedClips, we ensure that we skip any file which is part of an already visited sequence.
  def isVisitedClip(self, filename):
    filehead = self.getFileHead(filename)

#    log.debug("isVisitedClip: %s is %d for %s", filename, (filehead in self._visitedClips), self._visitedClips)   

    return filehead in self._visitedClips    

  # Optimisation: When we get the glob results, we look in the found files for discovering new versions..
  #               Using _visitedClips, we ensure that we skip any file which is part of an already visited sequence.
  def markVisitedClip(self, filename):
    filehead = self.getFileHead(filename)
    self._visitedClips.add(filehead)  
    
  # Helper method: Extracts "filehead" from "filename", removing sequence numbers
  def getFileHead(self, filename):
    newSeqMatches = [match for match in re.finditer(_kRawSequenceRegex, filename, re.IGNORECASE) ]
    if len(newSeqMatches) > 0:
      # To avoid matching version numbers as sequence numbers, we include in the regex the two leading chars
      # before the sequence number to make sure they are not the prefix "_v". We need to trim this two chars
      # before performing substitution:
      sequence = newSeqMatches[-1].group(0)[2:]
      index = newSeqMatches[-1].start()

      # Let's try putting the extension on to prevent it filtering out .jpg files when we're doing a version scan on .dpx for example
      fileExtension = os.path.splitext(filename)[1]

      return filename[:index] + filename[index:].replace(sequence, "") + fileExtension
    else:
      return filename
  
  
  # Determine whether the file newVersionFile should be included as a new version of originalVersion
  def filterVersion(self, binitem, newVersionFile):

    extension = os.path.splitext(newVersionFile)[1]

    movieformats = set(['.mov', '.mp4', '.m4a', '.m4p', '.m4b', '.m4r', '.m4v', '.r3d'])

    ismovieformat = extension.lower() in movieformats
    isorigmovieformat = self._origextension.lower() in movieformats
    
    # Don't mix movie extensions with sequence extensions as it can much up the frame ranges
    if ismovieformat != isorigmovieformat:
      return False
  
    index = 0
    while index < binitem.numVersions():
      version = list(binitem.items())[index]    
      source = version.item().mediaSource()   
      if (source is not None and source.fileinfos() is not None):
        versionFile = source.fileinfos()[0].filename()
        if (versionFile == newVersionFile):
          return False
      index += 1
    
    return True
  
  # Basic bubble sort for versions (we do not expect large numbers of versions)
  def sortVersions(self, versionFiles):
    versions = list(versionFiles)
    stop = False
    while not stop:
      stop = True
      for i in range(len(versions)-1):
        version1 = versions[i]
        version2 = versions[i+1]
        if self.versionLessThan(version2, version1):
          versions[i] = version2
          versions[i+1] = version1
          stop = False
    return versions

  # Compare method for sorting. Compares version filenames according to:
  # 1st) Version index
  # 2nd) File extension
  # 3rd) Full file name
  def versionLessThan(self, filename1, filename2):
    # Retrieve version bit for these files
    newVersionMatches1 = [ match for match in re.finditer(_kVersionRegex, filename1, re.IGNORECASE) ]
    newVersionMatches2 = [ match for match in re.finditer(_kVersionRegex, filename2, re.IGNORECASE) ]
    
    if len(newVersionMatches1) > 0 and len(newVersionMatches2) > 0:        
      # Obtain version indices
      versionString1 = newVersionMatches1[-1].group(2)
      if versionString1.isdigit():
        versionIndex1 = int(versionString1)
      else:
        log.debug("versionLessThan: version is not digit %s", filename1)   
        versionIndex1 = -1
        
      versionString2 = newVersionMatches2[-1].group(2)
      if versionString2.isdigit():
        versionIndex2 = int(versionString2)
      else:
        log.debug("versionLessThan: version is not digit %s", filename2)   
        versionIndex2 = -1
      
      if versionIndex1 != versionIndex2:
        return versionIndex1 < versionIndex2
    else:
      log.debug("versionLessThan: could not find version indices in versions %s, %s", filename1, filename2)
    
    ext1 = os.path.splitext(filename1)[1]
    ext2 = os.path.splitext(filename2)[1]
    
    if ext1 != ext2:
      return ext1 < ext2
    
    return filename1 < filename2 


  def determineVersionIndex(self, binitem, newFilename):
    """ Get the index at which to insert new version files into a BinItem. """
    destinationIndex = 0
    while destinationIndex < binitem.numVersions():
      version = list(binitem.items())[destinationIndex]
      if version and version.item() is not None and version.item().mediaSource() is not None:
        if self.versionLessThan(newFilename, version.item().mediaSource().firstpath()):
          break
      else:
        log.debug("insertVersions() - Problem found with version at position", destinationIndex, "of object", binitem)
      destinationIndex += 1
    return destinationIndex
      

  def insertVersions(self, binitem, versionFiles):
    """ Create clips for a list of files and insert them as versions to a BinItem.
    @return the created Versions
    """
    newVersions = []
    for newFilename in versionFiles:
      newVersion = self.createAndInsertClipVersion(binitem, newFilename)
      if newVersion:
        newVersions.append(newVersion)
    return newVersions


  def createAndInsertClipVersion(self, binitem, newFilename):
    """ Create a clip for a path and insert it as a version into a BinItem. 
    @return the created Version, or None if it fails
    """
    # Reverse any path remapping that was applied to the original clip
    for remappedPath, origPath in self._pathRemaps:
      if newFilename.startswith(remappedPath):
        newFilename = origPath + newFilename[len(remappedPath):]
        break

    destinationIndex = self.determineVersionIndex(binitem, newFilename)
    try:
      newVersion = binitem.createClipVersion(destinationIndex, newFilename)
      return newVersion
    except:
      return None


  def getVersionIndicesForPath(self, path):
    """ Scan the given path and return a list of all the version indices which exist there. """
    versionFiles = self.findNewVersionsInPath(path)
    versionIndices = sorted( [ self.getActiveIndexFromPath(path) for path in versionFiles ] )
    return versionIndices


  def getNewVersionIndexForPath(self, path):
    """ Find the existing versions for the given path, and return a new version index which doesn't
        already exist. """
    versionIndices = self.getVersionIndicesForPath(path)
    if versionIndices:
      return versionIndices[-1] + 1
    else: # If there are no versioned files, raise an exception
      raise RuntimeError("No versioned files found")

