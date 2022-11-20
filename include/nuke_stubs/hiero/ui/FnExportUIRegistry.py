import hiero.core
import hiero.core.log
import ui


class TaskUIRegistry ( ui.IExporterUIRegistry ):
  """ Registry/factory for ITaskUI and IProcessorUI objects. """

  def __init__( self ):
    ui.IExporterUIRegistry.__init__(self)
    # _taskUIs[ str(type(TASK)) ] = TASKUI
    self._taskUIs = dict()
    # _processorUIs[ str(type(PROCESSOR)) ] = PROCESSORUI
    self._processorUIs = dict()
    self._instances = []
    

  def registerTaskUI(self, taskPreset, taskUI):
    """Register an ITaskUI class and associate with an ITaskPreset class """
    presetInstance = taskPreset("dummypreset", dict())
    instance = taskUI(presetInstance)
    self._taskUIs[presetInstance.ident()] = instance
    hiero.core.log.debug( "Task UI Registered " + str(taskPreset) + " " + str(taskUI) )
  

  def registerProcessorUI( self, processorPreset, processorUI):
    """Register IProcessorUI class and associate with IProcessorPreset class """
    hiero.core.log.debug( "registerProcessorUI" )
    presetInstance = processorPreset("dummypreset", dict())
    instance = processorUI(presetInstance)
    self._processorUIs[presetInstance.ident()] = instance
    hiero.core.log.debug( "Processor UI Registered " + str(processorPreset) + " " + str(processorUI) )


  def numTaskUIs( self ):
    """ Get the number of registered ITaskUI classes. """
    return len(self._taskUIs)
    

  def numProcessorUIs( self ):
    """ Get the number of registered IProcessorUI classes. """
    return len(self._processorUIs)
    

  def getTaskUI( self, index ):
    """ Return TaskUI registered at specified index """
    # Note: This is indexing into a dict, which isn't ordered.  Should it be?
    taskUI = list(self._taskUIs.values())[index]
    return taskUI
    

  def getProcessorUI( self, index ):
    """ Return ProcessorUI registered at specified index """
    # Note: This is indexing into a dict, which isn't ordered.  Should it be?
    return self.processorUIByIndex(index)
    

  def processorUIByIndex( self, index ):
    """Return ProcessorUI registered at specified index"""
    processorUI = list(self._processorUIs.values())[index]
    return processorUI
  

  def getTaskUIForPreset( self, preset ):
    """ Return TaskUI object associated with the preset type.  Note that this
    returns a stored instance of the preset, which is suitable for calling
    from C++ code.  For actually constructing UIs, getNewTaskUIForPreset()
    should be called to create a new object."""
    if preset.ident() in self._taskUIs:
      return self._taskUIs[preset.ident()]
    return None


  def getNewTaskUIForPreset(self, preset):
    """ Get a new instance of the task UI class for the preset. """
    ui = self.getTaskUIForPreset(preset)
    if ui:
      ui = type(ui)(preset)
    return ui


  def getProcessorUIForPreset ( self, preset ):
    """ Return ProcessorUI object associated with the preset type.  Note that
    this returns a stored instance of the preset. """
    if preset.ident() in self._processorUIs:
      return self._processorUIs[preset.ident()]
    hiero.core.log.error("Could not find %s in %s" % (str(type(preset)), str(list(self._processorUIs.keys()))))
    return None


# wrap this in a try block, as some functionality is missing from Player
try:
  taskUIRegistry = TaskUIRegistry()
  taskUIRegistry.registerme()
except:
  pass
