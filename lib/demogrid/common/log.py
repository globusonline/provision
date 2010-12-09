'''
Created on Dec 8, 2010

@author: borja
'''

import logging

def init_logging(level):
    if level == 2:
        level = logging.DEBUG
    elif level == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger('paramiko').setLevel(logging.CRITICAL)
    logging.basicConfig(level=level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S')

def log(msg, func, node):
    if node != None:
        msg = "%s - %s" % (node.hostname.split(".")[0], msg)     
    func(msg)

def debug(msg, node = None):
    log(msg, logging.debug, node)
    
def info(msg, node = None):
    log(msg, logging.info, node)
