'''
Created on Jun 17, 2011

@author: borja
'''

class Deployer(object):
    def __init__(self, demogrid_dir, no_cleanup = False, extra_files = []):
        self.demogrid_dir = demogrid_dir
        self.instance = None
        self.extra_files = extra_files
        self.no_cleanup = no_cleanup
        
class VM(object):
    def __init__(self):
        pass