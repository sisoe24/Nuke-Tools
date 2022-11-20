# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.


from . import util
from hiero.core import (IExporterRegistry,
                       log,
                       TaskBase,
                       TaskPresetBase,
                       project,
                       Format,
                       isNC,
                       isIndie,
                       FnFloatRange,
                       util,
                       FolderTask,
                       FolderTaskPreset)
from hiero.core.FnExporterBase import classBasename
import _nuke
import xml.etree.ElementTree as etree
from xml.dom import minidom
import glob
import re
import os
import shutil
import sys
import copy
import _fnpython
import hashlib
import itertools
import errno


class ExportHistory(object):
  def __init__(self, presets=[]):
    self._presets = presets

  def findPreset(self, presetId):
    for preset in self._presets:
      if preset._properties["id"] == presetId:
        return preset
    return None

  def addPreset(self, preset):
    presetId = taskRegistry.getPresetId(preset)

    if self.findPreset(presetId) == None:
      presetCopy = taskRegistry.copyPreset(preset)
      presetCopy.properties()["id"] = presetId
      self._presets.append(presetCopy)

    return presetId

  def presets(self):
    return self._presets


class TaskRegistry ( IExporterRegistry ):
  
  def __init__( self ):
    IExporterRegistry.__init__(self)
    # _tasks [str(type(task))] = type(task)
    self._tasks = dict()
    # _processors [str(type(processor))] = type(processor)
    self._processors = dict()
    # _presets [preset.parentType()] = type(preset)
    self._presets = dict()
            
    # _presets [filenameWithoutExtenion] = exporterpresetinstance
    self._processorPresets = []
    
    self._defaultPresets = None
    
    # Mapping of string type names to the types. This is used for serializing values
    # in presets
    self._typeDict = dict((classBasename(valuetype), valuetype) for valuetype in (int, tuple, bool, str, float, list, dict, type(None)))

    # In Python 2 Nuke, strings might have been saved as 'str' or 'unicode' make
    # sure they get loaded
    self._typeDict['unicode'] = str

    self._submissions = []
    self._currentSubmissionName = None

    self._projectExportHistories = dict()

    # A list of presets which are stored while the user is editing them.  Kept so the pre-edit state
    # can be restored.
    self._storedPresets = []

    
  def registerTask(self, preset, task):
    """Register the association between a Task and TaskPreset"""
    self._tasks[classBasename(task)] = task
    self.registerPreset( task, preset )
    log.info( "Task Registered " + str(task) )
       
  def registerProcessor (self, preset, processor):
    """Register the association between a Processor and ProcessorPreset"""
    self._processors[classBasename(processor)] = processor
    self.registerPreset( processor, preset )
    log.info( "Processor Registered " + str(processor) )
     
  def registerPreset( self, parentType, preset ):
    """Register a preset instance and association with parentType"""
    self._presets[classBasename(parentType)] = preset
  
  def projectUnloaded(self, project):
    """Called on project unload to remove presets associated with project"""
    log.debug("ExportRegistry : Project %s Presets Unloaded"  % project.name())
    presets = self.projectPresets(project)
    for preset in presets:
      try:
        preset.setMarkedForDeletion()
        self._processorPresets.remove(preset)
      except Exception as e:
        log.error("Couldn't delete preset %s from list %s" % (preset.name(), ", ".join(presets)))
        log.error(str(e))

    if project in self._projectExportHistories:
      del self._projectExportHistories[project]


  def projectDuplicated ( self, project, newProject ):
    """Called on project clone to duplicate the associated project presets"""
    log.debug("ExportRegistry : Project %s Presets Duplicated" % project.name())

    # Duplicate the project presets
    presets = self.projectPresets(project)
    for preset in presets:
      newpreset = self.copyPreset(preset)
      # Assign preset to the duplicated project
      newpreset.setProject(newProject)
      newpreset.setReadOnly(preset.readOnly())
      self._processorPresets.append(newpreset)

    # Duplicate the project history xml
    historyXml = self.projectExportHistoryXml(project)
    self.restoreProjectExportHistoryXml(newProject, historyXml)

  
  def loadPresets ( self, path ):
    """Load all xml presets within specified path and register"""
    processorPresetResult = self._loadPresets(os.path.join(path, "Processors"), self._processorPresets)
    return processorPresetResult


  def _loadPresets ( self, path, list ):
    # If path doesn't exist there are no presets to load.
    if not util.filesystem.exists(path):
      return False

    dictionary = dict([ (preset.name(), preset) for preset in list if not preset.project() and not preset.markedForDeletion()])
    # for each file in each subdirectory 
    for dir in os.listdir(path):

      presets = glob.glob(os.path.join(path, dir, "*.xml"))
 
      for filepath in presets:
        try:
          # open file and parse xml
          file = util.filesystem.openFile(filepath, 'r')
        except Exception as e:
          log.error("Unable to open preset file : %s \n%s" % (filepath, str(e)) )
          continue
          
        # extract preset name from the filename
        presetName = os.path.splitext(os.path.basename(filepath))[0]
        preset = None
        try :
          preset = self.presetFromXml ( file.read(), False )
        except Exception as e:
          log.exception( "Failed to build preset from file: %s\n%s",  filepath, str(e) )
        
        # if preset was successfully created
        if preset:
          log.info( "Loaded preset : " + presetName )
          
          # If don't have write permissions for file, set preset as read only
          if not util.filesystem.access(filepath, os.W_OK):
            preset.setReadOnly(True)
          
          # ensure no name clash
          if presetName in dictionary:
            if dictionary[presetName].savePath() != path:
              presetName = util.uniqueKey(presetName, dictionary)
            else:
              continue
              
          preset.setName(presetName)

          # Keep the path the preset was loaded from so it can be saved back there
          preset.setSavePath(path)

          # add to registry
          self.addProcessorPreset(presetName, preset)

    return True
        
  def presetFromXml ( self, xml, register = True):
    """Deserialize preset from xml string.
    Requires derived TaskPreset classes to be registered."""
    preset = None
    
    # Create a dictionary where the key is a string representation of the Task
    # and the value is the type(Task). Used to figure out the Task type and instantiate.
    taskTypeDict = {}
    taskTypeDict.update(dict((classBasename(value), self._presets[key]) for (key, value) in list(self._tasks.items())))
    taskTypeDict.update(dict((classBasename(value), self._presets[key]) for (key, value) in list(self._processors.items())))

    try:
      root = etree.XML(xml)
    except Exception as e:
      log.error( "Error Parsing XML\n" + str(e) )
      raise
      
    #the Task type is store as a string attribute on the root node
    taskType = root.get("tasktype")        
    presetName = root.get("presetname", "New Preset")
    properties = {}
    
    # ensure this task exists in the registry
    if taskType is not None:
      if taskType in taskTypeDict:
      
        # each element in root represents one preset property        
        for element in root:
          properties[element.tag] = self._loadPresetElement(element)
        
        # Instantiate preset type and add to registry
        preset = taskTypeDict[taskType]("preset", properties)
        preset.setName(presetName)
        
        # Register preset incase it is being passed back to C++ 
        # otherwise object will be cleaned up when reference goes out of scope
        if register:
          self.addProcessorPreset(presetName, preset)
          
      else:
        log.error( "Error! Task type %s Not recognised " % taskType )
        
    return preset
  
  def _loadPresetElement ( self, element ):
    # lookup 'valuetype' in type dictionary. 
    typeName = element.get("valuetype")
    
    elementtext = element.text
    if elementtext is not None:
      elementtext = elementtext.strip()

    if typeName in self._typeDict:
      valueType = self._typeDict[typeName]
      # If the this is a nested dictionary, recurse
      if valueType is dict:
        properties = {}
        for childElement in element:        
          properties[childElement.tag] = self._loadPresetElement(childElement)
        return properties
      elif valueType in (list, tuple):
        properties = []
        for childElement, index in zip(element, list(range(0, len(element)))):
          properties.append(self._loadPresetElement(childElement))
        return valueType(properties)
      elif valueType is bool:
        return elementtext == 'True'
      elif valueType is type(None):
        return None
      elif valueType is str and not element.text:
        return valueType("")
      else:     
        # instantiate value as correct type and assign to dictionary 
        # with element name as the key
        return valueType(elementtext)
    elif typeName in [ classBasename(value) for value in list(self._presets.values()) ] :
      try:
        preset = self.presetFromXml(etree.tostring(element.find("root")), False)
        return preset
        
      except Exception as e:
        log.error( "Failed to parse nested Preset " + str(e) )
        return None
    else:
      log.error( "Type " + typeName + " not recognised" )
      return None
      
  
  def savePresets ( self, path ):
    """ Save all registered presets, as xml, to path specified. """
    try:
      # Clear the stored presets, which means projectPresetsChanged() and localPresetsChanged() will return False until after another startPresetChanges() and then any modifications.
      # The relevant C++ code is now using modification times to keep track of project preset modifications.
      self._storedPresets = []

      processorPresetResult = self._savePresets(os.path.join(path, "Processors"), self._processorPresets, self._processors)

      return processorPresetResult
    except Exception as e:
      log.error("Could not write to preset path %s. Check permissions" % path)
      log.error("Exception : " + str(e))
      return False


  def _savePresets ( self, path, presetlist, dictionary ):
    # for each preset in the dictionary
    for preset in presetlist:
      
      presetName = preset.name()
      
      newPath = None

      savePath = preset.savePath()
      
      # This preset will be saved within the project file
      if preset.project() is not None:
        continue
      
      # If this preset is set as ReadOnly don't try and write to it.
      if preset.readOnly():
        continue
        
      # If the preset was loaded from XML, try to save it back to its original location.  
      # If that's not writeable, we save it to the default path.      
      if savePath:
        newPath = os.path.join(preset.savePath(), classBasename(preset.parentType()), presetName+".xml")
        if util.filesystem.exists(newPath) and not util.filesystem.access(newPath, os.W_OK):
          newPath = None
    
      if not newPath:
        # build a path <root>/<taskname>/<presetname>.xml
        newPath = os.path.join(path, classBasename(preset.parentType()), presetName+".xml")
    
      if preset.markedForDeletion():
        # Preset has been marked for deletion, remove file and skip xml generation
        try:
          os.remove(newPath)
        except OSError as e:
          if e.errno == errno.ENOENT:
            # The file might not exist if the preset was added then removed without it being saved
            # Don't log an error
            pass
          else:
            hiero.core.log.exception("Failed to delete preset file")
        
        continue
            
      # if path doesn't already exist, create it
      dstDir = os.path.dirname(newPath)
      try:
        util.filesystem.makeDirs(dstDir)
      except:
        log.error("Could not create preset path %s. Check permissions" % dstDir)
        return False

      # build xml from preset
      xml = self.presetToPrettyXml(preset)
      
      try:
        # open and write to file
        file = util.filesystem.openFile(newPath, 'w')
        file.write(xml)
        log.info( "Saved Preset : " + presetName + " to: " + newPath )
      except:
        log.info( "Failed to write preset to path: %s", newPath )
        return False
      
    return True
    
  def presetToXml ( self, preset ):
    """Serialise a TaskPreset to XML and return as string. 
    Returns an empty string on failure.
    """
    try:
      root = self._presetToXml(preset)
      return etree.tostring(root).decode()
    except TypeError:
      return ''
    

  def _presetToXml ( self, preset ):
    """ Serialize a preset to XML and return the root element. Throws on failure. """
    if issubclass(type(preset), TaskPresetBase):
      # create a root node with the task type as an attribute
      root = etree.Element("root", tasktype=classBasename(preset.parentType()), presetname=preset.name())       
      # for each key value pair in the properties dictionary, create an element
      for (key, value) in list(preset._properties.items()):
        # add the type(value) as an attribute
        self._savePresetElement( key, value, root)
      return root
    else:
      raise TypeError("Unexpected type %s" % type(preset))
    

  def _savePresetElement (self, key, value, parent):
    """ Save a preset key/value as an XML element and append it to the parent.  Called recursively for containers. """

    # Check for the objects with the Default type, and extract the wrapped value
    if isinstance(value, FnFloatRange.Default):
      value = value.value()

    valueType = type(value)

    # Is the export of this value type supported?
    if classBasename(valueType) in self._typeDict or issubclass( valueType, TaskPresetBase ) or hasattr(value, '_toXml'):
      # Add New Element
      element = etree.Element( str(key), valuetype=classBasename(valueType) )
      parent.append(element)

      # If this is a nested dictionary, recurse
      if valueType is dict:
        for (childKey, childValue) in list(value.items()):
          self._savePresetElement( childKey, childValue, element )
      elif valueType in (list, tuple):
        for child, index in zip(value, list(range(0, len(value)))):
          self._savePresetElement( "SequenceItem", child, element)
      elif issubclass( valueType, TaskPresetBase ):
        element.append(self._presetToXml(value))
      elif hasattr(value, '_toXml'):
        value._toXml(element)
      else:
        element.text = str(value)
    else:
      log.error( "Warning: Invalid property Name: " + str(key) + " of Type: " + str(valueType) )

  def presetsSubDirectory(self):
    # Task presets are now versioned. They are stored in a sub-directory with
    # Nuke version information under TaskPresets.
    env = _nuke.env
    major = env["NukeVersionMajor"]
    minor = env["NukeVersionMinor"]
    phase = env["NukeVersionPhase"]
    versionString = "%s.%s" % (major, minor)
    # For non-final release builds, a 'beta' suffix is also added. Phase will
    # empty for a release build.
    if phase:
      versionString += "beta"
    return os.path.join("TaskPresets", versionString)

  def revertDefaultPresets(self):
    if callable(self._defaultPresets):
      self._defaultPresets(True)
    else:
      log.error("Default Preset callback not set")

  def setDefaultPresets(self, defaultPresets):
    self._defaultPresets = defaultPresets
  
  def addDefaultPresets(self, overwrite=False):
    if callable(self._defaultPresets):
      self._defaultPresets(overwrite)
    else:
      log.error("Default Preset callback not set")


  def startPresetChanges(self, project):
    # Create copies of all the local and project presets and store them so they can be restored if necessary
    local = self.localPresets()
    project = self.projectPresets(project) if project is not None else []

    self._storedPresets = []
    for preset in itertools.chain(local, project):
      presetCopy = self.copyPreset(preset)
      presetCopy.setProject(preset.project()) # Give the copy the same project
      self._storedPresets.append(presetCopy)


  def discardPresetChanges(self, project):
    if not self._storedPresets:
      return

    # Remove presets which are local or belong to this project from the main preset list
    self._processorPresets = [preset for preset in self._processorPresets if preset.project() not in (project,None)]

    # Restore the stored presets to the list
    self._processorPresets.extend(self._storedPresets)
    self._storedPresets = []


  def createAndAddProcessorPreset ( self, name, typeTemplate):
    project = None
    dictionary = dict([ (p.name(), p) for p in self._processorPresets if p.project() == project and not p.markedForDeletion()])
    fixedName = util.uniqueKey(name, dictionary)
    preset = type(typeTemplate)(fixedName, dict())
    self._processorPresets.append(preset)
    preset.setName(fixedName)
    return preset

  def copyPreset(self, preset):
    """ Create a copy of a preset.  The copy is not added to the registry. """

    # The best way to deep copy this is just to serialize to/from xml
    # Python deep copy doesn't work quite right.
    xml = self.presetToXml(preset)
    presetCopy = self.presetFromXml(xml, False)
    return presetCopy
    
  def copyAndAddProcessorPreset ( self, preset ):
    project = preset.project()
    dictionary = dict([ (p.name(), p) for p in self._processorPresets if p.project() == project and not p.markedForDeletion()])
    fixedName = util.uniqueKey(preset.name(), dictionary)

    newpreset = self.copyPreset(preset)
    newpreset.setName(fixedName)
    newpreset.setProject(project)
    self._processorPresets.append(newpreset)

    return newpreset
  
  def copyAndAddProjectPreset ( self, preset, project ):
    """Duplicate a preset and assign it to a project imediately to prevent name clashes"""
    newpreset = self.copyPreset(preset)
    newpreset.setProject(project)
    self.addProcessorPreset(newpreset.name(), newpreset)
    return newpreset
    
  def addProcessorPreset (self, name, preset):
    """Register Processor Preset Instance"""
    dictionary = dict([ (p.name(), p) for p in self._processorPresets if p.project() == project and not p.markedForDeletion()])
    uniqueName = util.uniqueKey(name, dictionary)
    preset.setName(uniqueName)
    self._processorPresets.append(preset)
  
  def removeProcessorPreset ( self, preset ):
    """Remove Processor preset from registry"""
    presetName = None
    
    # This function used to accept a preset name to identify preset from removal
    # Now preset name uniqueness isn't as strictly enforced because presets can be in different projects
    # If preset is a string then search for a preset with that name 
    if isinstance(preset, str):
      presetName = preset
      for p in self._processorPresets:
        if presetName == p.name():
          preset = p
          break
    elif hasattr(preset, "name"):
      presetName = preset.name()
      
    if preset in self._processorPresets:
      self._processorPresets.remove(preset)
    else:
      log.info( "Preset '%s' cannot be deleted as it is not registered" % (presetName, ) )
    
  def renameProcessorPreset (self, preset, newName):
    """Validate and update name of Processor Preset"""
    project = preset.project()
    presets = dict([ (p.name(), p) for p in self._processorPresets if p.project() == project and not p.markedForDeletion()])   
    
    fixedName = util.uniqueKey(newName, presets)
    preset.setName(fixedName)
    
  def assignPresetToProject (self, preset, project):
    """Assign preset to project and ensure name is unique within project. Project may be None in which case preset will be assigned 'local'"""
    if project and project.isNull():
      project = None
    # Build a dictionary of presets already assigned to specified project (Even if project is None)
    presets = dict([ (p.name(), p) for p in self._processorPresets if p.project() == project and not p.markedForDeletion()])    
    
    # If preset name already exists within this subset
    if preset.name() in presets:
      # Find a unique name
      fixedName = util.uniqueKey(preset.name(), presets)
      preset.setName(fixedName)
    
    preset.setProject(project)

  def numProcessorPresets(self) :
    """Return the total number of Processor preset instances registered"""
    return len(self._processorPresets);
  
  def processorPresetName(self, index):
    """Return the name of Processor preset by index"""
    return list(self._processorPresets.values())[index].name()
 
  def numTasks( self ) :
    """Returns the number of Tasks Registered"""
    return len(self._tasks)
    
  def numProcessors(self):
    """Return the number or processors in the Registry"""
    return len(self._processors)
      
  def taskName ( self, index ):
    """Returns a Task name by Index"""
    return list(self._tasks.keys())[index]

  def processorName ( self, index ):
    """Returns a Processor name by index"""
    return list(self._processors.keys())[index]
    
  def processorPresetNames(self):
    """Returns a tuple of Processor Preset names"""
    return [preset.name() for preset in self._processorPresets]
    
  def processorPresetByName(self, name, project=None):
    """Returns the preset with specified name associated with project. If project is None preset will be searched for in local presets"""
    presets = self.projectPresets(project)
    for preset in presets:
      if name == preset.name():
        return preset
    return None


  def _getPresetsFromList( self , presetsList , projectToFilter ):
    """Returns a list of presets name associated with 'projectToFilter' from the specified 'presetsList'"""
    presets = [ preset for preset in presetsList if preset.project() == projectToFilter and not preset.markedForDeletion()]
    return presets

  def projectPresets(self, project):
    """Returns a list of preset names associated with the specified project"""
    return self._getPresetsFromList( self._processorPresets , project )
    
  def localPresets(self):
    """Returns a list of preset names NOT associated with the specified project"""
    return self._getPresetsFromList( self._processorPresets , None )


  def projectExportHistoryXml(self, project):
    """ Get the project export history as a list of xml fragments. Use the xml to avoid problems with reference
        counting the preset objects when calling from C++. """
    try:
      return [ self.presetToXml(preset) for preset in self._projectExportHistories[project].presets() ]
    except:
      return []


  def restoreProjectExportHistoryXml(self, project, presetsXml):
    """ Set the project export history as a list of xml fragments. Use the xml to avoid problems with reference
        counting the preset objects when calling from C++. """
    presets = [ self.presetFromXml(presetXml, False) for presetXml in presetsXml ]
    self._projectExportHistories[project] = ExportHistory(presets)


  def addPresetToProjectExportHistory(self, project, preset):
    """ Add a preset to the export history for a project. """
    try:
      history = self._projectExportHistories[project]
    except:
      history = ExportHistory()
      self._projectExportHistories[project] = history
    return history.addPreset(preset)


  def findPresetInProjectExportHistory(self, project, presetId):
    """ Attempt to find a preset in a project's export history. """
    try:
      return self._projectExportHistories[project].findPreset(presetId)
    except:
      return None


  def _computePresetsHash(self, presets):
    # Create a hash of the current state of the given list of task presets, returning None if the list is empty.
    if not presets:
      return None
    m = hashlib.md5()
    for preset in presets:
      m.update( self.presetToXml(preset) )
    return m.digest()


  def getPresetId(self, preset):
    """ Get the id (hash) of the given preset. """

    # If the preset has the id set as a property on it, use that.  This should only be the case
    # for presets which have been added to the export history.
    if "id" in preset.properties():
      return preset.properties()["id"]
    else:
      # We don't want the version to change the id, set it to 1 before computing the hash
      version = preset.properties()["versionIndex"]
      preset.properties()["versionIndex"] = 1
      presetXml = self.presetToXml(preset)
      preset.properties()["versionIndex"] = version

      presetHash = hashlib.md5()
      presetHash.update(presetXml.encode())
      return presetHash.hexdigest()


  def localPresetsChanged(self):
    """ Check if the local task presets have changed since startPresetChanges() was called. """

    localPresets = list( sorted( self.localPresets() , key = lambda preset : preset.name() ) )
    storedLocalPresets = list( sorted( self._getPresetsFromList( self._storedPresets , None ) , key = lambda preset : preset.name() ) )
    return localPresets != storedLocalPresets

  def projectPresetsChanged(self, project):
    """ Check if the task presets for the given project have changed since startPresetChanges(project) was called. """

    storedProjectPresets = list( sorted( self._getPresetsFromList( self._storedPresets , project ) , key = lambda preset : preset.name() ) )
    projectPresets = list( sorted( self.projectPresets(project) , key = lambda preset : preset.name() ) )
    return storedProjectPresets != projectPresets
    
  def getProcessor(self, index):
    return self.processorByIndex(index)
  
  def processorByIndex(self, index):
    """Returns a processor by index"""
    return list(self._processors.values())[index]
  
  def getPresetType (self, ident):
    return self.presetTypeFromIdent(ident)
    
  def presetTypeFromIdent(self, ident):
    """Resolve preset ident string to Preset class type"""
    if ident in self._presets:
      return self._presets[ident]
    return None
    
  def createTaskFromPreset(self, preset, initDictionary):
    if preset.ident() in self._tasks:
      taskType = self._tasks[preset.ident()]
      return (taskType)(initDictionary)
    return None
    
  def getProcessorFromPreset (self, presetName):
    return self.processorFromPreset (presetName)
    
  def processorFromPreset (self, presetName):
    """Return type of task from preset name"""
    preset = self._processorPresets[presetName]
    processor = self._processors[preset.ident()]
    return processor  


  def _checkPresetToFormat(self, presetName, exportTemplate):
    """Checks if 'exportTemplate' defines a specific output format and if its
    valid by creating a hiero.core.Format.
    Raises a ValueError exception if a format is not valid.
    """
    for exportPath, presetTask in exportTemplate:
      toFormat = presetTask.properties().get('reformat',None)
      if toFormat and toFormat['to_type'] == 'to format':
        try:
          Format( toFormat['width'],toFormat['height'],toFormat['pixelAspect'],toFormat['name'])
        except ValueError as e:
          raise ValueError( "The selected Preset '%s' has an invalid output resolution.\n%s" % (presetName, e.message) )


  def _getToScaleFromPreset(self, exportTemplate):
    """Returns a list of scale options defined in 'exportTemplate'
    """
    outToScale = []
    for exportPath, presetTask in exportTemplate:
      toScale = presetTask.properties().get('reformat',None)
      if toScale and toScale['to_type'] == 'scale':
        outToScale.append( toScale['scale'] )
    return outToScale


  def _checkToScaleForSequence(self, presetName, toScaleOptions, itemName, seqFormat):
    """Checks if the output format for a specific sequence/clip is valid when
    scalled with th 'scale' option defined in the exportTemplate preset.
    Raises a ValueError exception if a format is not valid.
    """
    for toScale in toScaleOptions:
      try:
        Format( seqFormat.width() * toScale, seqFormat.height() * toScale, seqFormat.pixelAspect() , seqFormat.name() )
      except ValueError as e:
        raise ValueError("Unable to export '%s' because Preset '%s' is scalling it to an invalid output resolution.\n%s" % (itemName, presetName, e.message) )


  def _checkOutputResolution(self, preset, items):
    """Checks if the output resolution defined in the preset or defined by the
    items to be exported are valid for PLE / Indie variants.
    Raises a ValueError exception if a format is not valid.
    """
    if isNC() or isIndie():
      exportTemplate = preset.properties()['exportTemplate']
      presetName = preset.name()

      # check 'to format' for preset
      self._checkPresetToFormat(presetName, exportTemplate)

      presetToScale = self._getToScaleFromPreset(exportTemplate)
      for itemWrapper in items:
        item = itemWrapper.clip()
        if not item:
          item = itemWrapper.sequence()

        # checks item format
        itemFormat = None
        try:
          itemFormat = item.format()
          # create format to know if it's allowed
          itemFormat = Format( itemFormat.width(), itemFormat.height(), itemFormat.pixelAspect() , itemFormat.name())
        except ValueError as e:
          raise ValueError("Unable to export item %s.\n%s" % (item.name(), e.message))

        # checks scalled item format
        self._checkToScaleForSequence(presetName, presetToScale, item.name(), itemFormat)


  def validateExport(self, preset, items):
    """ Implements IExporterRegistry.validateExport """
    # Check the output resolution
    try:
      self._checkOutputResolution(preset, items)
    except ValueError as e:
      return str(e)

    # Generate tasks and validate them
    try:
      processor = self.createProcessor(preset)
      tasks = processor.startProcessing(items, preview=True)
      for task in tasks:
        task.validate()
    except Exception as e:
      return str(e)

    # All ok, return an empty string
    return str()


  def createProcessor(self, preset, submissionName=None, synchronous=False):
    """ Create the processor for an export and return it. This doesn't start
    the export.
    """
    # Create the submission.  If no name was given choose the first in the list
    if not submissionName:
      submissionName = self._submissions[0][0]

    submission = self.submissionByName(submissionName)
    if not submission:
      raise RuntimeError( "Submission class not found for name %s, valid names are: %s" % (submissionName, ", ".join(self.submissionNames())) )

    submission.initialise()

    processor = self._processors[preset.ident()](preset, submission, synchronous=synchronous)
    processor.setPreset(preset)
    return processor


  def createAndExecuteProcessor( self, preset, items, submissionName=None, synchronous=False ):
    """Instantiate the Processor associated with preset and startProcessing items"""

    self._checkOutputResolution(preset, items)

    try:
      processor = self.createProcessor(preset, submissionName, synchronous)
      processor.startProcessing(items)

    except:
      # Problems with the export are caught and set error messages on the individual tasks, and the exception
      # that arrives here doesn't contain any useful information.  Get the error string from the processor and
      # raise a new exception from that.
      errorString = processor.errors()
      if errorString:
        raise RuntimeError( processor.errors() )
      else:
        raise



  def getProcessorPreset ( self, index ):
    return self.processorPresetByIndex ( index )
    
  def processorPresetByIndex ( self, index ):
    """Return instance of TaskPreset Object"""
    return list(self._processorPresets.values())[index]


  def submissionNames(self):
    return [ submission[0] for submission in self._submissions ]

  def submissionByName(self, name):
    for n, submissionClass in self._submissions:
      if n == name:
        return (submissionClass)()

  def addSubmission(self, name, submissionClass):
    self._submissions.append( (name, submissionClass) )

  def submissionChanged(self, submissionName):
    self._currentSubmissionName = submissionName

  def isNukeShotExportPreset(self, preset):
    """ Check if a preset is valid for Nuke shot export.  To be considered valid, the preset must contain
        a NukeShotExporter and a NukeRenderTask (write node). """

    kNukeShotTaskName = 'hiero.exporters.FnNukeShotExporter.NukeShotExporter'
    kWriteNodeTaskName = 'hiero.exporters.FnExternalRender.NukeRenderTask'

    hasNukeShotExporter = False
    hasWriteNode = False

    for itemPath, itemPreset in preset.properties()["exportTemplate"]:
      if isinstance(itemPreset, TaskPresetBase):
        itemIdent = itemPreset.ident()
        if itemIdent == kNukeShotTaskName:
          hasNukeShotExporter = True
        elif itemIdent == kWriteNodeTaskName:
          hasWriteNode = True

    return (hasNukeShotExporter and hasWriteNode)


  def nukeShotExportPresets(self, project):
    """ Get a list of presets which can export shots as Nuke scripts.
        Includes local presets and those in the project. """
    presets = []
    for preset in itertools.chain(self.localPresets(), self.projectPresets(project)):
      if self.isNukeShotExportPreset(preset):
        presets.append(preset)
    return presets


  def isSingleSocketAllowed(self):
    """ Return whether or not single socket exports are allowed. """
    singleSocketAllowed = self._currentSubmissionName == "Single Render Process" and util.hasMultipleCPUSockets()
    return singleSocketAllowed


taskRegistry = TaskRegistry()
log.debug( str(taskRegistry) )
taskRegistry.registerme()

# Register Base Task - This will create structures when no format 
# Do this here, because FnExporterBase gets imported in __init__.py before FnExportRegistry.py
taskRegistry.registerTask(TaskPresetBase, TaskBase)

# Register folder task
taskRegistry.registerTask(FolderTaskPreset, FolderTask)
