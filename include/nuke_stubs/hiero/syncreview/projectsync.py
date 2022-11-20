from foundry.ui import ProgressTask
import hiero.core
import hiero.ui
import nuke_internal as nuke
import os
from datetime import datetime
from . import config
from . import messages
from . synctool import SyncTool
from . log import logMessage


def syncReviewTempDir(name=""):
  """ Get the directory for temp files related to the sync functionality, with an
  option sub-directory name, creating if necessary.
  """
  path = nuke.toNode("preferences").knob(config.PROJECT_SAVE_DIR_KEY).evaluate()
  if name:
    path = os.path.join(path, name)
  if not hiero.core.util.filesystem.exists(path):
    hiero.core.util.filesystem.makeDirs(path)
  return path

messages.defineMessageType('ProjectPushBegin', ('guids', messages.Json))
messages.defineMessageType('ProjectPushEnd')
messages.defineMessageType('ProjectPush', ('guid', str), ('name', str), ('filename', str), ('content', messages.Compressed))
messages.defineMessageType('ProjectClose', ('guid', str))
messages.defineMessageType('ProjectLoadProgress', ('progress', int))


class ProjectSyncData(object):
  """ Data container for a synced project """
  def __init__(self, project):
    self.project = project
    self.projectGuid = project.guid()
    self.originalPath = project.path()
    self.lastTempSavePath = None


class ProjectPushTool(SyncTool):
  """
  Sync tool used for pushing projects to other clients and loading projects pushed from elsewhere. Provides
  functions for getting the current project, loading projects, and pushing projects to other clients.
  """

  # Flags for the current state of the tool. Currently, pushing isn't really a
  # state as all the messages are sent in one go, but I've included it here in case
  # that changes
  STATE_IDLE = 0
  STATE_LOADING_PROJECTS = 1
  STATE_PUSHING_PROJECTS = 2

  def __init__(self, messageDispatcher, viewerSyncTool, clientData):
    super(ProjectPushTool, self).__init__(messageDispatcher)
    self.viewerSyncTool = viewerSyncTool
    self.messageDispatcher._registerCallback(messages.ProjectPushBegin, self._onProjectPushBeginReceived)
    self.messageDispatcher._registerCallback(messages.ProjectPushEnd, self._onProjectPushEndReceived)
    self.messageDispatcher._registerCallback(messages.ProjectPush, self._onProjectPushReceived)
    self.messageDispatcher._registerCallback(messages.ProjectClose, self._onProjectCloseReceived)
    self._clientData = clientData
    self._projectsData = []
    self._receivingProjectsCount = 0
    self._receivingProjectsTotal = 0
    self._state = ProjectPushTool.STATE_IDLE

  def addProjects(self, projects, pushNow=False):
    """ Add projects for syncing. This should only be called on the host, clients
    get the project pushed to them.
    The optional pushNow arg can be set to True to have the new project pushed
    to connected clients.
    """
    projects = [projects] if isinstance(projects, hiero.core.Project) else projects
    newProjectsData = [ProjectSyncData(proj) for proj in projects]
    self._projectsData.extend(newProjectsData)
    if pushNow:
      self._pushProjects(messages.Message.TARGET_BROADCAST, newProjectsData)

  def removeProject(self, project):
    """ Remove a project from the sync session (this happens when the host closes it or
    uses save as). This sends messages to have it closed on connected clients.
    """
    self._projectsData = [pd for pd in self._projectsData if pd.project != project]
    self.messageDispatcher.sendMessage(messages.ProjectClose(guid=project.guid()))

  def projects(self):
    """ Get a list of synced projects """
    return [data.project for data in self._projectsData]

  def _saveNewProjectVersion(self, projectData):
    """ Save a project to a temp file with user, timestamp and version """
    projName = projectData.project.name()
    tempDir = syncReviewTempDir(projName)
    # If this is the first save to the temp dir, start at version 1, otherwise extract
    # the version from the last save and increment it
    oldPath = projectData.lastTempSavePath
    if not oldPath:
      version = 1
    else:
      version = int(oldPath[oldPath.rfind('v')+1:oldPath.rfind('.')]) + 1
    userName = self._clientData[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    newFileName = "{}_{}_{}_v{:02d}.hrox".format(projName, userName, timestamp, version)
    newPath = os.path.join(tempDir, newFileName)
    saveFlags = (hiero.core.Project.kProjectSaveKeepName |
                 hiero.core.Project.kProjectSaveDontAddToRecent |
                 hiero.core.Project.kProjectSaveDontChangeProjectPath)
    # Back up the project path.
    path = projectData.project.path()
    projectData.project.saveAs(newPath, saveFlags)
    if len(projectData.project.path()) == 0:
      # The Python API for Project.saveAs will set the project path to empty. The project sync code needs to keep the
      # path unchanged. Restore the path if it is now empty.
      projectData.project.setPath(path)
    projectData.lastTempSavePath = newPath

  def pushAllProjects(self, receiver):
    """ Push all synced projects to the specified recipients """
    self._pushProjects(receiver, self._projectsData)

  def _pushProjects(self, receiver, projectsData):
    """ Push a list of projects (ProjectSyncData objects) to the specified recipients """
    self._state = ProjectPushTool.STATE_PUSHING_PROJECTS
    self.viewerSyncTool.stopPlayback()
    guids = [pd.projectGuid for pd in projectsData]
    self.messageDispatcher.sendMessage(messages.ProjectPushBegin(target=receiver, guids=guids))
    for projectData in projectsData:
      self._pushProject(receiver, projectData)
    self.messageDispatcher.sendMessage(messages.ProjectPushEnd(target=receiver))
    self._state = ProjectPushTool.STATE_IDLE

  def _pushProject(self, receiver, projectData):
    """ Push a project. This should only be called by _pushProjects """
    self._saveNewProjectVersion(projectData)

    # Read the file data and send a message
    projPath = projectData.lastTempSavePath
    with hiero.core.util.filesystem.openFile(projPath, 'rb') as projFile:
      projContent = projFile.read()

    _, projFileName = os.path.split(projPath)
    project = projectData.project
    msg = messages.ProjectPush(guid=project.guid(),
                            name=project.name(),
                            filename=projFileName,
                            content=projContent)
    msg.target = receiver
    self.messageDispatcher.sendMessage(msg)
    # The state of the viewers is only partially stored in hrox files, send the
    # full state of the viewer to be restored after the project is loaded
    self.viewerSyncTool.pushViewerState()

  def _onProjectPushBeginReceived(self, msg):
    """ Prepare to receive pushed projects """
    self._state = ProjectPushTool.STATE_LOADING_PROJECTS

    # Block messages from the viewer tool, the viewers getting restored while loading
    # the project causes callbacks which we don't want to send back to other clients
    self.viewerSyncTool.setProjectLoading(True)

    self._receivingProjectsCount = 0
    self._receivingProjectsTotal = len(msg.guids)
    self.messageDispatcher.sendMessage(messages.ProjectLoadProgress(progress=0))

    # If this is the first time receiving project data after connecting, close
    # any open projects.
    if not self._projectsData:
      for proj in hiero.core.projects():
        proj.close()
    else:
      # Close all the projects that are being pushed. Keep the ProjectSyncData
      # objects as they contain info about the projects that should be persistent
      # between pushes
      for pd in self._projectsData:
        if pd.projectGuid in msg.guids:
          pd.project.close()
          pd.project = None

  def _onProjectPushEndReceived(self, msg):
    """ Finish receiving pushed projects """
    self.viewerSyncTool.setProjectLoading(False)
    self._receivingProjectsCount = 0
    self._receivingProjectsTotal = 0
    self._state = ProjectPushTool.STATE_IDLE

  def _onProjectPushReceived(self, msg):
    """ Load a pushed project """

    # Write the project xml to a temp file, then load it
    projName = msg.name
    projFileName = msg.filename
    projTempPath = os.path.join(syncReviewTempDir(projName), projFileName)
    with hiero.core.util.filesystem.openFile(projTempPath, 'wb') as projFile:
      projFile.write(msg.content)

    proj = hiero.core.openProject(projTempPath, hiero.core.Project.kProjectOpenDontAddToRecent)
    # Try to find existing data about the project. If there isn't any, it's the first
    # time it's been pushed from the host and should be created. The project path
    # is cleared to remove the association with the temp file it was loaded from
    # (although this doesn't currently matter too much for clients because they're
    # not supposed to be saving synced projects)
    projectData = next((pd for pd in self._projectsData if pd.projectGuid == msg.guid), None)
    if not projectData:
      proj.setPath('')
      projectData = ProjectSyncData(proj)
      self._projectsData.append(projectData)
    else:
      projectData.project = proj
      proj.setPath(projectData.originalPath)
      proj.setModified() # Flag the project as modified so the user will be prompted to save it on close etc
    projectData.lastTempSavePath = projTempPath

    # Send progress message
    self._receivingProjectsCount += 1
    progress = int(self._receivingProjectsCount * 100 / self._receivingProjectsTotal)
    progressMsg = messages.ProjectLoadProgress(progress=progress)
    self.messageDispatcher.sendMessage(progressMsg)

  def _onProjectCloseReceived(self, msg):
    """ Handle message sent when a synced project is closed on the host, and close
    it here.
    """
    projectData = next((pd for pd in self._projectsData if pd.projectGuid == msg.guid), None)
    if not projectData:
      logMessage("_onProjectCloseReceived could not find project with id {}".format(msg.guid))
      return
    self._projectsData.remove(projectData)
    projectData.project.close()

  def state(self):
    """ Get the current state of the tool """
    return self._state


class ProjectSyncProgressTool(SyncTool):
  """ Manages the project sync progress of all other clients, and shows a progress task when appropriate.  """

  def __init__(self, messageDispatcher):
    super(ProjectSyncProgressTool, self).__init__(messageDispatcher)
    self.messageDispatcher._registerCallback(messages.ProjectLoadProgress, self._onClientLoadProgress)
    self.messageDispatcher._registerCallback(messages.Disconnected, self._onClientDisconnected)
    self._loadingClients = dict()
    self._progressTask = None

  def _onClientsUpdated(self):
    loadingCount = 0
    progress = 0
    if self._loadingClients:
      for client, clientProgress in self._loadingClients.items():
        progress += clientProgress
        if clientProgress < 100:
          loadingCount += 1
      progress = progress // len(self._loadingClients)

    if loadingCount == 0:
      self._progressTask = None
      self._loadingClients.clear()
    else:
      if not self._progressTask:
        self._progressTask = ProgressTask('Users syncing', 100, ProgressTask.kModal | ProgressTask.kShowTimeToGo)
      if loadingCount == 1:
        self._progressTask.setMessage('{} user is currently syncing...'.format(loadingCount))
      else:
        self._progressTask.setMessage('{} users are currently syncing...'.format(loadingCount))
      self._progressTask.setProgress(progress)

  def _onClientLoadProgress(self, msg):
    self._loadingClients[msg.sender] = msg.progress
    self._onClientsUpdated()

  def _onClientDisconnected(self, msg):
    try:
      del self._loadingClients[msg.disconnected]
      self._onClientsUpdated()
    except KeyError:
      pass


class HostProjectSyncTool(SyncTool):
  """
  Class for managing project syncing logic which is specific to the host.
  This includes:
    - Sending synced projects to clients when they first connect
    - Listening for opening and closing of projects and pushing those changes
      to other participants
  """

  def __init__(self, messageDispatcher, pushTool):
    super(HostProjectSyncTool, self).__init__(messageDispatcher)
    self.messageDispatcher._registerCallback(messages.Connect, self._onClientConnected)
    self._pushTool = pushTool

    self.registerEventCallback('kAfterNewProjectCreated', self._onProjectLoadOrCreate)
    self.registerEventCallback('kAfterProjectLoad', self._onProjectLoadOrCreate)
    self.registerEventCallback('kAfterProjectClose', self._onProjectClose)
    self.registerEventCallback('kBeforeProjectGUIDChange', self._onProjectClose)
    self.registerEventCallback('kAfterProjectGUIDChange', self._onProjectGUIDChanged)

  def _onClientConnected(self, msg):
    self._pushTool.pushAllProjects(msg.sender)

  def _onProjectLoadOrCreate(self, event):
    """ When a project is loaded or a new one created, add it to the list of
    synced projects and push to connected clients.
    """
    if self._pushTool.state() == ProjectPushTool.STATE_IDLE:
      self._pushTool.addProjects(event.project, pushNow=True)

  def _onProjectClose(self, event):
    """ When a project is closed, remove it to the list of synced projects and close
    it on connected clients
    """
    if self._pushTool.state() == ProjectPushTool.STATE_IDLE:
      self._pushTool.removeProject(event.project)

  def _onProjectGUIDChanged(self, event):
    if self._pushTool.state() == ProjectPushTool.STATE_IDLE:
      """ The GUIDs of sequences on the viewer change after using 'Save As' but sequenceChanged is not being emitted.
      Force an update of the sequence GUIDs cached in the viewer tool.
      """
      self._pushTool.viewerSyncTool.updateCurrentSequences()
      self._pushTool.addProjects(event.project, pushNow=True)
