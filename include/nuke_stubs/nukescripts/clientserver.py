# Copyright (c) 2009 The Foundry Visionmongers Ltd.  All Rights Reserved.

import socket, threading
import nuke
from nukescripts import utils

HOST='localhost'
PORT=50007


class client():
  """
  Example of running an IPV6 socket client to create nodes in Nuke.

  from nukescripts import clientserver
  c = clientserver.client()
  c.send("Blur")
  """

  def __init__(self, host = HOST, port = PORT):
    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
      af, socktype, proto, canonname, sa = res
      try:
        self.s = socket.socket(af, socktype, proto)
      except socket.error as msg:
        self.s = None
        continue
      try:
        self.s.connect(sa)
      except socket.error as msg:
        self.s.close()
        self.s = None
        continue
      break

    if not self.s: raise RuntimeError("Unable to initialise client.")

  def send(self, msg):
    self.s.send(msg)

  def close(self):
    self.s.close()


class server():
  """
  Example of running an IPV6 socket server on a separate thread inside Nuke.
  The default command is to create the named node.

  from nukescripts import clientserver
  clientserver.threaded_server()
  """

  def __init__(self, host = HOST, port = PORT):
    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
      af, socktype, proto, canonname, sa = res
      try:
        self.s = socket.socket(af, socktype, proto)
      except socket.error as msg:
        self.s = None
        continue
      try:
        self.s.bind(sa)
        self.s.listen(1)
      except socket.error as msg:
        self.s.close()
        self.s = None
        continue
      break

    if not self.s: raise RuntimeError("Unable to initialise server.")

  def start(self):
    (conn, addr) = self.s.accept()
    print("Connection from ", addr)
    while 1:
      data = conn.recv(1024)
      if not data: break
      print("Command ", data)
      utils.executeInMainThread(nuke.createNode, (data,))
    conn.close()

def start_server(host = HOST, port = PORT):
  s = server(host, port)
  s.start()

def threaded_server():
  t = threading.Thread(None, start_server)
  t.start()

