#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions for dealing with the filesystem which try to handle
unicode correctly.
"""

import os
import platform
from hiero.core.util import asUnicode


def makeDirs(dirPath):
  """ Make the directories for the given path if they don't already
  exist.
  """
  dirPath = asUnicode(dirPath)
  if not os.path.exists(dirPath):
    os.makedirs(dirPath)


def exists(path):
  """ Wrapper around os.path.exists() """
  return os.path.exists(asUnicode(path))

def stat(path):
  """ Wrapper around os.stat() """
  return os.stat(asUnicode(path))

def lexists(path):
  """ Wrapper around os.path.lexists() """
  return os.path.exists(asUnicode(path))


def access(path, mode):
  """ Wrapper around os.access() """
  return os.access(asUnicode(path), mode)


def openFile(path, *args):
  """ Wrapper around open. """
  return open(asUnicode(path), *args)


def remove(path):
  """ Wrapper around os.remove. """
  return os.remove(asUnicode(path))


if platform.system() == "Windows":
  import ctypes
  from ctypes import wintypes
  _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
  _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
  _GetShortPathNameW.restype = wintypes.DWORD

  def getShortPathName(long_name):
    """ On Windows, gets the short path name of a given long path. Returns
    an empty string if it fails.
    Taken from: http://stackoverflow.com/a/23598461/200291
    """
    long_name = asUnicode(long_name)
    output_buf_size = 0
    while True:
      output_buf = ctypes.create_unicode_buffer(output_buf_size)
      needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
      if output_buf_size >= needed:
        return output_buf.value
      else:
        output_buf_size = needed
