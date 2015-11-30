#!/usr/bin/env python
from watchman.squad import PingGuard, QstatFGuard

# define your list of guards you want send to watch
#
# A PingGuard pings the host and checks the return code of the ping command.
# The QstatFGuard greps the qstat -f command for some unavailable queues.
guards = [PingGuard('PingGuard 001', host='ekpblus001'),
          PingGuard('PingGuard 002', host='ekpblus002'),
          PingGuard('PingGuard 003', host='ekpblus003'),
          PingGuard('PingGuard 007', host='ekpblus007'),
          QstatFGuard('QStatFGuard')]

# EMail address of the admin who will be noticed by errors
admin_email = 'michael.ziegler2@kit.edu'

# defines the waiting time between two checks (in seconds)
sleep = 600
