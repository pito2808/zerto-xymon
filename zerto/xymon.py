#!/usr/bin/env python




import os, re
import syslog
import subprocess
import shlex
import socket
from zertoconfig import *
from zertomonitor import *

log = Logger()

class Constants:
    BUTTONLVL = {
                 -1: '&blue',
                 0:'&green',
                 1:'&yellow',
                 2:'&red',
                 3:'&blue'}
    BUTTONLVL2 = {
                  -1:'blue',
                  0:'green',
                  1:'yellow',
                  2:'red',
                  3:'blue'}

class GlobalStatus:
    def __init__(self, state=0):
        self.state = state

    def cmpstatus(self,state_tmp):
        if self.state > int(state_tmp):
            return self.state
        else:
            self.state = int(state_tmp)
            return self.state

class HobbitState:
    def __init__(self, hostdisplay = socket.gethostname(), state=0):
        self.state = state
        self.finalstate = state
        self.hostname   =  hostdisplay

    def comparestatus(self,state):
        if self.state >= state:
            return self.state
        else:
            self.state = state
            self.finalstate = state
            return self.state

    def sendtoxymon(self, testname, title, mesg):
        #hostname = socket.gethostname()
        hostname = self.hostname
        color = Constants.BUTTONLVL2.get(self.finalstate)
        date = subprocess.Popen(['date'],stdout=subprocess.PIPE).communicate()[0]
        date = date.rstrip()
        line = "status %s.%s %s %s - %s \n\n %s" % (hostname,
                                                    testname,
                                                    color,
                                                    date,
                                                    title,mesg)
        #print "sendtoxymon line \n%s" % line
        log.info("sendtoxymon line \n %r " % line)
        #print os.getenv("BB",'BBenv')
        #print os.getenv("BBDISP", 'BBDISP env not found')
        cmdline = "%s %s \"%s\"" % (os.getenv("BB",'BBenv'),
                                    os.getenv("BBDISP",'BBDISPenv'),
                                    line)
        #print "cmdline %s " % cmdline
        log.info("xymon.py cmdline %r " % cmdline, 0)
        os.system(cmdline)


