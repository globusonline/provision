'''
Created on Nov 1, 2010

@author: borja
'''

#!/usr/bin/python

import demogrid.common.defaults as defaults

from demogrid.cli import Command
from demogrid.core.api import API
from demogrid.common.utils import parse_extra_files_files
import time


        
class demogrid_create(Command):
    
    name = "demogrid-create"

    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.")
        
        self.optparser.add_option("-t", "--topology", 
                                  action="store", type="string", dest="topology",
                                  help = "Topology file.")        
         

                
    def run(self):    
        self.parse_options()
        
        jsonfile = open(self.opt.topology)
        topology_json = jsonfile.read()
        jsonfile.close()
          
        configf = open(self.opt.conf)
        config_txt = configf.read()
        configf.close()

        api = API(self.dg_location, self.opt.dir)
        api.create(topology_json, config_txt)
        

class demogrid_start(Command):
    
    name = "demogrid-start"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-n", "--no-cleanup", 
                                  action="store_true", dest="no_cleanup", 
                                  help = "Don't release resources on failure.")

        self.optparser.add_option("-x", "--extra-files", 
                                  action="store", type="string", dest="extra_files", 
                                  help = "Upload extra files")
                
    def run(self):    
        t_start = time.time()        
        self.parse_options()
        
        inst_id = self.args[1]

        if self.opt.extra_files != None:
            extra_files = parse_extra_files_files(self.opt.extra_files, self.dg_location)
        else:
            extra_files = []

        api = API(self.dg_location, self.opt.dir)
        api.start(inst_id, self.opt.no_cleanup, extra_files)

        t_end = time.time()
        
        delta = t_end - t_start
        minutes = int(delta / 60)
        seconds = int(delta - (minutes * 60))
        #print "You just went \033[1;34mfrom zero to grid\033[0m in \033[1;37m%i minutes and %s seconds\033[0m!" % (minutes, seconds)
        
class demogrid_stop(Command):
    
    name = "demogrid-stop"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)
        api.stop(inst_id)        


class demogrid_terminate(Command):
    
    name = "demogrid-terminate"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)
        api.terminate(inst_id)

class demogrid_list_instances(Command):
    
    name = "demogrid-terminate"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        if len(self.args) == 2:
            inst_id = self.args[1]
        else:
            inst_id = None
        
        api = API(self.dg_location, self.opt.dir)
        api.list_instances(inst_id)

class demogrid_add_users(Command):
    
    name = "demogrid-add-users"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-j", "--json", 
                                  action="store", type="string", dest="json",
                                  help = "json file.")        

                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)
        api.add_users(inst_id)            
        
class demogrid_add_hosts(Command):
    
    name = "demogrid-add-hosts"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-j", "--json", 
                                  action="store", type="string", dest="json",
                                  help = "json file.")        

        self.optparser.add_option("-n", "--no-cleanup", 
                                  action="store_true", dest="no_cleanup", 
                                  help = "Don't release resources on failure.")

        self.optparser.add_option("-x", "--extra-files", 
                                  action="store", type="string", dest="extra_files", 
                                  help = "Upload extra files")
                
    def run(self):    
        self.parse_options()
        
        jsonfile = open(self.opt.json)
        hosts_json = jsonfile.read()
        jsonfile.close()        

        if self.opt.extra_files != None:
            extra_files = parse_extra_files_files(self.opt.extra_files, self.dg_location)
        else:
            extra_files = []
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)
        api.add_hosts(inst_id, hosts_json, self.opt.no_cleanup, extra_files)       
        

class demogrid_remove_user(Command):
    
    name = "demogrid-remove-user"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]
        user = self.args[2]

        api = API(self.dg_location, self.opt.dir)
        api.remove_user(inst_id)
        
        
class demogrid_remove_host(Command):
    
    name = "demogrid-remove-host"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]
        host = self.args[2]

        api = API(self.dg_location, self.opt.dir)
        api.remove_host(inst_id)
                