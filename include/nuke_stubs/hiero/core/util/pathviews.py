import re


def isMultiViewPath(path):
  """ Test if a path contains %v placeholders for multiple views """
  return '%v' in path or '%V' in path


def formatMultiViewPath(path, view):
  """ Format a path string with %v/V placeholders with a view name """
  return path.replace('%V', view).replace('%v', view[0])


def findViewInPath(path, views):
  """ Try to find a view name in a path from the list of views. If successful,
  returns a list of the matched view name and the path with %v/%V substituted.
  Otherwise returns None.
  """
  # Match regex. The view name should be surrounded by non-alphanumeric characters
  boundary = '([^a-zA-Z0-9])'
  pattern = boundary + '({0})' + boundary

  # First try to match full view names
  sub = r'\1%V\3'
  for view in views:
    matchedPath = re.sub(pattern.format(view), sub, path)
    if matchedPath != path:
      # If the full view name was matched, it is possible there will also be 
      # use of the first letter elsewhere in the path. Call recursively to check that
      firstLetterMatch = findViewInPath(matchedPath, (view,))
      if firstLetterMatch:
        matchedPath = firstLetterMatch[1]
      return [view, matchedPath]

  # If that fails look for the first letter
  sub = r'\1%v\3'
  for view in views:
    matchedPath = re.sub(pattern.format(view[0]), sub, path)
    if matchedPath != path:
      return [view, matchedPath]

  return None


if __name__ == '__main__':
  import unittest

  # Need to run the same test with different data, so construct a TestSuite
  def createTestSuite():
    return unittest.TestSuite([TestFindView(args, output) for args, output in TestData])

  TestData = (
    # Path with 'left' view specified
    (('/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/cathedral1/cathedral1_left.%04d.tif', ('left', 'right')),
     ('left', '/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/cathedral1/cathedral1_%V.%04d.tif')),
    # View in directory and file name
    (('/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/Attenborough_DPX_INT/ATLANTIC_FM_MAIN_SHOW_01_to_foundry_right/to_foundry_right.%05d.dpx', ('left', 'right')),
     ('right', '/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/Attenborough_DPX_INT/ATLANTIC_FM_MAIN_SHOW_01_to_foundry_%V/to_foundry_%V.%05d.dpx')),
    # View first letter in file name
    (('/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/tron_INT/hs0040_fgd_a037_82e_4_group_v001.hds/hs0040_fgd_a037_82e_4_group_l_v001.%04d.exr', ('left', 'right')),
     ('left', '/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/tron_INT/hs0040_fgd_a037_82e_4_group_v001.hds/hs0040_fgd_a037_82e_4_group_%v_v001.%04d.exr')),
    # View name in directory and first letter in file name
    (('/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/tron_INT/hs0040_fgd_a037_82e_4_group_left_v001.hds/hs0040_fgd_a037_82e_4_group_l_v001.%04d.exr', ('left', 'right')),
     ('left', '/mnt/netqa/Testing/Nuke/ShotsByCategory/Stereo/tron_INT/hs0040_fgd_a037_82e_4_group_%V_v001.hds/hs0040_fgd_a037_82e_4_group_%v_v001.%04d.exr')),
    # Make sure not matching in Windows drive letters
    (('L:/Testing/Nuke/ShotsByCategory/Stereo/cathedral1/cathedral1.%04d.tif', ('Left', 'Right')),
     None),
  )

  class TestFindView(unittest.TestCase):
    def __init__(self, args, output):
      unittest.TestCase.__init__(self, methodName='testPaths')
      self.args = args
      self.output = output

    def testPaths(self):
      self.assertEqual(self.output, findViewInPath(*self.args))
  testRunner = unittest.TextTestRunner()
  testRunner.run(createTestSuite())
