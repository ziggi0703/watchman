#!/usr/bin/env
import numpy
import os
import subprocess

import datetime

import xmltodict
from abc import ABCMeta, abstractmethod, abstractproperty
import logging
import cStringIO
from email.mime.text import MIMEText
import smtplib
import pandas as pd
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
        try:
            process = subprocess.Popen(self._command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        except OSError as e:
            _logger.warning('{} not available. Skip it and inform admin'.format(self._command))
            alerts.append((self._name, self._command, -999, 'Command not found.'))
            return

        out, error = process.communicate()
        rc = process.returncode

        own_alerts = self._check_output(rc, out, error)

        if len(own_alerts) > 0:
            alerts += own_alerts
        _logger.debug('Watch ends with {} alerts'.format(len(own_alerts)))

    def report_back(self):
        """
        Report back: execute the command and return the output of the command.

        :return: output of the command
        :rtype: str
        """
        _logger.info('Report from {} with command {}.'.format(self._name, self._command))
        process = subprocess.Popen(self._command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        out, error = process.communicate()

        rv = '{} reports on command {}:\n'.format(self._name, self._command)
        rv = rv + 'stdout:\n{}\n'.format(out) + \
             'stderr:\n{}\n'.format(error) + \
             'Return code: {}'.format(process.returncode)
        return rv

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
            return [(self._name, self.command, return_code, error)]


class QstatFGuard(Watchman):
    """
    Guard to control the qhost command output
    """
    def __init__(self, name):
        super(QstatFGuard, self).__init__(name)
        self.command = ['qstat', '-f', '-xml']  # trigger xml output

    def _check_output(self, return_code, out, error):
        alerts = []
        dict_from_xml = xmltodict.parse(out)
        df = pd.DataFrame(dict_from_xml['job_info']['queue_info']['Queue-List'])

        if 'state' in df:
            error_queues = []
            states = df['state'].dropna().unique()
            for state in states:
                state = str(state)
                if 'a' in state or 'u' in state or 'E' in state:
                    error_queues += (df[df['state'] == state]['name'].unique().tolist())

            for error_queue in error_queues:
                alerts.append((self._name, self._command, return_code, 'Queue {} is not available or set to ERROR.'.format(error_queue)))

        return alerts


class RadioOperator(object):
    """
    A RadioOperator sends the alert given by a Watchman via email to the admin.

    :param name: Name of the Instance
    :type name: str

    :param from_mail: Address from which the mails are send
    :type from_mail: str

    :param admin_mail: Address of the admin
    :type admin_mail: str
    """
    def __init__(self, name, from_mail, admin_mail):
        self._name = name
        self._from_mail = from_mail
        self._admin_mail = admin_mail
        self._host = os.getenv('HOST') if os.getenv('HOSTNAME') is None else os.getenv('HOSTNAME')

    def _create_message(self, alerts):
        """
        Create the message body of the alert email

        :param alerts: list with alerts
        :type alerts: list

        :return: message with from, to and subject
        :rtype: MIMEText
        """
        _logger.debug('Create message')
        mail = cStringIO.StringIO()
        mail.write('Dear Admin,\n\nat {} some errors occurred:\n\n'.format(datetime.
                                                                           datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        for alert in alerts:
            alert_message = 'Guard {} with command {} observed return state {} and error message {}.\n'.format(*alert)
            mail.write(alert_message)

        mail.write('\n\nPlease take your actions...Over and out.\n')

        message = MIMEText(mail.getvalue())
        message['From'] = self._from_mail
        message['To'] = self._admin_mail
        message['Subject'] = 'Errors on host {}'.format(self._host)

        return message

    def send_alerts(self, alerts):
        """
        Send an alerts to the admin via email.

        :param alerts: list of alerts
        :type alerts: list
        """
        _logger.info('Send alert message to {}'.format(self._admin_mail))
        message = self._create_message(alerts)

        self._send_mail(message)

    def _send_mail(self, message):
        """
        Send the mail
        :param message: actual message
        :type message: MIMEText
        """
        sender = smtplib.SMTP('localhost')
        sender.sendmail(message['From'], message['To'], message.as_string())
        sender.quit()

    def send_status_report(self, report):
        """
        Send the status report to the admin

        :param report: Some message which is send to the admin
        :type report: str
        """
        _logger.info('Send status report to {}'.format(self._admin_mail))

        report = 'Dear Admin,\n here comes the daily status report:\n\n:' + report

        message = MIMEText(report)
        message['From'] = '{}@{}'.format(self._name, self._host)
        message['To'] = self._admin_mail
        message['Subject'] = 'Status report from host {}'.format(self._host)

        self._send_mail(message)


