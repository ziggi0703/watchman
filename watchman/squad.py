#!/usr/bin/env
import os
import subprocess

import datetime
from abc import ABCMeta, abstractmethod, abstractproperty
import logging
import cStringIO
from email.mime.text import MIMEText
import smtplib
_logger = logging.getLogger(__name__)


class Watchman(object):
    """
    A Watchman controls the output of a command
    and will give an alert if something is wrong.
    """
    __metaclass__ = ABCMeta

    def __init__(self, name):
        """
        Initialize a Watchman with a command

        :param name: name of the Watchman
        :type name: str
        """
        self._name = name
        self._command = None

    def __str__(self):
        return '<{}: {}>'.format(self.__class__, self._name)

    def guard(self, alerts):
        """
        Start the watch for the Watchman.

        :param alerts: watchman adds his alerts to it
        :type alerts: list
        """
        _logger.debug('{} starts the watch.'.format(self._name))
        _logger.debug('Check command: {}'.format(self._command))
        process = subprocess.Popen(self._command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, error = process.communicate()
        rc = process.returncode

        own_alerts = self._check_output(rc, out, error)

        if len(own_alerts) > 0:
            alerts.append(own_alerts)
        _logger.debug('Watch ends with {} alerts'.format(len(own_alerts)))

    @abstractmethod
    def _check_output(self, return_code, out, error):
        """
        Check the output of the command for errors.

        :param return_code: return code of the command
        :type return_code: int

        :param out: stdout of the command
        :type out: str

        :param error: stderr of the command
        :type error: str

        :return: list with alerts: [(guard_name, command, return_code, error message)]
        :rtype: list
        """
        raise NotImplementedError

    @property
    def command(self):
        """
        Get the command of the Watchman.

        :return: command
        :rtype: list
        """
        return self._command

    @command.setter
    def command(self, command):
        """
        Set the command.

        :param command: command to guard. Format: ['command', 'options1', 'option2', ...]
        :type command: list
        """
        self._command = command


class PingGuard(Watchman):
    """
    Guard watches the ping output to host.
    """
    def __init__(self, name, host):
        super(PingGuard, self).__init__(name)
        self.command = ['ping', '-c 4', host]

    def _check_output(self, return_code, out, error):
        if return_code == 0:
            return []
        else:
            return [self._name, self.command, return_code, error]


class RadioOperator(object):
    """
    A RadioOperator sends the alert given by a Watchman via email to the admin.
    """
    def __init__(self, name, admin_mail):
        self._name = name
        self._admin_mail = admin_mail
        self._host = os.getenv('HOST') if os.getenv('HOSTNAME') is None else os.getenv('HOSTNAME')

    def send_alerts(self, alerts):
        """
        Send an alerts to the admin via email.

        :param alerts: list of alerts
        :type alerts: list
        """
        mail = cStringIO.StringIO()
        mail.write('Dear Admin,\nat {} some errors occured:\n\n'.format(datetime.
                                                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        for alert in alerts:
            alert_message = 'Guard {} with command {} observed return state {} and error message {}.\n'.format(*alert)
            mail.write(alert_message)

        mail.write('\n\nPlease take your actions...\n')

        subject = 'Errors on host {}.'.format(self._host)

        _logger.info('Send alerts to admin {}'.format(self._admin_mail))

        message = MIMEText(mail.getvalue())
        message['From'] = '{}@{}'.format(self._name, self._host)
        message['To'] = self._admin_mail
        message['Subject'] = subject

        sender = smtplib.SMTP('localhost')
        sender.sendmail(message['From'], message['To'], message.as_string())
        sender.quit()
