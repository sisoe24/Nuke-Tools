#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
APIs for Nuke's localization functionality.

Use help('_localization') to get detailed help on the classes exposed here.

This module provides the public interface to the localization module and will
remain stable. It uses an underlying native module called _localization to
provide this interface. While there is nothing stopping you from using the
_localization module directly, it may change in a future release and break 
backwards compatibility.
"""

# Import the internal module from C++
from _localization import *

class FileEvent:
  """Events received in file callbacks"""
  LOCALIZED   = 0
  REMOVED     = 1
  CACHE_FULL  = 2
  DISK_FULL   = 3
  OUT_OF_DATE = 4

class ReadStatus:
  """Localization status recieved by Read callbacks"""
  LOCALIZATION_DISABLED = 0
  NOT_LOCALIZED         = 1
  LOCALIZING            = 2
  PARTIALLY_LOCALIZED   = 3
  LOCALIZED             = 4
  OUT_OF_DATE           = 5

