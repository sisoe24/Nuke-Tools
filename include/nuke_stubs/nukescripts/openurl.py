# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke


def start(url):
  '''Open a URL or file.'''
  nuke.tcl('start', url)


#proc start {url} {
#  if [catch {set command [getenv BROWSER]}] {
#    global WIN32
#    global MACOS
#    if $WIN32 {
#      set command "rundll32.exe url.dll,FileProtocolHandler"
#    } elseif $MACOS {
#      set command "/usr/bin/open"
#    } else {
#      global browser
#      if [catch {set browser}] {set browser "firefox"}
#      if [catch {set browser [get_input "\$BROWSER is not set.\nPlease type the name of your browser here.\nSome examples: firefox, konqueror, netscape, mozilla, opera" $browser]}] return
#      set command $browser
#    }
#    setenv BROWSER $command
#  }
#  if [catch {eval [concat exec $command [list $url] &]} msg] {
#    unsetenv BROWSER
#    message "$msg\nSet the environment variable \$BROWSER to fix this"
#  }
#}

