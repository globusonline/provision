'''
Created on Nov 1, 2010

@author: borja
'''

#!/usr/bin/python

import demogrid.common.defaults as defaults

from demogrid.cli import Command
from demogrid.core.api import API
from demogrid.common.utils import parse_extra_files_files, SIGINTWatcher
import time
from demogrid.core.topology import Topology, Node


        
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
        
        self._check_exists_file(self.opt.topology)
        self._check_exists_file(self.opt.conf)
        
        jsonfile = open(self.opt.topology)
        topology_json = jsonfile.read()
        jsonfile.close()
          
        configf = open(self.opt.conf)
        config_txt = configf.read()
        configf.close()

        api = API(self.dg_location, self.opt.dir)
        (status_code, message, inst_id) = api.instance_create(topology_json, config_txt)

        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not create instance.", message)
            exit(1) 
        else:
            print inst_id
        
class demogrid_describe_instance(Command):
    
    name = "demogrid-describe-instance"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        inst_id = self.args[1]
        
        api = API(self.dg_location, self.opt.dir)
        (status_code, message, topology_json) = api.instance(inst_id)
        
        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not access instance.", message)
            exit(1) 
        else:
            if self.opt.verbose:
                print topology_json
            else:
                topology = Topology.from_json_string(topology_json)
                print "%s: %s" % (inst_id, Topology.state_str[topology.state])
                print
                for domain in topology.domains:
                    print "Domain '%s'" % domain.id
                    for node in domain.get_nodes():
                        if node.has_property("state"):
                            state = Node.state_str[node.state]
                        else:
                            state = "New"

                        if node.has_property("hostname"):
                            hostname = node.hostname
                        else:
                            hostname = ""                            

                        if node.has_property("ip"):
                            ip = node.ip
                        else:
                            ip = ""                            
                            
                        print "  %s\t%s\t%s\t%s" % (node.id, state, hostname, ip) 
                    print
                    

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
        SIGINTWatcher(self.cleanup_after_kill)
        
        t_start = time.time()        
        self.parse_options()
        
        inst_id = self.args[1]

        if self.opt.extra_files != None:
            self._check_exists_file(self.opt.topology)
            extra_files = parse_extra_files_files(self.opt.extra_files, self.dg_location)
        else:
            extra_files = []

        if self.opt.run != None:
            self._check_exists_file(self.opt.topology)
            run_cmds = [l.strip() for l in open(self.opt.run).readlines()]
        else:
            run_cmds = []

        api = API(self.dg_location, self.opt.dir)
        status_code, message = api.instance_start(inst_id, self.opt.no_cleanup, extra_files, run_cmds)
        
        if status_code == API.STATUS_SUCCESS:
            t_end = time.time()
            
            delta = t_end - t_start
            minutes = int(delta / 60)
            seconds = int(delta - (minutes * 60))
            print "\033[1;37m%i minutes and %s seconds\033[0m" % (minutes, seconds)
        elif status_code == API.STATUS_FAIL:
            self._print_error("Could not start instance.", message)
            exit(1) 


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
        
        self.optparser.add_option("-r", "--run", 
                                  action="store", type="string", dest="run", 
                                  help = "Run commands after configuration")        
                
    def run(self):    
        t_start = time.time()        
        self.parse_options()

        jsonfile = open(self.opt.topology)
        topology_json = jsonfile.read()
        jsonfile.close()
                
        inst_id = self.args[1]

        if self.opt.extra_files != None:
            self._check_exists_file(self.opt.topology)
            extra_files = parse_extra_files_files(self.opt.extra_files, self.dg_location)
        else:
            extra_files = []
            
        if self.opt.run != None:
            self._check_exists_file(self.opt.topology)
            run_cmds = [l.strip() for l in open(self.opt.run).readlines()]
        else:
            run_cmds = []            

        api = API(self.dg_location, self.opt.dir)
        status_code, message = api.instance_update(inst_id, topology_json, self.opt.no_cleanup, extra_files, run_cmds)
        
        if status_code == API.STATUS_SUCCESS:
            t_end = time.time()
            
            delta = t_end - t_start
            minutes = int(delta / 60)
            seconds = int(delta - (minutes * 60))
            print "\033[1;37m%i minutes and %s seconds\033[0m" % (minutes, seconds)
        elif status_code == API.STATUS_FAIL:
            self._print_error("Could not update topology.", message)
            exit(1)
        
        
class demogrid_stop(Command):
    
    name = "demogrid-stop"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill)        
        
        self.parse_options()
        
        inst_id = self.args[1]

        api = API(self.dg_location, self.opt.dir)
        status_code, message = api.instance_stop(inst_id)
        
        if status_code == API.STATUS_SUCCESS:
            print "Instance %s stopped" % inst_id
        elif status_code == API.STATUS_FAIL:
            self._print_error("Could not start instance.", message)
            exit(1)       


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
                for domain, node in t.get_nodes():
                    print "\t%s\t%s\t%s" % (node.id, node.hostname, node.ip)
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
                