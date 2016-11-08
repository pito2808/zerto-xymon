#!/usr/bin/env python

# import jsonpath-0.54

import os
import re
import logging
import urllib2
import urllib
import sys
import re
import base64
import ssl
import time
import datetime
from urlparse import urlparse
from zertoconfig import *
#from events import *
import simplejson as json

log = Logger()

class ZertoSessionException(Exception):
    ''' use for raise exeception '''

    def __init__(self,msg):
        self.msg = msg 

class ZertoSession():
    ''' class get zvm parmaeters, connect , manage
        zerto session, retrieve info'''

    def __init__(self, zvm):
        self.zvm_name = zvm.zvm_name
        self.zvm_user = zvm.zvm_user
        self.zvm_pwd  = zvm.zvm_pwd
        self.zvm_ip   = zvm.zvm_ip
        self.zvm_port = zvm.zvm_port
        self.zvm_url = zvm.zvm_url
        self.sessiondir = os.getenv('BBCLIENTLOGS','/tmp')
        self.zertosession = 'x-zerto-session' + self.zvm_ip +  \
                                            '_' + self.zvm_port
        self.sessionfile = self.sessiondir + '/' + self.zertosession
        self.customers_opts = ""
  
    def addCustomersOpts(self,customers_opts):
        self.customers_opts = customers_opts

    def _file_is_empty(self, path):
        try:
            s = os.stat(path)
            if s.st_size == 0:
                return True 
        except OSError as e:
            return True 
        return False 

    def retrieve_session(self):
        ''' query zerto session '''
        req = urllib2.Request(self.zvm_url + '/v1/session/add')
        # check authentication
        try:
            handle = urllib2.urlopen(req)
        except IOError, e:
            # here we *want* to fail
            pass
            log.info(self.zvm_url +
                    "This page is protected by authentication.")
        else:
            # If we don't fail then the page isn't protected
            msg = "This page isn't protected by authentication."
            log.error(msg, 1)
            raise ZertoSessionException(msg)

        base64string = base64.encodestring(
                        '%s:%s' % (self.zvm_user, self.zvm_pwd))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)
        req.add_header("Content-Type", "application/json")
        req.add_header("Content-Length", 0)
        req.add_data(urllib.urlencode(''))
        print req.get_method()
        try:
            handle = urllib2.urlopen(req,)
        except IOError, e:
            # here we shouldn't fail if the username/password is right
            msg = "It looks like the username or password is wrong."
            print e
            log.error(msg,1)
            raise ZertoSessionException(msg)            

        zerto_session = handle.info().getheader('x-zerto-session')
        print "zerto sessio %s end" % zerto_session
        #write session hash to file
        print (" sessoin file %s ") % self.sessionfile
        #if not os.path.exists(self.sessionfile) :
        #    mkdir(self.sessionfile)
        with open(self.sessionfile,'w+') as FILE:
            FILE.write(zerto_session)

    def connect(self):
        ''' connect to zvm and manage zerto session '''
        
        # create session zerto if not exists or empty
        print "path %s " + self.sessionfile
        if self._file_is_empty(self.sessionfile): 
            # retrieve zerto session and write to file
            try:
                self.retrieve_session()
            except ZertoSessionException:
                log.error('skipping this zvm '+instance.zvm_ip)
                raise
        else:
            # check zerto sessionfile timestamp
            # should be lower than 30 minutes
            file_timestamp = os.stat(self.sessionfile).st_mtime
            now = int(time.time())
            # 30 minutes lag
            lag =  30 * 60 
            diff = now - file_timestamp 
            if diff >= lag :
                log.info('x-session file too old, getting a new one')
                # retrieve zerto session and write to file
                try:
                    self.retrieve_session()
                except ZertoSessionException:
                    log.error('skipping this zvm '+instance.zvm_ip)
                    raise
                 
    def get_json(self, uri):
        ''' call restful GET api, return format is json'''
        zerto_url = self.zvm_url + '/v1/' + uri  
        log.info("zerto url called : " + zerto_url)
        
        # get zerto session from file
        with open(self.sessionfile,'r') as FILE:
            zerto_session = FILE.readline()

        # get value
        req = urllib2.Request(zerto_url)
        # add headers
        req.add_header("x-zerto-session", zerto_session)
        req.add_header("Content-Type", "application/json")
        handle = urllib2.urlopen(req,)
        json_page = handle.read()
        return json_page


def monitor(zvm, *argv):
    print "zvm %s" % zvm
    print "monitor ip %s" % zvm.zvm_ip
    zerto = ZertoSession(zvm)
    zerto.addCustomersOpts(*argv)
    try:
        zerto.connect()
    except ZertoSessionException:
        log.error('skipping this zvm '+instance.zvm_ip)
        raise 
    return zerto


def map_search(listOfDict, key,arg_pattern):
    '''
    json get result list of Dict. this function get index following
    pattern on key of dictionary
    use mostly to get vps
    return a list of tuples
    '''
    listOfOccurances = []
    pattern = re.compile(arg_pattern, re.IGNORECASE)
    for i , dic in enumerate(listOfDict):
        log.info("dic %s %s" % (key,dic[key]),0) 
        log.info(" lenght %s  "% len(dic[key]),0)
        if len(dic[key]) >= 1 and isinstance(dic[key], list) :
            for x in dic[key]:  
                log.info( "x ", x['Name'])
                if pattern.match(x['Name']) :
                    tup = (i, x['Name'])
                    listOfOccurances.append(tup)
        if not isinstance(dic[key], list):
            tup = ()
            if pattern.match(dic[key]):
                tup = (i, dic[key])
                listOfOccurances.append(tup)
    return listOfOccurances

def reformulate(cust):
    '''
    cust is dictionary, parse et add zogname or vpgs occurance
    per example:
    xymoncustomer = {'ip': '172.20.42.157',
                    'hostname': 'agabs-li001v',
                    'pattern': 'ZERTO:NOZOG:AGA'}
    to
    {'ip': '172.20.42.157', 'hostname': 'agabs-li001v', 'Vpgs': 'AGA',
            'ZorgName': 'AGA', 'pattern': 'ZERTO:NOZOG:AGA'}
    '''
    print "cust hostname ", cust['hostname']
    print "cust pattern", cust['pattern']
    nozog = re.compile('^ZERTO:.*(NOZOG:[A-Za-z0-9|]+):?.*', re.VERBOSE)
    # get NOZOG
    nozog = re.compile('^ZERTO:.*(NOZOG:[A-Za-z0-9|]+):?.*', re.VERBOSE)
    if nozog.match(cust['pattern']):
        matchObjectNozog = nozog.match(cust['pattern'])
        print "matchObjectNozog found :", matchObjectNozog.group(1)
        vpgs = matchObjectNozog.group(1).replace('NOZOG:','')
        cust['Vpgs'] =  vpgs
	print "********** VpGS : %s *************" % vpgs
    # get ZOG
    zog = re.compile('^ZERTO:.*(ZOG:[A-Za-z0-9|_-]+):?.*', re.VERBOSE)
    if zog.match(cust['pattern']):
        matchObjectZog = zog.match(cust['pattern'])
        print "matchObject ZOG found :", matchObjectZog.group(1)
        zorgName = matchObjectZog.group(1).replace('ZOG:', '')
        cust['ZorgName'] = zorgName
    return cust


def jsonDateToString(jsondate):
    '''
    transform json date (epoch in milliseonds) to readable date
    '''
    pattern = re.compile('.+? (\d+) ([+-]\d{,4})? ', re.X)
    if pattern.match(jsondate):
        pass
    else:
        log.error("%r no match " % jsondate,1)
    matchObj= pattern.match(jsondate)
    epoch_milliseconds = matchObj.group(1)
    epoch = int(epoch_milliseconds)/1000
    time_zone = matchObj.group(2)
    readableDate = time.strftime("%a  %b %d %Y %H:%M:%S " + time_zone,
                        time.localtime(epoch))
    log.info("%r convert to readable date %r" % (epoch, readableDate),0)
    #print "readable Date : ", readableDate
    return readableDate


if __name__ == "__main__":
    customersZerto =  [{'ip': '172.20.42.157', 'hostname': 'agabs-li001v', 'pattern': 'ZERTO:NOZOG:AGA'}, {'ip': '172.23.1.191', 'hostname': 'stalu-dc01', 'pattern': 'ZERTO:NOZOG:SMW:AGA'}]
    for instance in AllZvm.instances:
        print "going to monitor ZVM"
        print "ip %s" % instance.zvm_ip
        #zerto = ZertoSession(instance)
        #try:
        #    zerto.connect()
        #except ZertoSessionException:
        #    log.error('skipping this zvm '+instance.zvm_ip)
        #    continue
        try:
            zerto = monitor(instance, customersZerto)
        except:
            log.error('skipping this zvm '+instance.zvm_ip,1)
            continue

        today = datetime.date.today()
        today_date = today.isoformat()
        #filtered_events = "events?startDate=" + "2014-07-11" + \
        #    "&endDate=" + today_date
        filtered_events = "events?startDate=" + today_date + \
            "&endDate=" + today_date
        
        #events_page = zerto.get_json('events')
        log.info("uri used for events :"+filtered_events)
        try:
            events_page = zerto.get_json(filtered_events)
        except :
            print  " erreur urlHTTPError ", sys.exc_info()[0] 
        print json.dumps(events_page, sort_keys = False, indent = 4)
        # vpgs
        try:
            vpgs_page = zerto.get_json('vpgs')
        except :
            print  " erreur urlHTTPError ", sys.exc_info()[0] 
        print json.dumps(vpgs_page, sort_keys = True, indent = 4,
                                separators = (',', ':'))
        print vpgs_page
        decoded = json.loads(vpgs_page)
        print "DECODED: ", decoded
        print "INDENT: ", json.dumps(decoded, indent = 4)

        print "customers_opts: ", zerto.customers_opts
        # vras
        switch_vras = False
        if switch_vras == True:
            try:
                vras_page = zerto.get_json('vras')
            except :
                print  " erreur urlHTTPError ", sys.exc_info()[0]
            print json.dumps(vras_page, sort_keys = True, indent = 4,
                                    separators = (',', ':'))
            print vras_page
            decoded = json.loads(vras_page)
            print "DECODED: ", decoded
            print "INDENT: ", json.dumps(decoded, indent = 4)
    
            print "customers_opts: ", zerto.customers_opts
    
        
        # vpgs
        switch_vpgs = False 
        if switch_vpgs == True:
            try:
                vpgs_page = zerto.get_json('vpgs')
            except :
                print  " erreur urlHTTPError ", sys.exc_info()[0]
            print json.dumps(vpgs_page, sort_keys = True, indent = 4,
                                    separators = (',', ':'))
            print vpgs_page
            decoded = json.loads(vpgs_page)
            print "DECODED: ", decoded
            print "INDENT: ", json.dumps(decoded, indent = 4)
    
            print "customers_opts: ", zerto.customers_opts
    
        
        # vms
        switch_vms = True 
        if switch_vms == True:
            try:
                vms_page = zerto.get_json('vms')
            except :
                print  " erreur urlHTTPError ", sys.exc_info()[0]
            print json.dumps(vms_page, sort_keys = True, indent = 4,
                                    separators = (',', ':'))
            print vms_page
            decoded = json.loads(vms_page)
            print "DECODED: ", decoded
            print "INDENT: ", json.dumps(decoded, indent = 4)
    
            print "customers_opts: ", zerto.customers_opts
