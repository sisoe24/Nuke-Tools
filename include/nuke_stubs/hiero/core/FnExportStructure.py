# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import xml.etree.ElementTree as etree
from hiero.core.FnExporterBase import classBasename
from hiero.core import (IExportStructure,
                        IExportStructureElement,
                        TaskPresetBase,
                        TaskBase,
                        FolderTaskPreset,
                        taskRegistry,
                        log)
import os.path

class ExportStructure2 (IExportStructure):
  """ ExportStructure2 is the implementation of the datastructure used to represent
  the export tree, each node within the tree is represented by an ExportStructureElement.
  Although this matches how the export presets are viewed in the UI, when it comes
  running an export, or persisting the structure, it is flattened into a list
  of paths and task presets.
  """

  def __init__(self):
    IExportStructure.__init__ (self)
    self._rootElement = ExportStructureElement("root", True)
    self._exportRootPath = "{projectroot}"


  def rootElement ( self ):
    """Return the root element in this hierarchy.
    The root element is not included in the path generation"""
    return self._rootElement


  def findElementsByPath(self, path):
    """ Find the elements matching path. Returns a list. """
    return self._rootElement.findElementsByPath(path)


  def exportRootPath ( self ):
    """Returns the exportRootPath, the root of the export into which the export structure is built"""
    return self._exportRootPath


  def setExportRootPath ( self, rootPath ):
    """Set the exportRootPath, the root of the export into which the export structure is built"""
    self._exportRootPath = rootPath


  def _fromXml (self, element):
    self._rootElement._fromXml(element.find("root"))
    self._exportRootPath = taskRegistry._loadPresetElement(element.find("exportPath"))


  def _toXml (self, parent):
    rootElement = etree.Element( "root", valuetype=classBasename(ExportStructureElement) )
    self._rootElement._toXml(rootElement)
    taskRegistry._savePresetElement( "exportPath", self._exportRootPath, parent)


  def restore ( self, sequence ):
    """Restore the hierarchy from a list of (path, preset) tuples"""
    self._rootElement = ExportStructureElement("root", True)
    for path, preset in sequence:
      parent = self.rootElement()
      child = None
      path.replace('\\', '/')
      child = self.rootElement().createChildFromPreset(path, preset)


  def _traverse ( self, element ):
    """ Helper for flatten. Recursively traverse the structure, building a list
    of (path, preset) tuples for each element with no children.
    """
    leafElements = []
    for child in element.children():
      if child.childCount() == 0:
        path = child.path()
        if not child.isLeaf():
          path += '/'
        leafElements.append((path, child.preset()))
      else:
        leafElements += self._traverse(child)
    return leafElements


  def flatten ( self ):
    """Return the hierarchy as a list of (path, preset) tuples"""
    flattened = self._traverse(self.rootElement())
    return flattened
    
    
  def __repr__ (self):
    return str(self.rootElement())



class ExportStructureElement (IExportStructureElement):
  """ExportStructureElement represents a node within the export structure"""
  
  def __init__ ( self, name, isFolder ):
    IExportStructureElement.__init__(self)

    if '/' in name:
      raise RuntimeError("Cannot use '/' in element name.")
    
    self._name = name
    self._parent = None
    self._children = []

    if isFolder:
      self.setPreset( FolderTaskPreset("folder", {}) )
    else:
      self.setPreset( TaskPresetBase(TaskBase, "empty") )

    # Clients can register callbacks to be notified when path changes.
    self._callbacks = []
    

  def preset ( self ):
    """Return the preset assigned to this Element. May be None"""
    return self._preset


  def setPreset ( self, preset ):
    """Set the preset assigned to this Element. May be None"""
    assert (preset is None or isinstance(preset, TaskPresetBase)), "unexpected type %s" % type(preset)
    self._preset = preset


  def setPresetType ( self, identifier ):
    """setPresetType(self, identifier)
    @param identifier : Unique identifier from the Task which is used to associate the preset type"""
    newPreset = None
    data = self._preset.properties() if self._preset else {}
    if identifier:
      presetType = taskRegistry.getPresetType(identifier)      
      if presetType:
        newPreset = presetType(identifier, data)

    # If the preset type wasn't found in the registry, create a default one.
    # Not sure this is the correct behaviour.
    if not newPreset:
      newPreset = TaskPresetBase(TaskBase, "empty")
      newPreset._properties.update(data)

    self.setPreset(newPreset)


  def path ( self ):
    """Return the path of this Element"""
    if self.parent() is not None:
      return os.path.join(self.parent().path(), self.name()).replace('\\', '/')
    return ""


  def name ( self ):
    """Return the name of this Element"""
    return self._name


  def setName ( self, name ):
    """ Set the name of this element. """
    if '/' in name:
      raise RuntimeError("Cannot use '/' in element name.")

    oldPath = self.path()
    self._name = name
    self.pathChanged(oldPath)


  def pathChanged(self, oldPath):
    """ Notify children and any observers that the element's path has changed. """
    newPath = self.path()
  
    # Notify callbacks
    for callback in self._callbacks:
      callback(oldPath, newPath)
      
    # Notify children
    for child in self.children():
      child.pathChanged(os.path.join(oldPath, child.name()).replace('\\', '/'))


  def addPathChangedCallback( self, callback):
    """ Add a callback to be notified when the path of this element has changed,
    callbacks should take the arguments (oldPath, newPath).
    """
    if callable(callback):
      if callback not in self._callbacks:
        self._callbacks.append(callback)
    else:
      raise TypeError("callback must be callable")


  def isLeaf ( self ):
    """Returns True if node is flagged as leaf and may not accept children"""
    return not isinstance(self._preset, FolderTaskPreset)


  def parent ( self ):
    """Return the parent element of this Element"""
    return self._parent


  def _setParent ( self, parent ):
    """Set the parent element of this Element. Note: this is an internal method
    and should not be called directly. Elements should be added to a parent by
    calling parent.addChild() """
    oldPath = self.path() # Get the path based on the old parent
    self._parent = parent
    self.pathChanged(oldPath) # Notify observers the path has changed


  def childIndex ( self, element ):
    """Given a child element, identify and return the index of the child within
    the children array. Returns -1 if child not found.
    """
    try:
      return self.children().index(element)
    except ValueError:
      return -1


  def child ( self, index ):
    """Return a child by index"""
    return self._children[index]


  def children ( self ):
    """Return a list of children"""
    return self._children


  def childCount ( self ):
    """Return the number of children"""
    return len(self._children)


  def __bool__(self):
    """ Implemented because otherwise the __len__ method is used for evaluation
    in boolean contexts. 'if element' should always succeed.
    """
    return True


  def __len__ ( self ):
    return self.childCount()
    

  def __contains__ ( self, name ):   
    for child in self._children:
      if child.name() == name:
        return True
    return False


  def __getitem__(self, index):
    return self.child(index)


  def __repr__ ( self ):
    strn = str(self.name()) + "\r"
    for child in self.children():
      strn += "-" + str(child)
      strn += "\r"
    return strn


  def findElementsByPath(self, path):
    """ Search recursively through the element tree finding elements which
    match path. Returns a list.
    """
    if '/' in path:
      # Split the first part of the path and try to find a child matching than,
      # then call findElementsByPath() on it with the remainder of the path
      childname, remaining = path.split('/', 1)
      for child in self.children():
        if child.name() == childname:
          return child.findElementsByPath(remaining)
      return []
    else:
      # Return children matching the name
      return [ c for c in self.children() if c.name() == path ]
    

  def addChild ( self, child ):
    """Add a child to this Element"""
    assert child.parent() is None, "Cannot add a child which already has a parent"
    child._setParent( self )
    self._children.append(child)


  def _createChildren(self, path, isFolder, preset=None):
    """ Create and add a child element. If path has / separators, recursively
    adds children. Returns the final created element.
    """
    # Split the path into elements
    elements = [ elem for elem in path.split('/') if elem ]
    if not elements:
      return None

    # Loop over the elements, building the folder hierarchy as needed
    parent = self
    while elements:
      childName = elements.pop(0)
      childIsFolder = bool(isFolder or elements)
      child = None
      # If creating a folder, look for an existing one with this name. Duplicate 
      # task names are allowed
      if childIsFolder:
        child = next( (c for c in parent.children() if c.name() == childName), None )
      if not child:
        child = ExportStructureElement(childName, childIsFolder)
        parent.addChild(child)
      parent = child

    # If an existing preset was given, set it on the child
    if preset:
      child.setPreset(preset)

    return parent


  def createChildFolder(self, path):
    return self._createChildren(path, True)


  def createChildTask(self, path):
    return self._createChildren(path, False)


  def createChildFromPreset(self, path, preset):
    """ Create a child element from a path and existing preset """
    return self._createChildren(path, False, preset)


  def removeChild ( self, child ):
    """Remove a child from this Element"""    
    assert child.parent() is self
    assert child in self._children
    child._setParent(None)
    self._children.remove(child)


  def clearChildren ( self ):
    """Clear all the children"""
    self._children = []

  def toXml(self):
    """Serialize Element and children to XML"""
    # Create root node
    root = etree.Element("ExportStructureElement")
    # call internal function to populate root and convert the result to a unicode string.
    xml = etree.tostring(self._toXml(root), encoding='unicode')
    return xml

  def _toXml(self, parent):
    # Add properties as Elements to parent XmlElement
    taskRegistry._savePresetElement( "name", self.name(), parent)
    # This call will serialize the whole preset object to xml
    taskRegistry._savePresetElement( "preset", self.preset(), parent)
    
    # Create 'children'  XmlElement as container for child XmlElements
    children = etree.Element( "children", valuetype=classBasename(tuple) )
    parent.append(children)

    # For each child, recurse
    for child in self._children:
      childElement = etree.Element("ExportStructureElement")   
      children.append(childElement)    
      child._toXml(childElement)
    return parent


  def fromXml (self, xml):
    """Build Child Elements from XML data"""
    # Parse XML
    try:
      log.debug( "fromXml(%s)" % str(xml) )
      root = etree.XML(xml)
      self._fromXml(root)
    except:
      log.exception( "Failed to parse Xml for ExportStructureElement" )


  def _fromXml (self, element):
    # Restore name and TaskPresetObject from XML data
    name = taskRegistry._loadPresetElement(element.find("name"))
    preset = taskRegistry._loadPresetElement(element.find("preset"))
    
    # User properties to create child
    child = self.createChildFromPreset(name, preset)
    
    # for each child create grand child from xml
    for grandChildElement in element.find("children"):
      child._fromXml(grandChildElement)
      
