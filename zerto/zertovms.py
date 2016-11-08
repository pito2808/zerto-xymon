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


vm_headers = '''\

<table BORDER=1 CELLPADDING=5>
  <tr>
    <th>vm name</th>
    <th>hobbitstate</th>
    <th>VPG Name</th>
    <th>IOPS</th>       
    <th>Throughput</th>
    <th>Provisioned Storage</th>
    <th>Used Storage</th>
    <th>Actual RPO</th>
    <th>Status</th>
    <th>Last Test</th>
    <th>Comment</th>
  </tr>

'''

vm_close_headers = '''\
</table>
'''

vm_row_template = '''\
<tr>
    <td>  {vm} </td>
    <td>  {hobbitstate} </td>
    <td>  {vpg} </td>
    <td>  {iops} /sec </td>
    <td>  {throughput} MB/sec </td>
    <td>  {provstorage} </td>
    <td>  {usedstorage} </td>
    <td>  {actual_rpo} </td>
    <td>  {status} </td>
    <td>  {last_test} </td>
    <td>  {comment} </td>
</tr>
'''


class Vms(object):
    '''
    monitoring vms zerto , argument zerto instance
    '''
    
    def __init__(self,zerto):
        self.zerto = zerto

    def check(self, **kwargs):
        '''
          get vms values in json format  

        '''
        self.uri = 'vms'
        log.info("uri used for vms :%r" % self.uri)
        try:
            vms_page = self.zerto.get_json(self.uri) 
        except :
            log.error (" get urlHTTPError for vms_pages",1)
        decoded = json.loads(vms_page)
        #print "INDENT: ", json.dumps(decoded, indent = 4)
        #print "DECODED VM: ", decoded
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
                vpgsindex = map_search( decoded ,'VpgName', customer['Vpgs'])
                # sort vpgsindex by name
                vpgsindex = sorted(vpgsindex, key = itemgetter(1))
                #print "vpgsindex : ", vpgsindex
                log.info("vpgsindex : %r" % vpgsindex, 1)
                page4xymon, vmsstatus = self.parseVms(vpgsindex, 
                                                           decoded,
                                                           custcfg,
                                                           customer['hostname'])
                hobbitState.comparestatus(vmsstatus)
                hobbitState.sendtoxymon('zerto_vms',
                                            'zerto vms monitoring',
                                            page4xymon)
                log.info( "page4xymon %r customer %r" % (page4xymon, 
                                                    customer['hostname']), 0)


    def analyzeVm(self, rpo_thresh = 300, **kwargs):
        '''
        check each vpg for vm and trigger alert if need
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
        log.info("rpo %r rpo_thresh %r" % (rpo, rpo_thresh))
        if rpo >= rpo_thresh :
            thisStatus.cmpstatus(1)
            listcomment.append('rpo is higher than '+str(rpo_thresh)+' seconds')
        if not isinstance(rpo,(int, long)):
            thisStatus.cmpstatus(1)
            listcomment.append('rpo is not type integer or long')
        
        log.info("thisStatus.state %r thislabel %r" % (thisStatus.state,
                                                        thislabel))
        return thisStatus.state, thislabel, listcomment

    def getStatus(self, val_to_check, pattern, int_return):
        prog = re.compile(pattern)
        if prog.match(str(val_to_check)):
            return int_return
        else:
            return 0


    def parseVms(self,listOfTuples, listOfDict,custcfg, xymoncust):
        '''
        return list contained blocks of values per vm regarding its vpg or
        zorg
        '''

        thisStatus = GlobalStatus()
        vms_page = "" 
        # list vpgs  to skip
        listskips = zertocustomers.getlist_skipvpgs(custcfg, xymoncust) 
        log.info("list vpgs to skipped %r %r " % (xymoncust,listskips))
        for i in listOfTuples:
            assert isinstance((i[0]), int),"index is not an integer: %r " % i[0]
            index = i[0]
            vpg = i[1]
            vm = listOfDict[index]['VmName']
            iops = listOfDict[index]['IOPS']
            throughput = listOfDict[index]['ThroughputInMB']
            pstorage = listOfDict[index]['ProvisionedStorageInMB']
            ustorage = listOfDict[index]['UsedStorageInMB']
            actual_rpo = listOfDict[index]['ActualRPO']
            rawstatus = listOfDict[index]['Status']
            status =  zertocustomers.getlabel_vpgstatus(custcfg, rawstatus)
            last_test = listOfDict[index]['LastTest']
            if last_test is not None: 
                last_test = jsonDateToString(last_test)
            comment = ''

            
            # trigger alert or not
            rpo_thresh = zertocustomers.getrpo(custcfg, xymoncust)
            return_vm , return_vmlabel, comment = self.analyzeVm( 
                                                        custcfg = custcfg ,
                                                        vpgstatus = rawstatus,
                                                        rpo = actual_rpo,
                                                        rpo_thresh = rpo_thresh)
            
            # check if vpg is in the list
            if listskips is not None and vpg in listskips:
               log.info("vpg %s will be skip" % vpg)
               return_vm = -1
               comment.append('this vm in vpg is not checked')

            thisStatus.cmpstatus(return_vm)
            hobbit_state = Constants.BUTTONLVL.get(return_vm)

            #print vpg_row_
            #actual_rpo = str(actual_rpo) + ' sec/300 sec'
            actual_rpo_str = str(actual_rpo) + ' sec/300 sec'
            
            ustorage_str = str(round(ustorage/1024, 1)) + ' GB'
            pstorage_str = str(round(pstorage/1024, 1)) + ' GB'

            this_vmrow = vm_row_template.format(vpg = vpg,
                                              hobbitstate = hobbit_state,
                                              vm = vm,
                                              iops = iops,
                                              throughput = throughput,
                                              provstorage = pstorage_str,
                                              usedstorage = ustorage_str,
                                              actual_rpo = actual_rpo_str,
                                              status     = status,
                                              last_test  = last_test,
                                              comment    = comment)

            vms_page = vms_page + this_vmrow 
        vms_page = vm_headers + vms_page + vm_close_headers
        log.info("vms_page: ", vms_page)
        return vms_page , thisStatus.state 

 

if __name__ == "__main__":
    pass
