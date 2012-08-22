#!/usr/bin/env python
#
# Copyright 2011. All Rights Reserved.

"""Example bot."""

__author__ = 'schrepfer'

import logging
import optparse
import os
import sys

from lib import bot
from lib import config
from lib import events


class ExampleBot(bot.Bot):

  def __init__(self, options):
    self._options = options
    super(ExampleBot, self).__init__()

  @property
  def options(self):
    return self._options

  @events.event(events.READ)
  def onRead(self, line):
    if self.options.display:
      sys.stdout.write(line + '\n')
    super(ExampleBot, self).onRead(line)

  def send(self, commands, splitlines=True, escape=True):
    if splitlines:
      commands = commands.split(';')
    else:
      commands = [commands]
    for command in commands:
      if not command:
        continue
      self.engine.eventManager.triggerEvent(
          events.SEND, ('!' if escape else '') + command)

  @events.event(events.STARTUP)
  def onStartup(self):
    self.connection.connect(self.options.address, self.options.port)
    return True

  @events.event(events.CONNECT)
  def onConnect(self):
    self.send(self.options.username, escape=False)
    self.send(self.options.password, escape=False)
    return True

  @events.event(events.DISCONNECT)
  def onDisconnect(self):
    self.engine.startTimer(
      'reconnect', 5.0, self.connection.connect, self.options.address,
      self.options.port)
    return True

  @bot.trigger(r'^([A-Z][a-z]+) tells you \'')
  def gotTell(self, match):
    self.send('tell %s I bot!' % match[1].lower())


def defineFlags():
  parser = optparse.OptionParser(version='%prog v0.0', description=__doc__)
  # See: http://docs.python.org/library/optparse.html
  parser.add_option(
      '-v', '--verbosity',
      action='store',
      default=20,
      dest='verbosity',
      metavar='LEVEL',
      type='int',
      help='the logging verbosity')
  parser.add_option(
      '-f', '--config',
      action='store',
      default='configs/settings.cfg',
      dest='config',
      metavar='FILE',
      type='str',
      help='path to the booth config file')
  parser.add_option(
      '-d', '--display',
      action='store_true',
      default=False,
      dest='display',
      help='display mud output to screen')
  return parser.parse_args()


def main(options, args):
  try:
    cfg = config.readConfig(options.config)
  except AssertionError, e:
    logging.error('%s', e)
    return os.EX_DATAERR
  options.address = cfg.get('server', 'address')
  options.port = int(cfg.get('server', 'port'))
  options.username = cfg.get('character', 'name')
  options.password = cfg.get('character', 'password')
  inst = ExampleBot(options)
  inst.start()
  return os.EX_OK


if __name__ == '__main__':
  options, args = defineFlags()
  logging.basicConfig(
      level=options.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(options, args))

