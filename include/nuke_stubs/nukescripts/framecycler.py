# Copyright (c) 2010 The Foundry Visionmongers Ltd.  All Rights Reserved.
import platform
import sys
import os.path
import re
import _thread
import nuke
import subprocess
import nukescripts
from . import flipbooking

# An example implementation for a flipbook application using framecycler.
class FramecyclerFlipbook(flipbooking.FlipbookApplication):
  # Discover the location of FC on construction
  def __init__(self):
    self._fcPath = ""
    try:
      self._fcPath = os.environ["FC_PATH"]
    except:
      try:
        self._fcPath = os.path.join(os.environ["FC_HOME"], "bin", "framecycler")
      except:
        self._fcPath = os.path.join(os.path.dirname(nuke.EXE_PATH), "FrameCycler")
        if nuke.env['WIN32']:
          self._fcPath = os.path.join(self._fcPath+"Windows", "bin", "framecycler")
        elif not nuke.env['WIN32'] and not nuke.env['MACOS']:
          self._fcPath = os.path.join(self._fcPath+self.linux_version(), "bin", "framecycler")
        else:
          self._fcPath = os.path.join(self._fcPath + "OSX", "bin", "FrameCycler")
    if nuke.env['WIN32']:
        self._fcPath = self._fcPath + ".exe"
    self._fcPath = os.path.normpath(self._fcPath)

  ##############################################################
  # Interface implementation
  ##############################################################
  def name(self):
    return "FrameCycler"

  def path(self):
    return self._fcPath

  def cacheDir(self):
    return os.environ["FC_DISK_CACHE"]

  def run(self, filename, frameRanges, views, options):
    (filename, subs) = re.subn("(%[0-9]*)d", "#", filename)
    (filename, subs) = re.subn("%V", views[0], filename)
    (filename, subs) = re.subn("%v", views[0][0], filename)

    os.path.normpath(filename)

    args = []
    if nuke.env['WIN32']:
      args.append( "\"" + self.path() + "\"" )
      filename = filename.replace("/", "\\")
      filename = "\"" + filename + "\""
    else:
      args.append( self.path() )

    lut = options.get("lut", "")
    if lut != "":
      lutPath = flipbooking.getLUTPath(self.name(), lut)
      if lutPath != "" and os.path.exists(lutPath):
        args.append("-calibration")
        args.append("\"" + lutPath + "\"")

    roi = options.get("roi", None)
    if roi != None and not (roi["x"] == 0.0 and roi["y"] == 0.0 and roi["w"] == 0.0 and roi["h"] == 0.0):
      args.append("-c"+str(max(0, int(roi["x"]))))
      args.append(str(max(0, int(roi["y"]))))
      args.append(str(int(roi["w"])))
      args.append(str(int(roi["h"])))

    scaleW = 100
    scaleH = 100

    pixelAspect = options.get("pixelAspect", 1)
    if pixelAspect != 1:
      scaleW *= pixelAspect

    if scaleW != 100 or scaleH != 100:
      args.append("-r"+str(scaleW)+"%")
      args.append(str(scaleH) + "%")

    if len(views) > 1:
      args.append("-stereo")

    # I didn't find any python call that return the maximum argument size for command line.
    # I hope that 1000 is enough.
    maximun_cmd_args_size = 1000

    # audio to be added this may be empty or not
    self._audio = ""
    audio = options.get("audio", "")
    if audio != "":
      self._audio = "\"-s" + audio + "\""

    for frameRange in frameRanges:
      args += self.sequence( frameRange, filename, maximun_cmd_args_size )


    nuke.IrToken()
    os.spawnv(os.P_NOWAITO, self.path(), args)

  def capabilities(self):
    return {
      'proxyScale': False,
      'crop': True,
      'canPreLaunch': False,
      'supportsArbitraryChannels': False,
      'maximumViews' : 2,
      'fileTypes' : ["exr", "mov", "tif", "tiff", "tga", "cin", "avi", "raw", "bmp", "gif", "jpg", "jpeg", "yuv", "pic", "rla", "dpx", "r3d", "png", "sgi", "rgb"]
    }

  ##############################################################
  # FrameCycler specific functions
  ##############################################################

  def run_app(self, app, in_args):
    args = [app]
    for a in in_args:
      args.append(a)
    try:
      p = subprocess.Popen(args=args, executable=app, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      output, errors = p.communicate()
      return output
    except:
      return ""

  def linux_version(self):
    default_path = "CentOS5"
    output = self.run_app("/usr/bin/lsb_release",  ["-a"])
    if len(output) == 0:
      output = self.run_app("/usr/local/bin/lsb_release", ["-a"])
      if len(output) == 0:
        output = self.run_app("/bin/lsb_release", ["-a"])
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

  def _sequenceStr(self, fname, start, end):
    return ["Q[", fname, "%d-%d" % (start, end), self._audio, "]Q"]

  def sequence(self, frange, filename, cmd_args_size):
    sequence = []
    if frange.increment() == 1:
      sequence += self._sequenceStr(filename, frange.first(), frange.last())
    else:
      for i in range(min(frange.frames(), cmd_args_size)):
        sequence += self._sequenceStr(filename,
            frange.getFrame(i), frange.getFrame(i))
    return sequence


# Example call to register a flipbook app.
fc = FramecyclerFlipbook()
flipbooking.register(fc)

# Get the fc install folder so we can register the Nuke specific LUTS, just need
# to remove the last two components from the path.
fcBinPath = os.path.split(fc.path())[0]
fcBasePath = os.path.split(fcBinPath)[0]
flipbooking.registerLUTPath('FrameCycler', 'linear-sRGB', os.path.join(fcBasePath, 'LUTs', 'NukeLinearTosRGB.ilut'))
flipbooking.registerLUTPath('FrameCycler', 'linear-rec709', os.path.join(fcBasePath, 'LUTs', 'NukeLinearToRec709.ilut'))
flipbooking.registerLUTPath('FrameCycler', 'Cineon-sRGB', os.path.join(fcBasePath, 'LUTs', 'NukeCineonTosRGB.cube'))
