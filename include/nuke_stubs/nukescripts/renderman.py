import os
import subprocess
import shlex
# filter a RIB file

# The function should take the input RIB filename
# filter it and write the modified version to a file called out_RIB_file
#
# This function should return true if the RIB file is filtered or throw an exception if unmodified
#
# args specifies extra arguments field on the prmanRender RIB tab
#
# the default version tries to call catrib to filter the RIB


def filterRIB( in_RIB_file, out_RIB_file, argsStr ):

  catRibPath = os.environ['RMANTREE'] + '/bin/catrib'
  args = [ catRibPath ]
  args.extend( shlex.split(argsStr) )
  args.append( "-o" )
  args.append( out_RIB_file)
  args.append( in_RIB_file)

  process = subprocess.Popen( args, shell=False, stdout=subprocess.PIPE)
  output = process.communicate()

  if process.returncode != 0:
    raise Exception( "Error running RIB filter (" + str(process.returncode) + ")" )





