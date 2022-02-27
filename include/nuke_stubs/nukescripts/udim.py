# Copyright (c) 2012 The Foundry Visionmongers Ltd.  All Rights Reserved.
import os, re, sys, math, time
import nuke
from nukescripts import execute_panel
from nukescripts import panels
from PySide2 import (QtCore, QtGui, QtWidgets)


def parseUdimFile(f):

  """Parsing a filename string in search of the udim number.
     The function returns the udim number, and None if it is not able to decode the udim value.

     The udim value is a unique number that defines the tile coordinate.
     If u,v are the real tile coordinates the equivalent udim number is calculated with the following formula:
     udim = 1001 + u + 10 * v    (Note: u >=0 && u < 10 && udim > 1000 && udim < 2000)

     Redefine this function if the parsing function is not appropriate with your filename syntax."""

  sequences = re.split("[._]+", f)

  udim = None

  # find the udim number
  # it gets the last valid udim number available in the filename
  for s in sequences:
    try:
      udim_value = int(s)
    except ValueError:
      # not a number
      udim_value = 0

    if udim_value > 1000 and udim_value < 2000:
      udim = udim_value

  if udim == None:
    return None

  return udim

def uv2udim(uv):
  u,v = uv
  return 1001 + u + 10 * v

def checkUdimValue(udim):
  if udim == None:
    return True

  if type(udim) == int:
    return True

  if type(udim) != tuple:
    return False

  u,v = udim

  if type(u) == int and type(v) == int:
    return True

  return False

def udimStr(s, label):
  return s.format(label)

class UDIMErrorDialog(QtWidgets.QDialog):
  def __init__(self, parent=None, error_msg="", udim_label="UDIM"):
    super(UDIMErrorDialog, self).__init__(parent)

    # Create widgets
    self.Text =  QtWidgets.QTextEdit()
    self.OkButton = QtWidgets.QPushButton("Ok")

    hlayout = QtWidgets.QHBoxLayout()
    spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    hlayout.insertSpacerItem(0, spacer)
    hlayout.addWidget(self.OkButton)

    # Create layout and add widgets
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(self.Text)
    layout.addLayout(hlayout)

    # Set dialog layout
    self.setMinimumSize( 600, 400 )
    self.setLayout(layout)
    self.setModal(True)
    self.setWindowTitle( udimStr("{0} files import error", udim_label))

    # Set error message
    self.Text.setReadOnly(True)
    self.Text.setText(error_msg)

    # Add buttons signal
    self.OkButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self.OkButton.clicked.connect(self.accept)


class UDIMFile:
  def __init__(self, udim, uv,  filename):
    self.udim = udim
    self.uv = uv
    self.filename = filename
    self.enabled = True
    self.conflict = False


class TableDelegate(QtWidgets.QStyledItemDelegate):

  def initStyleOption(self, option, index):
    QtWidgets.QStyledItemDelegate.initStyleOption(self, option, index)
    if index.column() == 1:
      option.textElideMode = QtCore.Qt.ElideLeft

class UDIMOptionsDialog(QtWidgets.QDialog):

  def __init__(self, parent=None, parsing_func=parseUdimFile, udim_label="UDIM"):
    super(UDIMOptionsDialog, self).__init__(parent)

    self.setWindowTitle(udim_label + " import")

    self.UdimMap = []
    self.UdimConflict = False
    self.UdimParsingFunc = parsing_func
    self.cellChangedConnected = False
    self.ForceToExit = False
    self.ErrorMsg = None
    self.UdimLabel = udim_label

    # Create widgets
    self.UdimList = QtWidgets.QTableWidget(0, 3, self)
    self.AddFilesButton = QtWidgets.QPushButton("Add Files")
    self.ConflictLabel = QtWidgets.QLabel("")
    self.Separator = QtWidgets.QFrame()
    self.ReadModeComboBox = QtWidgets.QComboBox()
    self.PostageStampCheckBox = QtWidgets.QCheckBox("postage stamp")
    self.GroupNodesCheckBox = QtWidgets.QCheckBox("group nodes")

    self.OkButton = QtWidgets.QPushButton("Ok")
    self.CancelButton = QtWidgets.QPushButton("Cancel")

    # Setup tooltip
    self.PostageStampCheckBox.setToolTip( udimStr("Enable the node postage stamp generation for all {0} files.", self.UdimLabel) )
    self.GroupNodesCheckBox.setToolTip( udimStr("Place all {0} files in a group.", self.UdimLabel) )

    # Create layout and add widgets
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(self.UdimList)
    layout.addWidget(self.AddFilesButton)
    layout.addWidget(self.ConflictLabel)
    layout.addWidget(self.Separator)
    layout.addWidget(self.ReadModeComboBox)
    layout.addWidget(self.PostageStampCheckBox)
    layout.addWidget(self.GroupNodesCheckBox)

    hlayout = QtWidgets.QHBoxLayout()
    hlayout.insertSpacerItem(0, QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
    hlayout.addWidget(self.OkButton)
    hlayout.addWidget(self.CancelButton)

    layout.addLayout(hlayout)

    # Set dialog layout
    self.setMinimumSize(800, 400)
    self.setLayout(layout)
    self.setModal(True)

    self.Separator.setFrameShape(QtWidgets.QFrame.HLine)
    self.Separator.setFrameShadow(QtWidgets.QFrame.Sunken)

    self.AddFilesButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self.OkButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self.CancelButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    self.ReadModeComboBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    headerView = self.UdimList.horizontalHeader()
    headerView.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
    headerView.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
    headerView.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

    self.UdimList.setItemDelegate(TableDelegate())
    self.UdimList.setHorizontalHeaderLabels( [self.UdimLabel, "filename", ""] )
    self.UdimList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    self.ReadModeComboBox.addItems( ["single read node", "multiple read nodes"] )

    # Add buttons signal
    self.AddFilesButton.clicked.connect(self.importUdimFiles)
    self.OkButton.clicked.connect(self.accept)
    self.CancelButton.clicked.connect(self.reject)

  def updateTableWidget(self):
    self.UdimMap.sort(key=lambda udmFile: udmFile.udim)

    # validate all udim entry
    udimCountMap = {}

    self.UdimConflict = False

    # count the number of time a udim tile is been used
    for u in self.UdimMap:

      if u.enabled == False:
        continue

      if u.udim in udimCountMap:
        udimCountMap[u.udim] = udimCountMap[u.udim] + 1
        self.UdimConflict = True
      else:
        udimCountMap[u.udim] = 1

    # Disable the OK button in case of conflict
    self.OkButton.setEnabled(not self.UdimConflict)

    if self.UdimConflict :
      palette = QtGui.QPalette()
      palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.yellow)
      self.ConflictLabel.setText(udimStr("Conflict : multiple files with the same {0} number. Disable unnecessary files.", self.UdimLabel))
      self.ConflictLabel.setPalette(palette)
    else:
      self.ConflictLabel.setText("Conflict : none")
      self.ConflictLabel.setPalette(QtGui.QPalette())

    # Table cell changed
    if self.cellChangedConnected:
      self.UdimList.cellChanged.disconnect(self.cellChanged)
      self.cellChangedConnected = False

    # recreat the QT table
    self.UdimList.setRowCount( len(self.UdimMap) )

    row = 0
    for u in self.UdimMap:

      if u.uv == None:
        udim_id = QtWidgets.QTableWidgetItem( str(u.udim) )
      else:
        u_coord,v_coord = u.uv
        udim_id = QtWidgets.QTableWidgetItem( "(%(u)02d,%(v)02d)" % {"u":u_coord, "v":v_coord} )

      udim_filename = QtWidgets.QTableWidgetItem( u.filename )

      if u.enabled and u.udim in udimCountMap and udimCountMap[u.udim] > 1:
        udim_id.setForeground(QtGui.QBrush(QtCore.Qt.yellow))
        udim_filename.setForeground(QtGui.QBrush(QtCore.Qt.yellow))

      checked = QtWidgets.QTableWidgetItem("")

      if u.enabled == True:
        checked.setCheckState(QtCore.Qt.Checked)
      else:
        checked.setCheckState(QtCore.Qt.Unchecked)
        udim_id.setForeground(QtGui.QBrush(QtCore.Qt.darkGray))
        udim_filename.setForeground(QtGui.QBrush(QtCore.Qt.darkGray))

      self.UdimList.setItem( row, 0, udim_id )
      self.UdimList.setItem( row, 1, udim_filename )
      self.UdimList.setItem( row, 2, checked )

      row = row + 1

    # Table cell changed
    self.UdimList.cellChanged.connect(self.cellChanged)
    self.cellChangedConnected = True

  def cellChanged(self, row, column):

    if column == 2:
      checked = self.UdimList.item(row, column)

      if checked.checkState() == QtCore.Qt.Checked:
        self.UdimMap[row].enabled = True
      else:
        self.UdimMap[row].enabled = False

      # regenerate table
      self.updateTableWidget()

  def addUdimFile(self, udim_file):

    # avoid to add the same file if present
    for u in self.UdimMap:
      if u.filename == udim_file.filename:
        return

    self.UdimMap.append(udim_file)

  def importUdimFiles(self):
    default_dir = None
    # get all files
    files = nuke.getClipname( "Read File(s)", default=default_dir, multiple=True )

    if files == None:
      if len(self.UdimMap) == 0:
        self.ForceToExit = True
      return

    warning_msg = ""

    # save the new files in the internal map
    for f in files:

      # the file could be a sequence split it
      sequences = splitInSequence(f)

      for s in sequences:

        if os.path.isfile(s) == False:
          continue

        # parse the udim file
        udim = self.UdimParsingFunc(s)

        # check the parsing function result
        if checkUdimValue(udim) == False:
          self.reject()
          self.ErrorMsg = udimStr("Error. Wrong type returned by {0} parsing function.",self.UdimLabel )
          raise ValueError(self.ErrorMsg)

        if udim == None:
          warning_msg = warning_msg +  s + "\n"
          warning = True
        else:
          uv = None
          udim_value = 0

          try:
            udim_value = int(udim)
          except TypeError:
            udim_value = uv2udim(udim)
            uv = udim

          self.addUdimFile(UDIMFile(udim_value, uv, s))

    # show a warning message in case of problems
    if len(warning_msg) > 0:
      errorMsg = udimStr( "The following files do not contain a valid {0} number: \n\n" + warning_msg,  self.UdimLabel )
      udimLabel = self.UdimLabel
      e = UDIMErrorDialog(error_msg = errorMsg, udim_label = udimLabel)
      e.exec_()

    # regenerate table
    self.updateTableWidget()

def splitInSequence(f):

  # a file is a sequence if it is expressed in this way:
  # filename.####.ext  1-10
  # filename_####.ext  1-10
  # filename####.ext  1-10

  idx = f.find('#')
  if idx == -1:
    return [f]

  # find the sub string that needs to be substituted with the frame number
  subst = ''
  for x in range(idx, len(f)):
    if f[x] != '#':
      break
    subst = subst + '#'

  # split the file name in filename,frange
  sfile = f.split(' ')

  # get the frame range
  try :
    frame_range = nuke.FrameRange( sfile[1] )
  except ValueError:
    return [f]

  args = "%(#)0" + str(len(subst)) + "d"

  sequences = []
  for r in frame_range:
    # replace in filename the pattern #### with the right frame range
    filename = sfile[0].replace( subst, args % {"#":r} )
    sequences.append( filename )

  return sequences

def findNextName(name):
  i = 1
  while nuke.toNode ( name + str(i) ) != None:
    i += 1

  return name + str(i)

def allign_nodes(nodes, base):
  # allign an array of node over a node

  nodeSize = 100

  left = right = nodes[0].xpos()
  top = bottom = nodes[0].ypos()

  for n in nodes:

    if n.Class() == "Dot":
      continue

    if n.xpos() < left:
      left = n.xpos()

    if n.xpos() > right:
      right = n.xpos()

    if n.ypos() < top:
      top = n.ypos()

    if n.ypos() > bottom:
      bottom = n.ypos()

  xpos = base.xpos()
  ypos = base.ypos()

  for n in nodes:
    x = n.xpos() - right
    y = n.ypos() - bottom
    n.setXYpos( x + xpos, y + ypos - nodeSize )

def udim_group(nodes):
  # collaspe all udim tree nodes in a group
  for n in nodes:
    n["selected"].setValue ( True )
  group_node = nuke.collapseToGroup(False)
  group_node.autoplace()

  return group_node

def udim_import( udim_parsing_func = parseUdimFile, udim_column_label = "UDIM" ):

  """ Imports a sequence of UDIM files and creates the node material tree needed.
      This function simplifies the process of importing textures. It generates a tree of nodes which
      adjusts the texture coordinates at rendering time for a model containing multiple texture tiles.
      In general a tile texture coordinate can be expressed with a single value(UDIM) or with a tuple(ST or UV).
      The udim_import function can decode a UDIM number from a filename.
      To determine the tile coordinate encoding for a generic filename convention, the udim_import script can use an
      external parsing function.

      The redefined parsing function needs to decode a filename string and return the udim or the u,v tile coordinate
      as an integer or tuple of integers. It should return None if the tile coordinate id can not be determined.

  @param udim_parsing_func:   The parsing function. This parses a filename string and returns a tile id.
  @param udim_column_label:   The name of the column in the dialog box used to show the tile id.
  @return:                    None
  """


  # get the UDIM sequence
  p = UDIMOptionsDialog(parsing_func = udim_parsing_func, udim_label = udim_column_label)

  try:
    p.importUdimFiles()
  except ValueError as e:
    nuke.message(str(e))
    return

  if p.ForceToExit:
    return

  result = p.exec_()

  if result == False:
    if p.ErrorMsg != None:
      nuke.message(p.ErrorMsg)
    return

  UdimMap = p.UdimMap
  postagestamp = p.PostageStampCheckBox.isChecked()
  makegroup = p.GroupNodesCheckBox.isChecked()
  makesingleread = (p.ReadModeComboBox.currentIndex() == 0)

  uvtile = []
  nodes  = []

  read_node_width = 80
  dot_node_width = 12
  read_node_height = 78
  dot_node_height = 12
  frame_hold_width = 80
  frame_hold_height = 28
  other_node_height = 18

  if postagestamp == False:
    read_node_height = 28

  h_spacing = 30
  v_spacing = 20

  udim_file_count = 0

  # check all valid udim file
  for u in UdimMap:
    # skip disabled udim
    if u.enabled == False:
      continue

    if os.path.isfile(u.filename) == False:
      u.enabled = False
      continue

    udim_file_count += 1

  # nothing to do
  if udim_file_count == 0:
    return
  if udim_file_count == 1:
    makesingleread = False

  selected_nodes = nuke.selectedNodes()

  # deselect all nodes, needed for the group creation
  for n in selected_nodes:
    n["selected"].setValue ( False )

  groupBaseName = None
  single_read_node = None
  udim_file_sequence = ""
  sequence_index = 1
  parent_dot_frame_hold = None

  # create a single read node that keep all udim files
  if makesingleread:
    single_read_node = nuke.nodes.Read()
    parent_dot_frame_hold = single_read_node

  for u in UdimMap:

    # skip disabled udim
    if u.enabled == False:
      continue

    # split the tuble
    udim = u.udim
    uv   = u.uv
    img  = u.filename

    if groupBaseName == None:
      groupBaseName = os.path.basename(img)

    xpos = None
    ypos = None
    udim_node = None

    # compose the sequence of udim files
    if single_read_node != None:
      udim_file_sequence += img + "\n"

      # create the dot that connect the single read to the frame hold node
      frame_hold_xpos = single_read_node.xpos() + (frame_hold_width + h_spacing) * (sequence_index-1)

      dot_node = nuke.nodes.Dot( xpos = frame_hold_xpos + (frame_hold_width - dot_node_width) / 2,
                                 ypos = single_read_node.ypos() + read_node_height + v_spacing )
      dot_node.setInput(0, parent_dot_frame_hold)
      parent_dot_frame_hold = dot_node

      # create the frame hold node
      udim_node = nuke.nodes.FrameHold( xpos = frame_hold_xpos,
                                        ypos = dot_node.ypos() + dot_node_height + v_spacing )

      udim_node['first_frame'].setValue(sequence_index)
      udim_node.setInput(0, dot_node)

      xpos = udim_node.xpos()
      ypos = udim_node.ypos() + frame_hold_height + v_spacing

      nodes.append(dot_node)

      # next udim file inside sequence
      sequence_index += 1
    else:
      # create the read node
      udim_node = nuke.nodes.Read()
      udim_node['file'].setValue( img )
      udim_node['postage_stamp'].setValue( postagestamp )
      udim_node.autoplace()

      xpos = udim_node.xpos()
      ypos = udim_node.ypos() + read_node_height + v_spacing

    # create the UV Tile node
    uvtile_node = nuke.nodes.UVTile2(xpos=xpos, ypos=ypos)
    uvtile_node.setInput(0, udim_node)

    if uv == None:
      uvtile_node['udim_enable'].setValue(True)
      uvtile_node['udim'].setValue(udim)
    else:
      u,v = uv
      uvtile_node['tile_u'].setValue( u )
      uvtile_node['tile_v'].setValue( v )

    uvtile.append(uvtile_node)

    nodes.append(udim_node)
    nodes.append(uvtile_node)

  if (len(uvtile) == 0):
    return

  if single_read_node != None:
    single_read_node['file'].setValue("[lindex [knob sequence] [expr [frame]-1]]")
    single_read_node['postage_stamp'].setValue( postagestamp )
    single_read_node['sequence'].setValue(udim_file_sequence)
    single_read_node['last'].setValue(sequence_index-1)
    single_read_node['origlast'].setValue(sequence_index-1)

  latest_merge =  uvtile[0]

  if len(uvtile) > 1:

    xpos = latest_merge.xpos()
    ypos = latest_merge.ypos() + other_node_height + v_spacing

    dot_node = nuke.nodes.Dot( xpos=xpos + (read_node_width - dot_node_width) / 2,
                               ypos=ypos + (other_node_height - dot_node_height) / 2)

    dot_node.setInput(0, latest_merge)
    nodes.append(dot_node)
    latest_merge = dot_node

  for x in range(1, len(uvtile)):

    xpos = uvtile[x].xpos()
    ypos = uvtile[x].ypos() + other_node_height + v_spacing

    mergemat_node = nuke.nodes.MergeMat(xpos=xpos, ypos=ypos)
    mergemat_node.setInput(0, latest_merge)
    mergemat_node.setInput(1, uvtile[x])

    latest_merge = mergemat_node
    nodes.append(mergemat_node)

  # enable the multi texture udim optimization only for the root
  # node of the udim shading tree
  if len(uvtile) > 1:
    xpos = latest_merge.xpos()
    ypos = latest_merge.ypos() + other_node_height + v_spacing

    multitexture = nuke.nodes.MultiTexture(xpos=xpos, ypos=ypos)
    multitexture.setInput(0, latest_merge)
    latest_merge = multitexture
    nodes.append(latest_merge)

  for n in nodes:
    n["selected"].setValue ( True )

  if makegroup == True:
    latest_merge = udim_group( nodes )

    # set the group name
    split = re.split("[._]+", groupBaseName)
    name = split[0]

    latest_merge.setName( findNextName(name) )

    nodes = []
    nodes.append( latest_merge )

  if single_read_node != None:
    single_read_node["selected"].setValue ( True )

  if len(selected_nodes) == 1:
    if single_read_node != None:
      nodes.append(single_read_node)

    allign_nodes( nodes,  selected_nodes[0] )

  for n in selected_nodes:
    n["selected"].setValue ( True )
    if n.Class() == 'ReadGeo2':
      n.setInput(0, latest_merge)
