#
# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.
#

# Run framecycler on a Read or Write node. See the flipbook command
# for how we run framecycler on *any* node.

import platform
import sys
import os.path
import re
import _thread
import nuke
import subprocess

def framecycler_stereo_available():
  """This function used to detect if we were running on Mac OS Tiger; we no longer support Tiger, so this function always returns true now."""
  return True

def run_app(app, in_args):
  args = [app]
  for a in in_args:
    args.append(a)
  try:
    p = subprocess.Popen(args=args, executable=app, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    return output
  except:
    return ""

def framecycler_linux_version():
  default_path = "CentOS5"
  output = run_app("/usr/bin/lsb_release",  ["-a"])
  if len(output) == 0:
    output = run_app("/usr/local/bin/lsb_release", ["-a"])
    if len(output) == 0:
      output = run_app("/bin/lsb_release", ["-a"])
      if len(output) == 0:
        return default_path
  try:
    if output.find('CentOS') >= 0:
      match = re.search('Release:\s*[\d.]+', output)
      if match != None:
        substring = match.group(0)
        versionMatch = re.search('[\d.]+', substring)
        versionString = versionMatch.group(0)
        if (float(versionString)) < 5.0:
          return "CentOS4.4"
  except:
    pass
  return default_path

fc_path=""
if fc_path == "":
  try:
    fc_path = os.environ["FC_PATH"]
  except:
    try:
      fc_path = os.path.join(os.environ["FC_HOME"], "bin", "framecycler")
    except:
      fc_path = os.path.join(os.path.dirname(nuke.EXE_PATH), "FrameCycler")
      fc_suffix = ""
      if nuke.env['WIN32']:
        fc_path = os.path.join(fc_path+"Windows", "bin", "framecycler")
      elif not nuke.env['WIN32'] and not nuke.env['MACOS']:
        fc_path = os.path.join(fc_path+framecycler_linux_version(), "bin", "framecycler")
      else:
        fc_path = os.path.join(fc_path + "OSX", "bin", "FrameCycler")
  if nuke.env['WIN32']:
      fc_path = fc_path + ".exe"


def framecycler_sequence(frange, filename, cmd_args_size):
  sequence = []
  for i in range(min(frange.frames(), cmd_args_size)):
    sequence.append( "Q[" )
    sequence.append( filename )
    sequence.append( "%d-%d" % (frange.getFrame(i), frange.getFrame(i)) )
    sequence.append( "]Q" )
  return sequence

def framecycler_this(node, start, end, incr, view):
  """Run framecycler on a Read or Write node. See the flipbook command
  for how we run framecycler on *any* node."""

  global fc_path

  if not os.access(fc_path, os.X_OK):
    raise RuntimeError("Framecycler cannot be executed (%s)." % (fc_path,) )

  filename = nuke.filename(node)
  if filename is None or filename == "":
    raise RuntimeError("Framecycler cannot be executed on '%s', expected to find a filename and there was none." % (node.fullName(),) )

  sequence_interval = str(start)+"-"+str(end)
  (filename, subs) = re.subn("(%[0-9]+)d", "#", filename)

  # if the step beetwen frames is bigger then one
  # we have to build the framecycler syntax in a special way
  # the idea is to add multiple queue sequence of 1 frame

  if subs == 0 or incr > 1:
    sequence_interval = ""

  (filename, subs) = re.subn("%V", view[0], filename)
  (filename, subs) = re.subn("%v", view[0][0], filename)

  os.path.normpath(filename)

  w = nuke.value(node.name()+".actual_format.width")
  h = nuke.value(node.name()+".actual_format.height")
  cropa = nuke.value(node.name()+".actual_format.x")
  cropb = nuke.value(node.name()+".actual_format.y")
  cropc = str(nuke.expression(node.name()+".actual_format.r"+"-"+cropa))
  cropd = str(nuke.expression(node.name()+".actual_format.t"+"-"+cropb))
  pa = nuke.value(node.name()+".actual_format.pixel_aspect")

  args = []
  fc_path = os.path.normpath(fc_path)
  if nuke.env['WIN32']:
    args.append( "\"" + fc_path + "\"" )
    filename = filename.replace("/", "\\")
    filename = "\"" + filename + "\""
  else:
    args.append( fc_path )

  if incr == 1:
    args.append(filename)
    args.append(sequence_interval)

  if cropa is not None or cropb is not None or cropc != w or cropd != h:
    args.append("-c")
    args.append(cropa)
    args.append(cropb)
    args.append(cropc)
    args.append(cropd)

  resample = ""
  if float(pa)>1:
    args.append("-r")
    args.append("100%")
    args.append(str(int(100/float(pa)))+"%")
  elif float(pa)<1:
    args.append("-r")
    args.append(str(int(100/float(pa)))+"%")
    args.append("100%")

  if len(view) > 1:
    args.append("-stereo")

  if incr > 1:
    # I didn't find any python call that return the maximum argument size for command line.
    # I hope that 1000 is enough.
    maximun_cmd_args_size = 1000

    frange =  nuke.FrameRange(start, end, incr)
    sequence = framecycler_sequence( frange, filename, maximun_cmd_args_size )
    args += sequence

  nuke.IrToken()
  os.spawnv(os.P_NOWAITO, fc_path, args)

