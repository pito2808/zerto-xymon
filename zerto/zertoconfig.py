import ConfigParser
import logging
import os, sys
import re

class Logger:
    def __init__(self,file= 'defaultfile.log'):
        self.logdir = os.getenv('BBCLIENTLOGS','/tmp')
        self.logfile = self.logdir+'/'+ file
        # level DEBUG , INFO, WARNING, ERROR, CRITICAL
        logging.basicConfig(filename = self.logfile,
                            level  = logging.WARNING,
                            format = '%(asctime)s %(message)s')

    def debug(self, text):
        if flag == 0:
            logging.debug(text)
        else:
            logging.debug(text + str(sys.exc_info()[1]))
            print text + str(sys.exc_info()[1])

    def info(self, text, flag = 0):
        if flag == 0:
            logging.info(text)
        else:
            logging.info(text + str(sys.exc_info()[1]))
            print text + str(sys.exc_info()[1])

    def warning(self, text):
        logging.warning(text)

    def warn(self, text):
        logging.warning(text)

    def error(self, text, flag = 0):
        if flag == 0:
            logging.error(text)
        else:
            logging.critical(text + str(sys.exc_info()[1]))
            print text + str(sys.exc_info()[1])

    def err(self, text):
        logging.error(text)

    def critical(self, text):
        logging.critical(text)

    def crit(self, text):
        logging.critical(text)



DEBUG = 0
log = Logger('zertoxymon_logger.log')
#from ConfigParser import SafeConfigParser

def criticalmsg(msg):
    log.critical(msg + str(sys.exc_info()[1]))
    print msg + str(sys.exc_info()[1])

config = ConfigParser.SafeConfigParser()
#config = SafeConfigParser() 
#cfgdir = os.getenv

cfgbase = os.getenv('XYMONSERVERROOT', '/data/xymon')
log.info("current path for execution %r, base %r" % (os.getcwd(),cfgbase),1)
cfgfile = 'zertoconfig.ini'
cfgdir = cfgbase + "/server/ext/zerto/"

#config.read('zertoconfig.ini')
cfglocation = cfgdir + cfgfile
config.read(cfglocation)
log.info("config location %r" % cfglocation, 1)


print "the config.sections ", config.sections()
sectionsOrdered = config.sections()
# change sections by asc
sectionsOrdered.reverse()

class AllZvm(object):
    ''' create a list of instance of  zvm '''
    instances = []
    
    def __init__(self,zvm_name='NA' ,zvm_user='NA',
                 zvm_pwd = 'NA',zvm_ip = 'NA', zvm_port = 'NA'):
        self.instances.append(self)
        self.zvm_name = zvm_name
        self.zvm_user = zvm_user
        self.zvm_pwd  = zvm_pwd
        self.zvm_ip   = zvm_ip
        self.zvm_port = zvm_port
        self.zvm_url  = 'https://' + zvm_ip +':'+zvm_port





def adding_Zvm(zvm_name, zvm_user,zvm_pwd,zvm_ip, zvm_port):
    Z = AllZvm(zvm_name, zvm_user,zvm_pwd,zvm_ip, zvm_port)  

#for section in config.sections():
for section in sectionsOrdered:
    try: 
        print " section %s " % section
        print config.get(section, 'username')
        print config.get(section, 'password')
        print config.get(section, 'zvm_ip')
        print config.get(section, 'zvm_port')
        zvm_name = section
        zvm_user = config.get(section, 'username') 
        zvm_pwd = config.get(section, 'password') 
        zvm_ip = config.get(section, 'zvm_ip') 
        zvm_port = config.get(section, 'zvm_port') 
    
        adding_Zvm(zvm_name, zvm_user,zvm_pwd,zvm_ip, zvm_port) 

    except ConfigParser.NoOptionError:
            criticalmsg(" exception config parameters ")

Zinstances = AllZvm.instances
if __name__ == "__main__":
    print AllZvm.instances
    for instance in AllZvm.instances:
        print "going to monitor ZVM"
        print "ip %s" % instance.zvm_ip
        #monitor(instance)

else :
    Zinstances = AllZvm.instances

