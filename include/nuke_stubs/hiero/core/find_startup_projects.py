# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

# At startup, search the plugin path for folders named "StartupProjects" and load all *.hrox projects found there.
# This should be the way for users to include their own preset projects into Hiero. 

import hiero.core
import sys
import os
import re

verboseStartupProjects = True

def loadProjectsFromFolder(path):
  if verboseStartupProjects:
    hiero.core.log.info( "Looking for startup projects in: " + path )
  if os.path.isdir(path):
    # Don't load files starting with "."
    regex = re.compile(".*\.hrox$", re.IGNORECASE)
    files = os.listdir(path)
    for file in files:
      if not file.startswith(".") and regex.search(file):
        projectPath = os.path.join(path, file)
        try:
          if verboseStartupProjects:
            hiero.core.log.info( " - Opening startup project: " + projectPath )
          hiero.core.openProject(projectPath, hiero.core.Project.kProjectOpenStartup) # Load as startup project
        except Exception as detail:
          hiero.core.log.exception( "Project", projectPath, "could not be loaded:", detail )


# Load all Startup Projects
def findStartupProjects():
  if verboseStartupProjects:
    hiero.core.log.info( "Searching for startup projects:" )
  paths = hiero.core.pluginPath()
  startupDir = hiero.core.env["ProductName"]

  # For NukeStudio, for the time being we want to load Hiero startup projects
  if startupDir == "NukeStudio":
    startupDir = "Hiero"

  for path in paths:
    loadProjectsFromFolder(os.path.join(path, "StartupProjects", startupDir))
