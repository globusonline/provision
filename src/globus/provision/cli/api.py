'''
Created on Nov 1, 2010

@author: borja
'''

#!/usr/bin/python

import time
import sys

from colorama import Fore, Style

import globus.provision.common.defaults as defaults

from globus.provision.cli import Command
from globus.provision.core.api import API
from globus.provision.common.utils import parse_extra_files_files
from globus.provision.common.threads import SIGINTWatcher
from globus.provision.core.topology import Topology, Node, User
from globus.provision.core.config import SimpleTopologyConfig
from globus.provision.common.config import ConfigException


def gp_create_func():
    return gp_create(sys.argv).run()
        
class gp_create(Command):
    
    name = "gp-create"

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

        if self.opt.conf is None:
            print "You must specify a configuration file using the -c/--conf option."
            exit(1)

        self._check_exists_file(self.opt.conf)

        if self.opt.topology is None:
            topology_file = self.opt.conf
        else:
            self._check_exists_file(self.opt.topology)
            topology_file = self.opt.topology
        
        if topology_file.endswith(".json"):
            jsonfile = open(topology_file)
            topology_json = jsonfile.read()
            jsonfile.close()
        elif topology_file.endswith(".conf"):
            try:
                conf = SimpleTopologyConfig(topology_file)
                topology = conf.to_topology()
                topology_json = topology.to_json_string()
            except ConfigException, cfge:
                self._print_error("Error in topology configuration file.", cfge)
                exit(1)         
        else:   
            self._print_error("Unrecognized topology file format.", "File must be either a JSON (.json) or configuration (.conf) file.")
            exit(1)         

        configf = open(self.opt.conf)
        config_txt = configf.read()
        configf.close()

        api = API(self.opt.dir)
        (status_code, message, inst_id) = api.instance_create(topology_json, config_txt)

        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not create instance.", message)
            exit(1) 
        else:
            print "Created new instance:",
            print Fore.WHITE + Style.BRIGHT + inst_id
            
            
def gp_describe_instance_func():
    return gp_describe_instance(sys.argv).run()            
        
class gp_describe_instance(Command):
    
    name = "gp-describe-instance"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
    def __colorize_topology_state(self, state):
        state_str = Topology.state_str[state]
        reset = Fore.RESET + Style.RESET_ALL
        if state == Topology.STATE_NEW:
            return Fore.BLUE + Style.BRIGHT + state_str + reset
        elif state == Topology.STATE_RUNNING:
            return Fore.GREEN + Style.BRIGHT + state_str + reset
        elif state in (Topology.STATE_STARTING, Topology.STATE_CONFIGURING, Topology.STATE_STOPPING, Topology.STATE_RESUMING, Topology.STATE_TERMINATING):
            return Fore.YELLOW + Style.BRIGHT + state_str + reset
        elif state in (Topology.STATE_TERMINATED, Topology.STATE_FAILED):
            return Fore.RED + Style.BRIGHT + state_str + reset
        elif state == Topology.STATE_STOPPED:
            return Fore.MAGENTA + Style.BRIGHT + state_str + reset
        else:
            return state_str

    def __colorize_node_state(self, state):
        state_str = Node.state_str[state]
        reset = Fore.RESET + Style.RESET_ALL
        if state == Node.STATE_NEW:
            return Fore.BLUE + Style.BRIGHT + state_str + reset
        elif state == Node.STATE_RUNNING:
            return Fore.GREEN + Style.BRIGHT + state_str + reset
        elif state in (Node.STATE_STARTING, Node.STATE_RUNNING_UNCONFIGURED, Node.STATE_CONFIGURING, Node.STATE_STOPPING, Node.STATE_RESUMING, Node.STATE_TERMINATING):
            return Fore.YELLOW + Style.BRIGHT + state_str + reset
        elif state in (Node.STATE_TERMINATED, Node.STATE_FAILED):
            return Fore.RED + Style.BRIGHT + state_str + reset
        elif state == Node.STATE_STOPPED:
            return Fore.MAGENTA + Style.BRIGHT + state_str + reset
        else:
            return state_str
        
    def __pad(self, str, colorstr, width):
        if colorstr == "":
            return str.ljust(width)
        else:
            return colorstr + " " * (width - len(str))
                
    def run(self):    
        self.parse_options()
        
        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)
         
        inst_id = self.args[1]
        
        api = API(self.opt.dir)
        (status_code, message, topology_json) = api.instance(inst_id)
        
        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not access instance.", message)
            exit(1) 
        else:
            if self.opt.verbose or self.opt.debug:
                print topology_json
            else:
                topology = Topology.from_json_string(topology_json)
                reset = Fore.RESET + Style.RESET_ALL
                print Fore.WHITE + Style.BRIGHT + inst_id + reset + ": " + self.__colorize_topology_state(topology.state)
                print
                for domain in topology.domains.values():
                    print "Domain " + Fore.CYAN + "'%s'" % domain.id
                    
                    # Find "column" widths and get values while we're at it
                    node_width = state_width = hostname_width = ip_width = 0
                    rows = []
                    for node in domain.get_nodes():
                        if len(node.id) > node_width:
                            node_width = len(node.id)                        
                        
                        if node.has_property("state"):
                            state = node.state
                        else:
                            state = Node.STATE_NEW                            
                        state_str = Node.state_str[state]

                        if len(state_str) > state_width:
                            state_width = len(state_str)

                        if node.has_property("hostname"):
                            hostname = node.hostname
                        else:
                            hostname = ""                            

                        if len(hostname) > hostname_width:
                            hostname_width = len(hostname)

                        if node.has_property("ip"):
                            ip = node.ip
                        else:
                            ip = "" 

                        if len(ip) > ip_width:
                            ip_width = len(ip)    
                            
                        rows.append((node.id, state, state_str, hostname, ip))                          
                                                
                    for (node_id, state, state_str, hostname, ip) in rows:
                        node_id_pad = self.__pad(node_id, Fore.WHITE + Style.BRIGHT + node_id + Fore.RESET + Style.RESET_ALL, node_width + 2) 
                        state_pad = self.__pad(state_str, self.__colorize_node_state(state), state_width + 2) 
                        hostname_pad   = self.__pad(hostname, "", hostname_width + 2)
                        ip_pad = self.__pad(ip, "", ip_width)
                        print "    " + node_id_pad + state_pad + hostname_pad + ip_pad
                    print
                    
def gp_start_func():
    return gp_start(sys.argv).run()  

class gp_start(Command):
    
    name = "gp-start"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

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
        
        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)
        inst_id = self.args[1]
            
        if self.opt.extra_files != None:
            self._check_exists_file(self.opt.extra_files)
            extra_files = parse_extra_files_files(self.opt.extra_files)
        else:
            extra_files = []

        if self.opt.run != None:
            self._check_exists_file(self.opt.run)
            run_cmds = [l.strip() for l in open(self.opt.run).readlines()]
        else:
            run_cmds = []

        print "Starting instance",
        print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
        api = API(self.opt.dir)
        status_code, message = api.instance_start(inst_id, extra_files, run_cmds)
        
        if status_code == API.STATUS_SUCCESS:
            print Fore.GREEN + Style.BRIGHT + "done!"
            t_end = time.time()
            
            delta = t_end - t_start
            minutes = int(delta / 60)
            seconds = int(delta - (minutes * 60))
            print "Started instance in " + Fore.WHITE + Style.BRIGHT + "%i minutes and %s seconds" % (minutes, seconds)
        elif status_code == API.STATUS_FAIL:
            print
            self._print_error("Could not start instance.", message)
            exit(1) 

def gp_update_topology_func():
    return gp_update_topology(sys.argv).run()  

class gp_update_topology(Command):
    
    name = "gp-update-topology"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-t", "--topology", 
                                  action="store", type="string", dest="topology",
                                  help = "Topology file.")

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

        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)
        inst_id = self.args[1]

        if self.opt.topology != None:
            self._check_exists_file(self.opt.topology)
    
            jsonfile = open(self.opt.topology)
            topology_json = jsonfile.read()
            jsonfile.close()
        else:
            topology_json = None
                

        if self.opt.extra_files != None:
            self._check_exists_file(self.opt.extra_files)
            extra_files = parse_extra_files_files(self.opt.extra_files)
        else:
            extra_files = []
            
        if self.opt.run != None:
            self._check_exists_file(self.opt.run)
            run_cmds = [l.strip() for l in open(self.opt.run).readlines()]
        else:
            run_cmds = []            

        print "Updating topology of",
        print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",

        api = API(self.opt.dir)
        status_code, message = api.instance_update(inst_id, topology_json, extra_files, run_cmds)
        
        if status_code == API.STATUS_SUCCESS:
            print Fore.GREEN + Style.BRIGHT + "done!"
            t_end = time.time()
            
            delta = t_end - t_start
            minutes = int(delta / 60)
            seconds = int(delta - (minutes * 60))
            print "Updated topology in " + Fore.WHITE + Style.BRIGHT + "%i minutes and %s seconds" % (minutes, seconds)
        elif status_code == API.STATUS_FAIL:
            self._print_error("Could not update topology.", message)
            exit(1)


def gp_stop_func():
    return gp_stop(sys.argv).run()         
        
class gp_stop(Command):
    
    name = "gp-stop"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill)        
        
        self.parse_options()
        
        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)
        inst_id = self.args[1]            

        print "Stopping instance",
        print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
        api = API(self.opt.dir)
        status_code, message = api.instance_stop(inst_id)
        
        if status_code == API.STATUS_SUCCESS:
            print Fore.GREEN + Style.BRIGHT + "done!"
        elif status_code == API.STATUS_FAIL:
            self._print_error("Could not stop instance.", message)
            print
            exit(1)       


def gp_terminate_func():
    return gp_terminate(sys.argv).run()     

class gp_terminate(Command):
    
    name = "gp-terminate"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill)        
        
        self.parse_options()

        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)        
        inst_id = self.args[1]

        print "Terminating instance",
        print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
        api = API(self.opt.dir)
        status_code, message = api.instance_terminate(inst_id)
        
        if status_code == API.STATUS_SUCCESS:
            print Fore.GREEN + Style.BRIGHT + "done!"
        elif status_code == API.STATUS_FAIL:
            print
            self._print_error("Could not terminate instance.", message)
            exit(1)  


def gp_list_instances_func():
    return gp_list_instances(sys.argv).run()     

class gp_list_instances(Command):
    
    name = "gp-list-instances"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
    def run(self):    
        self.parse_options()
        
        if len(self.args) >= 2:
            inst_ids = self.args[1:]
        else:
            inst_ids = None
        
        api = API(self.opt.dir)
        insts = api.instance_list(inst_ids)
        
        for i in insts:
            t = i.topology
            print "%s\t%s" % (i.id, Topology.state_str[t.state])
            if self.opt.verbose:
                for node in t.get_nodes():
                    print "\t%s\t%s\t%s" % (node.id, node.hostname, node.ip)
                    if self.opt.debug:
                        print "\t%s" % node.deploy_data


def gp_add_user_func():
    return gp_add_user(sys.argv).run()     

class gp_add_user(Command):
    
    name = "gp-add-user"
    
    def __init__(self, argv):
        Command.__init__(self, argv)    

        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain",
                                  help = "Add user to this domain")  

        self.optparser.add_option("-l", "--login", 
                                  action="store", type="string", dest="login",
                                  help = "User's UNIX login name")        

        self.optparser.add_option("-p", "--password-hash", 
                                  action="store", type="string", dest="passwd", 
                                  default = "!",
                                  help = "Password hash (default is disabled password)")
        
        self.optparser.add_option("-s", "--ssh-pubkey", 
                                  action="store", type="string", dest="ssh", 
                                  help = "User's public SSH key")        

        self.optparser.add_option("-a", "--admin", 
                                  action="store_true", dest="admin", 
                                  help = "Give the user sudo privileges.")
        
        self.optparser.add_option("-c", "--certificate", 
                                  action="store", type="string", dest="certificate", 
                                  default = "generated",                                  
                                  help = "Type of certificate (default is generate a certificate for the user)")   

                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill) 
                
        t_start = time.time()        
        self.parse_options()
                
        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)        
        inst_id = self.args[1]

        api = API(self.opt.dir)
        (status_code, message, topology_json) = api.instance(inst_id)
        
        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not access instance.", message)
            exit(1) 
        else:
            t = Topology.from_json_string(topology_json)
            
            if not t.domains.has_key(self.opt.domain):
                self._print_error("Could not add user", "Domain '%s' does not exist" % self.opt.domain)
                exit(1) 
            
            domain = t.domains[self.opt.domain]
            
            user = User()
            user.set_property("id", self.opt.login)
            user.set_property("password_hash", self.opt.passwd)
            user.set_property("ssh_pkey", self.opt.ssh)
            if self.opt.admin != None:
                user.set_property("admin", self.opt.admin)
            else:
                user.set_property("admin", False)
            user.set_property("certificate", self.opt.certificate)

            domain.add_to_array("users", user)
            
            topology_json = t.to_json_string()

            print "Adding new user to",
            print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
            status_code, message = api.instance_update(inst_id, topology_json, [], [])
            
            if status_code == API.STATUS_SUCCESS:
                print Fore.GREEN + Style.BRIGHT + "done!"
                t_end = time.time()
                
                delta = t_end - t_start
                minutes = int(delta / 60)
                seconds = int(delta - (minutes * 60))
                print "Added user in " + Fore.WHITE + Style.BRIGHT + "%i minutes and %s seconds" % (minutes, seconds)
            elif status_code == API.STATUS_FAIL:
                self._print_error("Could not update topology.", message)
                exit(1)
        
        
def gp_add_host_func():
    return gp_add_host(sys.argv).run()     
        
class gp_add_host(Command):
    
    name = "gp-add-host"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain",
                                  help = "Add node to this domain")  

        self.optparser.add_option("-n", "--id", 
                                  action="store", type="string", dest="id",
                                  help = "New node's ID")        

        self.optparser.add_option("-p", "--depends", 
                                  action="store", type="string", dest="depends", 
                                  default = None,
                                  help = "Node (if any) the new node depends on.")
        
        self.optparser.add_option("-r", "--run-list", 
                                  action="store", type="string", dest="runlist", 
                                  help = "Node's run list")     
                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill) 
                
        t_start = time.time()        
        self.parse_options()
                
        if len(self.args) != 2:
            print "You must specify an instance id."
            print "For example: %s [options] gpi-37a8bf17" % self.name
            exit(1)        
        inst_id = self.args[1]

        api = API(self.opt.dir)
        (status_code, message, topology_json) = api.instance(inst_id)
        
        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not access instance.", message)
            exit(1) 
        else:
            t = Topology.from_json_string(topology_json)
            
            if not t.domains.has_key(self.opt.domain):
                self._print_error("Could not add host", "Domain '%s' does not exist" % self.opt.domain)
                exit(1) 
            
            domain = t.domains[self.opt.domain]
            
            node = Node()
            node.set_property("id", self.opt.id)
            node.set_property("run_list", self.opt.runlist.split(","))
            if self.opt.depends != None:
                node.set_property("depends", "node:%s" % self.opt.depends)

            domain.add_to_array("nodes", (node))
            
            topology_json = t.to_json_string()

            print "Adding new host to",
            print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
            status_code, message = api.instance_update(inst_id, topology_json, [], [])
            
            if status_code == API.STATUS_SUCCESS:
                print Fore.GREEN + Style.BRIGHT + "done!"
                t_end = time.time()
                
                delta = t_end - t_start
                minutes = int(delta / 60)
                seconds = int(delta - (minutes * 60))
                print "Added host in " + Fore.WHITE + Style.BRIGHT + "%i minutes and %s seconds" % (minutes, seconds)
            elif status_code == API.STATUS_FAIL:
                self._print_error("Could not update topology.", message)
                exit(1) 
        
        
def gp_remove_users_func():
    return gp_remove_users(sys.argv).run()     

class gp_remove_users(Command):
    
    name = "gp-remove-users"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
                
        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain",
                                  help = "Remove hosts from this domain")  
                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill) 
                
        t_start = time.time()        
        self.parse_options()
                
        if len(self.args) <= 2:
            print "You must specify an instance id and at least one host."
            print "For example: %s [options] gpi-37a8bf17 simple-wn3" % self.name
            exit(1)        
        inst_id = self.args[1]
        users = self.args[2:]
        
        api = API(self.opt.dir)
        (status_code, message, topology_json) = api.instance(inst_id)
        
        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not access instance.", message)
            exit(1) 
        else:
            t = Topology.from_json_string(topology_json)
            
            if not t.domains.has_key(self.opt.domain):
                self._print_error("Could not remove users", "Domain '%s' does not exist" % self.opt.domain)
                exit(1) 
                            
            removed = []
            domain_users = t.domains[self.opt.domain].users
            
            for user in users:
                if user in domain_users:
                    domain_users.pop(user)
                    removed.append(user)
                        
            remaining = set(removed) ^ set(users)
            for r in remaining:
                print Fore.YELLOW + Style.BRIGHT + "Warning" + Fore.RESET + Style.RESET_ALL + ":",
                print "User %s does not exist." % r

            topology_json = t.to_json_string()

            if len(removed) > 0:
                print "Removing users %s from" % list(removed),
                print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
                status_code, message = api.instance_update(inst_id, topology_json, [], [])
    
                if status_code == API.STATUS_SUCCESS:
                    print Fore.GREEN + Style.BRIGHT + "done!"
                    t_end = time.time()
                    
                    delta = t_end - t_start
                    minutes = int(delta / 60)
                    seconds = int(delta - (minutes * 60))
                    print "Removed users in " + Fore.WHITE + Style.BRIGHT + "%i minutes and %s seconds" % (minutes, seconds)
                elif status_code == API.STATUS_FAIL:
                    self._print_error("Could not update topology.", message)
                    exit(1) 

        
        
def gp_remove_hosts_func():
    return gp_remove_hosts(sys.argv).run()             
        
class gp_remove_hosts(Command):
    
    name = "gp-remove-hosts"
    
    def __init__(self, argv):
        Command.__init__(self, argv)

        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain",
                                  help = "Remove hosts from this domain")  
                
    def run(self):    
        SIGINTWatcher(self.cleanup_after_kill) 
                
        t_start = time.time()        
        self.parse_options()
                
        if len(self.args) <= 2:
            print "You must specify an instance id and at least one host."
            print "For example: %s [options] gpi-37a8bf17 simple-wn3" % self.name
            exit(1)        
        inst_id = self.args[1]
        hosts = self.args[2:]
        
        api = API(self.opt.dir)
        (status_code, message, topology_json) = api.instance(inst_id)
        
        if status_code != API.STATUS_SUCCESS:
            self._print_error("Could not access instance.", message)
            exit(1) 
        else:
            t = Topology.from_json_string(topology_json)
            
            if not t.domains.has_key(self.opt.domain):
                self._print_error("Could not remove hosts", "Domain '%s' does not exist" % self.opt.domain)
                exit(1) 
                            
            removed = []
            nodes = t.domains[self.opt.domain].nodes
            
            for host in hosts:
                if host in nodes:
                    nodes.pop(host)
                    removed.append(host)
                        
            remaining = set(removed) ^ set(hosts)
            for r in remaining:
                print Fore.YELLOW + Style.BRIGHT + "Warning" + Fore.RESET + Style.RESET_ALL + ":",
                print "Host %s does not exist." % r

            topology_json = t.to_json_string()

            if len(removed) > 0:
                print "Removing hosts %s from" % list(removed),
                print Fore.WHITE + Style.BRIGHT + inst_id + Fore.RESET + Style.RESET_ALL + "...",
                status_code, message = api.instance_update(inst_id, topology_json, [], [])
    
                if status_code == API.STATUS_SUCCESS:
                    print Fore.GREEN + Style.BRIGHT + "done!"
                    t_end = time.time()
                    
                    delta = t_end - t_start
                    minutes = int(delta / 60)
                    seconds = int(delta - (minutes * 60))
                    print "Removed hosts in " + Fore.WHITE + Style.BRIGHT + "%i minutes and %s seconds" % (minutes, seconds)
                elif status_code == API.STATUS_FAIL:
                    self._print_error("Could not update topology.", message)
                    exit(1) 
                