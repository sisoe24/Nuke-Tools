from _fnpython import *
import builtins
import pydoc
import sys

class FnPySingleton(object):
  def __new__(type, *args, **kwargs):
    if not '_the_instance' in type.__dict__:
      type._the_instance = object.__new__(type)
    return type._the_instance

class SERedirector(object):
  def __init__(self, stream):
    fileMethods = ('fileno', 'flush', 'isatty', 'read', 'readline', 'readlines',
                   'seek', 'tell', 'write', 'writelines', 'xreadlines', '__iter__')

    for i in fileMethods:
      if not hasattr(self, i) and hasattr(stream, i):
        setattr(self, i, getattr(stream, i))

    self.savedStream = stream

  def close(self):
    self.flush()

  def stream(self):
    return self.savedStream

class SESysStdIn(SERedirector, FnPySingleton):
  def readline(self):
    return ""

class SESysStdOut(SERedirector, FnPySingleton):
  def write(self, out):
    outputRedirector(out)

class SESysStdErr(SERedirector, FnPySingleton):
  def write(self, out):
    stderrRedirector(out)


def nonInteractiveHelp(object=None):
  """
  Non-interactive version of the built-in help function. This prevents the Nuke UI from freezing when Nuke is launched
  from an interactive terminal and help is used in the Script Editor.
  :param object: Show help for this object.
  """
  # Print the help text without using formatting, which is not compatible with the Script Editor.
  print(pydoc.render_doc(object, renderer=pydoc.plaintext))


sys.stdin  = SESysStdIn(sys.stdin)
sys.stdout = SESysStdOut(sys.stdout)
sys.stderr = SESysStdErr(sys.stderr)
builtins.help = nonInteractiveHelp
