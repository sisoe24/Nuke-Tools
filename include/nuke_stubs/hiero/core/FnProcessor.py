import core
from . import util
from .FnFloatRange import IntRange
from .FnExporterBase import TaskPresetBase


def _expandTaskGroup( group ):
  """ Helper function to flatten a hierarchy of task groups into a list containing child tasks. """
  tasks = []
  if not group.children():
    tasks.append(group)
  else:
    for child in group.children():
      tasks.extend(_expandTaskGroup(child))
  return tasks


class ProcessorBase(object):
  """ProcessorBase is the base class from which all Processors should derive.
  The Processor object is responible for taking the object selection and spawning
  Tasks with the appropriate parameters.
  """
  def __init__(self, preset, submission, synchronous=False):
    self._submission = submission
    self._synchronous = synchronous
    self._skipOffline = preset.skipOffline()


  def startProcessing(self, exportItems, preview=False):
    """ Generate export tasks and add them to the export queue. If preview is
    True, the tasks are created and returned, but not scheduled for execution.
    """
    raise NotImplementedError()

    
  def skipOffline(self):
    return self._skipOffline


  def processTaskPreQueue(self):
    """processTaskPreQueue() Walk Tasks in submission and mark any duplicates.
    """
  
    # Just some dummy structures for working on this code without the context of the exporters
    """
    from hiero.core import *
    class TaskDummy:
      def __init__ (self, first_frame, last_frame):
        self._first = first_frame
        self._last = last_frame
        self._dupe = False
      def __repr__(self):
        return "(%i - %i | %i | %s)" % (self._first, self._last, self._last  -self._first, self._dupe )
      def setDuplicate(self):
        self._dupe = True
      def outputRange(self):
        return self._first, self._last
      def resolvedExportPath(self):
        return "dummy"
      
    dummytasks = [TaskDummy(4,7), TaskDummy(8,10), TaskDummy(15, 20), TaskDummy(0,9)]
    """

    pathSet = {}
    for task in _expandTaskGroup(self._submission):
      if hasattr (task,"resolvedExportPath"):
        path = task.resolvedExportPath()
        if path not in pathSet:
          pathSet[path] = []
        pathSet[path].append(task)
        
    for path, tasks in pathSet.items():
    
      if util.HasFrameIdentifier(path):
        # Frame files will only overwrite eachother if they have the same frame index
        def int_range( range ):
          return IntRange( range[0], range[1] )
        # Build list of range/task tuples
        task_ranges = [ (int_range(task.outputRange()), task) for task in tasks ]
        
        # Walk list of tasks
        for range_a, task_a in task_ranges:
          # Compare with every other task
          for range_b, task_b in task_ranges:
            if task_a is not task_b:
              # The IntRange object overrides the contains interface
              # if range_b is within range_a return true
              if range_b in range_a:
                # And mark task_b as a duplicate
                task_b.setDuplicate()
      
      ## This builds supersets of overlapping output ranges.
      ## May come in useful later
      #task_ranges = [ (int_range(task.outputRange()), [task]) for task in tasks ]
      #def join ( task_ranges ):
      #  for range_a, tasklist_a in task_ranges:
      #    for range_b, tasklist_b in task_ranges:
      #    
      #      if range_a is not range_b:
      #        intersectsStart = range_a.min() <= range_b.min() and range_a.max() > range_b.min()
      #        intersectsEnd = range_a.min() <= range_b.max() and range_a.max() >= range_b.max()
      #                  
      #        if intersectsStart or intersectsEnd or range_b in range_a:
      #          tasklist_a.extend(tasklist_b)
      #          range_a.setMin(min(range_a.min(), range_b.min()))
      #          range_a.setMax(max(range_a.max(), range_b.max()))
      #          task_ranges.remove( (range_b, tasklist_b) )
      #          return True
      #  return False

      #while join(task_ranges):
      #  pass




  def validItem(self, supportedTypes, item):  
    """Get if the task is able to run on the item it was initialised with."""
    supported = False
    if supportedTypes & TaskPresetBase.kSequence:
      supported |= item.sequence() != None
    if supportedTypes & TaskPresetBase.kTrackItem:
      supported |= item.trackItem() != None
    if supportedTypes & TaskPresetBase.kClip:
      supported |= item.clip() != None
    return supported

  def _tagCopiedSequence( self, sequence, sequenceCopy ):
    self._addCopyTag(sequenceCopy, sequence)
    for track, trackCopy in zip(sequence.videoTracks() + sequence.audioTracks(), sequenceCopy.videoTracks() + sequenceCopy.audioTracks()):
      # Unlock copied track so that tags may be added
      trackCopy.setLocked(False)
      self._addCopyTag(trackCopy, track)
      # walk the track items in the track and add copy Tags
      for trackItem, trackItemCopy in zip(list(track.items()), list(trackCopy.items())):
        self._addCopyTag(trackItemCopy, trackItem)

  def _addCopyTag (self, copy, original ):
    tag = core.Tag("Copy")
    tag.metadata().setValue("tag.guid", original.guid())
    
    # If the parent object is a trackitem, add the event id
    # as this may change in the copy if the parent sequence is cropped.
    if hasattr(original, 'eventNumber'):
      tag.metadata().setValue("tag.event", str(original.eventNumber()))
      
    copy.addTag(tag)


  def errors(self):
    """ Get an error string from the processor.  Iterates over child tasks and
        adds their error messages to the string.  Returns None if there were no errors. """
    errors = []
    for task in _expandTaskGroup(self._submission):
      taskError = task.error()
      if taskError:
        errors.extend( (task.ident(), taskError) )

    if errors:
      return "\n".join(errors)
    else:
      return None
    

class ProcessorPreset (TaskPresetBase):
  """ProcessorPreset is the base class from which all Processor Presets must derrive
  The purpose of a Processor Preset is to store and data which must be serialized to file
  and shared between the Processor and ProcessorUI user interface component"""
  def __init__ (self, parentType, presetName):
    """Initialise Exporter Preset Base Class
    @param parentType : Processor type to which this preset object corresponds
    @param presetName : Name of preset"""
    TaskPresetBase.__init__(self, parentType, presetName)


  def __eq__(self, other):
    """ Override to compare projects.  The TaskRegistry relies on presets which are otherwise identical but with different projects not comparing equal. """
    if not isinstance(other, ProcessorPreset):
      return False

    if self.project() != other.project():
      return False

    return super(ProcessorPreset, self).__eq__(other)
