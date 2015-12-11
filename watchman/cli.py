#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

import click
import sys
import logging
from logging.handlers import SysLogHandler
import daemon
import time
import schedule

from watchman import __version__
from watchman.squad import PingGuard, RadioOperator, QstatFGuard

__author__ = "Michael Ziegler"
__copyright__ = "Michael Ziegler"
__license__ = "none"

_logger = logging.getLogger()
#_handler = SysLogHandler(address='/dev/log')


@click.command()
@click.option('--as_daemon', '-d', is_flag=True, default=False, help='Start watchman as a daemon.')
@click.option('--config', '-c', type=str, default='/usr/share/watchman_config/default.py', help='path to config file')
def cli(config, as_daemon):
    config = __load_config(config)
    if as_daemon:
        with daemon.DaemonContext():
            run(config)
    else:
        _stream_handler = logging.StreamHandler()
        _formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        _stream_handler.setFormatter(_formatter)
        _logger.addHandler(_stream_handler)
        run(config)


def __load_config(config):
    import imp
    config = imp.load_source('config', config)
    return config


def __send_status_report(rto, guards):
    """
    Send a status report of all guards to the admin

    :param rto: Actual RadioOperator
    :type rto: RadioOperator

    :param guards: list of guards
    :type guards: list
    """
    reports = '---\n'.join([guard.report_back for guard in guards])
    rto.send_status_report(reports)


def __start_the_watch(guards, rto):
    """
    Send the guards on watch and send possible alerts via the rto

    :param guards: list of guards
    :type guards: list

    :param rto: RadioOperator
    :type rto: RadioOperator
    """
    alerts = []
    for guard in guards:
        guard.guard(alerts)
    if len(alerts) > 0:
        rto.send_alerts(alerts)


def run(config):
    _handler = logging.FileHandler('/home/michael/logs/watchman.log')
    _formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)

    _logger.info('Start watchman')

    rto = RadioOperator('RTO1', admin_mail=config.admin_email)

    schedule.every(config.interval).seconds.do(__start_the_watch, config.guards, rto)
    schedule.every().day.at(config.status_time).do(__send_status_report, rto, config.guards)

    while True:
        schedule.run_pending()
        time.sleep(10)