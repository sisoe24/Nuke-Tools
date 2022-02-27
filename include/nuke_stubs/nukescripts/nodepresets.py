import os
import nuke
import nukescripts
import fileinput
import imp
import errno

def getNukeUserFolder():
  for d in nuke.pluginPath():
    if os.path.isdir(d):
      if d.endswith(".nuke"):
        return d
  return None

def buildPresetFileList(fullPath):
  fileList = []
  if not os.path.exists(fullPath) or not os.path.isdir(fullPath):
    return fileList

  fileName = fullPath + "/user_presets.py"
  if os.path.exists(fileName):
    fileList.append(fileName)

  filecontents = os.listdir(fullPath + '/')
  for d in filecontents:
    newPath = os.path.join(fullPath, d)
    if os.path.isdir(newPath):
      fileList += buildPresetFileList(newPath)

  return fileList

class CreateNodePresetsPanel(nukescripts.PythonPanel):
  def __init__(self, node):
    self.node = node

    # Loop through and find all user folders
    userFolder = getNukeUserFolder()
    newFileList = []
    if userFolder != None:
      userFolder = os.path.join(userFolder, "NodePresets")
      fileList = buildPresetFileList(userFolder)

      for file in fileList:
        # We need to convert these absolute filenames into items that can be passed to a cascading enumeration knob.
        # First strip the nuke user folder path from the start
        newFileName = file[len(str(userFolder)):].replace("\\", "/")

        # Now strip the "/user_presets.py" part from the end
        endSize = 16

        if len(newFileName) > endSize:
          newFileName = newFileName[:len(newFileName) - endSize]

        if newFileName != "/user_presets.py":
          if newFileName[:1] == '/':
            newFileName = newFileName[1:]
          newFileList.append(newFileName)

    nukescripts.PythonPanel.__init__( self, 'Create Node Preset', 'uk.co.thefoundry.CreateNodePreset')

    self.menuItemChoice = nuke.CascadingEnumeration_Knob('menuItemChoice','Presets menu', ['root'] + newFileList)
    self.menuItemChoice.setTooltip("The menu location that the Preset will appear in. Specify 'root' to place the Preset in the main Presets menu.")
    self.menuPath = nuke.String_Knob('presetname', 'Name:')
    self.menuPath.setFlag(0x00001000)
    self.okButton = nuke.PyScript_Knob ('create', 'Create')
    self.okButton.setFlag(0x00001000)
    self.cancelButton = nuke.PyScript_Knob ('cancel', 'Cancel')

    # ADD KNOBS
    self.addKnob(self.menuItemChoice)
    self.addKnob(self.menuPath)
    self.addKnob(self.okButton)
    self.addKnob(self.cancelButton)

  def createPreset(self):
    if createNodePreset(self.node, str(self.menuPath.value())):
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

class UserPresetsLoadPanel(nukescripts.PythonPanel):
  def __init__(self):
    nukescripts.PythonPanel.__init__( self, 'Load User Preset', 'uk.co.thefoundry.LoadUserPreset')
    self.presets = []
    self.presets = nuke.getUserPresets()

    self.menuItemChoice = nuke.Enumeration_Knob('menuItemChoice','Menu item', self.presets)
    self.okButton = nuke.PyScript_Knob ('load', 'Load')
    self.okButton.setFlag(0x00001000)
    self.cancelButton = nuke.PyScript_Knob ('cancel', 'Cancel')

    # ADD KNOBS
    self.addKnob(self.menuItemChoice)
    self.addKnob(self.okButton)
    self.addKnob(self.cancelButton)

  def loadPreset(self):
    if nuke.applyUserPreset(str(self.menuItemChoice.value())):
      self.finishModalDialog( True )

  def knobChanged( self, knob ):
    if knob == self.okButton:
      self.loadPreset()
    elif knob == self.cancelButton:
      self.finishModalDialog( False )

class UserPresetsDeletePanel(nukescripts.PythonPanel):
  def __init__(self):
    nukescripts.PythonPanel.__init__( self, 'Delete User Preset', 'uk.co.thefoundry.DeleteUserPreset')
    self.presets = []
    self.presets = nuke.getUserPresets()

    self.menuItemChoice = nuke.Enumeration_Knob('menuItemChoice','Menu item', self.presets)
    self.okButton = nuke.PyScript_Knob ('delete', 'Delete')
    self.okButton.setFlag(0x00001000)
    self.cancelButton = nuke.PyScript_Knob ('cancel', 'Cancel')

    # ADD KNOBS
    self.addKnob(self.menuItemChoice)
    self.addKnob(self.okButton)
    self.addKnob(self.cancelButton)

  def deletePreset(self):
    if deleteUserNodePreset(nuke.getNodeClassName(), str(self.menuItemChoice.value())):
      self.finishModalDialog( True )

  def knobChanged( self, knob ):
    if knob == self.okButton:
      self.deletePreset()
    elif knob == self.cancelButton:
      self.finishModalDialog( False )

class PresetsLoadPanel(nukescripts.PythonPanel):
  def __init__(self):
    nukescripts.PythonPanel.__init__( self, 'Load Preset', 'uk.co.thefoundry.LoadPreset')
    self.presets = []
    self.presets = nuke.getPresets()

    self.menuItemChoice = nuke.Enumeration_Knob('menuItemChoice','Menu item', self.presets)
    self.okButton = nuke.PyScript_Knob ('load', 'Load')
    self.okButton.setFlag(0x00001000)
    self.cancelButton = nuke.PyScript_Knob ('cancel', 'Cancel')

    # ADD KNOBS
    self.addKnob(self.menuItemChoice)
    self.addKnob(self.okButton)
    self.addKnob(self.cancelButton)

  def loadPreset(self):
    if nuke.applyPreset(str(self.menuItemChoice.value())):
      self.finishModalDialog( True )

  def knobChanged( self, knob ):
    if knob == self.okButton:
      self.loadPreset()
    elif knob == self.cancelButton:
      self.finishModalDialog( False )

class PresetsDeletePanel(nukescripts.PythonPanel):
  def __init__(self):
    nukescripts.PythonPanel.__init__( self, 'Delete Preset', 'uk.co.thefoundry.DeletePreset')
    self.presets = []
    self.presets = nuke.getPresets()

    self.menuItemChoice = nuke.Enumeration_Knob('menuItemChoice','Menu item', self.presets)
    self.okButton = nuke.PyScript_Knob ('delete', 'Delete')
    self.okButton.setFlag(0x00001000)
    self.cancelButton = nuke.PyScript_Knob ('cancel', 'Cancel')

    # ADD KNOBS
    self.addKnob(self.menuItemChoice)
    self.addKnob(self.okButton)
    self.addKnob(self.cancelButton)

  def deletePreset(self):
    if deleteNodePreset(nuke.getNodeClassName(), str(self.menuItemChoice.value())):
      self.finishModalDialog( True )

  def knobChanged( self, knob ):
    if knob == self.okButton:
      self.deletePreset()
    elif knob == self.cancelButton:
      self.finishModalDialog( False )

def processPresetFile(location):
  fulName = ""
  if str(location).endswith('/') or str(location).endswith('\\'):
    fulName = str(location) + "user_presets.py"
  else:
    fulName = str(location) + "/user_presets.py"

  if os.path.exists(fulName):
    try:
      module =  imp.load_source('user_presets', fulName)
      module.nodePresetsStartup()
    except:
      pass

def createNodePresetsMenu():
  for d in nuke.pluginPath():

    if ".nuke" in d:
      nuke.setReadOnlyPresets(False)
    else:
      nuke.setReadOnlyPresets(True)

    # First look for a user_presets.py in the nuke path
    processPresetFile(d)

    # Now load all user_presets.py files in a directory tree below nodePresets
    fulName = os.path.join(d, "NodePresets")
    userFiles = buildPresetFileList(fulName)

    for pyFile in userFiles:
      try:
        module = imp.load_source('user_presets', pyFile)
        module.nodePresetsStartup()
      except:
        pass

  nuke.setReadOnlyPresets(False)

  # now parse the .nuke root presets again to make sure deleted items get processed properly
  processPresetFile(getNukeUserFolder())


def populatePresetsMenu(nodeName, className):
  knobValues = {}
  node = nuke.toNode(nodeName)
  m = nuke.getPresetsMenu(node)
  # reset the menus in case of preset deletion
  m.clearMenu()
  presets = []
  userpresets = []
  userpresets = nuke.getUserPresets(node)
  presets = nuke.getPresets(node)
  allpresets = userpresets + presets

  buildSavePanelFunc = lambda node = node: nukescripts.buildPresetSavePanel("", node)
  m.addCommand("Save as Preset", buildSavePanelFunc)

  if allpresets != []:
    m.addCommand("-", "", "")
    for k in userpresets:
      f = lambda node=node, k=k : nuke.applyUserPreset("", k, node)
      m.addCommand('[User] ' + k, f)
    for k in presets:
      f = lambda node=node, k=k : nuke.applyPreset("", k, node)
      m.addCommand(k, f)
  if allpresets != []:
    m.addCommand("-", "", "")
    n = m.addMenu("Delete Preset")
    for k in userpresets:
      n.addCommand('[User] ' + k, 'nukescripts.deleteUserNodePreset("%s", "%s")\n' % (className, k))
    for k in presets:
      n.addCommand(k, 'nukescripts.deleteNodePreset("%s", "%s")\n' % (className, k))

def buildUserPresetLoadPanel():
  presets = []
  presets = nuke.getUserPresets()
  if presets == []:
    nuke.message("No user presets defined.")
  else:
    UserPresetsLoadPanel().showModalDialog()

def buildPresetLoadPanel():
  presets = []
  presets = nuke.getPresets()
  if presets == []:
    nuke.message("No presets defined.")
  else:
    PresetsLoadPanel().showModalDialog()

def buildPresetSavePanel(nodeName, node = None):
  if (node == None):
    node = nuke.toNode(nodeName)
  return CreateNodePresetsPanel(node).showModalDialog()

def buildUserPresetDeletePanel():
  presets = []
  presets = nuke.getUserPresets()
  if presets == []:
    nuke.message("No user presets defined.")
  else:
    UserPresetsDeletePanel().showModalDialog()

def buildPresetDeletePanel():
  presets = []
  presets = nuke.getPresets()
  if presets == []:
    nuke.message("No presets defined.")
  else:
    PresetsDeletePanel().showModalDialog()

def getItemDirName(d, item):
  # Convert a preset's name (including it's menu hierarchy) into the corresponding directory
  # for it's user_presets.py file
  itemName = os.path.join(d, "NodePresets")
  itemName = os.path.join(itemName, item[1])

  length = len(os.path.basename(itemName))

  itemName = itemName[:len(itemName) - length - 1]

  return itemName

def saveNodePresets():

  # Get the root location for writing preset files to. By default we get the nuke user folder (.nuke),
  # and a NodePresets sub-directory is created below this.
  # user_presets.py files are then written in a directory tree inside this in a hierarchy that mimics their
  # names at creation (ie '/' separated strings to specify a relative directory path)

  # find the .nuke folder path
  d = getNukeUserFolder()
  if d != None and os.path.isdir(d):
    userPresets = nuke.getAllUserPresets()
    deletedPresets = nuke.getDeletedPresets()

    for k in userPresets:
      dirName = getItemDirName(d, k)

      try:
        os.makedirs(dirName)
      except OSError as exc:
        if exc.errno == errno.EEXIST:
          pass
        else: raise

      with open(os.path.join(dirName, "user_presets.py"), "w") as outfile:
        outfile.write('import nuke\n')
        outfile.write('def nodePresetsStartup():\n')

    if userPresets != []:
      for k in userPresets:
        filename = os.path.join(getItemDirName(d, k), "user_presets.py")

        with open(filename, "a") as outfile:
          namePair = k
          knobValues = nuke.getUserPresetKnobValues(namePair[0], namePair[1])
          outfile.write('  nuke.setUserPreset("%s", "%s", %s)\n' % (k[0], k[1], repr(knobValues)))

    if deletedPresets != []:
      filename = os.path.join(d, "user_presets.py")
      with open(filename, "w") as outfile:
        outfile.write('import nuke\n')
        outfile.write('def nodePresetsStartup():\n')
        for k in deletedPresets:
          namePair = k
          outfile.write('  nuke.deletePreset("%s", "%s")\n' % (namePair[0], namePair[1]))

def createNodePreset(node, name):
  nuke.saveUserPreset(node, name)
  saveNodePresets()

def deleteNodePreset(classname, presetName):
  if nuke.ask("Are you sure you want to delete preset " + presetName + "?"):
    nuke.deletePreset(classname, presetName)
    saveNodePresets()

def deleteUserNodePreset(classname, presetName):
  if nuke.ask("Are you sure you want to delete preset " + presetName + "?"):
    nuke.deleteUserPreset(classname, presetName)
    saveNodePresets()

