import nuke
import string
from os import unlink as unlink
from foundry.frameserver.nuke.bases import RenderQueueObserverMixin
from foundry.ui import executeInMainThread

incompleteRenderStr = """Render did not complete, do you want to show the completed range?
Frame range contains %s frames but only %s finished."""


class SimpleFlipbook():
  #todo: extract the flipbookdialog options and the flipbooktorun options into
  #another class so that we dont need it's details
  def __init__(self, flipbookDialog, flipbookToRun):
    self._flipbookDialog = flipbookDialog
    self._flipbookToRun = flipbookToRun

  def getFlipbookOptions(self):
    #common method
    frameRange = nuke.FrameRanges(self._flipbookDialog._frameRange.value().split(','))
    views = self._flipbookDialog._selectedViews()
    return (frameRange, views)


  def getOptions(self):
    #common method
    options = self._flipbookDialog._getOptions( self._nodeToFlipbook )
    extraOptions = self._flipbookToRun.getExtraOptions( self._flipbookDialog, self._nodeToFlipbook )
    options.update( extraOptions )
    return options


  def doFlipbook(self):
    self.initializeFlipbookNode()
    self.runFlipbook()


  def initializeFlipbookNode(self):
    self._nodeToFlipbook = self._flipbookDialog._node


  def runFlipbook(self):
    #this method is used for firing up the flipbook viewer given a node
    if self._nodeToFlipbook:
      frameRange, views = self.getFlipbookOptions()
      self._flipbookToRun.runFromNode(self._nodeToFlipbook,
                                      frameRange,
                                      views,
                                      self.getOptions() )


class SynchronousRenderedFlipbook(SimpleFlipbook):

  def __init__(self, flipbookDialog, flipbookToRun):
    SimpleFlipbook.__init__(self, flipbookDialog, flipbookToRun)

  def doFlipbook(self):
    self.initializeFlipbookNode()
    self.renderFlipbookNode()


  def initializeFlipbookNode(self):
    self._nodeToFlipbook, self._writeNode = self._flipbookDialog._createIntermediateNode()


  def renderFlipbookNode(self):
    try:
      frameRange, views = self.getFlipbookOptions()
      nuke.executeMultiple((self._writeNode,),
                           frameRange,
                           views,
                           self._flipbookDialog._continueOnError.value())
    except RuntimeError as msg:
      import traceback
      print(traceback.format_exc())
      if msg.args[0][0:9] == "Cancelled":
        splitMsg = string.split(msg.args[0])
        msg =  incompleteRenderStr% (splitMsg[3], splitMsg[1])
        if nuke.ask(msg) == False:
          nuke.delete(self._nodeToFlipbook)
          self._nodeToFlipbook = None
      else:
        nuke.delete(self._nodeToFlipbook)
        self._nodeToFlipbook = None
        nuke.message("Flipbook render failed:\n%s" % (msg.args[0],))
    self.runFlipbook()



class BackgroundRenderedFlipbook(SynchronousRenderedFlipbook):

  def __init__(self, flipbookDialog, flipbookToRun):
    SynchronousRenderedFlipbook.__init__(self, flipbookDialog, flipbookToRun)

  def renderFlipbookNode(self):
    # Override of renderFlipbookNode from SynchronousRenderedFlipbook
    # this will trigger the render on a bg process that will launch the flipbook
    # on finished.
    try:
      frameRange, views = self.getFlipbookOptions()
      self._flipbookDialog._showDeprecatedWarningMessage()
      nuke.executeBackgroundNuke(nuke.EXE_PATH,
                                 [self._writeNode],
                                 frameRange,
                                 views,
                                 self._flipbookDialog._getBackgroundLimits(),
                                 self._flipbookDialog._continueOnError.value(),
                                 self._flipbookDialog._flipbookEnum.value(),
                                 self.getOptions() )
    except RuntimeError as msg:
      import traceback
      print(traceback.format_exc())
      nuke.delete(self._nodeToFlipbook)
      self._nodeToFlipbook = None
      nuke.message("Flipbook render failed:\n%s" % (msg.args[0],))

class FrameserverRenderedFlipbook(SynchronousRenderedFlipbook):
  def __init__(self, flipbookDialog, flipbookToRun):
    SynchronousRenderedFlipbook.__init__(self, flipbookDialog, flipbookToRun)


  def renderFlipbookNode(self, ):
    name, wasSaved = self._flipbookDialog.saveFileToRender("tmp_flipbook",True)
    try:
      nodeName = self._writeNode.fullName()
      frameRange, views = self.getFlipbookOptions()
      flipbookRenderPath= nuke.filename(self._nodeToFlipbook)
      options = self.getOptions()
      import hiero.ui.nuke_bridge.FnNsFrameServer as FrameServer
      task = FlipbookFrameServerTask(name,
        frameRange,
        nodeName,
        flipbookRenderPath,
        options,
        views,
        self._flipbookToRun )
      FrameServer.renderFrames(
        name,
        frameRange,
        nodeName,
        views)
    finally:
      if wasSaved:
        unlink(name)

class FlipbookFrameServerTask(RenderQueueObserverMixin):

  def __init__(self, scriptPath, frameRange, nodeName, flipbookpath, options, views,flipbookToRun):
    #flipbook options
    self._flipbookToRun = flipbookToRun
    self._flipbookpath = flipbookpath
    self._frameRange = frameRange
    self._options = options
    self._views = views
    #needed to control the observer process
    self._scriptPath = scriptPath
    self._nodeName = nodeName
    self._totalFrames = frameRange.maxFrame() - frameRange.minFrame() + 1
    self._successfulFrames = 0
    self._completedFrames = 0
    import hiero.ui.nuke_bridge.FnNsFrameServer as FrameServer
    FrameServer.addBackgroundRenderObserver(self)

  def showFlipbookWindow(self):
    try:
      if self._totalFrames != self._successfulFrames:
        msg =  incompleteRenderStr% (self._totalFrames, self._successfulFrames)
        if nuke.ask(msg) == False:
          return
      self._flipbookToRun.run(self._flipbookpath,
                              self._frameRange,
                              self._views,
                              self._options)
    except Exception as e:
      nuke.tprint(e)
    finally:
      import hiero.ui.nuke_bridge.FnNsFrameServer as FrameServer
      FrameServer.removeBackgroundRenderObserver(self)

  def renderFinished(self):
    executeInMainThread(self.showFlipbookWindow)

  def onFrameRendered(self, scriptPath, frame, nodeName):
    """ Callback when a frame is rendered.  If it's for the script being
    rendered, increment the count. """
    if scriptPath == self._scriptPath and nodeName == self._nodeName:
      self._completedFrames = self._completedFrames + 1
      self._successfulFrames = self._successfulFrames + 1
      if self._completedFrames == self._totalFrames:
        self.renderFinished()


  def onFrameRenderError(self, scriptPath, frame, nodeName, errorMsg):
    """ Callback when there is an error rendering a frame.  Set the error state
    and cancel. """
    if scriptPath == self._scriptPath and nodeName == self._nodeName:
      self._completedFrames = self._completedFrames + 1
      if self._completedFrames == self._totalFrames:
        self.renderFinished()

  def onFrameRenderCancelled(self, scriptPath, frame, nodeName):
    if scriptPath == self._scriptPath and nodeName == self._nodeName:
      self._completedFrames = self._completedFrames + 1
      if self._completedFrames == self._totalFrames:
        self.renderFinished()


def getFlipbookRenderer(flipbookDialog, flipbookToRun):
  if not flipbookDialog._requireIntermediateNode(flipbookDialog._node):
    return SimpleFlipbook( flipbookDialog, flipbookToRun )
  else:
    #require intermediateNode
    if flipbookDialog.isBackgrounded():
      return BackgroundRenderedFlipbook( flipbookDialog, flipbookToRun )
    elif flipbookDialog._frameserverRender.value():
      return FrameserverRenderedFlipbook( flipbookDialog, flipbookToRun )
    else:
      return SynchronousRenderedFlipbook( flipbookDialog, flipbookToRun )
  raise RuntimeError("No suitable Flipbook Rendered could be found")


