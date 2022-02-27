# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path
import re
import nuke

####################
#
# this function returns filenames from all Read nodes
# options :
# file - outputs only file names
# dir  - outputs only dir names
# long - entire path
#

def get_reads(method):
  """Returns file names from all Read nodes.

  Options:
    file - outputs only file names
    dir  - outputs only directory names
    long - outputs the entire path"""

  # create variable for the text
  finalmsg = ""
  #go thru all the nodes
  allnodes = nuke.allNodes(group = nuke.root())
  for i in allnodes:
    _class = i.Class()
    if _class == "Read":
      # get the name of the file dir (just the last part)
      # use this to get only the filename
      curname = ""
      name = nuke.filename(i)
      if name is None:
        continue
      if method == "file":
        curname = os.path.basename(name)
      # use this to get only the dir
      if method == "dir" or method == "":
        curname = os.path.dirname(name)
      # get the whole path
      if method == "long":
        curname = name

      curname = re.sub("\.%.*", "", curname)

      # add on to existing variable
      # make sure to avoid adding the slate image :)
      match = re.search("slate", curname)
      if match is None:
        finalmsg += curname

      finalmsg += "\n"

  return finalmsg

