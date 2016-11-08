import urllib2
import urllib
import sys
import re
import base64
import ssl
import datetime
import json

from operator import itemgetter
from urlparse import urlparse
#from zertoconfig import AllZvm
from zertoconfig import * 
from zertomonitor import * 
from xymon import *
import zertocustomers

log = Logger()


vpg_headers = '''\

<table BORDER=1 CELLPADDING=5>
  <tr>
    <th>name</th>
    <th>hobbitstate</th>
    <th>Priority</th>       
    <th>#VMs</th>
    <th>Source Site</th>
    <th>Target Site</th>
    <th>Actual RPO</th>
    <th>Status</th>
    <th>Last Test</th>
    <th>Comment</th>
  </tr>

'''

vpg_close_headers = '''\
</table>
'''

vpg_row_template = '''\
<tr>
    <td>  {vpg} </td>
    <td>  {hobbitstate} </td>
    <td>  {priority} </td>
    <td>  {vms} </td>
    <td>  {sourcesite} </td>
    <td>  {targetsite} </td>
    <td>  {actual_rpo} </td>
    <td>  {status} </td>
    <td>  {last_test} </td>
    <td>  {comment} </td>
</tr>
'''


class Vpgs(object):
    '''
    monitoring vps zerto , argument zerto instance
    '''
    
    def __init__(self,zerto):
        self.zerto = zerto

    def check(self, **kwargs):
        '''
          get vps values in json format  

        '''
        self.uri = 'vpgs'
        log.info("uri used for vpgs :%r" % self.uri)
        try:
            vpgs_page = self.zerto.get_json(self.uri) 
        except :
            log.error (" get urlHTTPError for vpgs_pages",1)
        decoded = json.loads(vpgs_page)
        print "INDENT: ", json.dumps(decoded, indent = 4)
        print "DECODED: ", decoded
        # decoded has listofdict structure
        log.info( " list of cust on hobbit %r " % kwargs['dict_cust'],1) 
        # get custcfg from zertocustomers module
        custcfg = zertocustomers.custcfg
        for customer in kwargs['dict_cust']:
            customer = reformulate(customer)
            log.info(' customer to check %r' % customer, 1)
            # instance hobbit per customer
            hobbitState =  HobbitState(customer['hostname'])
            if customer.has_key('Vpgs'):
                #vpgsindex = map_search( decoded ,'Name', customer['Vpgs'])
                vpgsindex = map_search( decoded ,'VpgName', customer['Vpgs'])
                # sort vpgsindex by name
                vpgsindex = sorted(vpgsindex, key = itemgetter(1))
                #print "vpgsindex : ", vpgsindex
                log.info("vpgsindex : %r" % vpgsindex, 1)
                page4xymon, vpgsstatus = self.parseVpgs(vpgsindex, 
                                                           decoded,
                                                           custcfg,
                                                           customer['hostname'])
                hobbitState.comparestatus(vpgsstatus)
                hobbitState.sendtoxymon('zerto_vpgs',
                                            'zerto vpgs monitoring',
                                            page4xymon)
                log.info( "page4xymon %r customer %r" % (page4xymon, 
                                                    customer['hostname']), 0)


    def analyzeVpg(self, rpo_thresh = 300, **kwargs):
        '''
        check each vpg and trigger alert if need
        return level, label
        '''
        #rpo_thresh = 300
        custcfg    = kwargs['custcfg']
        vpgstatus  = kwargs['vpgstatus']
        rpo        = kwargs['rpo'] 
        rpo_thresh = rpo_thresh 

        listcomment = [] 
        thisStatus = GlobalStatus()
        label = zertocustomers.getlabel_vpgstatus(custcfg, vpgstatus)
        level = zertocustomers.getlevel_vpgstatus(custcfg, vpgstatus)
       
        thisStatus.cmpstatus(level)
        thislabel = label
        log.info(" level %r and label %r vpgstatus %r " % (level,label,
                                                            vpgstatus))
        # rpo check 
        log.info("VPG rpo %r rpo_thresh %r thisStatus.state %r" % (rpo, 
                                                rpo_thresh, thisStatus.state))
        if rpo >= rpo_thresh :
            thisStatus.cmpstatus(1)
            listcomment.append('rpo is higher than '+str(rpo_thresh)+' seconds')
        if not isinstance(rpo,(int, long)):
            thisStatus.cmpstatus(1)
            listcomment.append('rpo is not type integer or long')
        log.info("VPG thisStatus.state %r" % thisStatus.state)    
        return thisStatus.state, thislabel, listcomment

    def getStatus(self, val_to_check, pattern, int_return):
        prog = re.compile(pattern)
        if prog.match(str(val_to_check)):
            return int_return
        else:
            return 0


    def parseVpgs(self,listOfTuples, listOfDict,custcfg, xymoncust):
        '''
        return list contained blocks of values per vpg or
        zorg
        '''

        thisStatus = GlobalStatus()
        vpgs_page = "" 
        # list vpgs  to skip
        listskips = zertocustomers.getlist_skipvpgs(custcfg, xymoncust) 
        log.info("list vpgs to skipped %r %r " % (xymoncust,listskips))
        for i in listOfTuples:
            assert isinstance((i[0]), int),"index is not an integer: %r " % i[0]
            index = i[0]
            vpg = i[1]

            priority =  listOfDict[index]['Priority']
            priority =  zertocustomers.getlabel_vpgprio(custcfg,priority)
            vms =  listOfDict[index]['VmsCount']
            sourcesite = listOfDict[index]['SourceSite']
            targetsite = listOfDict[index]['TargetSite']
            actual_rpo = listOfDict[index]['ActualRPO']
            rawstatus = listOfDict[index]['Status']
            status =  zertocustomers.getlabel_vpgstatus(custcfg, rawstatus)
            last_test = listOfDict[index]['LastTest']
            if last_test is not None: 
                last_test = jsonDateToString(last_test)
            comment = ''

            
            # trigger alert or not
            rpo_thresh = zertocustomers.getrpo(custcfg, xymoncust)
            return_vpg , return_vpglabel, comment = self.analyzeVpg( 
                                                        custcfg = custcfg ,
                                                        vpgstatus = rawstatus,
                                                        rpo = actual_rpo,
                                                        rpo_thresh = rpo_thresh)
            
            # check if vpg is in the list
            if listskips is not None and vpg in listskips :
                log.info("vpg %s will be skip" % vpg)
                return_vpg = -1
                comment.append('this vpg is not checked')

            thisStatus.cmpstatus(return_vpg)
            hobbit_state = Constants.BUTTONLVL.get(return_vpg)

            #print vpg_row_
            #actual_rpo = str(actual_rpo) + ' sec/300 sec'
            actual_rpo_str = str(actual_rpo) + ' sec/300 sec'
            this_vpgrow = vpg_row_template.format(vpg = vpg,
                                              hobbitstate = hobbit_state,
                                              priority = priority,
                                              vms = vms,
                                              sourcesite = sourcesite,
                                              targetsite = targetsite,
                                              actual_rpo = actual_rpo_str,
                                              status     = status,
                                              last_test  = last_test,
                                              comment    = comment)

            vpgs_page = vpgs_page + this_vpgrow 
        vpgs_page = vpg_headers + vpgs_page + vpg_close_headers
        log.info("vpgs_page: ", vpgs_page)
        return vpgs_page , thisStatus.state 

 

if __name__ == "__main__":
    pass
