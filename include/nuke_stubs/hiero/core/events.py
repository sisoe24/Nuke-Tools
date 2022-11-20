# Event registration and dispatching
import queue
import traceback

__all__ = ['EventType', 'Event', 'Connection', 'registerInterest', 'unregisterInterest',
           'sendEvent', 'registerEventType', 'unregisterEventType']

# An enum of all registered event types
class EventType:
  kAny = '*'

# The class which is passed to event handlers
class Event:
  def __init__( self, type = None, subtype = None, **kwargs ):
    self.type = type
    self.subtype = subtype
    self.__dict__.update( kwargs )
    self._accepted = True

  def accept(self):
    self._accepted = True
    
  def ignore(self):
    self._accepted = False
    
  def isAccepted(self):
    return self._accepted
  
  def setAccepted(self, accepted):
    self._accepted = accepted

# Enum of connection types
class Connection:
  """ Execute callback always, no matter how the event is triggered. """
  kAny = 1
  """ Execute callback only if event is triggered through sendEvent (or signalEvent). Execution is synchronous (blocking) """
  kDirect = 2
  """ Execute callback only if event is triggered through postEvent (or signalEvent). Execution is asynchronous (add to event queue, non-blocking) """
  kQueued = 4

# Represents an event handler
class Callback:
  
  def __init__(self, method, connection = Connection.kAny, *args, **kwargs):
    self.method = method
    self.connection = connection
    self.args = args
    self.kwargs = kwargs
  
  def call(self, event):
    self.method.__call__(event, *self.args, **self.kwargs)
    

# Private APIs
_eventHandlers = dict()

def _callCallbacks(event, callbacks, connectionTypeFlags):
  for callback in callbacks:
    try:
      if callback.connection & connectionTypeFlags != 0:
        callback.call(event)
    except Exception as detail:
      print("ERROR: Error in event handler: ", detail)
      traceback.print_exc()

def _dispatchEvent( event, connectionTypeFlags ):
  type = event.type
  if type in _eventHandlers:
    handlers = _eventHandlers[type]
    subtype = event.subtype

    if subtype != None and subtype in handlers:
      _callCallbacks( event, handlers[subtype], connectionTypeFlags )

    if EventType.kAny in handlers:
      _callCallbacks( event, handlers[EventType.kAny], connectionTypeFlags )
  
def _splitType( type, methodName ):
  if isinstance(type, str):
    type = type.split('/')
  elif not isinstance(type, tuple):
    type = (type,)
  if len(type) == 1:
    type.append("*")
  if len(type) != 2 or len(type[0]) == 0 or len(type[0]) == 1:
    raise RuntimeError("%s event type '%s' must be of the form 'type/subtype'" % (methodName, type))
  return type

# Public APIs
def registerInterest( type, callback, connection = Connection.kAny, *args, **kwargs ):
  """Register interest in an event type. The callback will be called whenever an event of the given type is dispatched."""
  type = _splitType(type, "registerInterest")
  if type[0] not in _eventHandlers:
    _eventHandlers[type[0]] = dict()
  handlers = _eventHandlers[type[0]];
  if type[1] not in handlers:
    handlers[type[1]] = []
  handlers[type[1]].append( Callback(callback, connection, *args, **kwargs) )

def unregisterInterest( type, callback ):
  """Unregister interest in an event type. The callback will no longer be called whenever an event of the given type is dispatched."""
  type = _splitType(type, "unregisterInterest")
  if type[0] in _eventHandlers:
    handlers = _eventHandlers[type[0]]
    if type[1] in handlers:
      callbacks = handlers[type[1]]
      callbacks[:] = [x for x in callbacks if x.method != callback]

def _sendEvent( event ):
  """Send an event immediately. The caller will block until the event has been handled.
  This only calls listeners registered with connection = kDirect or connection = kAny."""
  _dispatchEvent( event, Connection.kDirect | Connection.kAny )

def sendEvent( type, subtype, **kwargs ):
  """Send an event immediately. The caller will block until the event has been handled.
  This only calls listeners registered with connection = kDirect or connection = kAny."""
  _sendEvent( Event( type, subtype, **kwargs ) )

def registerEventType( name ):
  """Register a new event type. The type should be a string (suitable as an attribute name) describing the event, e.g. 'kStartup'."""
  if hasattr( EventType, name ):
    raise RuntimeError("Event type '%s' already exists" % type)
  else:
    setattr( EventType, name, name )

def unregisterEventType( name ):
  """Unregister an event type."""
  delattr( EventType, name )

# Register built-in EventTypes

# Application EventTypes
registerEventType('kStartup')  # triggered when Hiero starts up
registerEventType('kShutdown')  # triggered when Hiero shuts down
registerEventType('kShutdownFinal')  # Not intended for external use.

# Context change EventTypes. They have a ‘focusInNuke’ property that is True when switching to the node graph.
registerEventType('kContextChanged')  # triggered after switching between the timeline, node graph and other views

# Project EventTypes. They have a project property containing the project that triggered the event.
registerEventType('kBeforeNewProjectCreated')  # triggered before a new Project is created
registerEventType('kAfterNewProjectCreated')  # triggered after a new Project is created
registerEventType('kBeforeProjectLoad')  # triggered before a Project starts loading
registerEventType('kAfterProjectLoad')  # triggered after a Project has finished loading
registerEventType('kBeforeProjectSave')  # triggered before a Project is saved
registerEventType('kAfterProjectSave')  # triggered after a Project has been saved
registerEventType('kBeforeProjectClose')  # triggered before a Project has closed
registerEventType('kAfterProjectClose')  # triggered after a Project has closed
registerEventType('kBeforeProjectGUIDChange')  # Not intended for external use.
registerEventType('kAfterProjectGUIDChange')  # Not intended for external use.

# Playback EventTypes
registerEventType('kCurrentViewerChanged')
registerEventType('kPlaybackStarted')  # triggered when a playback starts
registerEventType('kPlaybackStopped')  # triggered when a playback stops
registerEventType('kPlaybackClipChanged')  # Not intended for external use.

# Dialog EventTypes
registerEventType('kExportDialog')  # triggered when the Export Dialog is opened

# View EventTypes. They can be used in conjunction with the event subtypes below.
registerEventType('kShowContextMenu')  # triggered when a right-click context menu is shown in a view.
registerEventType('kSelectionChanged')  # triggered when a selection of items (e.g. Shots, Clips) in the view changes.
registerEventType('kDrop')  # triggered when something is dropped into the view
registerEventType('kDoubleClick')  # Not intended for external use.

# Event subtypes (for use in conjunction with View EventTypes)
registerEventType('kTimeline')
registerEventType('kViewer')
registerEventType('kBin')
registerEventType('kSpreadsheet')

# Private EventTypes
registerEventType('kAutoSaveTriggered')
registerEventType('kPlayheadAtStart')
registerEventType('kPlayheadAtEnd')

# Private Event subtypes
registerEventType('kPlayback')

# Callbacks when objects change.  Not intended for external use.
registerEventType('kSequenceFormatChanged')
registerEventType('kSequenceEdited')
registerEventType('kAnnotationChanged')
registerEventType('kVersionChanged')
registerEventType('kVersionLinkedChanged')
registerEventType('kInOutPointsChanged')
registerEventType('kInOutLockEnabledChanged')
registerEventType('kTrackEnabledChanged')
registerEventType('kEffectItemKnobChanged')

# Clip events.  Not intended for external use.
registerEventType('kClipAdded')

# Bin item events.  Not intended for external use.
registerEventType('kBinItemAdded')
registerEventType('kBinItemRemoved')
registerEventType('kBinItemRenamed')
registerEventType('kBinItemMoved')
