import urllib2
import urllib
import sys
import re
import base64
import ssl
import datetime
import json

from urlparse import urlparse
#from zertoconfig import AllZvm
from zertoconfig import * 
from zertomonitor import * 
from xymon import *
import zertocustomers

log = Logger()

event_cell = '''\
+++++++++++++++++++++++++++++++++++++++++
vpg: {vpg}
====
zorg organization: {zorg}
==================
date: {date}
=====
eventId: {id}
========
username: {user}
=========
site: {site}
=====
description: 
============
{desc}
completion status: {status}
==================

'''


class Events(object):
    '''
    monitoring events zerto , argument zerto instance
    '''
    
    def __init__(self,zerto):
        self.today_date = datetime.date.today().isoformat()     
        #self.begin_date = '2014-10-7'
        self.filtered_events = "events?startDate=" + self.today_date + \
                                "&endDate=" + self.today_date
        #self.filtered_events = "events?startDate=" + self.begin_date + \
        #                        "&endDate=" + self.today_date
        log.info("uri used for events :" + self.filtered_events, 0) 
        self.zerto = zerto

    def check(self, **kwargs):
        '''
          get events values in json format  

        '''
        log.info("uri used for events :%r" % self.filtered_events)
        try:
            events_page = self.zerto.get_json(self.filtered_events) 
        except :
            log.error (" get urlHTTPError for events_pages",0)
        decoded = json.loads(events_page)
        #print "INDENT: ", json.dumps(decoded, indent = 4)
        #print "DECODED: ", decoded
        # decoded has listofdict structure
        log.info( " list of cust on hobbit %r " % kwargs['dict_cust'],0) 
        # get custcfg from zertocustomers module
        custcfg = zertocustomers.custcfg
        for customer in kwargs['dict_cust']:
            customer = reformulate(customer)
            log.info(' customer to check %r' % customer, 0)
            # instance hobbit per customer
            hobbitState =  HobbitState(customer['hostname'])
            if customer.has_key('Vpgs'):
                vpgsindex = map_search( decoded ,'Vpgs', customer['Vpgs'])
                #print "vpgsindex : ", vpgsindex
                log.info("vgsindex %r " % vpgsindex, 0)
                within = zertocustomers.getwithin(custcfg, customer['hostname'])
                log.info("Customer %r has within val %r " % \
                            (customer['hostname'], within ),0)
                page4xymon, eventstatus = self.parseEvents(vpgsindex, 
                                                           decoded,
                                                           custcfg,
                                                           customer['hostname'])
                hobbitState.comparestatus(eventstatus)
                # not to do let page empty
                if not page4xymon:
                   page4xymon = "NO NEW EVENTS TRIGGERED"
                hobbitState.sendtoxymon('zerto_events',
                                            'zerto events monitoring',
                                            page4xymon)
                log.info( "page4xymon %r customer %r" % (page4xymon, 
                                                    customer['hostname']), 0)


    def analyzeEvent(self, WITHIN= 10*60 ,**kwargs):
        '''
        check each event and trigger alert if need
        only event under 10 minutes is examinded by default
        '''
        thisStatus = GlobalStatus()
        # extract epoch in second
        epoch = kwargs['epoch']
        pattern = re.compile('.+? (\d+) ([+-]\d{,4})? ', re.X)
        if pattern.match(epoch):
            pass
        else:
            log.error("%r no match " % jsondate,1)
        matchObj= pattern.match(epoch)
        epoch_milliseconds = matchObj.group(1)
        epoch = int(epoch_milliseconds)/1000
        # compare if event is not older than WITHIN seconds
        current_epoch = int(time.time())
        if ( current_epoch - epoch ) < WITHIN:
            log.info( "going to analayze this event cause within ",
                    current_epoch - epoch )
            desc_return = self.getStatus( kwargs['description'], 
                                    'Alert turned on', 
                                    1)
            thisStatus.cmpstatus(desc_return)
            completion_return = self.getStatus( kwargs['eventcompletion'], 
                                                            'False', 1)
            thisStatus.cmpstatus(completion_return)
        return thisStatus.state

    def getStatus(self, val_to_check, pattern, int_return):
        prog = re.compile(pattern)
        if prog.match(str(val_to_check)):
            return int_return
        else:
            return 0


    def parseEvents(self,listOfTuples, listOfDict,custcfg, xymoncust):
        '''
        return list contained blocks of values per vpg or
        zorg
        '''

        thisStatus = GlobalStatus()
        events_page = "" 
        for i in listOfTuples:
            assert isinstance((i[0]), int), "index is not an interger: %r " % i[0]
            index = i[0]
            vpg = i[1]
            eventId =  listOfDict[index]['EventIdentifier']
            description =  listOfDict[index]['Description']
            epoch = listOfDict[index]['OccurredOn']
            # transform epoch to readable date
            timestamp = jsonDateToString(epoch)
            siteName =  listOfDict[index]['SiteName']
            username =  listOfDict[index]['UserName']
            zorgName = listOfDict[index]['ZorgName']
            eventcompletion =  listOfDict[index]['EventCompletedSuccessfully']
            vpg_cell = '''
            vpg: {vpg}
            eventId: {id}
            description: {desc}
            '''.format(vpg = vpg, id = eventId , desc = description)
            #events_page = events_page + vpg_cell 
            within = zertocustomers.getwithin(custcfg, xymoncust)
            
            # trigger alert or not
            return_event = self.analyzeEvent( epoch = epoch,
                            description = description,
                            eventcompletion = eventcompletion ,WITHIN = within)
            thisStatus.cmpstatus(return_event)
            if return_event > 0 :
                vpg = vpg + " " + Constants.BUTTONLVL.get(return_event)
                log.info("new vpg %r" % vpg,0)

            #print vpg_cell
            this_eventcell = event_cell.format(vpg = vpg, 
                                               date = timestamp,
                                               id = eventId ,
                                               site = siteName,
                                               desc = description,
                                               timestamp = timestamp,
                                               user = username,
                                               status = eventcompletion,
                                               zorg = zorgName)
            events_page = events_page + this_eventcell
        log.info("events_page: ", events_page)
        return events_page , thisStatus.state 

 

if __name__ == "__main__":
    pass
