import os
import os.path
import sys
import shutil


from demogrid.core.topology import Topology, Domain, Node, User
from demogrid.common.certs import CertificateGenerator
from demogrid.core.instance import Instance, InstanceStore
from demogrid.common.utils import parse_extra_files_files

try:
    from mako.template import Template
except Exception, e:
    print "Mako Templates for Python are not installed."
    print "You can download them at http://www.makotemplates.org/"
    print "or 'apt-get install python-mako' on most Debian/Ubuntu systems"
    exit(1)

class API(object):
    
    def __init__(self, demogrid_dir, instances_dir):
        self.demogrid_dir = demogrid_dir
        self.instances_dir = instances_dir

    def create(self, topology_json, config_txt):
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.create_new_instance(topology_json, config_txt)
        
        print inst.id
        
    def start(self, inst_id):
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        
        print "Launching %s" % inst.id
            
        exit()
        
        if self.opt.debug:
            loglevel = 2
        elif self.opt.verbose:
            loglevel = 1
        else:
            loglevel = 0
      
        if self.opt.extra_files != None:
            extra_files = parse_extra_files_files(self.opt.extra_files, self.opt.dir)
        else:
            extra_files = []

        #c = EC2Launcher(self.dg_location, config, self.opt.dir, loglevel, self.opt.no_cleanup, extra_files)
        #c.launch()          

                









        
                

        
        

             
            
        
        

        
        
