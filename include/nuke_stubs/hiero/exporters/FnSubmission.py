from hiero.core import TaskGroup


class Submission(TaskGroup):
  """
  The Submission class is used for sending jobs such as renders to
  external processes.

  Tasks which need to start a job call addJob(), and the Submission may
  optionally return a Task to report on the job's progress.
  """

  kNukeRender = "nuke"
  kCommandLine = "commandline"

  def __init__(self):
    TaskGroup.__init__(self)
    pass


  def initialise(self):
    """
    Called before any jobs are added, can be used to e.g. show a dialog
    to configure the Submission.
    """
    pass


  def addJob(self, jobType, initDict, filePath):
    """
    Add a job to the submission.  May return a Task object which should be processed
    by the caller.
    """
    pass

  def startTask(self):
    """
    This will be called when the export queue starts processing this submission,
    before any jobs are added.
    """
    pass

  def finishTask(self):
    """
    This will be called after jobs have been added.
    """
    pass

  def taskStep(self):
    return False

