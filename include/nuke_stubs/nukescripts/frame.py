# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

def goto_frame():
  f = nuke.frame()
  p = nuke.Panel("Goto Frame")
  p.addSingleLineInput("Frame:", f)
  result = p.show()
  if result == 1:
    nuke.frame(int(nuke.expression(p.value("Frame:"))))


import re
def replaceHashes(filename):
  '''replaceHashes(filename) -> string
  Replace any sequences of 1 or more hash marks (#) with a printf-style %0nd specifier.'''
  def _hashRepl(matchobj):
      return "%%0%dd" % len(matchobj.group(0))
  _pat = re.compile(r'(\#+)')
  return re.sub(_pat, _hashRepl, filename)
