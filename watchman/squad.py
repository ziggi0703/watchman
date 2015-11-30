#!/usr/bin/env
import subprocess

from abc import ABCMeta, abstractmethod, abstractproperty
import logging
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

    def guard(self):
        """
        Start the watch for the Watchman.
        """
        _logger.info('{} starts the watch.'.format(self._name))
        _logger.info('Check command: {}'.format(self._command))
        process = subprocess.Popen(self._command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, error = process.communicate()
        rc = process.returncode

        self._check_output(rc, out, error)


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
            return True
        else:
            return


class RadioOperator(object):
    """
    A RadioOperator sends the alert given by a Watchman via email to the admin.
    """
    def __init__(self):
        pass