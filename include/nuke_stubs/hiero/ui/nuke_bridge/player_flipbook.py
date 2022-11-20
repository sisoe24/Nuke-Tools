import json
import hiero.core
import hiero.ui
import nuke_internal as nuke
import nukescripts.flipbooking as flipbooking
import subprocess
from .flipbook_common import (getColorspaceFromNode,
                             getIsUsingNukeColorspaces,
                             mapViewerLUTString,
                             getRawViewerLUT,
                             getOCIOConfigPath,
                             kNukeFlipbookCapabilities)
from PySide2.QtCore import QDateTime
from PySide2.QtCore import QCoreApplication

"""
Code for managing the HieroPlayer flipbook functionality.
This takes JSON data which can be passed on the command line, and is forwarded
to the Python code by the application.
"""

# Keys for data stored in the json dict
kFilepathKey = "filepath"
kFrameRangeKey = "framerange"
kOcioConfigKey = "ocioconfig"
kViewerLutKey = "viewerlut"
kCompNameKey = "compname"
kNodeNameKey = "nodename"
kAudioNameKey = "audioname"
kViewsKey = "views"
kColorspaceKey = "colorspace"
kAudioPathKey = "audiopath"
# Used when flipbooking from a Read node with 'frame_mode' set to 'start at'
kStartAtKey = "startat"


class PlayerFlipbookApplication(flipbooking.FlipbookApplication):
    """ Class which handles launching the flipbook in Hiero Player from Nuke """
    def __init__(self):
        super(PlayerFlipbookApplication, self).__init__()

    def name(self):
        return "Hiero Player"

    def path(self):
        return nuke.env['ExecutablePath']

    def cacheDir(self):
        return nuke.value("preferences.DiskCachePath")

    def run(self, path, frameRanges, views, options):
        ocioConfig = getOCIOConfigPath()
        frameRange = "{}-{}".format(frameRanges.minFrame(), frameRanges.maxFrame())

        burnIn = options.get("burnIn",False)
        viewerLut = mapViewerLUTString(options.get("viewerlut", "")) if not burnIn else getRawViewerLUT()

        params = {}
        params[kFilepathKey] = path
        params[kFrameRangeKey] = frameRange
        if ocioConfig:
            params[kOcioConfigKey] = ocioConfig
        if viewerLut:
            params[kViewerLutKey] = viewerLut

        for k in (kCompNameKey, kNodeNameKey, kAudioNameKey):
            v = options.get(k)
            if v:
                params[k] = v

        params[kViewsKey] = views
        colorspace = options.get("colorspace")
        if colorspace:
            params[kColorspaceKey] = colorspace
        startAt = options.get(kStartAtKey)
        if startAt:
            params[kStartAtKey] = startAt

        audioPath = options.get("audio")
        if audioPath:
            params[kAudioPathKey] = audioPath

        paramsJson = json.dumps(params)
        self._openFlipbookProcess(paramsJson)

    def _openFlipbookProcess(self, paramsJson):
        """ Run a Player process with the flipbook data """
        args = [self.path(), "-q", "--player", "--flipbook", paramsJson]
        subprocess.Popen(args, shell=False)

    def capabilities(self):
        return kNukeFlipbookCapabilities

    def _determineFlipbookNames(self, flipbookDialog, nodeToFlipbook, options):
        """ Get the names of the comp, node, and (if there is one) audio node
        and put them in the options dictionary
        """
        nodeName = nodeToFlipbook.name()
        if nodeName == 'Flipbook':
            nodeName = nodeToFlipbook.input(0).name()
        options[kNodeNameKey] = nodeName

        compName = nuke.root()['name'].value()
        if not compName:
            compName = 'Untitled'
        else:
            # Extract the filename (without extension)
            compName = compName[compName.rfind('/')+1:compName.rfind('.')]
        options[kCompNameKey] = compName

        audioNodeName = flipbookDialog._audioSource.value()
        if audioNodeName and nuke.toNode(audioNodeName):
            options[kAudioNameKey] = audioNodeName


    def getExtraOptions(self, flipbookDialog, nodeToFlipbook):
        options = {}

        burnInLUT = flipbookDialog._burnInLUT.value()
        options["burnInLUT"] = burnInLUT

        self._determineFlipbookNames(flipbookDialog, nodeToFlipbook, options)

        if not burnInLUT:
            # Store the input colorspace and LUT. The default implementation stores
            # these under one key, but there's really no need for this
            inputColourspace = getColorspaceFromNode( flipbookDialog._node )
            options["colorspace"] = inputColourspace

            # Check our output
            outputColourspace = flipbookDialog._getLUT()
            options["viewerlut"] = outputColourspace

        # get start at frame number
        if flipbookDialog._node.Class() == "Read":
            try:
                hasStartAtDefined = flipbookDialog._node['frame_mode'].value() == "start at"
                if hasStartAtDefined:
                    # 'frame_mode' knob is a string knob, so '20.0' will raise an exception
                    # if converted directly to integer
                    options[kStartAtKey] = int( float( flipbookDialog._node['frame'].value() ) )
            except:
                pass

        return options

# Try to register the flipbook. This will only work if running Nuke/Studio
try:
    flipbooking.register(PlayerFlipbookApplication())
except:
    pass


class FlipbookNamer(object):
    """ Helper class to generate names for flipbook objects in the bin. If naming
    information wasn't provided the methods will return None """
    def __init__(self, compName, nodeName, audioName):
        self._compName = compName
        self._nodeName = nodeName
        self._audioName = audioName
        self._dateString = QDateTime.currentDateTime().toString('yyyy-M-d_hh-mm-ss')

    def _formatString(self, string, *args):
        try:
            return string.format(*args)
        except:
            return None

    def videoName(self):
        return self._formatString('{}_{}_{}', self._compName, self._nodeName, self._dateString)

    def audioName(self):
        return self._formatString('{}_{}_{}', self._compName, self._audioName, self._dateString)

    def sequenceName(self):
        return self.videoName() # Match the video clip name

    def binName(self):
        return (self._formatString('{}_AudioAndVideo_{}', self._compName, self._dateString)
                  or 'Flipbook_{}'.format(self._dateString))


class PlayerFlipbookManager(object):
    """ Manage flipbooking on the Hiero Player side. Receives flipbook commands
    from Nuke through the command line and creates projects/clips etc.
    """
    def __init__(self):
        self._flipbookProjects = []
        self._flipbookProjectCounter = 1
        hiero.core.events.registerInterest('kBeforeProjectClose',
                                            self._onProjectClosed)

    def _onProjectClosed(self, event):
        """ Callback when a project is closed. Remove it from the list. """
        try:
            self._flipbookProjects.remove(event.project)
        except ValueError:
            pass

    def _configureProjectViews(self, project, views, replace):
        """ Set the views on a project. If replace is true, the existing views
        will be removed.
        """
        if not views:
            return
        if replace:
            project.setViews(views)
        else:
            existingViews = project.views()
            for v in views:
                if v not in existingViews:
                    project.addView(v)

    def _getFlipbookProject(self, ocioConfig, views):
        """ Get a project configured with a given ocio config and views. If a
        suitable project doesn't already exist, will create a new one.
        """
        # Try to find an existing project with a matching OCIO config. If the
        # config for a comp or project is set to 'nuke-default' you may get
        # an empty name or a full path. Make sure these compare equal
        def _normaliseOcioConfig(config):
            return 'nuke-default' if (not config or 'nuke-default' in config) else config
        newConfigName = _normaliseOcioConfig(ocioConfig)
        def _configMatches(config):
            return newConfigName == _normaliseOcioConfig(config)
        proj = next((p for p in self._flipbookProjects if _configMatches(p.ocioConfigPath())), None)
        if proj:
            self._configureProjectViews(proj, views, False)
        else:
            projName = "Nuke Flipbook {}".format(self._flipbookProjectCounter)
            self._flipbookProjectCounter += 1
            proj = hiero.core.newProject(projName)
            QCoreApplication.processEvents()
            if ocioConfig:
                proj.setOcioConfigPath(ocioConfig)
            self._configureProjectViews(proj, views, True)
            self._flipbookProjects.append(proj)
        return proj

    def _createClip(self, bin, filepath, frameRange, name, colorspace):
        """ Create a clip for flipbooking """
        clip = bin.createClip(filepath)
        if frameRange:
            clip.setFrameRange(frameRange.first(), frameRange.last())
        if name:
            clip.setName(name)
            clip.binItem().setName(name)
        if colorspace:
            clip.setSourceMediaColourTransform(colorspace)
        return clip

    def _openViewer(self, sequence, viewerLUT, views):
        """ Open a clip in a viewer """
        # Use openInNewViewer to avoid a linked timeline view being created
        viewer = hiero.ui.openInNewViewer(sequence)

        # Opening a clip in the viewer automatically shows its properties panel,
        # close it again. If the object is a Sequence, there is no read node to close
        # swallow the exception
        try:
            sequence.readNode().hideControlPanel()
        except:
            pass

        # Set lut on all the viewer's players. TODO There doesn't seem to be a
        # way to know how many players the viewer has in Python. Does it even make
        # sense to be setting the LUT on the players rather than the viewer?
        if viewerLUT:
            for i in range(2):
                viewer.player(i).setLUT(viewerLUT)

        # Set the first view active in the viewer
        if views:
            viewer.setView(views[0])

        viewer.setDisplayTimecode(False)

        viewer.play()

    def _createFlipbookVideoOnly(self, project, filepath, frameRange, startAt, namer, colorspace):
        """ Creates a clip for flipbooking. It's given the specified frame range,
        offset by startAt
        """
        bin = project.clipsBin()
        if frameRange and startAt:
            frameRange.setFirst(frameRange.first() - startAt)
            frameRange.setLast(frameRange.last() - startAt)
        return self._createClip(bin, filepath, frameRange, namer.videoName(), colorspace)

    def _createFlipbookVideoAudio(self, project, filepath, frameRange, startAt, namer, colorspace,
                                    audioPath):
        """ Creates a flipbook with audio and video. This constructs a clip for
        each then adds them to a sequence which is returned. All the objects are
        placed in a bin folder.
        A lot of the logic here is taken from nuke_flipbook:
        - the code places the clips on the sequence so the frame numbers match the
          requested range
        - The full length of the audio clip is used, which may not match up with
          the video. We may want to change this
        """
        bin = project.clipsBin().addItem(hiero.core.Bin(namer.binName()))
        # Calculate the clip frame range, and the position of the clips on the sequence
        if frameRange:
            if startAt is not None:
                clipFrameRange = nuke.FrameRange(frameRange.first() - startAt, frameRange.last() - startAt, 1)
                timelineIn = startAt
            else:
                clipFrameRange = frameRange
                timelineIn = frameRange.first()
        else:
            clipFrameRange = None
            timelineIn = 0
        videoClip = self._createClip(bin, filepath, clipFrameRange, namer.videoName(), colorspace)
        audioClip = self._createClip(bin, audioPath, None, namer.audioName(), None)
        seq = hiero.core.Sequence(namer.sequenceName())
        seq.setFormat(videoClip.format())
        seq.addClip(videoClip, timelineIn)
        seq.addClip(audioClip, timelineIn)
        bin.addItem(hiero.core.BinItem(seq))
        if frameRange:
            seq.setInTime(frameRange.first())
            seq.setOutTime(frameRange.last())
        return seq

    def openFlipbook(self, filepath, frameRange, startAt, ocioConfig, viewerLUT,
                    namer, views, colorspace, audioPath):
        """ Open a flipbook, creating clips, projects etc as needed """
        proj = self._getFlipbookProject(ocioConfig, views)
        with proj.beginUndo("Flipbook"):
            if audioPath:
                flipbookSeq = self._createFlipbookVideoAudio(
                  proj, filepath, frameRange, startAt, namer, colorspace, audioPath)
            else:
                flipbookSeq = self._createFlipbookVideoOnly(
                  proj, filepath, frameRange, startAt, namer, colorspace)
        self._openViewer(flipbookSeq, viewerLUT, views)


flipbookManager = PlayerFlipbookManager()


def _loadJson(data):
    """ Load flipbook json data into a dict """
    # data might be raw json, or a path to a file containing it
    if data[0] == '{':
        data = json.loads(data)
    else:
        with open(data, 'r') as f:
            data = json.load(f)

    try:
        data["framerange"] = nuke.FrameRange(data["framerange"])
    except KeyError:
        pass
    return data


def openFlipbook(data):
    """ Open a flipbook from json data. This can either be raw json, or a path to
    a file containing it
    """
    try:
        data = _loadJson(data)

        namer = FlipbookNamer(data.get(kCompNameKey),
                              data.get(kNodeNameKey),
                              data.get(kAudioNameKey))

        flipbookManager.openFlipbook(data[kFilepathKey],
                                    data.get(kFrameRangeKey),
                                    data.get(kStartAtKey),
                                    data.get(kOcioConfigKey),
                                    data.get(kViewerLutKey),
                                    namer,
                                    data.get(kViewsKey),
                                    data.get(kColorspaceKey),
                                    data.get(kAudioPathKey),
                                    )
    except:
        import traceback
        traceback.print_exc()
