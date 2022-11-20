# -*- coding: utf-8 -*-

"""
A file in which to place any hacks or fixes we need to work around bugs in
Python.
"""

import sys

# Check the Python version.  If it changes, the code in here will need to be
# updated

version_tuple = sys.version_info[:3]
( python_major, python_minor, python_patch ) = version_tuple
if (python_major, python_minor) == (2, 7) and python_patch == 3:
  # Workaround for bug in Python which can cause unwanted output while forking
  # a process. See http://bugs.python.org/issue14308 and
  # http://stackoverflow.com/questions/13193278/understand-python-threading-bug
  # which has this solution.  The bug is fixed in Python 2.7.4
  import threading
  threading._DummyThread._Thread__stop = lambda x: 42


