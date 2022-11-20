# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import os.path

import hiero.core



class ShotTask(hiero.core.TaskBase):
  def __init__( self, initDict ):
    """Initialize"""
    hiero.core.TaskBase.__init__( self, initDict )

  def preShot(self):
    pass

  def postShot(self):
    pass

  def startTask(self):
    hiero.core.TaskBase.startTask(self)
    self.preShot()
  
  def finishTask(self):
    self.postShot()
    hiero.core.TaskBase.finishTask(self)

  def forcedAbort(self):
    pass
