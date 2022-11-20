# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero.core

hiero.core.log.debug( "Loading Python hiero.exporters package" )

import os
from _nuke import env as nukeEnv

# Try to access the export task registry. If this doesn't exist it indicates
# the application is running in a mode that doesn't support exports.
try: 
  registry = hiero.core.taskRegistry
except AttributeError:
  raise ImportError("hiero.exporters module not available in %s" % hiero.core.env['ProductName'])

try:
  # Tasks
  from . import FnShotExporter
  from . import FnFrameExporter
  from . import FnSymLinkExporter
  from . import FnCopyExporter
  from . import FnNukeShotExporter
  from . import FnNukeAnnotationsExporter
  from . import FnExternalRender
  from . import FnTranscodeExporter
  from . import FnEDLExportTask
  from . import FnXMLExportTask
  from . import FnAudioExportTask

  # Task UI
  from . import FnSymLinkExporterUI
  from . import FnCopyExporterUI

  from . import FnNukeShotExporterUI
  from . import FnNukeAnnotationsExporterUI

  from . import FnExternalRenderUI
  from . import FnTranscodeExporterUI
  from . import FnEDLExportUI
  from . import FnXMLExportUI
  from . import FnAudioExportUI

  # Processors
  from . import FnShotProcessor
  from . import FnShotProcessorUI
  from . import FnTimelineProcessor
  from . import FnTimelineProcessorUI
  from . import FnBinProcessor
  from . import FnBinProcessorUI

  from .FnSubmission import Submission
  from . import FnLocalNukeRender

except NotImplementedError:
  pass
  
def MakeTranscodePreset(file_type, properties):
  """ Make a transcode preset for a given file type and
  codec properties dictionary."""
  props = {'file_type' : file_type,
            file_type : properties,
            'includeAudio':True,
            'deleteAudio':True,
          }
  return FnTranscodeExporter.TranscodePreset("", props)

def MakeExportProcessorTemplate(processorPreset, path, transcodePreset):
  """ Make a template for a processor preset, path, and transcode preset. """
  return (
            processorPreset,
            { "exportTemplate":
              (
                ( path, transcodePreset ),
              )
            }
          )

def GetDefaultMovTranscodePresets():
  """ Generate a dict of presets for the default mov transcode presets.
  These will be populated with all the default values for the encoder properties."""

  def makeMovTranscodePreset(properties):
    """ Make a TranscodePreset, populating it with the codec and default
    property values. """
    return MakeTranscodePreset('mov', properties)

  def makeMovSequenceTemplate(properties):
    """ Make the sequence template for a codec. """
    return MakeExportProcessorTemplate(FnTimelineProcessor.TimelineProcessorPreset,
                                      "{sequence}_{version}/{sequence}_{version}.{ext}",
                                      makeMovTranscodePreset(properties))

  def makeMovClipTemplate(properties):
    """ Make the clip template for a codec. """
    return MakeExportProcessorTemplate(FnBinProcessor.BinProcessorPreset,
                                      "{binpath}/{clip}.{ext}",
                                      makeMovTranscodePreset(properties))

  proRes4444Properties = { "mov64_codec" : "appr\tApple ProRes",
                           "mov_prores_codec_profile" : "ProRes 4:4:4:4 12-bit" }

  proRes422Properties = { "mov64_codec" : "appr\tApple ProRes",
                          "mov_prores_codec_profile" : "ProRes 4:2:2 10-bit" }

  avidDNxHDProperties = { "mov64_codec" : "AVdn\tAvid DNxHD" }

  photoJPEGProperties = { "mov64_codec" : "jpeg\tPhoto - JPEG" }

  movProperties = (proRes4444Properties,
                     proRes422Properties,
                     avidDNxHDProperties,
                     photoJPEGProperties)

  movSequenceTranscodeNames = ("Apple ProRes 4444 MOV",
                                "Apple ProRes 422 MOV",
                                "Avid DNxHD Codec MOV",
                                "Photo - JPEG MOV")

  movClipTranscodeNames = ("Transcode Clips Apple ProRes 4444 MOV",
                            "Transcode Clips Apple ProRes 422 MOV",
                            "Transcode Clips Avid DNxHD Codec MOV",
                            "Transcode Clips Photo - JPEG MOV")

  processorPresets = dict()

  # Make the sequence presets
  for name, properties in zip(movSequenceTranscodeNames, movProperties):
    processorPresets[name] = makeMovSequenceTemplate(properties)

  # Make the clip presets
  for name, properties in zip(movClipTranscodeNames, movProperties):
    processorPresets[name] = makeMovClipTemplate(properties)


  return processorPresets

def GetDefaultMxfPreset():

  def getOP1aSettings():
    return { "mxf_op_pattern_knob" : "OP-1a", 
             "mxf_codec_profile_knob" : "HQX 4:2:2 12-bit",
             "mxf_edit_rate_knob" : "24" }

  def getOPAtomSettings():
    return { "mxf_op_pattern_knob" : "OP-Atom", 
             "mxf_codec_profile_knob" : "HQX 4:2:2 12-bit",
             "mxf_edit_rate_knob" : "24" }

  def makeMxfSequenceTemplate(transcodePreset):
    return MakeExportProcessorTemplate(FnTimelineProcessor.TimelineProcessorPreset,
                                "{sequence}_{version}/{sequence}_{version}.{ext}",
                                transcodePreset)

  def makeMxfClipTemplate(transcodePreset):
    return MakeExportProcessorTemplate(FnBinProcessor.BinProcessorPreset,
                                "{binpath}/{clip}.{ext}",
                                transcodePreset)

  mxfPresets = dict()
  OP1aSequencePreset = makeMxfSequenceTemplate(MakeTranscodePreset("mxf", getOP1aSettings()))
  OPAtomSequencePreset = makeMxfSequenceTemplate(MakeTranscodePreset("mxf", getOPAtomSettings()))
  OP1aClipPreset = makeMxfClipTemplate(MakeTranscodePreset("mxf", getOP1aSettings()))
  OPAtomClipPreset = makeMxfClipTemplate(MakeTranscodePreset("mxf", getOPAtomSettings()))

  mxfPresets["DNxHR MXF codec (OP-1a - HQX 422 12bit) - 24 FPS"] = OP1aSequencePreset
  mxfPresets["DNxHR MXF codec (OP-Atom - HQX 422 12bit) - 24 FPS"] = OPAtomSequencePreset
  mxfPresets["Transcode Clips DNxHR MXF codec (OP-1a - HQX 422 12bit) - 24 FPS"] = OP1aClipPreset
  mxfPresets["Transcode Clips DNxHR MXF codec (OP-Atom - HQX 422 12bit) - 24 FPS"] = OPAtomClipPreset
  return mxfPresets


def AddDefaultPresets(overwrite):
  """ Configure the default export presets.  If overwrite is true, this will
  replace the existing presets. """

  shotTemplateNkPath = "{shot}/nuke/script/{shot}_comp{_nameindex}_{version}.{ext}"
  shotTemplateRenderPath = "{shot}/nuke/renders/{shot}_comp{_nameindex}_{version}.####.{ext}"
  shotTemplateRenderPreset = FnExternalRender.NukeRenderPreset( "", {'file_type' : 'dpx', 'dpx' : {'datatype' : '10 bit'}} )

  shottemplate = ((shotTemplateNkPath, FnNukeShotExporter.NukeShotPreset( "",
                    {
                      'readPaths': [],
                      'writePaths': [shotTemplateRenderPath],
                      'timelineWriteNode': shotTemplateRenderPath
                      }
                  )),
                  (shotTemplateRenderPath, registry.copyPreset(shotTemplateRenderPreset) ) )

  shotAnnotationsNkPath = '{shot}/nuke/annotations/{shot}_comp_annotations_{version}.{ext}'
  shotAnnotationsRenderPath = '{shot}/nuke/annotations/{shot}_comp_annotations_{version}.####.{ext}'

  # the folder structure can be change by dragging items on the treeview so
  # this should have the same order as they will appear to detect any changes
  # made by dragging
  shotannotationstemplate = (
                  (
                    shotTemplateNkPath,
                    FnNukeShotExporter.NukeShotPreset( "",
                      {
                        'readPaths': [],
                        'writePaths': [shotTemplateRenderPath],
                        'annotationsPreCompPaths' : [shotAnnotationsNkPath],
                        'timelineWriteNode': shotTemplateRenderPath
                      }
                    )
                  ),
                  (
                    shotTemplateRenderPath,
                    registry.copyPreset(shotTemplateRenderPreset)
                  ),
                  (
                    shotAnnotationsNkPath,
                    FnNukeAnnotationsExporter.NukeAnnotationsPreset( "",
                      {
                        'readPaths': [],
                        'writePaths': [shotAnnotationsRenderPath],
                        'timelineWriteNode': shotAnnotationsRenderPath
                      }
                    )
                  ),
                  (
                    shotAnnotationsRenderPath,
                    registry.copyPreset(shotTemplateRenderPreset)
                  )
                )

  multiViewShotRenderPath = "{shot}/nuke/renders/{version}/view_%v/{shot}_%v_comp{_nameindex}_{version}.####.{ext}"
  multiViewShotTemplate = ((shotTemplateNkPath, FnNukeShotExporter.NukeShotPreset( "",
                    {
                      'readPaths': [],
                      'writePaths': [multiViewShotRenderPath],
                      'timelineWriteNode': multiViewShotRenderPath
                      }
                  )),
                  (multiViewShotRenderPath, registry.copyPreset(shotTemplateRenderPreset) ) )

  shottranscodeTemplate = (("{shot}/{shot}.####.{ext}", FnTranscodeExporter.TranscodePreset("", {'file_type' : 'dpx', 'dpx' : {'datatype' : '10 bit'}}) ), )

  dpxTranscodePreset = FnTranscodeExporter.TranscodePreset( "", {'file_type' : 'dpx', 'dpx' : {'datatype' : '10 bit'}})
  sequencetemplate = ( ("{sequence}_{version}/{sequence}_{version}.####.{ext}", registry.copyPreset(dpxTranscodePreset) ), )
  sequenceMultiViewTemplate = ( ("{sequence}_{version}_%v/{sequence}_{version}_%v.####.{ext}", registry.copyPreset(dpxTranscodePreset) ), )

  if not nukeEnv['ple']:
    edltemplate = (("{sequence}/{track}.edl", FnEDLExportTask.EDLExportPreset("", {})),)
    xmltemplate = (("{sequence}/{sequence}.xml", FnXMLExportTask.XMLExportPreset("", {})),)

  clipstemplate = (("{binpath}/{clip}.####.{ext}", registry.copyPreset(dpxTranscodePreset)), )

  processorPresets = { "Basic Nuke Shot" :
                            ( FnShotProcessor.ShotProcessorPreset, { "exportTemplate" : shottemplate, "cutLength" : True } ),
                       "Basic Nuke Shot With Annotations" :
                            ( FnShotProcessor.ShotProcessorPreset, { "exportTemplate" : shotannotationstemplate, "cutLength" : True } ),
                      "Multi-View Nuke Shot (%v)" :
                            ( FnShotProcessor.ShotProcessorPreset, { "exportTemplate" : multiViewShotTemplate, "cutLength" : True } ),
                       "Transcode Shots DPX" :
                            ( FnShotProcessor.ShotProcessorPreset, { "exportTemplate" : shottranscodeTemplate, "cutLength" : True  } ),
                       "Log10 Cineon DPX":
                            ( FnTimelineProcessor.TimelineProcessorPreset, { "exportTemplate" : sequencetemplate } ),
                       "Log10 Cineon DPX Multi-View":
                            ( FnTimelineProcessor.TimelineProcessorPreset, { "exportTemplate" : sequenceMultiViewTemplate } ),
                       "Transcode Clips DPX" :
                            ( FnBinProcessor.BinProcessorPreset, {"exportTemplate" : clipstemplate} ),
                     }

  # Add the mov transcode presets
  processorPresets.update( GetDefaultMovTranscodePresets() )
  # Add the MXF transcode presets
  processorPresets.update( GetDefaultMxfPreset() )

  if not nukeEnv['ple']:
    processorPresets["CMX 3600 EDL"] = ( FnTimelineProcessor.TimelineProcessorPreset, { "exportTemplate" : edltemplate } )
    processorPresets["Final Cut Pro 7 XML"] = ( FnTimelineProcessor.TimelineProcessorPreset, { "exportTemplate" : xmltemplate } );

  localpresets = [ preset.name() for preset in registry.localPresets()]
  for name, preset in processorPresets.items():
    if overwrite or name not in localpresets:
      presetType, presetProperties = preset
      registry.removeProcessorPreset(name)
      registry.addProcessorPreset(name, presetType(name, presetProperties))


registry.setDefaultPresets(AddDefaultPresets)

# Register our built in submission types. 
# In Nuke studio "Frame server" task will be added later and set to default
registry.addSubmission( "Single Render Process", FnLocalNukeRender.LocalNukeSubmission )
