# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import nuke

isHiero = nuke.env['hiero']
if isHiero:
  from .panels import *
  from .nodepresets import *

  # Callbacks for localisation preferences
  from . import localisationprefs
else:

  from .all_plugins import *
  from .animation import *
  from .autobackdrop import *
  from .cache import *
  from .camera import *
  from .create import *
  from .crop import *
  from .drop import *
  from .edit import *
  from .execute import *
  from .flags import *
  from .flip import *
  from .flipbooking import *
  from .frame import *
  from .group import *
  from .importexport import *
  from .info import *
  from .misc import *
  from .nodes import *
  from .nukeprofiler import *
  from .openurl import *
  # from .panel_test import *
  from .plugin_menu import *
  from .precomp import *
  from .reads import *
  from .renderpanel import *
  from .script import *
  from .scripteditorknob import *
  from .searchreplace import *
  from .select import *
  from .snap3d import *
  from .udim import *
  from .utils import *
  from .version import *
  if nuke.GUI:
    from .panels import *
    from .toolbars import *
    from .toolsets import *
    from .nodepresets import *
    from .trackerlinkingdialog import *

    from .renderdialog import *
    from .framerangepanel import *

    from . import readviewscheck

    # Callback for viewsettings preferences
    from . import viewsettingsprefs

    # Callbacks for localisation preferences
    from . import localisationprefs

  # Leave these in their module namespace rather than pulling into
  # top level of nukescripts.
  from . import stereo
  from . import psd
  from . import bookmarks

