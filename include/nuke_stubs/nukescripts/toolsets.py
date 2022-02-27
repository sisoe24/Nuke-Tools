import os
import nuke
import nukescripts

class CreateToolsetsPanel(nukescripts.PythonPanel):
  def __init__(self):
    nukescripts.PythonPanel.__init__( self, 'Create ToolSet', 'uk.co.thefoundry.CreateToolset')

    # CREATE KNOBS
    # Loop through and find all user folders
    self.userFolders = []
    for d in nuke.pluginPath():
      if os.path.isdir(d):
        if ".nuke" in d:
          dircontents = os.listdir(d)
          if "ToolSets" in dircontents:
            fullPath = os.path.join(d, "ToolSets")
            self.buildFolderList(fullPath, '')

    self.menuItemChoice = nuke.CascadingEnumeration_Knob('menuItemChoice','ToolSets menu', ['root'] + self.userFolders)
    self.menuItemChoice.setTooltip("The menu location that the ToolSet will appear in. Specify 'root' to place the ToolSet in the main ToolSets menu.")
    self.menuPath = nuke.String_Knob('itemName', 'Menu item:')
    self.menuPath.setFlag(0x00001000)
    self.menuPath.setTooltip("ToolSet name. Use the '/' character to create a new submenu for this ToolSet, eg to create a ToolSet named 'Basic3D' and place it in a new submenu '3D', type '3D/Basic3D'. Once created the 3D menu will appear in the ToolSet menu.")
    self.okButton = nuke.PyScript_Knob ('create', 'Create')
    #self.okButton.setToolTip("Create a ToolSet from the currently selected nodes with the given name")
    self.okButton.setFlag(0x00001000)
    self.cancelButton = nuke.PyScript_Knob ('cancel', 'Cancel')

    # ADD KNOBS
    self.addKnob(self.menuItemChoice)
    self.addKnob(self.menuPath)
    self.addKnob(self.okButton)
    self.addKnob(self.cancelButton)

  # BUILD A LIST Of PRE_CREATED FOLDER LOCATIONS
  def buildFolderList(self, fullPath, menuPath):
    filecontents = sorted(os.listdir(fullPath), key=str.lower)
    for group in filecontents:
      if os.path.isdir(os.path.join(fullPath, group)):
        self.userFolders.append(menuPath + group)
        self.buildFolderList(fullPath + '/' + group, menuPath + group + '/')

  def createPreset(self):
    if nuke.createToolset(str(self.menuPath.value())):
      self.finishModalDialog( True )

  def getPresetPath(self):
    if str(self.menuItemChoice.value()) == "root":
      self.menuPath.setValue("")
    else:
      self.menuPath.setValue(self.menuItemChoice.value() + "/")

  def knobChanged( self, knob ):
    if knob == self.okButton:
      self.createPreset()
    elif knob == self.cancelButton:
      self.finishModalDialog( False )
    elif knob == self.menuItemChoice:
      self.getPresetPath()

# NUKESCRIPT FUNCTIONS

def addToolsetsPanel():
  res = False
  if nuke.nodesSelected() == True:
    res = CreateToolsetsPanel().showModalDialog()
    # now force a rebuild of the menu
    refreshToolsetsMenu()
  else:
    nuke.message("No nodes are selected")
  return res

def deleteToolset(rootPath, fileName):
  if nuke.ask('Are you sure you want to delete ToolSet %s?' %fileName):
    os.remove(fileName)
    # if this was the last file in this directory, the folder will need to be deleted.
    # Walk the directory tree from the root and recursively delete empty directories
    checkForEmptyToolsetDirectories(rootPath)
    # now force a rebuild of the menu
    refreshToolsetsMenu()

def checkForEmptyToolsetDirectories(currPath):
  removed = True
  while removed == True:
    removed = False
    for root, dirs, files in os.walk(currPath):
      if files == [] and dirs == []:
        os.rmdir(root)
        removed = True

def refreshToolsetsMenu():
  toolbar = nuke.menu("Nodes")
  m = toolbar.findItem("ToolSets")
  if m != None:
    m.clearMenu()
    createToolsetsMenu(toolbar)

def createToolsetsMenu(toolbar):
  m = toolbar.addMenu("ToolSets", "ToolbarToolsets.png")
  m.addCommand("Create", "nukescripts.toolsets.addToolsetsPanel()", "", icon="ToolsetCreate.png")
  m.addCommand("-", "", "")
  if populateToolsetsMenu(m, False):
    m.addCommand("-", "", "")
    n = m.addMenu("Delete", "ToolsetDelete.png")
    populateToolsetsMenu(n, True)

def traversePluginPaths(m, delete, allToolsetsList, isLocal):
  ret = False
  if delete and (not isLocal):
    return True
  excludePaths = nuke.getToolsetExcludePaths()
  for d in nuke.pluginPath():
    d = d.replace('\\', '/')
    ignore = False
    for i in excludePaths:
      i = i.replace('\\', '/')
      if d.find(i) != -1:
        ignore = True
        break
    if ignore:
      continue
    if (not isLocal) and (d.find(".nuke") != -1):
      continue
    if isLocal and (d.find(".nuke") == -1):
      continue
    if os.path.isdir(d):
      dircontents = os.listdir(d)
      if "ToolSets" in dircontents:
        fullPath = "/".join([d, "ToolSets"])
        if createToolsetMenuItems(m, fullPath, fullPath, delete, allToolsetsList, isLocal):
          ret = True
  return ret

def populateToolsetsMenu(m, delete):
  ret = False
  allToolsetsList = []
  # first build the menu for toolsets in shared locations
  if traversePluginPaths(m, delete, allToolsetsList, False):
    m.addCommand("-", "", "")
    ret = True
  # now do toolsets in the local .nuke
  if traversePluginPaths(m, delete, allToolsetsList, True):
    ret = True
  return ret

def createToolsetMenuItems(m, rootPath, fullPath, delete, allToolsetsList, isLocal):
  filecontents = sorted(os.listdir(fullPath), key=str.lower)
  excludePaths = nuke.getToolsetExcludePaths()
  # First list all directories
  retval = False
  if filecontents != []:
    for group in filecontents:
      newPath = "/".join([fullPath, group])
      ignore = False
      if newPath.find(".svn") != -1:
        ignore = True
      else:
        for i in excludePaths:
          i = i.replace('\\', '/')
          if newPath.find(i) != -1:
            ignore = True
            break
      if os.path.isdir(newPath) and not ignore:
        menuName = group
        if isLocal and (menuName in allToolsetsList):
          menuName = "[user] " + menuName
        elif not isLocal:
          allToolsetsList.append(menuName)
        n = m.addMenu(menuName)
        retval = createToolsetMenuItems(n, rootPath, "/".join([fullPath, group]), delete, allToolsetsList, isLocal)
        # if we are deleting, and the sub directory is now empty, delete the directory also
        if delete and os.listdir(fullPath)==[]:
          os.rmdir(fullPath)
    # Now list individual files
    for group in filecontents:
      fullFileName = "/".join([fullPath, group])
      if not os.path.isdir(fullFileName):
        extPos = group.find(".nk")
        if extPos != -1 and extPos == len(group) - 3:
          group = group.replace('.nk', '')
          if delete:
            m.addCommand(group, 'nukescripts.toolsets.deleteToolset("%s", "%s")' % (rootPath, fullFileName), "")
            retval = True
          else:
            # get the filename below toolsets
            i = fullFileName.find("ToolSets/")
            if i != -1:
              subfilename = fullFileName[i:]
            else:
              # should never happen, but just in case ...
              subfilename = fullfilename
            if isLocal and (subfilename in allToolsetsList):
              # if we've already appended [user] to the menu name, don't need it on the filename
              if (i != -1) and subfilename[len("ToolSets/"):].find("/") == -1:
                group = "[user] " + group
            elif not isLocal:
              allToolsetsList.append(subfilename)
            m.addCommand(group, 'nuke.loadToolset("%s")' % fullFileName, "")
            retval = True
  return retval
