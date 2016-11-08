#!/usr/bin/env python

import os
from zertoconfig import *
#import ConfigParser

#customersConfig = ConfigParser.SafeConfigParser()
#customersConfig.read('zertocustomers.ini')
    
#if __name__ == "__main__":
#    print customersConfig.sections()
#    print customersConfig.get('default', 'lag')

import yaml
import pprint



log = Logger()

cfgbase = os.getenv('XYMONSERVERROOT', '/data/xymon')
log.info("current path for execution %r, base %r" % (os.getcwd(),cfgbase),1)
cfgfile = 'zertocustomers.yaml'
cfgdir = cfgbase + "/server/ext/zerto/"
cfglocation = cfgdir + cfgfile

with open(cfglocation, 'r') as f:
    custcfg = yaml.load(f)

def get_index(sequence, hostname):
    '''
    return index of hostname from list of dictionary
    otherwise return 0 the default
    '''
    try:
        return next( index for (index,d) in enumerate(sequence) \
            if d.keys()[0] == hostname)
    except StopIteration:
        return 0

def getwithin(tcustcfg, thostname ):
    '''
    get WITHIN value from zertocustomers yaml
    this value limit the interval to check zerto events
    '''
    tindex = get_index(tcustcfg,thostname)
    #print " getwithin t index %r hostname %r" % (tindex, thostname)
    try:
         return tcustcfg[tindex][thostname]['WITHIN']
    except (TypeError ,KeyError):
         #return tcustcfg[0]['default']['WITHIN']
         return tcustcfg[get_index(custcfg,'default')]['default']['WITHIN']


def getlabel_vpgprio(tcustcfg, priority):
    '''
    get VPG PRIORITY label from zertocustomers yaml
    '''
    #return tcustcfg[0]['default']['vpg_priority'][priority]
    index = get_index(custcfg,'default')
    return tcustcfg[index]['default']['vpg_priority'][priority]

def getlabel_vpgstatus(tcustcfg, status):
    '''
    get VPG status label from zertocustomers yaml file
    '''
    try:
        index = get_index(custcfg,'default')
        #return tcustcfg[0]['default']['vpg_status'][status]['label']
        return tcustcfg[index]['default']['vpg_status'][status]['label']
    except KeyError:
        return "Error: value %r is not listed on conf file %r" % (status,
                                                            cfglocation)

def getlevel_vpgstatus(tcustcfg, status):
    '''
    get VPG status level from zertocustomers yaml file
    '''
    try:
        index = get_index(custcfg,'default')
        return tcustcfg[index]['default']['vpg_status'][status]['level']
    except KeyError:
        return 3

def getlist_skipvpgs(tcustcfg,thostname):
    '''
    get list of vpgs to skiped from monitoring
    '''
    tindex = get_index(tcustcfg,thostname)
    #if tindex == 0:
    #    return None
    #else:
    try:
        return tcustcfg[tindex][thostname]['skip_vpg_check']
    except:
        return None

def getrpo(tcustcfg, thostname ):
    '''
    get rpo value from zertocustomers yaml
    this value limit the interval to check zerto events
    '''
    tindex = get_index(tcustcfg,thostname)
    try:
        return tcustcfg[tindex][thostname]['rpo']
    except (TypeError, KeyError):
        #return tcustcfg[0]['default']['rpo']
        return tcustcfg[get_index(custcfg,'default')]['default']['rpo']


if __name__ == "__main__":
   # print xymoncusts
    #for project in yaml.load_all(open("zertocustomers.yaml")):
    #    pprint.pprint(project)
  
    print custcfg 
    print custcfg[0]
    print "custcfg 3 %r " % custcfg[get_index(custcfg,'default')]['default']['toto_thres']['warning']
    print "get_index ",get_index(custcfg, 'stalu-dc01')
    print custcfg[get_index(custcfg, 'stalu-dc01')]['stalu-dc01']
    print "getwithin %r " % getwithin(custcfg,'agabs-li001v')
    print "getwithin %r " % getwithin(custcfg,'stalu-dc01')
 

    print " testo %r " % custcfg[get_index(custcfg,'default')]['default']['toto_thres']['warning']
    print " testa rpo %r " % custcfg[get_index(custcfg,'default')]['default']['rpo']
    
    # get vpg_status
    #print custcfg[get_index(custcfg,'default')]['default']['vpg_status'][16]['level']
    #print custcfg[get_index(custcfg,'default')]['default']['vpg_status'][16]['label']
    #print getlabel_vpgstatus(custcfg, 3)
    #print getlevel_vpgstatus(custcfg, 3)
    # get vpg priority
    #print  getlabel_vpgprio(custcfg, 1) 


    # get skip vpg 
    # print custcfg[get_index(custcfg,'agabs-li001v')]['agabs-li001v']['skip_vpg_check']
    print getlist_skipvpgs(custcfg,'agabs-li001v')
    print getrpo(custcfg, 'stalu-dc01')
    print getlist_skipvpgs(custcfg, 'stalu-dc011')
