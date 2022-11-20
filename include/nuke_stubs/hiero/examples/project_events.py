# Shows how to use hiero.core.events to register callbacks for startup, shutdown and various project event types.
# See help on hiero.core.events.registerInterest and hiero.core.events.unregisterInterest for more details

import hiero.core.events

def startupCompleted(event):
  print('kStartup happened')

def shutDown(event):
  print('kShutDown happened')

def beforeNewProjectCreated(event):
  print('kBeforeNewProjectCreated happened : Project was:' + str(event.project))

def afterNewProjectCreated(event):
  print('kAfterNewProjectCreated happened : Project was:' + str(event.project))

def beforeProjectLoad(event):
  print('kBeforeProjectLoad happened : Sender was:' + str(event.sender))

def afterProjectLoad(event):
  print('kAfterProjectLoad happened : Project was:' + str(event.project))

def beforeProjectClosed(event):
  print('kBeforeProjectClose happened : Project was:' + str(event.project))

def afterProjectClosed(event):
  print('kAfterProjectClose happened : Project was:' + str(event.sender))  

def beforeProjectSaved(event):
  print('kBeforeProjectSave happened : Project was:' + str(event.project))

def afterProjectSaved(event):
  print('kAfterProjectSave happened : Project was:' + str(event.project))  

print('Registering events for: kBeforeNewProjectCreated, kAfterNewProjectCreated, kBeforeProjectLoad, kAfterProjectLoad, kBeforeProjectSave, kAfterProjectSave, kBeforeProjectClose, kAfterProjectClose, kShutdown, kStartup')

hiero.core.events.registerInterest('kBeforeNewProjectCreated',beforeNewProjectCreated)
hiero.core.events.registerInterest('kAfterNewProjectCreated',afterNewProjectCreated)

hiero.core.events.registerInterest('kBeforeProjectLoad',beforeProjectLoad)
hiero.core.events.registerInterest('kAfterProjectLoad',afterProjectLoad)

hiero.core.events.registerInterest('kBeforeProjectSave',beforeProjectSaved)
hiero.core.events.registerInterest('kAfterProjectSave',afterProjectSaved)

hiero.core.events.registerInterest('kBeforeProjectClose',beforeProjectClosed)
hiero.core.events.registerInterest('kAfterProjectClose',afterProjectClosed)

hiero.core.events.registerInterest('kShutdown',shutDown)
hiero.core.events.registerInterest('kStartup',startupCompleted)