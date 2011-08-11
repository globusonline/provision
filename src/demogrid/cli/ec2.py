'''
Created on Jun 16, 2011

@author: borja
'''
import sys

from demogrid.cli import Command
from demogrid.deploy.ec2.images import EC2AMICreator, EC2AMIUpdater
from demogrid.common import defaults
from demogrid.core.config import DemoGridConfig
from demogrid.common.utils import parse_extra_files_files

        
def demogrid_ec2_create_ami_func():
    return demogrid_ec2_create_ami(sys.argv).run()        

class demogrid_ec2_create_ami(Command):
    
    name = "demogrid-ec2-create-ami"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.") 

        self.optparser.add_option("-a", "--ami", 
                                  action="store", type="string", dest="ami", 
                                  help = "AMI to use to create the volume.")

        self.optparser.add_option("-s", "--snapshot", 
                                  action="store", type="string", dest="snap", 
                                  help = "Snapshot with Chef files")

        self.optparser.add_option("-n", "--name", 
                                  action="store", type="string", dest="aminame", 
                                  help = "Name of AMI to create")

                
    def run(self):    
        self.parse_options()

        config = DemoGridConfig(self.opt.conf)

        c = EC2AMICreator(self.dg_location, self.opt.ami, self.opt.aminame, self.opt.snap, config)
        c.run()
        
        
def demogrid_ec2_update_ami_func():
    return demogrid_ec2_update_ami(sys.argv).run()     
        
class demogrid_ec2_update_ami(Command):
    
    name = "demogrid-ec2-update-ami"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-a", "--ami", 
                                  action="store", type="string", dest="ami", 
                                  help = "AMI to update.")

        self.optparser.add_option("-n", "--name", 
                                  action="store", type="string", dest="aminame", 
                                  help = "Name of new AMI.")

        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.") 
        
        self.optparser.add_option("-l", "--files", 
                                  action="store", type="string", dest="files", 
                                  help = "Files to add to AMI")
                
    def run(self):    
        self.parse_options()
        
        files = parse_extra_files_files(self.opt.files, self.dg_location)
        config = DemoGridConfig(self.opt.conf)
        
        c = EC2AMIUpdater(self.dg_location, self.opt.ami, self.opt.aminame, files, config)
        c.run()        

