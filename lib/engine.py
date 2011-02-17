#!/usr/bin/env python
#
# Copyright 2010. All Rights Reserved.

"""Engine which runs everything."""

__author__ = 'schrepfer'

import ConfigParser
import getpass
import logging
import optparse
import os
import re
import select
import sys
import threading

from lib import events


class Engine(object):

  def __init__(self):
    self._running = False
    self._shutdown = threading.Event()
    self._threads = []
    self._timers = []
    self._eventManager = events.EventManager(self)
    events.registerEvents(self, self)

  @property
  def eventManager(self):
    return self._eventManager

  def startThread(self, name, function):
    self.cleanupThreads()
    thread = threading.Thread(target=function)
    thread.setName(name)
    logging.debug('startThread %s', function.func_name)
    thread.start()
    self._threads.append(thread)

  def startTimer(self, name, interval, function, *args, **kwargs):
    self.cleanupThreads()
    self.killTimer(name)
    timer = threading.Timer(interval, function, args=args, kwargs=kwargs)
    timer.setName(name)
    logging.debug('startTimer %f %s', interval, function.func_name)
    timer.start()
    self._timers.append(timer)

  def killTimer(self, name):
    for timer in self._timers:
      if timer.getName() != name:
        continue
      timer.cancel()
      self._timers.remove(timer)
      break
    self.cleanupThreads()

  def cleanupThreads(self):
    self._threads = [t for t in self._threads if t.isAlive()]
    self._timers = [t for t in self._timers if t.isAlive()]

  def running(self):
    return not self._shutdown.isSet()

  def start(self):
    self.startThread('events', self._eventManager.eventDispatcher)

    logging.info('Starting up')
    self._eventManager.triggerEvent(events.STARTUP)

    if os.isatty(sys.stdin.fileno()):
      try:
        while self.running():
          if not select.select([sys.stdin], [], [], 0.2)[0]:
            continue
          sys.stdin.readline()
      except KeyboardInterrupt:
        self.shutdown()
        print
    else:
      self._shutdown.wait()

    logging.info('Shutting down')
    self._eventManager.triggerEvent(events.SHUTDOWN)

    for thread in self._threads:
      thread.join(10)

    for timer in self._timers:
      timer.cancel()

  def shutdown(self):
    self._shutdown.set()
