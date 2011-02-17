#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""Connection related information."""

__author__ = 'schrepfer'

import locale
import logging
import sys
import telnetlib
import select
import socket

from lib import events


class Connection(object):

  def __init__(self, engine):
    self._telnet = telnetlib.Telnet()
    self._running = False
    self._engine = engine
    self._sent = 0
    self._received = 0
    events.registerEvents(self, engine)
    locale.setlocale(locale.LC_ALL, '')

  @property
  def engine(self):
    return self._engine

  @property
  def sent(self):
    return self._sent

  @property
  def received(self):
    return self._received

  def connect(self, address, port):
    if self._telnet.sock:
      logging.warn('Already connected to server')
      return
    logging.info('Connecting to %s port %d..', address, port)
    try:
      self._telnet.open(address, port)
    except socket.error:
      logging.error('Could not connect to server')
      self.engine.eventManager.triggerEvent(events.CONFAIL)
      self.engine.startTimer('reconnect', 10.0, self.connect, address, port)
      return
    self._running = True
    self.engine.startThread('connection', self.start)

  def disconnect(self):
    self._running = False

  @events.event(events.SHUTDOWN)
  def onShutdown(self):
    self.disconnect()

  def start(self):
    self._sent = 0
    self._received = 0

    self.engine.eventManager.triggerEvent(events.CONNECT)
    previousLine = ''

    while self.running():
      # Add some code to detect a connection that has died abnormally..
      if not select.select([self._telnet], [], [], 0.2)[0]:
        continue
      try:
        data = self._telnet.read_eager()
      except EOFError:
        logging.info('Connection closed')
        self.disconnect()
        break
      if not data:
        continue
      self._received += len(data)
      data = previousLine + data.replace('\r', '')
      lines = data.split('\n')
      previousLine = lines[-1]
      currentLines = lines[0:-1]

      for line in currentLines:
        self.engine.eventManager.triggerEvent(events.READ, line)

    self._telnet.close()

    self.engine.eventManager.triggerEvent(events.DISCONNECT)

    logging.info('Sent: %s bytes, Received: %s bytes',
      locale.format('%d', self._sent, grouping=True),
      locale.format('%d', self._received, grouping=True))

  def running(self):
    return self._running and self._telnet.sock and self.engine.running()

  @events.event(events.SEND)
  def onSend(self, data):
    if not self.running():
      return False
    data += '\r\n'
    self._sent += len(data)
    self._telnet.write(data)
    return True
