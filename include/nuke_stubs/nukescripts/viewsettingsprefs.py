import nuke

def onCreateRoot():

  preferencesNode = nuke.toNode('preferences')

  # This should only be done if the Root being created is the global root used
  # in the DAG, *not* Root nodes created by Studio
  root = nuke.thisRoot()
  if root != nuke.root():
    return

  isNewComp = not root['name'].getValue()

  # Do not override the view-related knobs from the Preferences
  # if they've been set from a user-defined template.nk
  isNotFromUserTemplate = not root['set_by_user_template'].getValue()
  if isNewComp and isNotFromUserTemplate:
    for knob in ("views", "hero_view", "views_colours"):
      # Check knobDefaults to see if the value has been set. If it has been set, then preferences should not override it.
      if(nuke.knobDefault("Root."+knob) is None):
        root.knob(knob).fromScript(preferencesNode.knob(knob).toScript())


nuke.addOnCreate(onCreateRoot, nodeClass='Root')
