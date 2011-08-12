'''
Created on Jun 16, 2011

@author: borja
'''
import sys

from globus.provision.cli import Command
from globus.provision.deploy.ec2.images import EC2AMICreator, EC2AMIUpdater
from globus.provision.common import defaults
from globus.provision.core.config import GPConfig
from globus.provision.common.utils import parse_extra_files_files

        
def gp_ec2_create_ami_func():
    return gp_ec2_create_ami(sys.argv).run()        

class gp_ec2_create_ami(Command):
    
    name = "gp-ec2-create-ami"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-s", "--chef-directory", 
                                  action="store", type="string", dest="chef_dir", 
                                  help = "Location of Chef files.")        
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.") 

        self.optparser.add_option("-a", "--ami", 
                                  action="store", type="string", dest="ami", 
                                  help = "AMI to use to create the volume.")

        self.optparser.add_option("-n", "--name", 
                                  action="store", type="string", dest="aminame", 
                                  help = "Name of AMI to create")

                
    def run(self):    
        self.parse_options()

        config = GPConfig(self.opt.conf)

        c = EC2AMICreator(self.opt.chef_dir, self.opt.ami, self.opt.aminame, config)
        c.run()
        
        
def gp_ec2_update_ami_func():
    return gp_ec2_update_ami(sys.argv).run()     
        
class gp_ec2_update_ami(Command):
    
    name = "gp-ec2-update-ami"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-s", "--chef-directory", 
                                  action="store", type="string", dest="chef_dir", 
                                  help = "Location of Chef files.")
        
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
        
        self.optparser.add_option("-f", "--files", 
                                  action="store", type="string", dest="files", 
                                  help = "Files to add to AMI")
                
    def run(self):    
        self.parse_options()
        
        files = parse_extra_files_files(self.opt.files)
        config = GPConfig(self.opt.conf)
        
        c = EC2AMIUpdater(self.opt.chef_dir, self.opt.ami, self.opt.aminame, files, config)
        c.run()        

