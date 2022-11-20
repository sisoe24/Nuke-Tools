# conformer_options.py - Shows how to set options for the Conform (Match Media) and Import Folder dialog
# (for creating custom conform rules, see also conform_rules.py)
import hiero.core

# Grab a reference to the global conformer object, which manages the matching of media for conform, and importing directories of media
C = hiero.core.conformer()

# This is a list of common formats which we know we never want to import media from or conform against
excludeFormatList = ['*.txt','*.pdf','*.html','*.doc','*.zip''*.db','*.fbx','*.obj','*.lxo','*.xml', '*.nk', '*.abc','*.ma','*.mb','*.hrox','*.nk','*.katana','*.3dl','*.ocio']

# Set the exclude Pattern to reject trying to conform against the excluded list
C.setExcludePatterns(excludeFormatList)

# You can specify to always only include certain patterns file formats
C.setIncludePatterns(['*.dpx','*.exr','*.mov','*.ari','*.jpg'])

# When Matching media you can also set default options on the Conform dialog
C.setUseBestTimecodeMatch(True) # Sets option for 'Accept Best timecode shots that already have media'
C.setExcludeNonOverlappingTimecode(False) # Sets option for 'Ignore Clips with non-overlapping timecode'
C.setIncludeAlreadyMatched(True) # Sets option for 'Conform shots that already have media'