import hiero.core
import os
import fnmatch

def isabs(s):
  return s.startswith('/')

def join(a, *p):
  path = a
  for b in p:
    if b.startswith('/'):
      path = b
    elif path == '' or path.endswith('/'):
      path +=  b
    else:
      path += '/' + b
  return path

def split(p):
  i = p.rfind('/') + 1
  head, tail = p[:i], p[i:]
  if head and head != '/'*len(head):
    head = head.rstrip('/')
  return head, tail

def normpath(path):
  # Preserve unicode (if path is unicode)
  slash, dot = ('/', '.') if isinstance(path, str) else ('/', '.')
  if path == '':
    return dot
  initial_slashes = path.startswith('/')
  comps = path.split('/')
  new_comps = []
  for comp in comps:
    if comp in ('', '.'):
      continue
    if (comp != '..' or (not initial_slashes and not new_comps) or
        (new_comps and new_comps[-1] == '..')):
      new_comps.append(comp)
    elif new_comps:
      new_comps.pop()
  comps = new_comps
  path = slash.join(comps)
  if initial_slashes:
    path = slash + path
  return path or dot

def abspath(path):
  """Return an absolute path."""
  if not isabs(path):
    if isinstance(path, str):
      cwd = str(_currentPath)
    else:
      cwd = _currentPath
    path = join(cwd, path)
  return normpath(path)


def basename(p):
  """Returns the final component of a pathname"""
  i = p.rfind('/') + 1
  return p[i:]

def dirname(p):
  """Returns the directory component of a pathname"""
  i = p.rfind('/') + 1
  head = p[:i]
  if head and head != '/'*len(head):
    head = head.rstrip('/')
  return head


def _iglob( parent, path ):
  if len(path) == 0 or len(path[0]) == 0:
    yield parent
    return
  
  name = path[0]
  
  children = parent
  if hasattr( parent, "items" ):
    children = list(parent.items())
  elif hasattr( parent, "clipsBin" ):
    children = [children.clipsBin()]
  
  for a in children:
    if fnmatch.fnmatch( a.name(), name ):
      if len(path) == 1:
        yield a
      else:
        for i in _iglob( a, path[1:] ):
          if i is not None:
            yield i

def iglob( path, parent = None ):
  """ Returns a iterator of all items matching the given path, where the path may contain * and ? wildcards.
  """
  path = normpath(path)
  if path.startswith("/"):
    parent = hiero.core.projects()
    return _iglob( parent, path.split('/')[1:] )
  if parent is None:
    parent = hiero.core.projects()
  return _iglob( parent, path.split('/') )

def glob( path ):
  """ Returns a list of all items matching the given path, where the path may contain * and ? wildcards.
  """
  return [i for i in iglob( path )]

def itemForPath( path ):
  """ Returns the item corresponding to the given path, or None if no item exists at the path.
  """
  for i in iglob( path ):
    return i
  return None

def pathForItem( item ):
  """ Returns the path corresponding to the given item.
  """
  if item is not None:
    parent = None
    if hasattr(item, "parentBin"):
      parent = item.parentBin()
    elif hasattr(item, "parent"):
      parent = item.parent()
    if parent is not None:
      return pathForItem(parent)+"/"+item.name()
    return "/"+item.name()
  return ""


_currentPath = "/"

def cd(path):
  global _currentPath
  if path.startswith("/"):
    _currentPath = path
  else:
    _currentPath = join( _currentPath, path )

def pwd():
  global _currentPath
  print(_currentPath)

def ls(path = "*"):
  global _currentPath
  if not path.startswith("/"):
    path = join( _currentPath, path )
  for i in iglob( path ):
    print(i)
