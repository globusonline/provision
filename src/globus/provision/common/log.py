'''
Created on Dec 8, 2010

@author: borja
'''

import logging
import os.path

def init_logging(level):
    if level == 2:
        level = logging.DEBUG
    elif level == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger('paramiko').setLevel(logging.CRITICAL)
    
    l = logging.getLogger("globusprovision")
    l.setLevel(logging.DEBUG)
    
    fh = logging.StreamHandler()
    fh.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    fh.setFormatter(formatter)
    l.addHandler(fh)        

def set_logging_instance(instance):
    l = logging.getLogger("globusprovision")
    fh = logging.FileHandler(os.path.expanduser('~/.globusprovision/instances/%s/deploy.log' % instance))
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    l.addHandler(fh)    

def log(msg, func, node):
    if node != None:
        msg = "%s - %s" % (node.hostname.split(".")[0], msg)
    func(msg)

def debug(msg, node = None):
    log(msg, logging.getLogger('globusprovision').debug, node)
    
def info(msg, node = None):
    log(msg, logging.getLogger('globusprovision').info, node)
