'''Stubs generated automatically from Nuke's internal interpreter.'''
from numbers import Number
from typing import *

from .nuke_classes import *
from .nuke_internal import *

# Constants
ADD_VIEWS = 0
AFTER_CONST = 21
AFTER_LINEAR = 22
ALL = 1
ALWAYS_SAVE = 1048576
BEFORE_CONST = 19
BEFORE_LINEAR = 20
BREAK = 18
CATMULL_ROM = 3
CONSTANT = 1
CUBIC = 4
DISABLED = 128
DONT_CREATE_VIEWS = 2
DONT_SAVE_TO_NODEPRESET = 549755813888
DO_NOT_WRITE = 512
ENDLINE = 8192
EXE_PATH = '/Applications/Nuke13.0v1/Nuke13.0v1.app/Contents/Frameworks/Python.framework/Versions/3.7/bin/python3.7'
EXPAND_TO_WIDTH = 68719476736
EXPRESSIONS = 1
FLOAT = 5
FONT = 4
GEO = 16
GUI = False
HIDDEN_INPUTS = 4
HORIZONTAL = 17
IMAGE = 1
INPUTS = 2
INT16 = 3
INT8 = 2
INTERACTIVE = False
INVALIDHINT = -1
INVISIBLE = 1024
KNOB_CHANGED_RECURSIVE = 134217728
LINEAR = 2
LINKINPUTS = 8
LIVEGROUP_CALLBACK_CAN_MAKE_EDITABLE = 'livegroup.can_make_editable'
LIVEGROUP_CALLBACK_CAN_PUBLISH = 'livegroup.can_publish'
LIVEGROUP_CALLBACK_MADE_EDITABLE = 'livegroup.made_editable'
LIVEGROUP_CALLBACK_PUBLISHED = 'livegroup.published'
LIVEGROUP_CALLBACK_RELOADED = 'livegroup.reloaded'
LOG = 4
MATCH_CLASS = 0
MATCH_COLOR = 2
MATCH_LABEL = 1
MONITOR = 0
NODIR = 2
NO_ANIMATION = 256
NO_CHECKMARKS = 1
NO_MULTIVIEW = 1073741824
NO_POSTAGESTAMPS = False
NO_UNDO = 524288
NUKE_VERSION_DATE = 'Mar  9 2021'
NUKE_VERSION_MAJOR = 13
NUKE_VERSION_MINOR = 0
NUKE_VERSION_PHASE = ''
NUKE_VERSION_PHASENUMBER = 633628
NUKE_VERSION_RELEASE = 1
NUKE_VERSION_STRING = '13.0v1'
NUM_CPUS = 10
NUM_INTERPOLATIONS = 5
PLUGIN_EXT = 'dylib'
PRECOMP_CALLBACK_OPENED = 'precomp.opened'
PREPEND = 8
PROFILE_ENGINE = 3
PROFILE_REQUEST = 2
PROFILE_STORE = 0
PROFILE_VALIDATE = 1
PYTHON = 32
READ_ONLY = 268435456
REPLACE = 1
REPLACE_VIEWS = 1
SAVE_MENU = 33554432
SCRIPT = 2
SMOOTH = 0
STARTLINE = 4096
STRIP_CASCADE_PREFIX = 4
TABBEGINCLOSEDGROUP = 2
TABBEGINGROUP = 1
TABENDGROUP = -1
TABKNOB = 0
THREADS = 10
TO_SCRIPT = 1
TO_VALUE = 2
USER_SET_SLOPE = 16
VIEWER = 1
VIEW_NAMES = 'input/view_names'
WRITE_ALL = 8
WRITE_NON_DEFAULT_ONLY = 16
WRITE_USER_KNOB_DEFS = 4
env = {'64bit': '', 'ExecutablePath': '', 'ExternalPython': '', 'LINUX': '', 'MACOS': '', 'NukeLibraryPath': '', 'NukeVersionDate': '', 'NukeVersionMajor': '', 'NukeVersionMinor': '', 'NukeVersionPhase': '', 'NukeVersionPhaseNumber': '', 'NukeVersionRelease': '', 'NukeVersionString': '', 'PluginExtension': '', 'PluginsVerbose': '', 'WIN32': '', 'assist': '', 'gui': '', 'hiero': '', 'hieroNuke': '', 'hieroStudio': '', 'indie': '', 'interactive': '', 'nc': '', 'nukex': '', 'numCPUs': '', 'ple': '', 'studio': '', 'threads': ''}

# Built-in methods
def activeViewer():
    """
    activeViewer() -> ViewerWindow

    Return an object representing the active Viewer panel. This
    is not the same as the Viewer node, this is the viewer UI element.

    @return: Object representing the active ViewerWindow
    """
    return ViewerWindow()

def addFavoriteDir(name:str, directory:str, type:str=None, icon:str=None, tooltip:str=None, key:str=None):
    """
    addFavoriteDir(name, directory, type, icon, tooltip, key) -> None.

    Add a path to the file choosers favorite directory list. The path name can contain environment variables which will be expanded when the user clicks the favourites button

    @param name: Favourite path entry ('Home', 'Desktop', etc.).
    @param directory: FileChooser will change to this directory path.
    @param type: Optional bitwise OR combination of nuke.IMAGE, nuke.SCRIPT, nuke.FONT or nuke.GEO.
    @param icon: Optional filename of an image to use as an icon.
    @param tooltip: Optional short text to explain the path and the meaning of the name.
    @param key: Optional shortcut key.
    @return: None.
    """
    return None

def addFormat(s:str):
    """
    addFormat(s) -> Format or None.

    Create a new image format, which will show up on the pull-down menus for image formats. You must give a width and height and name. The xyrt rectangle describes the image area, if it is smaller than the width and height (for Academy aperture, for example). The pixel aspect is the ratio of the width of a pixel to the height.

    @param s: String in TCL format "w h ?x y r t? ?pa? name".
    @return: Format or None.
    """
    return Union[Format, None]

def addNodePresetExcludePaths(paths:Iterable):
    """
    addNodePresetExcludePaths( paths ) -> None
    @param paths Sequence of paths to exclude
    Adds a list of paths that will be excluded from Node preset search paths.
    @return: None.
    """
    return None

def addSequenceFileExtension(fileExtension:str):
    """
    addSequenceFileExtension( fileExtension )
    Adds the input file extension to the list of extensions that will get displayed as sequences in the file browser.
    @param fileExtension the new file extension. Valid examples are: 'exr', '.jpg'; invalid examples are: 'somefile.ext'
    """
    return None

def addToolsetExcludePaths(paths:Iterable):
    """
    addToolsetExcludePaths( paths ) -> None
    @param paths Sequence of paths to exclude
    Adds a list of paths that will be excluded from Toolset search paths.
    @return: None.
    """
    return None

def addView(s:str):
    """
    addView(s) -> None

    Deprecated. Use the Root node.

    Adds a new view to the list of views.

    @param s: View name.
    @return: None
    """
    return None

def alert(prompt:str):
    """
    alert(prompt) -> None

    Show a warning dialog box. Pops up a warning box and waits for the user to hit the OK button.

    @param prompt: Present user with this message.
    @return: None
    """
    return None

def allNodes(filter:str=None, group=None):
    """
    allNodes(filter, group) -> List.
    List of all nodes in a group. If you need to get all the nodes in the script
    from a context which has no child nodes, for instance a control panel, use
    nuke.root().nodes().

    @param filter: Optional. Only return nodes of the specified class.
    @param group: Optional. If the group is omitted the current group (ie the group the user picked a menu item from the toolbar of) is used.
    @param recurseGroups: Optional. If True, will also return all child nodes within any group nodes. This is done recursively and defaults to False.
    @return: List
    """
    return [Node]

def animation(object, *commands):
    """
    animation(object, *commands) -> None

    Does operations on an animation curve.

    The following commands are supported:
      - B{clear} deletes all the keys from the animation.
      - B{erase} C{index I{last_index}} removes all keyframes between index and last_index
      - B{expression} C{I{newvalue}} returns or sets the expression for
        the animation. The default is 'curve' or 'y' which returns the interpolation of the keys.
      - B{generate} C{start end increment field expression I{field expression} ...}
        generates an animation with start, end, and increment. Multiple field/expression pairs
        generate a keyframe. Possible field commands are:
          - B{x} sets the frame number for the next keyframe
          - B{y} sets the keyframe value
          - B{dy} sets the left slope
          - B{ldy} sets left and right slope to the same value
          - B{la} and B{ra} are the length of the slope handle in x direction. A value of 1
            generates a handle that is one third of the distance to the next keyframe.
      - B{index} C{x} returns the index of the last key with x <= t, return -1 for none.
      - B{is_key} return non-zero if there is a key with x == t. The actual return value is the index+1.
      - B{move} C{field expression I{field expression}} replaces all selected keys
        in an animation with new ones as explained above in B{generate}
      - B{name} returns a user-friendly name for this animation. This will eliminate
        any common prefix between this animation and all other selected ones,
        and also replaces mangled names returned by animations with nice ones.
      - B{size} returns the number of keys in the animation.
      - B{test} errors if no points in the animation are selected
      - B{y} index C{I{newvalue}} gets or sets the value of an animation.
      - B{x} index C{I{newvalue}} gets or sets the horizontal postion of a key.
        If the animation contains an expression or keyframes, the new value will be overridden.

    See also: animations

    @param object: The animation curve.
    @param commands: a varargs-style list of commands, where each command is one of those defined above.
    @return: None
    """
    return None

def animationEnd():
    """
    animationEnd() -> float.

    Returns the last frame (or x value) for the currently selected animations.

    @return: The end frame.
    """
    return float()

def animationIncrement():
    """
    animationIncrement() -> float

    Returns a recommended interval between samples of the currently selected animation.

    @return: The recommended interval.
    """
    return float()

def animationStart():
    """
    animationStart() -> float

    Returns the starting frame (or x value) for the currently selected animations.

    @return: The start frame.
    """
    return float()

def animations():
    """
    animations() -> tuple

    Returns a list of animatable things the user wants to work on.

    If this is a command being executed from a menu item in a curve editor, a list of the names of all selected curves is returned. If this list is empty a "No curves selected" error is produced.

    If this is a command being executed from the pop-up list in a knob then a list of all the fields in the knob is returned.

    If this is a command being executed from the right-mouse-button pop-up list in a field of a knob, the name of that field is returned.

    Otherwise this produces an error indicating that the command requries a knob context. You can get such a context by doing "in <knob> {command}"

    Also see the 'selected' argument to the animation command.

    See also: animation, animationStart, animationEnd, animationIncrement

    @return: A tuple of animatable things.
    """
    return tuple()

def applyPreset(nodeName:str, presetName:str):
    """
    applyPreset(nodeName, presetName) -> None
    Applies a given preset to the current node.
    @param nodeName: Name of the node to apply the preset to.
    @param presetName: Name of the preset to use.
    @param node: (optional) a Node object to apply the preset to. If this is provided, the nodeName parameter is ignored.
    @return: bool.
    """
    return None

def applyUserPreset(nodeName:str, presetName:str):
    """
    applyUserPreset(nodeName, presetName) -> None
    Applies a given user preset to the current node.
    @param nodeName: Name of the node to apply the preset to.
    @param presetName: Name of the preset to use.
    @param node: (optional) a Node object to apply the preset to. If this is provided, the nodeName parameter is ignored.
    @return: bool.
    """
    return None

def ask(prompt:str):
    """
    ask(prompt) -> bool

    Show a Yes/No dialog.

    @param prompt: Present the user with this message.
    @return: True if Yes, False otherwise.
    """
    return bool()

def askWithCancel(prompt):
    """
    askWithCancel(prompt) -> bool

    Show a Yes/No/Cancel dialog.

    @param prompt: Present the user with this question.
    @return: True if Yes, False if No, an exception is thrown if Cancel.
    """
    return bool()

def autoplace(n:Node):
    """
    autoplace(n) -> None.

    Deprecated. Use Node.autoplace.

    Automatically place nodes, so they do not overlap.

    @param n: Node.
    @return: None
    """
    return None

def autoplaceSnap(n:Node):
    """
    autoplaceSnap(n) -> None

    Move node to the closest grid position.

    @param n: Node.
    @return: None
    """
    return None

def autoplace_all():
    """
    autoplace_all() -> None.

    Performs autoplace of all nodes in current context group.

    @return: None. May return exception it top context group has subgraph locked.
    """
    return None

def autoplace_snap_all():
    """
    autoplace_snap_all() -> None.

    Performs autoplace snap of all nodes in current context group.

    @return: None. May return exception it top context group has subgraph locked.
    """
    return None

def autoplace_snap_selected():
    """
    autoplace_snap_selected() -> None.

    Performs autoplace snap of all selected nodes in current context group.

    @return: None. May return exception it top context group has subgraph locked.
    """
    return None

def cacheUsage():
    """
    cacheUsage() -> int

    Get the total amount of memory currently used by the cache.

    @return: Current memory usage in bytes.
    """
    return int()

def canCreateNode(name:str):
    """
    canCreateNode(name) -> True if the node can be created, or False if not.

    This function can be used to determine whether it is possible to create a node with the specified node class.
    @param name: Node name.
    @return: True if the node can be created, or False if not.
    """
    return bool()

def cancel():
    """
    cancel() -> None
    Cancel an in-progress operation. This has the same effect as hitting cancel on the progress panel.

    @return: None
    """
    return None

def center():
    """
    center() -> array with x, then y

    Return the center values of a group's display, these values are suitable to be passed to nuke.zoom as the DAG center point.  Like so:
    center = nuke.center()
    zoom = nuke.zoom()
    print center[0]
    print center[1]
    ## move DAG back to center point without changing zoom.
    nuke.zoom( zoom, center )
    @return: Array of x, y.
    """
    return list()

def channels(n=None):
    """
    channels(n=None) -> (string) 

    Deprecated. Use Node.channels.

    List channels. The n argument is a Nuke node and if given only the channels output by this node are listed. If not given or None, all channels known about are listed.

    @param n: Optional node parameter.
    @return: A list of channel names.
    """
    return str()

def choice(title:str, prompt:str, options:list, default = 0):
    """
    choice(title, prompt, options, default = 0) -> index

    Shows a dialog box with the given title and prompt text, and a combo box containing the given options.

    @param title: Text to put in the dialog's title bar.
    @param prompt: Text to display at the top of the dialog.
    @param options: A list of strings for the user to choose from.
    @param default: The index (starting from zero) of the option to select first.
    @return: An integer index (starting from zero) of the choice the user selected, or None if the dialog was cancelled.
    """
    return int()

def clearBlinkCache():
    """
    clearBlinkCache() -> None

    Clear the Blink cache for all devices.
    """
    return None

def clearDiskCache():
    """
    clearDiskCache() -> None

    Clear the disk cache of all files.
    """
    return None

def clearRAMCache():
    """
    clearRAMCache() -> None

    Clear the RAM cache of all files.
    """
    return None

def clearTabMenuFavorites():
    """
    clearTabMenuFavorites() -> None

    Uncheck every favourite node in tab search menu.
    """
    return None

def clearTabMenuWeighting():
    """
    clearTabMenuWeighting() -> None

    Set the weight of each node to 0 in tab search menu.
    """
    return None

def clone(n:Node, args:Number=None, inpanel:bool=None):
    """
    clone(n, args, inpanel) -> Node

    Create a clone node that behaves identical to the original. The node argument is the node to be cloned, args and inpanel are optional arguments similar to createNode.
    A cloned node shares the exact same properties with its original. Clones share the same set of knobs and the same control panel. However they can
    have different positions and connections in the render tree. Any clone, including the original, can be deleted at any time without harming any of its clones.

    @param n: Node.
    @param args: Optional number of inputs requested.
    @param inpanel: Optional boolean.
    @return: Node
    """
    return Node()

def cloneSelected(action=None):
    """
    cloneSelected(action) -> bool

    This makes a clone of all selected nodes, preserving connections between them, and makes only the clones be selected.

    @param action: Optional and if 'copy' it cuts the resulting clones to the clipboard.
    @return: True if succeeded, False otherwise.
    """
    return bool()

def collapseToGroup(show=True):
    """
    collapseToGroup(show=True) -> Group

    Moves the currently selected nodes to a new group, maintaining their previous connections.

    @param show: If show is True, the node graph for the new group is shown in the background.
    @return: The new Group node.
    """
    return Group()

def collapseToLiveGroup(show=True):
    """
    collapseToLiveGroup(show=True) -> Group

    Moves the currently selected nodes to a new group, maintaining their previous connections.

    @param show: If show is True, the node graph for the new group is shown in the background.
    @return: The new Group node.
    """
    return Group()

def connectNodes():
    """
    connectNodes() -> None

    Deprecated. Use Group.connectSelectedNodes.

    @return: None
    """
    return None

def connectViewer(inputNum:Number, node:Node):
    """
    connectViewer(inputNum, node) -> None

    Connect a viewer input to a node. The argument i is the input number and n is either a Nuke node or None.
    Some viewer in the current group is found, if there are no viewers one is created. The viewer is then altered to have at least n+1 inputs and then input n is connected to the given node.This function is used by the numeric shortcuts in the DAG view menu.

    @param inputNum: Input number.
    @param node: The Node to connect to the input.
    @return: None
    """
    return None

def createLiveInput():
    """
    createLiveInput() -> Node

    Creates a new LiveInput and populates the "file" and "liveGroup" knobs according to the filename and LiveGroup name of the parent group

    @return: The new LiveInput_Node.
    """
    return Node()

def createNode(node:str, args:str=None, inpanel:bool=None):
    """
    createNode(node, args, inpanel) -> Node.

    Creates a node of the specified type and adds it to the DAG.

    @param node: Node class (e.g. Blur).
    @param args: Optional string containing a TCL list of name value pairs (like "size 50 quality 19")
    @param inpanel: Optional boolean to open the control bin (default is True; only applies when the GUI is running).
    @return: Node.
    """
    return Node()

def createScenefileBrowser(fileName:str, nodeName:str):
    """
    createScenefileBrowser( fileName, nodeName ) -> None

    Pops up a scene browser dialog box. 
    Receives the path to an Alembic (abc) or Universal Scene Description (usd/usda/usdc/usdz) file,
    and displays a hierarchical tree of the nodes within the file.
    The user can select which nodes they are interested in, and nodes of the appropriate type will automatically.
    be created.
    If a valid scene file nodeName is specified, this node will be populated with the selected tree. 

    @param fileName: Path and filename for an alembic or usd/usda/usdc/usdz file.
    @param nodeName: name of a valid scene file node to populate. If the node is invalid, new nodes will be automatically created
    """
    return None

def createToolset(filename=None, overwrite=-1, rootPath = None):
    """
    createToolset(filename=None, overwrite=-1, rootPath = None) -> None

    Creates a tool preset based on the currently selected nodes. 

    @param filename: Saves the preset as a script with the given file name.
     @param overwrite: If 1 (true) always overwrite; if 0 (false) never overwrite; @param rootPath: If specified, use this as the root path to save the Toolset to. If not specified, save to the user's .nuke/Toolsets folder.  otherwise, in GUI mode ask the user, in terminal do same as False. Default  is -1, meaning 'ask the user'.
    """
    return None

def critical(message:str):
    """
    critical(message)-> None

    Puts the message into the error console, treating it like an error. Also pops up an alert dialog to the user, immediately.

    @param message: String parameter.
    @return: None.
    """
    return None

def debug(message:str):
    """
    debug(message)-> None

    Puts the message into the error console, treating it like a debug message, which only shows up when the verbosity level is high enough.

    @param message: String parameter.
    @return: None.
    """
    return None

def defaultFontPathname():
    """
    defaultFontPathname() -> str

    Get the path to Nukes default font.

    @return: Path to the font.
    """
    return str()

def defaultNodeColor(s:str):
    """
    defaultNodeColor(s) -> int

    Get the default node colour.

    @param s: Node class.
    @return: The color as a packed integer (0xRRGGBB00).
    """
    return int()

def delete(n:Node):
    """
    delete(n) -> None

    The named node is deleted. It can be recovered with an undo.

    @param n: Node.
    @return: None
    """
    return None

def deletePreset(nodeClassName:str, presetName:str):
    """
    deletePreset(nodeClassName, presetName) -> None
    Deletes a pre-created node preset
    @param nodeClassName: Name of the node class to create a preset for.
    @param presetName: Name of the preset to create.
    @return: bool.
    """
    return None

def deleteUserPreset(nodeClassName:str, presetName:str):
    """
    deleteUserPreset(nodeClassName, presetName) -> None
    Deletes a pre-created user node preset
    @param nodeClassName: Name of the node class to create a preset for.
    @param presetName: Name of the preset to create.
    @return: bool.
    """
    return None

def deleteView(s:str):
    """
    deleteView(s) -> None

    Deprecated. Use the Root node.

    Deletes a view from the list of views.

    @param s: View name.
    @return: None
    """
    return None

def display(s:str, node:Node, title:str=None, width:Number=None):
    """
    display(s, node, title, width) -> None.

    Creates a window showing the result of a python script. The script is
    executed in the context of the given node, so this and a knob
    name in expressions refer to that node.

    The window will have an 'update' button to run the script again.

    @param s: Python script.
    @param node: Node.
    @param title: Optional title of window.
    @param width: Optional width of window.
    @return: None.
    """
    return None

def duplicateSelectedNodes():
    """
    duplicateSelectedNodes() -> None.

    Creates a duplicate of all selected nodes in the current script context group
    @return None. May return exception it top context group has subgraph locked.
    """
    return None

def endGroup():
    """
    endGroup() -> None

    Deprecated. Use Group.run, Group.begin/Group.end pairs or (preferably) the with statement.

    Changes the current group to the parent of the current group. Does nothing if the current group is a Root (the main window of a script).

    @return: None.
    """
    return None

def error(message:str):
    """
    error(message)-> None

    Puts the message into the error console, treating it like an error.

    @param message: String parameter.
    @return: None.
    """
    return None

def execute(nameOrNode:str, start:Number=None, end:Number=None, incr:int=None, views:list=None, continueOnError = False):
    """
    execute(nameOrNode, start, end, incr, views, continueOnError = False) -> None.
    execute(nameOrNode, frameRangeSet, views, continueOnError = False) -> None.


    Execute the named Write node over the specified frames.

    There are two variants of this function. The first allows you to specify the frames to write range by giving the start frame number, the end frame number and the frame increment. The second allows you to specify more complicated sets of frames by providing a sequence of FrameRange objects.

    If Nuke is run with the GUI up, this will pop up a progress meter. If the user hits the cancel button this command will return 'cancelled' error. If Nuke is run from the nuke command line (ie nuke was started with the -t switch) execute() prints a text percentage as it progresses. If the user types ^C it will aborting the execute() and return a 'cancelled' error.

    @param nameOrNode: A node name or a node object.
    @param start: Optional start frame. Default is root.first_frame.
    @param end: Optional end frame. Default is root.last_frame.
    @param incr: Optional increment. Default is 1.
    @param views: Optional list of views. Default is None, meaning "all views".
    @return: None
    """
    return None

def executeBackgroundNuke(exe_path:str, nodes:list, frameRange, views:list, limits:dict, continueOnError = False, flipbookToRun =None, flipbookOptions = {}):
    """
    executeBackgroundNuke(exe_path, nodes, frameRange, views, limits, continueOnError = False, flipbookToRun = , flipbookOptions = {}) -> None
    Run an instance of Nuke as a monitored sub process. Returns an integer that's used as unique id for the started task. If it failed to launch this will be -1.
    @param exe_path: Path to Nuke or a script that can take Nuke arguments. You probably want to supply nuke.EXE_PATH.
    @param nodes: A list of nodes to execute.
    @param frameRanges: List of frame ranges to execute.
    @param views: A list of view names to execute.
    @param limits: A dictionary with system limits, currently uses keys maxThreads and maxCache.
    @param flipbookToRun: The name of the flipbook application to run after the render, or an empty string if not desired.
    @param flipbookOptions: A dictionary with options to pass to the flipbook. These should include roi and pixelAspect.
    @return: Int.
    """
    return None

def executeMultiple(nodes:list, ranges:Number=None, views:list=None, continueOnError=False):
    """
    executeMultiple(nodes, ranges, views, continueOnError=False) -> None

    Execute the current script for a specified frame range. The argument nodes is a sequence of Nuke nodes and ranges is a sequence of range lists. A Nuke range list is a sequence of 3 integers - first, last and incr ( e.g. nuke.execute((w,), ((1,100,1),)) ). The named nodes must all be Write or other executable operators. If no nodes are given then all executable nodes in the current group are executed.
    Note that DiskCache and Precomp nodes do not get executed with this call, unless explicitly specified.

    If Nuke is run with the GUI up, this will pop up a progress meter. If the user hits the cancel button this command will raise a 'cancelled' error. If Nuke is run in terminal mode (with the -t switch) this prints a text percentage as it progresses.

    If the user types ^C it will abort the execute() and raise a 'cancelled' error.

    @param nodes: Node list.
    @param ranges: Optional start frame. Default is root.first_frame.
    @param views: Optional list of views. Default is None. Execute for all.
    @return: None
    """
    return None

def executing():
    """
    executing() -> Bool.

    Returns whether an Executable Node is currently active or not.
    @param f: Optional frame number.
    @return: Current bool.
    """
    return bool()

def exists(s:str):
    """
    exists(s) -> bool

    Check for the existence of a named item.
    Function for backwards-compatibility with TCL.

    @param s: Name of item.
    @return: True if exists, False otherwise.
    """
    return bool()

def expandSelectedGroup():
    """
    expandSelectedGroup() -> None

    Moves all nodes from the currently selected group node into its parent group, maintaining node input and output connections, and deletes the group. Returns the nodes that were moved, which will also be selected.

    @return: None
    """
    return None

def expression(s:str):
    """
    expression(s) -> float

    Parse a Nuke expression. Runs the same expression parser as is used by animations. This is not the same as the tcl expr parser. The main differences are:
    - Only floating point numbers are calculated. There are no strings, boolean, or integer values.
    - You can name any knob that returns a floating point value, with a dot-separated name, see knob for details on these names. You may follow
    the knob name with a time in parenthesis (like a function call) and if it is animated it will be evaluated at that time. If it is animated and
    no time is given, 'frame' is used.
    - The words 'frame', 't', and 'x' evaluate to the frame number of the context node, or the frame number this animation is being evaluated at.
    - The word 'y' in an animation expression evaluates to the value the animation would have if the control points were used and there was no
    expression. Outside an animation expression y returns zero.

    @param s: The expression, as a string.
    @return: The result.
    """
    return float()

def expression(s:str):
    """
    expression(s) -> float

    Parse a Nuke expression. Runs the same expression parser as is used by animations. This is not the same as the tcl expr parser. The main differences are:
    - Only floating point numbers are calculated. There are no strings, boolean, or integer values.
    - You can name any knob that returns a floating point value, with a dot-separated name, see knob for details on these names. You may follow
    the knob name with a time in parenthesis (like a function call) and if it is animated it will be evaluated at that time. If it is animated and
    no time is given, 'frame' is used.
    - The words 'frame', 't', and 'x' evaluate to the frame number of the context node, or the frame number this animation is being evaluated at.
    - The word 'y' in an animation expression evaluates to the value the animation would have if the control points were used and there was no
    expression. Outside an animation expression y returns zero.

    @param s: The expression, as a string.
    @return: The result.
    """
    return float()

def extractSelected():
    """
    extractSelected() -> None

    Disconnects the selected nodes in the group from the tree, and shifts them to the side.

    @return: None
    """
    return None

def filename(node=None, i:Iterable=None):
    """
    filename(node, i) -> str

    Return the filename(s) this node or group is working with.

    For a Read or Write operator (or anything else with a filename
    knob) this will return the current filename, based on the
    root.proxy settings and which of the fullsize/proxy filenames are
    filled in. All expansion of commands and variables is
    done. However by default it will still have %%04d sequences in it,
    use REPLACE to get the actual filename with the current frame number.

    If the node is a group, a search is done for executable (i.e. Write)
    operators and the value from each of them is returned. This will duplicate
    the result of calling execute() on the group.

    @param node: Optional node.
    @param i: Optional nuke.REPLACE. Will replace %%04d style sequences with the current frame number.
    @return: Filename, or None if no filenames are found.
    """
    return str()

def forceClone():
    """
    forceClone() -> bool

    @return: True if succeeded, False otherwise.
    """
    return bool()

def forceLoad(n=None):
    """
    forceLoad(n) -> None

    Force the plugin to be fully instantiated.

    @param n: Optional node argument. Default is the current node.
    @return: None
    """
    return None

def fork(*args, **kwargs):
    """
    Forks a new instance of Nuke optionally with the contents of the named file.
    """
    return None

def formats():
    """
    formats() -> list

    @return: List of all available formats.
    """
    return [Format]

def frame(f:Number=None):
    """
    frame(f) -> Current frame.

    Return or set the current frame number. Deprecated. Use Root.frame.

    Returns the current frame. Normally this is the frame number set in the root
    node, typically by the user moving the frame slider in a viewer. If a number is
    given, it sets the current frame number to that number. If the current context
    is the root this changes the root frame.
    @param f: Optional frame number.
    @return: Current frame.
    """
    return Number()

def fromNode(n:Node):
    """
    fromNode(n) -> String.

    Return the Node n as a string.
    This function is most useful when combining Python and TCL scripts for backwards compatibility reasons.

    @param n: A Node.
    @return: String.
    """
    return str()

def getAllUserPresets():
    """
    getAllUserPresets() -> None
    gets a list of all current user presets
    @return: a list of tuples containing all nodename/presetname pairs.
    """
    return None

def getClipname(prompt:str, pattern=None, default=None, multiple=False):
    """
    getClipname(prompt, pattern=None, default=None, multiple=False) -> list of strings or string

    Pops up a file chooser dialog box. You can use the pattern to restrict the displayed choices to matching filenames,
    normal Unix glob rules are used here. getClipname compresses lists of filenames that only differ by an index number
    into a single entry called a 'clip'.

    @param prompt: Present the user with this message.
    @param pattern: Optional file selection pattern.
    @param default: Optional default filename and path.
    @param multiple: Optional boolean convertible object to allow for multiple  selection.
    @return: If multiple is True, the user input is returned as a list of  strings, otherwise as a single string. If the dialog is cancelled, the  return value is None.
    """
    return list()

def getColor(initial:int=None):
    """
    getColor(initial) -> int

    Show a color chooser dialog and return the selected color as an int.

    The format of the color values is packed 8bit rgb multiplied by 256 (ie in hex: 0xRRGGBB00).

    @param initial: Optional initial color. Integer with components packed as above.
    @return: The selected color.
    """
    return int()

def getDeletedPresets():
    """
    getDeletedPresets() -> None
    gets a list of all currently deleted presets
    @return: a pyDict containing all nodename/presetname pairs.
    """
    return None

def getFileNameList(dir:Iterable, splitSequences = False, extraInformation = False, returnDirs=True, returnHidden=False):
    """
    getFileNameList( dir, splitSequences = False, extraInformation = False, returnDirs=True, returnHidden=False ) -> str
    @param dir the directory to get sequences from
    @param splitSequences whether to split sequences or not
    @param extraInformation whether or not there should be extra sequence information on the sequence name
    @param returnDirs whether to return a list of directories as well as sequences
    @param returnHidden whether to return hidden files and directories.
    Retrieves the filename list .
    @return: Array of files.
    """
    return str()

def getFilename(message:str, pattern=None, default=None, favorites=None, type=None, multiple=False):
    """
    getFilename(message, pattern=None, default=None, favorites=None, type=None, multiple=False) -> list of strings or single string

    Pops up a file chooser dialog box. You can use the pattern to restrict the displayed choices to matching filenames, normal Unix glob rules are used here.

    @param message: Present the user with this message.
    @param pattern: Optional file selection pattern.
    @param default: Optional default filename and path.
    @param favorites: Optional. Restrict favorites to this set. Must be one of  'image', 'script', or 'font'.
    @param type: Optional the type of browser, to define task-specific behaviors;  currently only 'save' is recognised.
    @param multiple: Optional boolean convertible object to allow for multiple  selection. If this is True, the return value will be a list of strings; if  not, it will be a single string. The default is 
    @return: If multiple is True, the user input is returned as a list of  strings, otherwise as a single string. If the dialog was cancelled, the  return value will be None.
    """
    return list()

def getFonts():
    """
    getFonts() -> list of font  families and styl.

    Return a list of all available font families and styles 

    @return: List of font families and style.
    """
    return list()

def getFramesAndViews(label:str, default=None, maxviews=0):
    """
    getFramesAndViews(label, default=None, maxviews=0) -> (ranges, views)

    Pops up a dialog with fields for a frame range and view selection.

    @param label: User message.
    @param default: Optional value for the input field.
    @param maxviews: Optional max number of views.
    @return: List of ranges and views.
    """
    return Iterable()

def getInput(prompt:str, default:str):
    """
    getInput(prompt, default) -> str

    Pops up a dialog box with a text field for an arbitrary string.

    @param prompt: Present the user with this message.
    @param default: Default value for the input text field.
    @return: String from text field or None if dialog is cancelled.
    """
    return str()

def getNodeClassName():
    """
    getNodeClassName() -> None
    gets the class name for the currently selected node
    @return: a string containing the name.
    """
    return str()

def getNodePresetExcludePaths():
    """
    getNodePresetExcludePaths() -> string list

    Gets a list of all paths that are excluded from the search for node presets.

    @return: List of paths.
    """
    return list()

def getNodePresetID():
    """
    getNodePresetID() -> None
    gets the node preset identifier for the currently selected node
    @return: a string containing the ID.
    """
    return None

def getOcioColorSpaces():
    """
    getOcioColorSpaces() -> returns the list of OCIO colorspaces.
    @return: list of strings
    """
    return list()

def getPaneFor( panelName ):
    """
    getPaneFor( panelName ) -> Dock

    Returns the first pane that contains the named panel or None if it can't be found.
    Note that the panelName must be exact as described in the layout.xml file or the panel ID.
    For example, 'Properties.1' or 'Viewer.1 or 'co.uk.thefoundry.WebBrowser'

    @return: The pane or None.
    """
    return Any

def getPresetKnobValues():
    """
    getPresetKnobValues() -> None
    gets a list of knob values for a given preset
    @param nodeClassName: Name of the node class to get values for.
    @param presetName: Name of the preset to get values for.
    @return: a pyDict containing all knob name/value pairs.
    """
    return None

def getPresets():
    """
    getPresets() -> None
    gets a list of all presets for the currently selected node's class
    @return: a pyList containing all nodename/presetname pairs.
    """
    return None

def getPresetsMenu(Node):
    """
    getPresetsMenu(Node) -> Menu or None
    Gets the presets menu for the currently selected node.
    @return: The menu, or None if it doesn't exist.
    """
    return Union[Menu, None]

def getReadFileKnob(node:Node):
    """
    getReadFileKnob(node) -> knob

    @brief Gets the read knob for a node (if it exists).

    @param node: The node to get the knob for.

    @return: A PyObject containing the read knob if it exists, NULL otherwise
    """
    return knob()

def getRenderProgress():
    """
    getRenderProgress() -> Returns the progress of the render of a frame from 0 - 100 % complete.
    @return: The progress of the render.  Can be 0 if there is no progress to report.
    """
    return int()

def getToolsetExcludePaths():
    """
    getToolsetExcludePaths() -> string list

    Gets a list of all paths that are excluded from the search for node presets.

    @return: List of paths.
    """
    return list()

def getUserPresetKnobValues():
    """
    getUserPresetKnobValues() -> None
    gets a list of knob values for a given preset
    @param nodeClassName: Name of the node class to get values for.
    @param presetName: Name of the preset to get values for.
    @return: a pyDict containing all knob name/value pairs.
    """
    return None

def getUserPresets(Node):
    """
    getUserPresets(Node) -> None
    gets a list of all user presets for the currently selected node's class
    @return: a pyList containing all nodename/presetname pairs.
    """
    return None

def hotkeys():
    """
    hotkeys() -> str

    Returns the Nuke key assignments as a string formatted for use in nuke.display().

    @return: A formatted string.
    """
    return str()

def inputs(n:Node, i:Number=None):
    """
    inputs(n, i) -> int

    Deprecated. Use Node.inputs.

    Get how many inputs the node has. Normally this is a constant but some nodes have a variable number, the user can keep connecting them and the count will increase.
    Attempting to set the number will just disconnect all inputs greater or equal to number. For a variable input node this may decrease
    inputs to the new value. For most nodes this will have no effect on the value of inputs.

    @param n: Node.
    @param i: Optional number of inputs requested.
    @return: Number of inputs.
    """
    return int()

def invertSelection():
    """
    invertSelection() -> None

    Selects all unselected nodes, and deselects all selected ones.

    @return: None.
    """
    return None

def knob(name:str, value:Any=None, getType:int=None, getClass:str=None):
    """
    knob(name, value, getType, getClass) -> None

    @brief Returns or sets the entire state of a knob.

    Each individual control on a control panel is called a 'knob'. A
    knob's name is a dot-separated list. An example of a fully-expanded
    name of a knob is 'root.Group1.Blur1.size.w'. 'root' is the node
    name of the outermost group, 'Group1' is a group inside that
    containing the blur operator, 'Blur1' is the name of a blur
    operator, 'size' is the name of the actual knob, and 'w' is the
    name of the 'field' (there are two fields in a blur size, 'w' and
    'h').

    You can omit a lot of this because all knob names are figured out
    relative to a 'current knob' and 'current node'. These are set
    depending on the context of where the scripting is invoked. For
    menu items the current node is the group that contained the menu,
    and there is no current knob. For expressions typed into knob
    fields the current knob is that knob and the current node is the
    node the knob belongs to.

    If a name does not start with 'root' then a search upwards is done
    for the first word in the name, first against the fields in the
    current knob, then against the knobs in the current node, then
    against the nodes in the group containing the current node (or in
    it if it is a group), on up to the root.

    The word 'this' means the current knob or the current node.

    The word 'input' means the first (0 or B) input of a node. Ie
    'Blur1.input' returns the node connected to the input of Blur1,
    while 'Blur1.input.input' returns the input of that node.

    If you are getting the value for reporting to the user, you probably
    want to use the value or expression commands.

    If the getType argument is specified and is True, it will print out the type of the
    knob rather than getting or setting the value. The type is an integer,
    using the same list as addUserKnob.

    If the getClass argument is specified and is True, it will print out the type of the knob as a string, e.g. 'Int_Knob',
    'Enumeration_Knob', 'XY_Knob'.

    If both the getType and getClass arguments are present and are True, getType takes precedence.
    @param name: The name of the knob.
    @param value: Optional argument. If this is present, the value will be stored into the knob.
    @param getType: Optional boolean argument. If True, return the class ID for the knob instead of the knob itself. The class ID is an int.
    @param getClass: Optional boolean argument. If True, return the class name for the knob instead of the knob itself. The class name is a string.
    """
    return None

def knobDefault(classknob:str, value:str=None):
    """
    knobDefault(classknob, value) -> str

    Set a default value for knobs in nodes that belong to the
    same class. All knobs with matching names, that are created after this
    command was issued, will default to the new value. If class. is missing
    or is "*." then this default applies to all nodes with such a knob.
    If several values are supplied, the first value which is valid will be
    used as the default.
    knobDefault can be used to specify file format specific knobs.
    These are knobs that are added to Read, Write and other file format 
    dependent nodes when the file name changes. To specify defaults, use 
    the class name, followed by the file format extension, followed by the knob name, 
    all separated by periods. An example is shown below.

    Example:
    nuke.knobDefault("Blur.size", "20")

    Example:
    nuke.knobDefault("Read.exr.compression", "2")

    @param classknob: String in the form "class.knob" where "class" is the class of Node, i.e. Blur, and "knob" is the name of the knob. This can also include a file extension, as in "class.extension.knob"
    @param value: Optional string to convert to the default value.
    @return: None or String with the default value.
    """
    return str()

def knobTooltip(classknob:str, value:str):
    """
    knobTooltip(classknob, value) -> None

    Set an override for a tooltip on a knob.

    Example:

       nuke.knobTooltip('Blur.size', '[some text]')

    @param classknob: String in the form "class.knob" where "class" is the class of Node, i.e. Blur, and "knob" is the name of the knob.
    @param value: String to use as the tooltip
    @return: None
    """
    return None

def layers(node=None):
    """
    layers(node=None) -> string list.

    Lists the layers in a node. If no node is provided this will list all known layer names in this script.

    @param node: Optional node parameter.
    @return: A list of layer names.
    """
    return [str]

def licenseInfo():
    """
    licenseInfo() -> Shows information about licenses used by nuke.
    @return: None
    """
    return Any

def load(s:str):
    """
    load(s) -> None

    Load a plugin. You can force a certain plugin to load with this function. If the plugin has already been loaded nothing happens.
    If there is no slash in the name then the pluginPath() is searched for it. If there is a slash then the name is used directly as a
    filename, if it does not start with a slash the name is relative to the directory containing any plugin being currently loaded.
    If no filename extension is provided, it will try appending '.so' (or whatever your OS dynamic library extension is) and finding
    nothing will also try to append '.tcl' and '.py'.

    @param s: Plugin name or filename.
    @return: None
    @raise RuntimeError: if the plugin couldn't be loaded for any reason.
    """
    return None

def loadToolset(filename=None, overwrite=-1):
    """
    loadToolset(filename=None, overwrite=-1) -> None

    Loads the tool preset with the given file name. 

    @param filename: name of preset script file to load
 
    """
    return None

def localisationEnabled(knob):
    """
    localisationEnabled(knob) -> bool

    Checks if localisation is enabled on a given Read_File_Knob.

    [DEPRECATION WARNING] function will be removed in Nuke 12 use 'localizationEnabled' instead.

    @param knob: The Read_File_Knob to check.

    @return: true if enabled, false otherwise
    """
    return bool()

def localiseFiles(readKnobs):
    """
    localiseFiles(readKnobs) -> This functionality has been removed, please check the documentation
    @return: None.
    """
    return Any

def localizationEnabled(knob):
    """
    localizationEnabled(knob) -> bool

    Checks if localization is enabled on a given Read_File_Knob.

    @param knob: The Read_File_Knob to check.

    @return: true if enabled, false otherwise
    """
    return bool()

def makeGroup(show=True):
    """
    makeGroup(show=True) -> Group

    Creates a new group containing copies of all the currently selected nodes. Note that this creates duplicates of the selected nodes, rather than moving them.

    @param show: If show is True, the node graph for the new group is shown.
    @return: The new Group node.
    """
    return Group()

def maxPerformanceInfo(*args, **kwargs):
    """
    maxPerformanceInfo -> Get the max performance info for this session.

    Returns a struct containing the max performance info if performance timers are in use, otherwise returns None.
    """
    return Number()

def memory(cmd, value):
    """
    memory(cmd, value) -> str or int
    Get or set information about memory usage.

    The value parameter is optional and is only used by some of the commands (see below).

    The cmd parameter specifies what memory information to retrieve. It can be one of the following values:
    - info [node-name]                           Return a string describing current memory usage. Can optionally provide it for a specific node.
    - infoxml [format_bytes] [node-name]         Return current memory usage as above, but in XML format. Can optionally provide if bytes should be formatted to be human readable, and also a specific node
    - allocator_info [format_bytes]              Return current allocator usage in XML format. Can optionally provide if bytes should be formatted to be human readable
    - free [size]                                Free as much memory as possible. If a size is specified, if will stop trying to free memory when usage drops below the size.
    - usage                                      Return the amount of memory currently in use.
    - max_usage [size]                           If no size is specified, returns the current size of the memory limit.  If a size is given, then set this size as the memory limit.
    - total_ram                                  Return the total amount of RAM.
    - total_vm                                   Return the total virtual memory.
    - free_count [num]                           Get or set the free count.
    - new_handler_count [num]                    Get or set the new handler count.
    """
    return str or int()

def menu(name:str):
    """
    menu(name) -> Menu

    Find and return the Menu object with the given name. Current valid menus are:

    'Nuke'          the application menu
    'Pane'          the UI Panes & Panels menu
    'Nodes'         the Nodes toolbar (and Nodegraph right mouse menu)
    'Properties'    the Properties panel right mouse menu
    'Animation'     the knob Animation menu and Curve Editor right mouse menu
    'Viewer'        the Viewer right mouse menu
    'Node Graph'    the Node Graph right mouse menu
    'Axis'          functions which appear in menus on all Axis_Knobs.

    @param name: The name of the menu to get. Must be one of the values above.
    @return: The menu.
    @raise RuntimeError: if Nuke isn't in GUI mode.
    """
    return Menu()

def message(prompt:str):
    """
    message(prompt) -> None

    Show an info dialog box. Pops up an info box (with a 'i' and the text message) and waits for the user to hit the OK button.

    @param prompt: Present user with this message.
    @return: None
    """
    return None

def modified(status:bool=None):
    """
    modified(status) -> True if modified, False otherwise.

    Deprecated. Use Root.modified and Root.setModified.

    Get or set the 'modified' flag in a script. Setting the value will turn the indicator in the title bar on/off and will start or stop the autosave timeout.

    @param status: Optional boolean value. If this is present the status will be set to this value; otherwise it will be retrieved instead.
    @return: True if modified, False otherwise.
    """
    return bool()

def nodeCopy(s:str):
    """
    nodeCopy(s) -> bool

    Copy all selected nodes into a file or the clipboard.

    @param s: The name of a clipboad to copy into. If s is the string '%clipboard%' this will copy into the operating systems clipboard.
    @return: True if any nodes were selected, False otherwise.
    """
    return bool()

def nodeDelete(s):
    """
    nodeDelete(s) -> True if any nodes were deleted, False otherwise.

    Removes all selected nodes from the DAG.

    @return: True if all nodes were deleted, False if at least one wasn't.
    """
    return bool()

def nodePaste(s):
    """
    nodePaste(s) -> Node

    Paste nodes from a script file or the clipboard.
    This function executes the script stored in a file. It is assumed the script is the result of
    a nodeCopy command. The 's' argument can be '%clipboard%' to paste the operating system's clipboard contents.

    @param s: The 's' argument can be '%clipboard%' to paste the operating system's clipboard contents.
    @return: Node
    """
    return Node()

def nodeTypes(force_plugin_load=False):
    """
    nodeTypes(force_plugin_load=False) -> List
    @param force_plugin_load bool True to force loading all plugins on the path before querying node types (default: False)
    @return list of all loaded node types
    """
    return list()

def nodesSelected():
    """
    nodesSelected() -> None

    returns true if any nodes are currently selected 
    """
    return None

def numvalue(knob:Knob, default=None):
    """
    numvalue(knob, default=infinity) -> float

    The numvalue function returns the current value of a knob.

    This is the same as the value() command except it will always return a number. For enumerations this returns the index into the menu, starting at zero. For checkmarks this returns 0 for false and 1 for true.
    @param knob: A knob.
    @param default: Optional default value to return if the knob's value cannot  be converted to a number.
    @return: A numeric value for the knob, or the default value (if any).
    """
    return float()

def oculaPresent():
    """
    oculaPresent() -> bool

    Check whether Ocula is present.

    @return: True if Ocula is present, False if not.
    """
    return bool()

def ofxAddPluginAliasExclusion(fullOfxEffectName:list):
    """
    ofxAddPluginAliasExclusion(fullOfxEffectName) -> None
    Adds the ofx effect name to a list of exclusions that will not get tcl aliases automatically created for them.
    For example, if there is an ofx plugin with a fully qualified name of: 'OFXuk.co.thefoundry.noisetools.denoise_v100'.
    Nuke by default would automatically alias that so that nuke.createNode('Denoise') will create that node type.
    By calling nuke.ofxAddPluginAliasExclusion('OFXuk.co.thefoundry.noisetools.denoise_v100'), you'd be changing
    that such that the only way to create a node of that type would be to call nuke.createNode('OFXuk.co.thefoundry.noisetools.denoise_v100')
    This does not change saving or loading of Nuke scripts with that plugin used in any way.
    @param fullOfxEffectName: The fully qualified name of the ofx plugin to add to the exclusion list.
    @return: None.
    """
    return None

def ofxMenu():
    """
    ofxMenu() -> bool

    Find all the OFX plugins (by searching all the directories below $OFX_PLUGIN_PATH,
    or by reading a cache file stored in $NUKE_TEMP_DIR), then add a menu item for each
    of them to the main menu.

    @return: True if succeeded, False otherwise.
    """
    return bool()

def ofxPluginPath():
    """
    nuke.ofxPluginPath() -> String list

    List of all the directories Nuke searched for OFX plugins in.

    @return: String list
    """
    return list()

def ofxRemovePluginAliasExclusion(fullOfxEffectName:list):
    """
    ofxRemovePluginAliasExclusion(fullOfxEffectName) -> None
    Remove an ofx plugin alias exclusion that was previously added with .
    Example: nuke.ofxRemovePluginAliasExclusion('OFXuk.co.thefoundry.noisetools.denoise_v100')
    @param fullOfxEffectName: The fully qualified name of the ofx plugin to remove from the exclusion list.
    @return: None.
    """
    return None

def nodesSelected():
    """
    nodesSelected() -> List

    returns a list of Nodes which have panels open.The last item in the list is the currently active Node panel.
    """
    return list()

def pan():
    """
    pan() -> array with x, then y

    Return the pan values of a group's display.
    This function is deprecated and will be removed in a future version.  You probably want to use nuke.center().

    n = nuke.pan()
    print n[0]
    print n[1]

    @return: Array of x, y.
    """
    return list()

def performanceProfileFilename():
    """
    performanceProfileFilename() -> File to write performance profile to for this session.

    Returns the profile filename if performance timers are in use, otherwise returns None.
    """
    return str()

def pluginExists(name:str):
    """
    pluginExists(name) -> True if found, or False if not.

    This function is the same as load(), but only checks for the existence of a plugin rather than loading it.
    If there is no slash in the name then the pluginPath() is searched for it. If there is a slash then the name is used directly as a
    filename, if it does not start with a slash the name is relative to the directory containing any plugin being currently loaded.
    If no filename extension is provided, it will try appending '.so' (or whatever your OS dynamic library extension is) and finding
    nothing will also try to append '.tcl' and '.py'.

    @param name: Plugin name or filename.
    @return: True if found, or False if not.
    """
    return bool()

def pluginInstallLocation():
    """
    pluginInstallLocation() -> string list

    The system-specific locations that Nuke will look in for third-party plugins.

    @return: List of paths.
    """
    return list()

def pluginPath():
    """
    pluginPath() -> string list

    List all the directories Nuke will search in for plugins.

    The built-in default is ~/.nuke and the 'plugins' directory from the same location the NUKE executable file is in. Setting the environment variable $NUKE_PATH to a colon-separated list of directories will replace the ~/.nuke with your own set of directories, but the plugins directory is always on the end.

    @return: List of paths.
    """
    return list()

def plugins(switches=0, *pattern):
    """
    plugins(switches=0, *pattern)-> list of str

    Returns a list of every loaded plugin or every plugin available. By default each plugin is returned as the full pathname of the plugin file.

    You can give a glob-style matching pattern and only the plugins whose filenames (not path) match the pattern will be returned. You can give more than one glob pattern if desired.

    You can also put options before the glob patterns. Currently supported:

      ALL    Return all plugins in each of the plugin_path() directories,
             rather than only the currently loaded plugins.

      NODIR  Just put the filenames in the list, not the full path. There
             may be duplicates.

    If you don't specify any switches, the default behaviour is to return a list
    with the full paths of all loaded plugins.

    @param switches: Optional parameter. Bitwise OR of nuke.ALL, nuke.NODIR.
    @param pattern: Zero or more glob patterns.
    @return: List of plugins.
    """
    return list()

def recentFile(index:list):
    """
    recentFile(index) -> str

    Returns a filename from the recent-files list.

    @param index: A position in the recent files list. This must be a non-negative number.
    @return: A file path.
    @raise ValueError: if the index is negative.
    @raise RuntimeError: if there is no entry in the recent files list for the specified index.
    """
    return str()

def redo():
    """
    redo() -> None

    Perform the most recent redo.

    @return: None
    """
    return None

def registerFlipbook(s:str):
    """
    registerFlipbook(s) -> None

    Register a flipbook application name into Nuke.
    @param s: Name of the flipbook application to be registered.
    @return: None
    """
    return None

def removeFavoriteDir(name:str, type:str=None):
    """
    removeFavoriteDir(name, type) -> None.

    Remove a directory path from the favorites list.

    @param name: Favourite path entry ('Home', 'Desktop', etc.).
    @param type: Optional bitwise OR combination of nuke.IMAGE, nuke.SCRIPT, nuke.FONT or nuke.GEO.
    @return: None
    """
    return None

def execute(nameOrNode:str, start:Number=None, end:Number=None, incr:int=None, views:list=None, continueOnError = False):
    """
    execute(nameOrNode, start, end, incr, views, continueOnError = False) -> None.
    execute(nameOrNode, frameRangeSet, views, continueOnError = False) -> None.


    Execute the named Write node over the specified frames.

    There are two variants of this function. The first allows you to specify the frames to write range by giving the start frame number, the end frame number and the frame increment. The second allows you to specify more complicated sets of frames by providing a sequence of FrameRange objects.

    If Nuke is run with the GUI up, this will pop up a progress meter. If the user hits the cancel button this command will return 'cancelled' error. If Nuke is run from the nuke command line (ie nuke was started with the -t switch) execute() prints a text percentage as it progresses. If the user types ^C it will aborting the execute() and return a 'cancelled' error.

    @param nameOrNode: A node name or a node object.
    @param start: Optional start frame. Default is root.first_frame.
    @param end: Optional end frame. Default is root.last_frame.
    @param incr: Optional increment. Default is 1.
    @param views: Optional list of views. Default is None, meaning "all views".
    @return: None
    """
    return None

def rescanFontFolders():
    """
    rescanFontFolders() -> None

    Rebuild the font cache scanning all available font directories.

    @return: None.
    """
    return None

def resetPerformanceTimers():
    """
    resetPerformanceTimers() -> None

    Clears the accumulated time on the performance timers.
    """
    return None

def restoreWindowLayout(i:Number):
    """
    restoreWindowLayout(i) -> None.
    Restores a saved window layout.
    @param i: Layout number
    @return: None
    """
    return None

def resumePathProcessing():
    """
    resumePathProcessing() -> None
    Resume path processing.
    Use prior to performingmultiple node graph modifications, to avoid repeated path processing.
    @return: None.
    """
    return None

def root():
    """
    root() -> node 

    Get the DAG's root node. Always succeeds.

    @return: The root node. This will never be None.
    """
    return Node()

def runIn(object:str, cmd):
    """
    runIn(object, cmd) -> bool

    Execute commands with a given node/knob/field as the 'context'.
    This means that all names are evaluated relative to this object, and commands that modify 'this' node will modify the given one.

    @param object: Name of object.
    @param cmd: Command to run.
    @return: True if succeeded, False otherwise.
    """
    return bool()

def sample(n:Node, c:str, x:Number, y:Number, dx:Number=None, dy:Number=None):
    """
    sample(n, c, x, y, dx, dy) -> float.

    Get pixel values from an image. Deprecated, use Node.sample instead.

    This requires the image to be calculated, so performance may be very bad if this is placed into an expression in a control panel. Produces a cubic filtered result. Any sizes less than 1, including 0, produce the same filtered result, this is correct based on sampling theory. Note that integers are at the corners of pixels, to center on a pixel add .5 to both coordinates. If the optional dx,dy are not given then the exact value of the square pixel that x,y lands in is returned. This is also called 'impulse filtering'.

    @param n: Node.
    @param c: Channel name.
    @param x: Centre of the area to sample (X coordinate).
    @param y: Centre of the area to sample (Y coordinate).
    @param dx: Optional size of the area to sample (X coordinate).
    @param dy: Optional size of the area to sample (Y coordinate).
    @return: Floating point value.
    """
    return float()

def saveEventGraphTimers(filePath:str):
    """
    saveEventGraphTimers(filePath) -> None

    Save events in the event graph.
    @param filePath: specify the file path where the event graph profiling data should be saved to.
    """
    return None

def saveToScript(filename, fileContent):
    """
    saveToScript(filename, fileContent) -> None

    Saves the fileContent with the given filename.
    """
    return None

def saveUserPreset(node, presetName:str):
    """
    saveUserPreset(node, presetName) -> None
    Saves a node's current knob values as a user preset.
    @param presetName: Name of the preset to create.
    @return: bool.
    """
    return None

def saveWindowLayout(i=-1):
    """
    saveWindowLayout(i=-1) -> None

    Saves the current window layout.

    @param i: Optional layout index. If this is omitted or set to a negative value, save as the default layout.
    @return: None.
    """
    return None

def scriptClear(*args, **kwargs):
    """
    Clears a Nuke script and resets all the root knobs to user defined knob defaults. To reset to compiled in defaults only pass in resetToCompiledDefaults=True.
    """
    return None

def scriptClose(*args, **kwargs):
    """
    Close the current script or group. Returns True if successful.
    """
    return None

def scriptExit(*args, **kwargs):
    """
    Exit Nuke.
    """
    return None

def scriptName():
    """
    scriptName() -> String

    Return the current script's file name
    """
    return str()

def scriptNew(*args, **kwargs):
    """
    Start a new script. Returns True if successful.
    """
    return None

def scriptOpen(*args, **kwargs):
    """
    Opens a new script containing the contents of the named file.
    """
    return None

def scriptReadFile(*args, **kwargs):
    """
    Read nodes from a file.
    """
    return None

def scriptReadText(*args, **kwargs):
    """
    Read nodes from a string.
    """
    return None

def scriptSave(filename=None):
    """
    scriptSave(filename=None) -> bool

    Saves the current script to the current file name. If there is no current file name and Nuke is running in GUI mode, the user is asked for a name using the file chooser.

    @param filename: Save to this file name without changing the script name in the project (use scriptSaveAs() if you want it to change).
    @return: True if the file was saved, otherwise an exception is thrown.
    """
    return bool()

def scriptSaveAs(filename=None, overwrite=-1):
    """
    scriptSaveAs(filename=None, overwrite=-1) -> None

    Saves the current script with the given file name if supplied, or (in GUI mode) asks the user for one using the file chooser. If Nuke is not running in GUI mode, you must supply a filename.

    @param filename: Saves the current script with the given file name if  supplied, or (in GUI mode) asks the user for one using the file chooser.
    @param overwrite: If 1 (true) always overwrite; if 0 (false) never overwrite;  otherwise, in GUI mode ask the user, in terminal do same as False. Default  is -1, meaning 'ask the user'.
    """
    return None

def scriptSaveToTemp(string):
    """
    scriptSaveToTemp(string) -> string

    Saves the script to a file without modifying the root information or the original script
    """
    return str()

def scriptSource(*args, **kwargs):
    """
    Same as scriptReadFile().
    """
    return None

def selectAll():
    """
    selectAll() -> None

    Select all nodes in the DAG.

    @return: None
    """
    return None

def selectPattern():
    """
    selectPattern() -> None

    Selects nodes according to a regular expression matching pattern, entered through an input dialog. The pattern can include wildcards ('?' and '*') as well as regular expressions. The expressions are checked against the node name, label, class, and associated file names.

    @return: None
    """
    return None

def selectSimilar(matchType):
    """
    selectSimilar(matchType) -> None

    Selects nodes that match a node in the current selection based on matchType criteria.

    @param matchType: One of nuke.MATCH_CLASS, nuke.MATCH_LABEL, nuke.MATCH_COLOR.
    @return: None.
    """
    return None

def selectedNode():
    """
    selectedNode() -> Node.

    Returns the 'node the user is thinking about'.
    If several nodes are selected, this returns one of them. The one returned will be an 'output' node in that no other selected nodes
    use that node as an input. If no nodes are selected, then if the last thing typed was a hotkey this returns the node the cursor is pointing at.
    If none, or the last event was not a hotkey, this produces a 'No node selected' error.

    @return: Node.
    """
    return Node()

def selectedNodes(filter:str=None):
    """
    selectedNodes(filter) -> List.

    Returns a list of all selected nodes in the current group. An attempt is made to return them in 'useful' order where inputs are done before the final node, so commands applied to this list go from top-down.

    @param filter: Optional class of Node. Instructs the algorithm to apply only to a specific class of nodes.
    @return: The list of selected nodes.
    """
    return [Node]

def setPreset(nodeClassName:str, presetName:str, knobValues:dict):
    """
    setPreset(nodeClassName, presetName, knobValues) -> None
    Create a node preset for the given node using the supplied knob values
    @param nodeClassName: Name of the node class to create a preset for.
    @param presetName: Name of the preset to create.
    @param knobValues: A dictionary containing a set of knob names and preset values.
    @return: bool.
    """
    return None

def setReadOnlyPresets(readOnly):
    """
    setReadOnlyPresets(readOnly) -> None
    Sets whether newly created presets should be added in read-only mode.
    Read-only presets can be applied to a node, but can't be overwritten or deleted.
    """
    return None

def setUserPreset(nodeClassName:str, presetName:str, knobValues:dict):
    """
    setUserPreset(nodeClassName, presetName, knobValues) -> None
    Create a node preset for the given node using the supplied knob values
    @param nodeClassName: Name of the node class to create a preset for.
    @param presetName: Name of the preset to create.
    @param knobValues: A dictionary containing a set of knob names and preset values.
    @return: bool.
    """
    return None

def show(n=None, forceFloat:bool=None):
    """
    show(n, forceFloat) -> None

    Opens a window for each named node, as though the user double-clicked on them.  For normal operators this opens the
    control panel, for viewers it opens the viewer, for groups it opens the control panel.

    @param n: Optional node argument. Default is the current node.
    @param forceFloat: Optional python object. If it evaluates to True it will open the window as a floating panel. Default is False.
    @return: None
    """
    return None

def showBookmarkChooser(n):
    """
    showBookmarkChooser(n) -> None

    Show bookmark chooser search box.

    @return: None
    """
    return None

def showCreateViewsDialog(views:list):
    """
    showCreateViewsDialog(views) -> void

    Show a dialog to prompt the user to add or create missing views.

    @param views: List of views to be created.
    @return: An integer value representing the choice the user selected: nuke.ADD_VIEWS, nuke.REPLACE_VIEWS or nuke.DONT_CREATE_VIEWS
    """
    return Any

def showDag(n=None):
    """
    showDag(n) -> None

    Show the tree view of a group node or opens a node control panel.

    @param n: Optional Group.
    @return: None
    """
    return None

def showInfo(n=None):
    """
    showInfo(n) -> str

    Returns a long string of debugging information about each node and
    the operators it is currently managing. You should not rely on its
    contents or format being the same in different versions of Nuke.

    @param n: Optional node argument.
    @return: String.
    """
    return str()

def showSettings():
    """
    showSettings() -> None

    Show the settings of the current group.

    @return: None
    """
    return None

def splayNodes():
    """
    splayNodes() -> None

    Deprecated. Use Group.splaySelectedNodes.

    @return: None
    """
    return None

def startEventGraphTimers():
    """
    startEventGraphTimers() -> None

    Start keeping track of events in the event graph.
    """
    return None

def startPerformanceTimers():
    """
    startPerformanceTimers() -> None

    Start keeping track of accumulated time on the performance timers, and display the accumulated time in the DAG.
    """
    return None

def stopEventGraphTimers():
    """
    stopEventGraphTimers() -> None

    Stop keeping track of events in the event graph.
    """
    return None

def stopPerformanceTimers():
    """
    stopPerformanceTimers() -> None

    Stop keeping track of accumulated time on the performance timers, and cease displaying the accumulated time in the DAG.
    """
    return None

def stripFrameRange(clipname):
    """
    stripFrameRange(clipname) -> string

    Strip out the frame range from a clipname, leaving a file path (still possibly with variables).

    @param clipname: The clipname.
    @return: The name without the frame range.
    """
    return str()

def suspendPathProcessing():
    """
    suspendPathProcessing() -> None
    Suspend path processing.
    Use prior to performingmultiple node graph modifications, to avoid repeated path processing.
    @return: None.
    """
    return None

def tabClose(*args, **kwargs):
    """
    Close the active dock tab. Returns True if successful.
    """
    return None

def tabNext(*args, **kwargs):
    """
    Make the next tab in this dock active. Returns True if successful.
    """
    return None

def tcl(s:str, *args):
    """
    tcl(s, *args) -> str.

    Run a tcl command. The arguments must be strings and passed to the command. If no arguments are given and the command has whitespace in it then it is instead interpreted as a tcl program (this is deprecated).

    @param s: TCL code.
    @param args: The arguments to pass in to the TCL code.
    @return: Result of TCL command as string.
    """
    return str()

def thisClass():
    """
    thisClass() -> None

    Get the class name of the current node. This equivalent to calling nuke.thisNode().Class(), only faster.

    @return: The class name for the current node.
    """
    return None

def thisGroup():
    """
    thisGroup() -> Group

    Returns the current context Group node.

    @return: The group node.
    """
    return Group()

def thisKnob():
    """
    thisKnob() -> Knob

    Returns the current context knob if any.

    @return: Knob or None
    """
    return Knob()

def thisNode():
    """
    thisNode() -> Node.

    Return the current context node.

    @return: The node.
    """
    return Node()

def thisPane():
    """
    thisPane() -> the active pane.

    Returns the active pane. This is only valid during a pane menu callback or window layout restoration.

    @return: The active pane.
    """
    return Any

def thisParent():
    """
    thisParent() -> Node

    Returns the current context Node parent.

    @return: A node.
    """
    return Node()

def thisRoot():
    """
    thisRoot() -> Root

    Returns the current context Root node.

    @return: The root node.
    """
    return Root()

def thisView():
    """
    thisView() -> str
    Get the name of the current view.
    @return: The current view name as a string.
    """
    return str()

def toNode(s:str):
    """
    toNode(s) -> Node

    Search for a node in the DAG by name and return it as a Python object.

    @param s: Node name.
    @return: Node or None if it does not exist.
    """
    return Node()

def toggleFullscreen():
    """
    toggleFullscreen() -> None

    Toggles between windowed and fullscreen mode.

    @return: None
    """
    return None

def toggleViewers():
    """
    toggleViewers() -> None

    Toggles all the viewers on and off.

    @return: None
    """
    return None

def toolbar(name:str, create=True):
    """
    toolbar(name, create=True)-> ToolBar

    Find and return the ToolBar object with the given name. The name of the built-in nodes toolbar is 'Nodes'.

    A RuntimeException is thrown if not in GUI mode.

    @param name: The name of the toolbar to find or create.
    @param create: Optional parameter. True (the default value) will mean that a new  toolbar gets created if one with the given name couldn't be found; False will  mean that no new toolbar will be created.@return: The toolbar, or None if no toolbar was found and 'create' was False.
    """
    return ToolBar()

def tprint(value, sep=' ', end='\n', file=sys.stdout):
    """
    tprint(value, ..., sep=' ', end='\n', file=sys.stdout) -> None

    Prints the values to a stream, or to stdout by default.

    @param value: A python object
    @param file: a file-like object (stream); defaults to stdout.
    @param sep: string inserted between values, default a space.
    @param end: string appended after the last value, default a newline.
    @return: None
    """
    return None

def undo():
    """
    undo() -> None

    Perform the most recent undo.

    @return: None
    """
    return None

def usingOCIO():
    """
    usingOCIO() -> returns true if using OCIO instead of Nuke LUTs.
    @return: bool
    """
    return bool()

def usingPerformanceTimers():
    """
    usingPerformanceTimers() -> True if on, False if off

    Return true if performance timers are in use.
    """
    return bool()

def value(knob, default):
    """
    value(knob, default) -> string.

    The value function returns the current value of a knob. The knob argument is a string referring to a knob and default is an optional default value to be returned in case of an error. Unlike knob(), this will evaluate animation at the current frame, and expand brackets and dollar signs in string knobs.
    """
    return str()

def views():
    """
    views() -> List.

    List of all the globally existing views.

    @return: List
    """
    return list()

def waitForThreadsToFinish():
    """
    waitForThreadsToFinish() -> str
    Returns true if Nuke should wait for any Python threads to finish before exitting.
    @return: True or False.
    """
    return str()

def warning(message:str):
    """
    warning(message)-> None

    Puts the message into the error console, treating it like a warning.

    @param message: String parameter.
    @return: None.
    """
    return None

def zoom(scale, center:int=None, group=None):
    """
    zoom(scale, center, group) -> float

    Change the zoom and pan of a group's display. The scale argument is the new zoom factor.
    If the scale is given, but not the center, the zoom is set to that factor and the view is
    positioned so the cursor is pointing at the same place it was before zooming. A zero or negative
    scale value will cause a zoom-to-fit.

    If both scale and center arguments are given, the view is zoomed and then centered on the
    specified point.

    The new scale factor will be returned, or None if the function is run in a non-GUI context.

    @param scale: New zoom factor.
    @param center: Optional 2-item tuple specifying the center coordinates.
    @param group: Optional Group. This is ignored at present.
    @return: Current zoom factor or None if not in a GUI context.
    """
    return float()

def zoomToFitSelected():
    """
    zoomToFitSelected() -> None
    Does a zoom to fit on the selected nodes in the DAG
    @return: None.
    """
    return None