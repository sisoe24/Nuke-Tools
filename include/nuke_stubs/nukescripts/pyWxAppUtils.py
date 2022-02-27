# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

from nukescripts import pyAppUtils

class pyWxAppHelper(pyAppUtils.pyAppHelper):
  """ Helper class to initialise wxWidgets in a separate thread """

  def __init__(self, wxApp, start = None):
    super(pyWxAppHelper, self).__init__(start)
    self.__pyWxAppType = wxApp
    self.__pyWxApp = None
    if start:
      self.start()

  def getApplication(self):
    import wx
    if self.__pyWxApp is None:
      self.__pyWxApp = self.__pyWxAppType()
      import nuke
      if not nuke.env['MACOS']:
        self.__pyWxApp.MainLoop()
    return self.__pyWxApp

  def start(self):
    super(pyWxAppHelper, self).initiate()
    self.run(self.getApplication)

