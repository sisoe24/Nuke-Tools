# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import queue
import sys
import threading
import nuke


class pyAppHelper(object):
  """ Helper class to run python commands in a separate thread. """

  def __init__(self, start = None):
    """ constructor """
    self.__pyThread = threading.Thread(target = self.__pyThreadMain)
    self.__pyThread.setDaemon(True)
    self.__working = False
    self.__work = queue.Queue()


  def run(self, call, args = (), kwargs = {}):
    """ Runs the specified call in a separate thread. """
    self.__work.put((call, args, kwargs), True)


  def initiate(self):
    """ Start the thread associated with this object """
    if not self.__pyThread.isAlive():
      self.__working = True
      self.__pyThread.start()


  def terminate(self):
    """ Terminated the thread associated with this object """
    if self.__working:
      self.__working = False
      self.__pyThread.join()
      while not self.__work.empty():
        self.__work.get_nowait()


  def __pyThreadMain(self):
    """ Thread entry function """
    while self.__working:
      try:
        func, args, kwargs = self.__work.get(True)
        func(*args, **kwargs)
      except Exception:
        sys.excepthook(*sys.exc_info())
