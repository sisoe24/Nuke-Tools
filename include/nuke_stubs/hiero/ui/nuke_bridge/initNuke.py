from hiero.ui import findMenuAction, findRegisteredAction
import hiero.ui.nuke_bridge.initFrameServer
import nuke_internal as nuke
import nuke_internal.localization
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction

forceUpdateSelected = findRegisteredAction("foundry.project.localcacheforceupdateselectedNuke")
forceUpdateSelected.triggered.connect(nuke_internal.localization.forceUpdateSelectedNodes)

localisation = findRegisteredAction("foundry.menu.localizationNuke")
if nuke.env['studio']:
  timelineAction = findMenuAction("foundry.menu.cache")
  timelineAction.menu().removeAction(localisation)
nukeMenuBar = nuke.menu('Nuke')
cacheMenu = nukeMenuBar.menu('Cache')
cacheMenu.addAction(localisation)



