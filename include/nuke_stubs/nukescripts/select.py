# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke


def select_by_name():
  """Menu command to select nodes by a glob-pattern name.
  This function is only maintained for backwards compatibility.
  Please use nuke.selectPattern() instead."""
  nuke.selectPattern()


def select_similar(_type):
  "Included only for compatibility.  Use nuke.selectSimilar()."
  nuke.selectSimilar(_type)
