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
from demogrid.core.topology import Topology


        
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

        self.optparser.add_option("-r", "--run", 
                                  action="store", type="string", dest="run", 
                                  help = "Run commands after configuration")
                        
    def run(self):    
        t_start = time.time()        
        self.parse_options()
        
        inst_id = self.args[1]

        if self.opt.extra_files != None:
            extra_files = parse_extra_files_files(self.opt.extra_files, self.dg_location)
        else:
            extra_files = []

        if self.opt.run != None:
            run_cmds = [l.strip() for l in open(self.opt.run).readlines()]
        else:
            run_cmds = []

        api = API(self.dg_location, self.opt.dir)
        success, message = api.start(inst_id, self.opt.no_cleanup, extra_files, run_cmds)
        
        if not success:
            print "Unable to start instance. Reason:"
            print message
        else:
            t_end = time.time()
            
            delta = t_end - t_start
            minutes = int(delta / 60)
            seconds = int(delta - (minutes * 60))
            print "\033[1;37m%i minutes and %s seconds\033[0m" % (minutes, seconds)


class demogrid_update_topology(Command):
    
    name = "demogrid-update-topology"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-t", "--topology", 
                                  action="store", type="string", dest="topology",
                                  help = "Topology file.")        

        self.optparser.add_option("-n", "--no-cleanup", 
                                  action="store_true", dest="no_cleanup", 
                                  help = "Don't release resources on failure.")

        self.optparser.add_option("-x", "--extra-files", 
                                  action="store", type="string", dest="extra_files", 
                                  help = "Upload extra files")
                
    def run(self):    
        t_start = time.time()        
        self.parse_options()

        jsonfile = open(self.opt.topology)
        topology_json = jsonfile.read()
        jsonfile.close()
                
        inst_id = self.args[1]

        if self.opt.extra_files != None:
            extra_files = parse_extra_files_files(self.opt.extra_files, self.dg_location)
        else:
            extra_files = []

        api = API(self.dg_location, self.opt.dir)
        api.update_topology(inst_id, topology_json, self.opt.no_cleanup, extra_files)

        t_end = time.time()
        
        delta = t_end - t_start
        minutes = int(delta / 60)
        seconds = int(delta - (minutes * 60))
        
        
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
    
    name = "demogrid-list-instances"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        if len(self.args) >= 2:
            inst_ids = self.args[1:]
        else:
            inst_ids = None
        
        api = API(self.dg_location, self.opt.dir)
        insts = api.list_instances(inst_ids)
        
        for i in insts:
            t = i.topology
            print "%s\t%s" % (i.id, Topology.state_str[t.state])
            if self.opt.verbose:
                for node in t.get_nodes():
                    print "\t%s\t%s\t%s" % (node.node_id, node.hostname, node.ip)
                    if self.opt.debug:
                        print "\t%s" % node.deploy_data


# TODO: The following commands don't have corresponding API functions. They will simply
# provide easier access to update_topology 

class demogrid_add_user(Command):
    
    name = "demogrid-add-user"
    
    def __init__(self, argv):
        Command.__init__(self, argv)    

                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)   
        
class demogrid_add_host(Command):
    
    name = "demogrid-add-host"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)    
        

class demogrid_remove_users(Command):
    
    name = "demogrid-remove-user"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]
        users = self.args[2:]

        api = API(self.dg_location, self.opt.dir)
        
        
class demogrid_remove_hosts(Command):
    
    name = "demogrid-remove-hosts"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]
        hosts = self.args[2:]

        api = API(self.dg_location, self.opt.dir)
                