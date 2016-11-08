#!/usr/bin/env python
#-------------------------------------------------- 
# usage: zerto.py 
#       executed by hobbit
# 
# purpose: Monitor Zerto vms and vps
# requirements:
#   - read README file
#   - require module PyAML
#
# comments:
#   - never tested with ZORG
#   - use zertocustomers.yaml to filter per customers
#
# authors version:
#   georges.chaleunsinh@colt.net 2014 december
#
# TODO:
#   put some CHARTS
#
#-------------------------------------------------- 

import os, re
import subprocess
import shlex
import string
#from zertoconfig import *
import zertoconfig
from zertomonitor import *
from zertoevents import Events
from zertovpgs import Vpgs
from zertovms import Vms

log = Logger()

def parseXymonConf():
    '''
    parse ALL file 
    return list of get hostname, ip and zerto conf
    '''
    cmd = '/opt/xymon/server/bin/xymongrep --noextras ZERTO*'
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    res = proc.communicate()[0]
    log.info( "result %s " % res,1)
    res = res.rstrip()
    servers = res.split('\n')
    print servers
    return servers

def getdict(listservers):
    '''
    transform list 172.20.42.157 agabs-li001v # ZERTO:NOZOG:AGA
    to dict 
    '''
    keys = ['ip','hostname','pattern']
    dictList = []
    for l in listservers:
        pass
	print "*********** l:%s ****************" % l
        matchObj = re.match(r'^(.+)?\s(.+)?\s#\s(.+)$', l)
        dictList.append(dict(zip(keys,[matchObj.group(1),
                                matchObj.group(2),
                                matchObj.group(3)]))) 
	print "*********** DictList:%s ****************" % dictList,1
    log.info( "customersZerto %s" % dictList, 1)
    return dictList

if __name__ == "__main__":
    print "test"
    srvs = parseXymonConf()    
    customersZerto = getdict(srvs)
    log.info( "customersZerto main %s" % customersZerto)
    #pass customers parameters to monitoring
    log.info("enter loop AllZvm.instances ", 1)
    log.info("AllZvm.instances:  %r" % AllZvm.instances ,1)
    log.info("Zinstances:  %r" % zertoconfig.Zinstances ,1)
    print " zertoconfig.Zinstances %r " % Zinstances
    for instance in AllZvm.instances:
        log.info("inside loop AllZvm.instances", 1)
        try:
            zerto = monitor(instance, customersZerto)
        except:
            log.error('skipping this zvm '+instance.zvm_ip,1)
            continue
        log.info("using zvm ip %r " %  instance.zvm_ip) 
        events = Events(zerto)     
        events.check(dict_cust = customersZerto)
        
        # VPGS monitoring 
        vpgs = Vpgs(zerto)
        vpgs.check(dict_cust = customersZerto)

        # VMS monitoring 
        vms = Vms(zerto)
        vms.check(dict_cust = customersZerto)
