# find_items - convenience methods for returning objects in a Hiero Project
# Copyright (c) 2012 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero
import itertools

def typeName(type):
    typeItems = type.split('.')
    if len(typeItems) > 1:
      return typeItems[-1]
      
    return type

def convertToType(type):
  
  import hiero.core
  allowedFilters = [hiero.core.Bin,
                    hiero.core.BinItem,
                    hiero.core.Clip,
                    hiero.core.Sequence,
                    hiero.core.VideoTrack,
                    hiero.core.AudioTrack,
                    hiero.core.TrackItem,
                    hiero.core.Tag,
                    hiero.core.EffectTrackItem,
                    ]

  # none means all; it's valid
  if not type:
    return type
    
  if isinstance(type, str):
    # make it lower case
    type = type.lower()

    # check for all, just in case
    if type == "all":
      return None
      
    # allow plural for strings (so the user can pass in "tracks")
    if type.endswith('s'):
      type = type[:-1]
      
    # special case the track type, because we don't have a hiero.core.Track object
    if type == "track":
      return hiero.core.TrackBase

    # check if it matches anything in our list
    for filter in allowedFilters:
      filterName = filter.__name__.lower()
        
      # check if the name is a direct match
      if filterName == type:
        return filter
          
      # remove any modules in the name strings
      if typeName(filterName) == typeName(type):
        return filter

  else:
    if type in allowedFilters:
      return type
        
  allowedStrings = [typeName(filter.__name__) for filter in allowedFilters]
  raise Exception("The item filter must be set to a valid hiero.core object, e.g. hiero.core.Clip")
        

def findItemsInProject(proj=None, filter=None, partialName=None, verbose=0):
    '''findItemsInProject -> Returns all items in a Project's clipsBin. 
    User can filter by a specific type(s) or by partial name, and optionally print a verbose log to the output window.
    Takes up to 4 keyword arguments : Project object, a string, a type or an array of strings for filter type, partial name of item, and a bool to enable/disable verbose mode
    Returns an array of items. Note: to find Tags in a Project, use the findProjectTags method.
    
    @param proj: hiero.core.Project object, to find the items on. If None, then the last project in the currently loaded projects will be used.
    @param filter: optional. Used to filter the returned list. Can be None, a case insensitive single string or type, or a list of case insensitive strings and types.
    @param partialName: optional string. If specified, objects will only be returned if their name contains this string.
    @param verbose: optional value. If not None/False/0, findItems will print out information as it searches.
    @return: list of objects.
    
    Example uses:

    allItems = findItemsInProject(myProj)
    allSeqsAndTracksWith30SecInName = findItemsInProject(myProj, ['sequences', 'Tracks'], '30Sec', 1)
    allTracks = findItemsInProject(myProj, "Track")
    videoTracks = findItemsInProject(myProj, "VideoTrack")
    sequences = findItemsInProject(myProj, "Sequence") # Can also use plural: 'Sequences'
    sequences = findItemsInProject(myProj, hiero.core.Sequence)
    sequencesAndClips = findItemsInProject(myProj, [hiero.core.Sequence, hiero.core.Clip])
    binsOnly = findItemsInProject(myProj, hiero.core.Bin)
    
    hiero.core.findItems is deprecated. Please use hiero.core.findItemsInProject instead.
    
    '''
    #Solve 'tuple index out of range' error when adding script to startup dir
    if proj == None:
        proj = hiero.core.projects()[-1]
        
    #Check for a valid project now
    if type(proj) != hiero.core.Project:
        raise Exception("findItems requires a valid valid project object search for items.")

    #If it's only one filter or none, make it into a list anyways
    if isinstance(filter, str) or filter == None:
        filter = [filter]

    #Convert the list from strings to types
    filterList = []
    
    try:
      # Try to iterate over it, as if it's a list
      for f in filter:
        filterList.append(convertToType(f))
    except TypeError:
      # We get a type error when it's not iterable, so we assume it's a single item
      filterList.append(convertToType(filter))

    binLevel = 0
    allBins = []
    allBinItems = []
    allClips = []
    allSequences = []
    allVideoTracks = []
    allAudioTracks = []
    allAudioTrackItems = []
    allVideoTrackItems = []
    allEffectTrackItems = []
        
    # recursive function
    def parseBin(bin, binLevel) :
      binLevel += 1
      for each in list(bin.items()):

        if type(each) == hiero.core.Bin :
          # Is bin
          if verbose :
            print("  " * binLevel, "Bin :", each.name())
          allBins.append(each)
          parseBin(each, binLevel)
      
        else :
          seq = None
          clip = None
                  
          if isinstance(each, hiero.core.Version) :
            if isinstance(each.item(), hiero.core.Sequence) :
              seq = each.item()
            elif isinstance(each.item(), hiero.core.Clip) :
              clip = each.item()
        
          elif isinstance(each, hiero.core.BinItem):
            allBinItems.append(each)
            if isinstance(each.activeItem(), hiero.core.Sequence) :
              seq = each.activeItem()
            elif isinstance(each.activeItem(), hiero.core.Clip):
              clip = each.activeItem()

          if seq :
            if verbose :
              print("  " * binLevel, "Sequence :", seq.name())

            binLevel += 1
            for track in list(seq.items()):
              if isinstance(track, hiero.core.VideoTrack):
                if verbose :
                  print("  " * binLevel, "VideoTrack :", track.name())
                allVideoTracks.append(track)
                
                binLevel += 1
                for trackItem in list(track.items()) :
                  if verbose :
                    print("  " * binLevel, "Track Item :", trackItem.name())
                  allVideoTrackItems.append(trackItem)

                # Find effect items on the track
                effectItems = [i for i in itertools.chain(*track.subTrackItems()) if isinstance(i, hiero.core.EffectTrackItem)]
                allEffectTrackItems.extend(effectItems)

                binLevel -= 1
              if isinstance(track, hiero.core.AudioTrack):
                if verbose :
                  print("  " * binLevel, "AudioTrack :", track.name())
                    
                allAudioTracks.append(track)
                
                binLevel += 1
                for trackItem in list(track.items()) :
                  if verbose :
                    print("  " * binLevel, "Track Item :", trackItem.name())
                  allAudioTrackItems.append(trackItem)
                binLevel -= 1

            binLevel -= 1

            allSequences.append(seq)
                      
          if clip :
            if verbose :
              print("  " * binLevel, "Clip :", each.activeItem().name())
            allClips.append(clip)

            # Find effect items on the clip
            effectItems = [i for i in itertools.chain( *itertools.chain(*clip.subTrackItems()) )
                            if isinstance(i, hiero.core.EffectTrackItem)]
            allEffectTrackItems.extend(effectItems)
      binLevel -= 1

    # Parse the project clipsBin
    allBins.append(proj.clipsBin())  # Include the root clips bin
    parseBin(proj.clipsBin(), binLevel)

    # Parse the project tagsBin
    allBins.append(proj.tagsBin())  # Include the root tags bin
    parseBin(proj.tagsBin(), binLevel)

    allTracks = allVideoTracks + allAudioTracks
    allTrackItems = allVideoTrackItems + allAudioTrackItems

    # Check for no filter
    if (None in filterList) and not partialName:
      return allClips + allSequences + allTracks + allTrackItems + allBins

    finalResults = []
    
    # Apply filtering by type
    if hiero.core.Bin in filterList:
      finalResults += allBins

    if hiero.core.BinItem in filterList:
      finalResults += allBinItems
        
    if hiero.core.Clip in filterList:
      finalResults += allClips
        
    if hiero.core.Sequence in filterList:
      finalResults += allSequences
        
    if hiero.core.TrackBase in filterList:
      finalResults += allTracks
        
    if hiero.core.VideoTrack in filterList:
      finalResults += allVideoTracks
        
    if hiero.core.AudioTrack in filterList:
      finalResults += allAudioTracks
        
    if hiero.core.TrackItem in filterList:
      finalResults += allTrackItems

    if hiero.core.EffectTrackItem in filterList:
      finalResults += allEffectTrackItems

    # Apply partial name filter
    if partialName != None : 
      finalResults = [x for x in finalResults if partialName in x.name()]
                
    return finalResults

findItems = findItemsInProject

def findItemsInBin(rootBin, filter=None, partialName=None, verbose=0):
    '''findItemsInBin(rootBin, filter=None, partialName=None, verbose=0) -> Returns all items recursively in a Bin, found in rootBin.
    @param rootBin: hiero.core.Bin object, to find the items on.
    @param filter: optional. Used to filter the returned list. Can be None, a case insensitive single string or type, or a list of case insensitive strings and types.
    @param partialName: optional string. If specified, objects will only be returned if their name contains this string.
    @param verbose: optional value. If not None/False/0, findItems will print out information as it searches.
    @return: list of objects.
    
    Example uses:
    myBin = hiero.core.projects()[0].clipsBin()[0] # A hiero.core.Bin object
    allItemsInMyBin = findItemsInBin(myBin)    
    allClipsAndSequencesInMyBin = findItemsInBin(myBin, filter = [hiero.core.Sequence, hiero.core.Clip])
    allClipsWithPartialName = findItems(myProj, 'clips', 'C00')
    allSubBinsOnly = findItems(myProj, hiero.core.Bin)
    
    '''
    #Solve 'tuple index out of range' error when adding script to startup dir
    if rootBin == None or type(rootBin) != hiero.core.Bin:
        raise Exception("Please provide a valid hiero.core.Bin object as the first argument to hiero.core.findItemsInBin()")
        
    #If it's only one filter or none, make it into a list anyways
    if isinstance(filter, str) or filter == None:
        filter = [filter]

    #Convert the list from strings to types
    filterList = []
    
    try:
      # Try to iterate over it, as if it's a list
      for f in filter:
        filterList.append(convertToType(f))
    except TypeError:
      # We get a type error when it's not iterable, so we assume it's a single item
      filterList.append(convertToType(filter))
        
    binLevel = 0    
    allBins = []
    allClips = []
    allSequences = []
  
    # recursive function
    def parseBin(bin, binLevel) :
      binLevel += 1
      for each in list(bin.items()):

        if type(each) == hiero.core.Bin :
          # Is bin
          if verbose :
            print("  " * binLevel, "Bin :", each.name())
          allBins.append(each)
          parseBin(each, binLevel)
      
        else :
          seq = None
          clip = None
                  
          if isinstance(each, hiero.core.Version) :
            if isinstance(each.item(), hiero.core.Sequence) :
              seq = each.item()
            elif isinstance(each.item(), hiero.core.Clip) :
              clip = each.item()
        
          elif isinstance(each, hiero.core.BinItem):
            if isinstance(each.activeItem(), hiero.core.Sequence) :
              seq = each.activeItem()
            elif isinstance(each.activeItem(), hiero.core.Clip):
              clip = each.activeItem()

          if seq :
            if verbose :
              print("  " * binLevel, "Sequence :", seq.name())

            allSequences.append(seq)
                      
          if clip :
            if verbose :
              print("  " * binLevel, "Clip :", each.activeItem().name())
            allClips.append(clip)
      binLevel -= 1

    # Parse the project clipsBin
    parseBin(rootBin, binLevel)

    # Check for no filter
    if (None in filterList) and not partialName:
      return allClips + allSequences + allBins

    finalResults = []
    
    # Apply filtering by type
    if hiero.core.Bin in filterList:
      finalResults += allBins
        
    if hiero.core.Clip in filterList:
      finalResults += allClips
        
    if hiero.core.Sequence in filterList:
      finalResults += allSequences

    # Apply partial name filter
    if partialName != None : 
      finalResults = [x for x in finalResults if partialName in x.name()]
                
    return finalResults


def findProjectTags(proj=None, tagName=None, iconName=None, verbose=0):
    '''findProjectTags -> Returns all Tags in a project. User can filter by tag name, icon name, and optionally print a verbose log to the output window.
    Takes up to 4 arguments : Project object, partial name of Tag, partial icon name, and a bool to enable/disable verbose mode
    Returns a list of Tag objects.
    
    @param proj: hiero.core.Project object, to find the items on. If None, then the last project in the currently loaded projects will be used.
    @param tagName: optional string. If specified, Tags will only be returned if their name contains this string.
    @param iconName: optional string. If specified, Tags will only be returned if their icon path contains this string.    
    @param verbose: optional value. If not None/False/0, findProjectTags will print out information as it searches.
    @return: list of Tag objects.

    Example uses:

    allTags = findItems(myProj)
    allTagsWithNameLens = findItems(myProj, tagName = 'Lens')
    allTagsWithIconPath = findItems(myProj, iconName = 'lens.png')

    '''
    # Solve 'tuple index out of range' error when adding script to startup dir
    if proj == None:
      proj = hiero.core.projects()[-1]
        
    # Check for a valid project now
    if type(proj) != hiero.core.Project:
      raise Exception("findProjectTags requires a valid valid project object search for items.")

    # We're just going to filter for Tags...
    filter = hiero.core.Tag

    # Convert the list from strings to types
    filterList = []
    
    try:
      # Try to iterate over it, as if it's a list
      for f in filter:
        filterList.append(convertToType(f))
    except TypeError:
      # We get a type error when it's not iterable, so we assume it's a single item
      filterList.append(convertToType(filter))

          
    binLevel = 0    
    allTags = []
    allBins = []
    # recursive function
    def parseBin(bin, binLevel) :
      binLevel += 1
      for each in list(bin.items()):

        if type(each) == hiero.core.Bin :
          #Is bin
          if verbose :
              print("  " * binLevel, "Bin :", each.name())
          allBins.append(each)
          parseBin(each, binLevel)
        
        elif isinstance(each, hiero.core.Tag):
          if verbose :
            print("  " * binLevel, "Tag :", each.name())

          allTags.append(each)

      binLevel -= 1

    # Parse the project tagsBin
    parseBin(proj.tagsBin(), binLevel)
    finalResults = []
    
    # Apply filtering by type
    if hiero.core.Tag in filterList:
      finalResults += allTags

    # Apply Tag name and icon filters
    if tagName != None :
      finalResults = [x for x in finalResults if tagName in x.name()]

    if iconName != None :
      finalResults = [x for x in finalResults if iconName in x.icon()]

    return finalResults


def findItemsByGuid(guids, *args, **kwargs):
  """ Find all items matching a list of guids. This searches all open projects.
  The other arguments are the same as those to findItemsInProject.
  """
  guidSet = set(guids)
  resultList = list()
  for proj in hiero.core.projects():
    for item in findItemsInProject(proj, *args, **kwargs):
      if item.guid() in guidSet:
        resultList.append(item)
        guidSet.remove(item.guid())
        if not guidSet:
          return resultList

  return resultList


def findItemByGuid(guid, *args, **kwargs):
  """ Find an item matching a guid. This searches all open projects. The other
  arguments are the same as those to findItemsInProject.
  """
  items = findItemsByGuid((guid,), *args, **kwargs)
  return items[0] if items else None
