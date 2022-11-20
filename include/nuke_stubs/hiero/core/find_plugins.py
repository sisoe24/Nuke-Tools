# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

# At startup, search the plugin path for folders named "python" and load all Python modules and packages found in them.
# Plugins may do anything they like, but typically, they will install a menu command or button to perform an action.
# In this case, it's best to make the plugin a package, and install the command in the __init__.py, keeping the actual
# command in another module loaded by the command. This speeds up startup by allowing complicated command scripts to
# only be parsed when they're first invoked, rather than at startup.

import sys
import os
import re
import types
import imp
import hiero
import hiero.core
from hiero.core.log import (info, exception)

verbosePlugins = True

# We create a new module to hold all Hiero plugins. This helps to avoid namespace pollution.
hiero.plugins = types.ModuleType('plugins')

# Iterate through the given folder and load all modules and packages found in it. Also add the folder to sys.path.
def loadPluginsFromFolder( path ):
  if verbosePlugins:
    info( "  Looking for plugins in " + path )
  if os.path.isdir( path ):
    sys.path.append( path )

    # Don't load files starting with "."
    test = re.compile( ".*\.py$", re.IGNORECASE )
    files = os.listdir( path )
    files.sort()
    for f in files:
      p = os.path.join( path, f )
      if not f.startswith("."):
        if test.search( f ):
          moduleName = os.path.splitext( f )[0]
          if verbosePlugins:
            info( "    - Loading module " + moduleName )
          try:
            module = imp.load_source( moduleName, p )
            setattr( hiero.plugins, moduleName, module );
          except Exception as detail:
            exception( "Plugin %s could not be loaded: %s" % (p, str(detail)))
        elif os.path.isdir( p ):
          p = os.path.join( p, "__init__.py" )
          if os.path.exists( p ):
            packageName = os.path.splitext( f )[0]
            if verbosePlugins:
              info( "    - Loading package " + p )
            try:
              module = __import__( packageName )
              setattr( hiero.plugins, packageName, module );
            except Exception as detail:
              exception( "Plugin %s could not be loaded: %s" % (p, str(detail)))

def loadPluginsFromPluginPath(suffix):
  paths = hiero.core.pluginPath()
  for path in paths:
    loadPluginsFromFolder( os.path.join( path, "Python", suffix ) )

  # One of these plugins may have added to the search path. Search any newly-added paths
  new_paths = [x for x in hiero.core.pluginPath() if x not in paths]
  if len(new_paths) != 0:
    print("Plugin added new paths!", new_paths)
    for path in new_paths:
      loadPluginsFromFolder( os.path.join( path, "Python", suffix ) )

def launchedInSafeMode():
  """Returns whether Hiero was launched in Safe mode (--safe) on the command line"""
  safe = ("--safe" in hiero.core.rawArgs)
  return safe

# Load all Hiero plugins at startup
def findPlugins():
  # We do not load Startup/StartupUI plugins if the user specifies the --safe flag on the command line.
  if not launchedInSafeMode():
    if verbosePlugins:
      info( "Searching for Python plugins:" )

    loadPluginsFromPluginPath( "Startup" )

    if hiero.core.GUI:
      loadPluginsFromPluginPath( "StartupUI" )

# Load all custom Exporters, isolated because not loaded in Hiero Player
def findExporters():
  # We do not load custom Exporters if the user specifies the --safe flag on the command line.
  if not launchedInSafeMode():
    paths = hiero.core.pluginPath()
    for path in paths:
      loadPluginsFromFolder( os.path.join( path, "Python", "Exporters" ) )    
    
# A debugging function to print out details of the loaded plugins
def listPlugins():
  for i,j in hiero.plugins.__dict__.items():
    if isinstance( j, types.ModuleType ):
      if hasattr( j, "version" ):
        info( "Plugin: %s %s %s" % (str(i), str(j), str(j.version) ) )
      else:
        info( "Unversioned Plugin: %s %s " % (str(i), str(j)) )

# Load all Hiero export presets
def findExportPresets():
  # In the case of hiero player taskRegistry will not exist.
  if hasattr(hiero.core, "taskRegistry"):
    # We do not load custom Export Presets if the user specifies the --safe flag on the command line.
    if not launchedInSafeMode():
      subdir = hiero.core.taskRegistry.presetsSubDirectory()
      for path in hiero.core.pluginPath():
        path = os.path.join(path, subdir)
        hiero.core.taskRegistry.loadPresets(path)
        
    hiero.core.taskRegistry.addDefaultPresets(overwrite=False)
