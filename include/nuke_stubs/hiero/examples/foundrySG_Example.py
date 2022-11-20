# An example Hiero/Shotgun Python API integration.

########## SHOTGUN CREDENTIALS
########## Modify this to add shotgun studio URL, login and password details
sgURL = 'https://company.shotgunstudio.com'
sgLogin = 'login@login.com'
sgPassword = 'Password'


########## ENTER PROJECT NAME, AND SEQ/SHOT CHARACTER COUNT TO SPLIT OUT THE SEQ.
########## eg. tst0010 has a seqChars count of 3.  test0010 has a seqChars count of 4.
projectName = "Jeff Ranasinghe - Nuke Studio/Hiero Tests"
seqChars = 3


########## TASK COLOUR LIST
########## Add definitions for more departments and how to colour their outputs on the timeline.
taskListColours = {}
taskListColours.update( {'plates': [120,120,120]} )
taskListColours.update( {'comp': (40,0,40)} )


############################################################################
############################################################################
############################################################################


import sys
########## FOR FINDING THE FFMPEG.  ALTER THIS IF NEEDED.
if sys.platform == 'win32':
  ffmpeg = 'ffmpeg'
elif sys.platform == 'darwin':
  ffmpeg = '/usr/local/bin/ffmpeg'
else:
  ffmpeg = '/usr/bin/ffmpeg'


########## SHOTGUN ACCESS.  SG OBJECT CREATION HAPPENS HERE
import shotgun_api3, subprocess, hiero, nuke
sg = shotgun_api3.Shotgun(sgURL,
              login=sgLogin,
              password=sgPassword)


########## SHOT STATUS DICT
sgTaskStatusDict = {
'fin': 'Final',
'ip': 'In Progress',
'hld': 'On Hold',
'rdy': 'Ready To Start',
'wtg': 'Waiting to Start',
'rev': 'Awaiting Approval',
'pqc': 'Approved'
}


def sgTaskStatusGet(shotcode, projectname, sgTaskName):
  if sgTaskFind(shotcode, projectname, sgTaskName):
    tk = sgTaskFind(shotcode, projectname, sgTaskName)
    return sg.find("Task", [["id", "is", tk['id']]], ["id", "code", "sg_status_list"])


def sgTaskStatusSet(shotcode, projectname, sgTaskName, newStatus):
  if sgTaskFind(shotcode, projectname, sgTaskName):
    tk = sgTaskFind(shotcode, projectname, sgTaskName)
    data = {'sg_status_list': newStatus}
    sg.update("Task", tk['id'], data)


def returnProjectId(projectname):
  for p in sg.find("Project",[["name", "is", projectname]], ["name","id"]):
    return p["id"]


def sgShotFind(shotcode, projectname):
  result = -999
  for sh in sg.find("Shot", filters=[], fields=["code", "project"]):
    if "'name': '%s'" % projectname in str(sh['project']): ### match project
      if  sh['code'] == shotcode: ###match shotcode
        result = sh
  if result != -999: return result
  else: return False


def sgSeqFind(seqcode, projectname):
  result = -999
  for sq in sg.find("Sequence", filters=[], fields=["code", "sg_sequence", "project"]):
    if "'name': '%s'" % projectname in str(sq['project']): ### match project
      if  sq['code'] == seqcode: ###match seqcode
        result = sq
  if result != -999: return result
  else: return False


def sgTaskFind(shotcode, projectname, sgTaskName):
  result = -999
  if sgShotFind(shotcode, projectname):
    shot = sgShotFind(shotcode, projectname)
    filters = [['entity', 'is', {'type':'Shot', 'id':shot['id']}]]
    for tk in sg.find("Task", filters=filters, fields=["code", "project", 'content']):
      if "'name': '%s'" % projectname in str(tk['project']): ### match project
        if sgTaskName in str(tk['content']): ### match task
          result = tk
  if result != -999: return result
  else: return False


def sgVersionFind(shotcode, projectname, sgTaskName, sgVersion):
  import re
  result = -999
  if sgShotFind(shotcode, projectname):
    shot = sgShotFind(shotcode, projectname)
    filters = [['entity', 'is', {'type':'Shot', 'id':shot['id']}]]
    for v in sg.find("Version", filters=filters, fields=["code", "id"]):
      clipVersion = int(re.search('_v(\d{2,5})',a).group(1))
      if sgVersion == clipVersion and sgTaskName in str(v['code']):
        result = v
  if result != -999: return result
  else: return False


def sgPlaylistFind(playlistname, projectname):
  filters = [["project", "name_contains", projectname], ["code","is",playlistname]]
  fields = ["code", "project", "content"]
  fields = ['playlist.Playlist.code', 'sg_sort_order', 'version.Version.code', 'version.Version.user', 'version.Version.entity']
  fields= ['code','version']
  return sg.find("Playlist", filters=filters, fields=fields)


def sgPlaylistCreate(playlistname, projectname, versionslist):
  if sgPlaylistFind(playlistname, projectname):
    raise ValueError("*** Playlist with this name and Project combo already exists")
  
  sg_project = sg.find("Project", [['name', 'is', projectname]])
  sg_projectId = returnProjectId(projectname)
  data = {
    "project": {"type": "Project", "id": sg_projectId},
    "code": playlistname,
    "versions" : versionslist
  }
  curPlaylist = sg.create("Playlist",data)
  return curPlaylist


def sgPlaylistContent(playlistId):
  filters = [['playlist', 'is', {'type':'Playlist', 'id':playlistId}]]
  fields = ['playlist.Playlist.code', 'version.Version.code', 'version.Version.entity', 'version.Version.sg_path_to_frames']
  result = sg.find('PlaylistVersionConnection', filters, fields)
  return result


def sgShotCreate(shotcode, projectname, sgShotDescription = "NukeStudio created shot"):
  seqShotName = shotcode
  seqName = seqShotName[:seqChars]

  if sgShotFind(shotcode, projectname): return sgShotFind(shotcode, projectname)
  if not sgShotFind(shotcode, projectname):
    sg_project = sg.find("Project", [['name', 'is', projectname]])
    sg_projectId = returnProjectId(projectname)

    ### first test and create sequence if necessary, or find and return sequence code
    curSeq = sgSeqFind(seqName, projectname)
    if curSeq == False: ### couldnt return a sequence so probably doesnt exist
      data = {
        "project": {"type": "Project", "id": sg_projectId},
        "code": seqName,
        'sg_status_list': "ip"
      }
      curSeq = sg.create("Sequence", data)

    ### use previous sequence code to create shot
    data = {
      "project": {"type": "Project", "id": sg_projectId},
      'code': seqShotName,
      'sg_sequence': {'type':'Sequence', 'id':curSeq['id']},
      'description': sgShotDescription,
      'sg_status_list': 'ip'
    }
    curShot = sg.create("Shot",data)
    return curShot


def sgTaskCreate(shotcode, projectname, sgTaskName):
  seqShotName = shotcode
  seqName = seqShotName[:seqChars]

  if sgTaskFind(shotcode, projectname, sgTaskName): return sgTaskFind(shotcode, projectname, sgTaskName)
  if not sgTaskFind(shotcode, projectname, sgTaskName):
    sg_shot = sgShotFind(shotcode, projectname)
    sg_project = sg.find("Project", [['name', 'is', projectname]])
    sg_projectId = returnProjectId(projectname)
    ### use previous info to create tasks
    data = {
      "project": {"type": "Project", "id": sg_projectId},
      'content': sgTaskName,
      'entity': {'type':'Shot', 'id':sg_shot['id']}
    }
    curTask = sg.create("Task",data)
    return curTask


def sgVersionCreate(shotcode, projectname, sgTaskName, moviePath, sgVersion, sgPathFrames, sgVersionDescription = "NukeStudio created version"):
  sg_project = sg.find("Project", [['name', 'is', projectname]])
  sg_projectId = returnProjectId(projectname)
  sg_shot = sgShotFind(shotcode, projectname)
  task = sgTaskFind(shotcode, projectname, sgTaskName)

  if sgVersionFind(shotcode, projectname, sgTaskName, sgVersion):
    return sgVersionFind(shotcode, projectname, sgTaskName, sgVersion)
  if not sgVersionFind(shotcode, projectname, sgTaskName, sgVersion):
    data = { 'project': {'type': 'Project','id': sg_projectId},
      'code': shotcode + "_" + sgTaskName + "_v%03d" % sgVersion,
      'description': sgVersionDescription, 
      'sg_status_list': 'rev',
      'entity': {'type': 'Shot', 'id': sg_shot['id']},
      'sg_task': {'type': 'Task', 'id': task['id']},
      'sg_path_to_frames': sgPathFrames
      }

    versionId = sg.create('Version', data)
    moviePathId = sg.upload("Version", versionId['id'], moviePath, field_name="sg_uploaded_movie")#, field_name="sg_latest_quicktime", display_name="Latest QT")
  return "==> done with sgVersionCreate function"


########## collect all selected shots and find the paths
def qtFromFrames(framePath, rate=24):
  from PySide2.QtCore import QCoreApplication

  moviePath = framePath.split(".%04d")[0] + '-h264.mov'
  start_number = 1001
  cmds = [ffmpeg, '-y', '-r', str(rate), '-start_number', str(start_number), '-i', framePath, '-c:v','libx264','-crf','23', moviePath]
  p = subprocess.Popen(cmds)

  while p.poll() is None:
    QCoreApplication.processEvents()

  return moviePath, p.returncode


def startEndFromFrames(framePath):
  import os, glob
  frames = sorted(glob.glob(framePath.replace('%04d', '*')))
  return [frames[0].split('.')[-2],frames[-1].split('.')[-2]]


def selClipsToSg():
  import hiero, re

  pathMovie = ''
  seq = hiero.ui.activeSequence()

  if seq:
    ### Getting selection
    te = hiero.ui.getTimelineEditor(seq) # Can specify any sequence as argument
    te.selection() # Return currently selected items in timeline

    if len(te.selection()) == 0: raise ValueError("*** No clips selected on the track ***")
    else:
      for shot in te.selection():
        pathFrames = shot.source().mediaSource().metadata()['foundry.source.path'].split(" ")[0]
        clipShot = shot.name().split("_")[0]
        clipTask = shot.name().split("_")[1]
        a = shot.currentVersion().name()
        clipVersion = int(re.search('_v(\d{2,5})',a).group(1))

        print("==> Working on shot: %s - task: %s and version: v%03d" % (clipShot, clipTask, clipVersion))

        ### generate quicktime
        print("==> Generating QT")
        pathMovie, returnCode = qtFromFrames( pathFrames ) ### quicktime gen

        if returnCode != 0:
          print("==> Generating QT failed")
          return

        sgPathFrames = pathFrames
        print("==> Generating QT... complete")


        ### SG seqshot creation
        curShot = sgShotCreate(clipShot, projectName)

        ### SG task creation
        curTask = sgTaskCreate(clipShot, projectName, clipTask)
        

        ### SG version creation
        curVersion = sgVersionCreate(clipShot, projectName, clipTask, pathMovie, clipVersion, sgPathFrames, "NukeStudio version submission")

    print("==> Publishing attempt complete")


def selClipsToSgPlaylist(playlistname, projectname):
  import hiero, re

  playlist = sgPlaylistFind(playlistname, projectname)
  if playlist:
    raise ValueError("*** SG Playlist already exists with this name and Project combo.")

  listVersions = []
  seq = hiero.ui.activeSequence()
  ### Getting selection
  te = hiero.ui.getTimelineEditor(seq) # Can specify any sequence as argument
  te.selection() # Return currently selected items in timeline

  if len(te.selection()) == 0: raise ValueError("*** No clips selected on the track ***")
  else:
    for shot in te.selection():
      clipShot = shot.name().split("_")[0]
      clipTask = shot.name().split("_")[1]
      a = shot.currentVersion().name()
      clipVersion = int(re.search('_v(\d{2,5})',a).group(1))
      listVersions.append(sgVersionFind(clipShot, projectName, clipTask, clipVersion))

  curPlaylist = sgPlaylistCreate(playlistname, projectName, listVersions)
  return curPlaylist


def selClipsTaskColour():
  import hiero, re
  from PySide2 import QtGui

  pathMovie = ''

  seq = hiero.ui.activeSequence()
  ### Getting selection
  te = hiero.ui.getTimelineEditor(seq) # Can specify any sequence as argument
  te.selection() # Return currently selected items in timeline

  if len(te.selection()) == 0: print("*** No clips selected on the track ***")
  else:
    for shot in te.selection():
      clipTask = shot.name().split("_")[1]
      r = taskListColours[clipTask][0]
      g = taskListColours[clipTask][1]
      b = taskListColours[clipTask][2]
      newCol = QtGui.QColor(r, g, b)
      shot.source().binItem().setColor(newCol)


def selClipsTaskSgStatusGet():
  import hiero, re

  seq = hiero.ui.activeSequence()
  ### Getting selection
  te = hiero.ui.getTimelineEditor(seq) # Can specify any sequence as argument
  te.selection() # Return currently selected items in timeline

  if len(te.selection()) == 0: print("*** No clips selected on the track ***")
  else:
    for shot in te.selection():
      clipShot = shot.name().split("_")[0]
      clipTask = shot.name().split("_")[1]
      a = shot.currentVersion().name()
      clipVersion = int(re.search('_v(\d{2,5})',a).group(1))

      for tag in shot.tags():
        removeSgCompliantTag(shot, tag)
      
      sgTS = sgTaskStatusGet(clipShot, projectName, clipTask)
      tagsProj = hiero.core.projects(hiero.core.Project.kStartupProjects)[0]
      if sgTS[0]['sg_status_list'] != "wtg":
        newTag = hiero.core.findProjectTags(tagsProj, sgTaskStatusDict[ sgTS[0]['sg_status_list'] ])[0]
        newTagApplied = shot.addTag(newTag)


def selClipsTaskSgStatusSet():
  import hiero, re

  seq = hiero.ui.activeSequence()
  ### Getting selection
  te = hiero.ui.getTimelineEditor(seq) # Can specify any sequence as argument
  te.selection() # Return currently selected items in timeline

  if len(te.selection()) == 0: print("*** No clips selected on the track ***")
  else:
    for shot in te.selection():
      clipShot = shot.name().split("_")[0]
      clipTask = shot.name().split("_")[1]
      a = shot.currentVersion().name()
      clipVersion = int(re.search('_v(\d{2,5})',a).group(1))

      tag = findSgCompliantTag(shot)
      sgTag = ''
      ### Turn tag name into valid sg status
      tagName = str(tag).split("'")[1]
      for stat in sgTaskStatusDict:
        if tagName in sgTaskStatusDict[stat]:
          sgTag = stat

      sgTaskStatusSet(clipShot, projectName, clipTask, sgTag)



########## SG Playlist tools
def sgPlaylistToTrack(playlistname, projectname):
  playlist = sgPlaylistFind(playlistname, projectname)

  ### setup hiero/NS project
  project = hiero.core.projects()[-1] ### find the most recent loaded project - not ideal but adequate

  ### sequence/timeline
  seq = hiero.ui.activeSequence()

  if not playlist:
    raise ValueError("*** Couldn't find a SG Playlist using that Playlist name and Project name combo.")

  if not seq:
    raise ValueError("*** Couldn't find an active Hiero/NukeStudio Sequence.  Please create or select one.")

  playlistId = playlist[0]['id']
  ### Getting selection
  te = hiero.ui.getTimelineEditor(seq) # Can specify any sequence as argument


  ### create unique bin or return existing one
  binName = playlistname + '_bin'
  bin = 'NULL'
  for b in project.clipsBin().bins():
    if b.name() == binName:
      bin = b
  if bin == 'NULL':
    bin = binName
    bin = project.clipsBin().addItem(bin)

  ### install clips from playlist
  global listOfClips
  listOfClips = []
  for c in sgPlaylistContent(playlistId):
    f =  c['version.Version.sg_path_to_frames']
    # create a new media item for the plate specified in the shot data
    media_source = hiero.core.MediaSource(f)
  
    # create a clip item with the new media
    clip = hiero.core.Clip(media_source)
    listOfClips.append(clip)
  
    # create bin item
    bin_item = hiero.core.BinItem(clip)
    
    # add item to bin
    bin.addItem(bin_item)

  ###loop through clips and play on timeline, remembering last frame
  initFrame = 0
  for c in range(len(listOfClips)):
    track_items = seq.addClip(listOfClips[c], initFrame)
    initFrame += listOfClips[c].duration()


#shot status
def shotStatus():
  for l in sg.find("Shot", filters=[["sg_status_list", "is", "ip"]], fields=["code", "sg_status_list"]):
    print(l)


########## list all projects
def listProjects():
  for p in sg.find("Project",[], ['name','id']):
    print(p)


def removeSgCompliantTag(shot, tag):
  tagName = str(tag).split("'")[1]
  for stat in sgTaskStatusDict:
    if tagName in sgTaskStatusDict[stat]:
      shot.removeTag(tag)


def findSgCompliantTag(clip):
  # tagName = str(tag).split("'")[1]
  result = ''
  for tag in clip.tags():
    tagName = str(tag).split("'")[1]
    for stat in sgTaskStatusDict:
      if tagName in sgTaskStatusDict[stat]:
        result = tag
  return tag


############################################################################
########## Menu setup ######################################################
def menu_selClipsToSgPlaylist():
  playlistname = nuke.getInput('Enter a new name for a Shotgun playlist:', 'New Playlist')
  selClipsToSgPlaylist(playlistname, projectName)

def menu_sgPlaylistToTrack():
  playlistname = nuke.getInput('Enter Shotgun playlist name to pull to bottom video track:', 'Existing Playlist')
  sgPlaylistToTrack(playlistname, projectName)


print('\n*** loaded foundrySG tools ***\n')
menuBar = hiero.ui.menuBar()
menu = menuBar.addMenu("FoundrySG")

menu.addAction("Set Clips task colours", selClipsTaskColour)
menu.addSeparator()
menu.addSeparator()
menu.addAction("Publish selected Clips", selClipsToSg)
menu.addSeparator()
menu.addSeparator()
menu.addAction("Pull Clips Statuses from Shotgun", selClipsTaskSgStatusGet)
menu.addAction("Push Clips Statuses to Shotgun", selClipsTaskSgStatusSet)
menu.addSeparator()
menu.addAction("Push Selected Clips to new Shotgun Playlist", menu_selClipsToSgPlaylist)
menu.addAction("Pull Shotgun Playlist clips to the bottom track", menu_sgPlaylistToTrack)
############################################################################
############################################################################
