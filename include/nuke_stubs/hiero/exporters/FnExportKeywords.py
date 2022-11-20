""" File containing definitions of keywords for use in the exporters. """


# TODO: Only a few of the keywords have been put in this file.  Other keywords which are used in multiple places should also be moved here to avoid duplicating tooltips etc.


kFileBaseKeyword = "{filebase}"
kFileHeadKeyword = "{filehead}"
kFilePathKeyword = "{filepath}"

KeywordTooltips = {
  kFileBaseKeyword : ("Base part of the file name for the media being processed.  Includes everything preceding the period before the extension.\n"
                      "                  For example, {filebase} for 'myshot.%04d.dpx' would resolve to 'myshot.%04d'."),
  kFileHeadKeyword : ("Head part of the file name for the media being processed.  For a file sequence, includes everything preceding the frame numbers, for single files behaves the same as {filebase}.\n"
                      "                  For example, {filehead} for 'myshot.%04d.dpx' would resolve to 'myshot'.  'myshot.mov' would also resolve to 'myshot'."),
  kFilePathKeyword : ("Path to the file name for the media being processed.")
}
