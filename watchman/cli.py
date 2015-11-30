#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

import click
import sys
import logging
from logging.handlers import SysLogHandler
import daemon
import time

from watchman import __version__
from watchman.squad import PingGuard, RadioOperator

__author__ = "Michael Ziegler"
__copyright__ = "Michael Ziegler"
__license__ = "none"

_logger = logging.getLogger()
#_handler = SysLogHandler(address='/dev/log')


@click.command()
@click.option('--as_daemon', '-d', is_flag=True, default=False, help='Start watchman as a daemon.')
@click.option('--config', '-c', type=str, default=None, help='path to config file')
def cli(config, as_daemon):
    if as_daemon:
        with daemon.DaemonContext():
            run(config)
    else:
        run(config)


def run(config):
    _handler = logging.FileHandler('/home/michael/logs/watchman.log')
    _stream_handler = logging.StreamHandler()
    _formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    _stream_handler.setFormatter(_formatter)
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
    _logger.addHandler(_stream_handler)
    _logger.setLevel(logging.DEBUG)

    _logger.info('Start watchman')

    if config is None:
        _logger.info('Load default config.')
        with open('/home/michael/PycharmProjects/watchman/watchman/config/default.py', 'r') as config_file:
            config = eval(config_file.read())
    else:
        _logger.info('Load config: {}'.format(config))
        with open(config) as config_file:
            config = eval(config_file.read())

    _logger.info('Config: {}'.format(config))
    _logger.debug('Start ping guards')
    ping_guards = [PingGuard('PingGuard {}'.format(index), host=hostname)
                   for index, hostname in enumerate(config['hosts'])]
    rto = RadioOperator('RTO1', admin_mail=config['admin_mail'])
    while True:
        alerts = []
        _logger.debug('PingGuards checking again.')
        for guard in ping_guards:
            guard.guard(alerts)

        if len(alerts) > 0:
            rto.send_alerts(alerts)

        time.sleep(config['sleep'])
