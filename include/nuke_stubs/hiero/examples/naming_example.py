# Example for how to override hiero naming scheme.
# Copyright (c) 2012 The Foundry Visionmongers Ltd.  All Rights Reserved.
#
# The following example provides a set of functions for extracting clip, name and root names from a clip.
# The example aims to read a specific (hypothetical) convention for DPX files, in which filepaths look like:
#
#        .../longpath/shotname/version_01/001.dpx
#
# The current implementation of Hiero fails to retrieve a useful name for the clip due to the obscure naming convention
# followed, so we would like to extract something like:
#
#        Clip:    shotname_v01
#        Version: shotname_v01
#        Root:    shotname
#
# Notes:
#  - "Root" is the object which groups together several versions  
#  - Clip and Version will often receive the same name, but we might want them to be different. For instance, we could
#    hide version information from clips.
#  - When Root and Version information is displayed together in the application, the string "Root > Version" is usually
#    used.
#    Note that if they share the start of the name, it will be omitted for version, e.g. "shotname > v01".


from hiero.core import NamingScheme
import re


def user_clipName(clip):
  names = extractNames(clip)

  if names[0]:
    # This file follows our naming convention
    return names[1]
  
  # This file does not follow our specific convention, let the default implementation of Hiero handle it
  return NamingScheme.default_clipName(clip)


def user_versionName(clip):
  names = extractNames(clip)

  if names[0]:
    # This file follows our naming convention
    return names[2]
  
  # This file does not follow our specific convention, let the default implementation of Hiero handle it
  return NamingScheme.default_versionName(clip)


def user_rootName(clip):
  names = extractNames(clip)

  if names[0]:
    # This file follows our naming convention
    return names[3]
  
  # This file does not follow our specific convention, let the default implementation of Hiero handle it
  return NamingScheme.default_rootName(clip)


def extractNames(clip):  
  path = clip.mediaSource().firstpath()
  
  pieces = path.split("/")
  if len(pieces) >= 3:
    # We will perform different tests on our file to check whether it follows our desired convention.
    # matching will store the result of these tests.
    pfile = pieces[-1]
    pversion = pieces[-2]
    pname = pieces[-3]
    
    # Test filename piece is of the form "001.dpx"
    # regex: Start of string, one or more digits, followed by .dpx, then string ends
    regex = "^\\d+\\.dpx$"
    matching = re.search(regex, pfile, re.IGNORECASE) is not None

    # Test version piece is of the form: "version_01"
    # regex: Start of string, version_, followed by one or more digits, then string ends
    regex = "^version_\\d+$"
    matching = matching and re.search(regex, pversion, re.IGNORECASE) is not None

    if matching:
      # Build version/clip name of the form: "shotname_01"
      version = pname + "_v" + pversion[8:]
      return True, version, version, pname

  # This file does not follow our specific convention, let the default implementation of Hiero handle it.
  return False, None, None, None


# Enable this to activate the custom naming example
# Note: Do not remove 'staticmethod' from the assignment.
NamingScheme.clipName = staticmethod(user_clipName)
NamingScheme.versionName = staticmethod(user_versionName)
NamingScheme.rootName = staticmethod(user_rootName)
