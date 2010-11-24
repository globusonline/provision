'''
Created on Nov 1, 2010

@author: borja
'''

#!/usr/bin/python

from demogrid.prepare import Preparator
import demogrid.defaults as defaults
from demogrid.config import DemoGridConfig, DemoGridHostsFile
import os
from optparse import OptionParser
import getpass
import subprocess

class Command(object):
    
    def __init__(self, argv, root = False):
        
        if root:
            if getpass.getuser() != "root":
                print "Must run as root"
                exit(1)         
                 
        if not os.environ.has_key("DEMOGRID_LOCATION"):
            print "DEMOGRID_LOCATION not set"
            exit(1)
        
        self.dg_location = os.environ["DEMOGRID_LOCATION"]
        
        # TODO: Validate that this is a correct DEMOGRID_LOCATION
                
        self.argv = argv
        self.optparser = OptionParser()
        self.opt = None
        self.args = None

    def parse_options(self):
        opt, args = self.optparser.parse_args(self.argv)
        self.opt = opt
        self.args = args
        
    def _run(self, cmd, exit_on_error=True, silent=True):
        if silent:
            devnull = open("/dev/null")
        cmd_list = cmd.split()
        if silent:
            retcode = subprocess.call(cmd_list, stdout=devnull, stderr=devnull)
        else:
            retcode = subprocess.call(cmd_list)
        if silent:
            devnull.close()
        if retcode != 0 and exit_on_error:
            print "Error when running %s" % cmd
            exit(1)        
        return retcode
        
class demogrid_prepare(Command):
    
    name = "demogrid-prepare"

    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.")
        
        self.optparser.add_option("-d", "--dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory to generate files in.")        

        self.optparser.add_option("-f", "--force", 
                                  action="store_true", dest="force", 
                                  help = "Overwrite existing files.")        

                
    def run(self):    
        self.parse_options()
        
        config = DemoGridConfig(self.opt.conf)

        p = Preparator(self.dg_location, config, self.opt.dir, self.opt.force)
        p.prepare()        
        
        
class demogrid_clone_image(Command):
    
    name = "demogrid-clone-image"
    
    def __init__(self, argv):
        Command.__init__(self, argv, root = True)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-f", "--hostsfile", 
                                  action="store", type="string", dest="hostsfile", 
                                  default = "%s/hosts.csv" % defaults.GENERATED_LOCATION,
                                  help = "Hosts file.")
        
    def run(self):    
        self.parse_options()
        
        hosts = DemoGridHostsFile(self.opt.hostsfile)

        host = hosts.get_host(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        args_newvm = ["%s/ubuntu-vm-builder/master_img.qcow2" % defaults.GENERATED_LOCATION, 
                      "/var/vm/%s.qcow2" % host["name"], 
                      host["ip"], 
                      host["name"],
                      "%s/hosts" % defaults.GENERATED_LOCATION
                      ]
        cmd_newvm = ["%s/lib/create_from_master_img.sh" % self.dg_location] + args_newvm
        
        print "Creating VM for %s" % host["name"]
        retcode = subprocess.call(cmd_newvm)
        if retcode != 0:
            print "Error when running %s" % " ".join(cmd_newvm)
            exit(1)

        print "Created VM for host %s" % host["name"]
        

class demogrid_register_host_chef(Command):
    
    name = "demogrid-register-host-chef"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-f", "--hostsfile", 
                                  action="store", type="string", dest="hostsfile", 
                                  default = "%s/hosts.csv" % defaults.GENERATED_LOCATION,
                                  help = "Hosts file.")
        
    def run(self):    
        self.parse_options()
        
        hosts = DemoGridHostsFile(self.opt.hostsfile)

        host = hosts.get_host(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        retcode = self._run("knife node show %s" % host["fqdn"], exit_on_error = False)
        node_exists = (retcode == 0)
        retcode = self._run("knife client show %s" % host["fqdn"], exit_on_error = False)
        client_exists = (retcode == 0)

        if node_exists:
            self._run("knife node delete %s -y" % host["fqdn"])
        if client_exists:
            self._run("knife client delete %s -y" % host["fqdn"])
        self._run("knife node create %s -n" % host["fqdn"])
        self._run("knife node run_list add %s role[%s]" % (host["fqdn"], host["role"]))            
        print "Registered host %s in the Chef server" % host["name"]        
        

class demogrid_register_host_libvirt(Command):
    
    name = "demogrid-register-host-libvirt"
    
    def __init__(self, argv):
        Command.__init__(self, argv, root=True)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-f", "--hostsfile", 
                                  action="store", type="string", dest="hostsfile", 
                                  default = "%s/hosts.csv" % defaults.GENERATED_LOCATION,
                                  help = "Hosts file.")

        self.optparser.add_option("-m", "--memory", 
                                  action="store", type="int", dest="memory", 
                                  default = 512,
                                  help = "Memory")        
        
    def run(self):    
        self.parse_options()
        
        hosts = DemoGridHostsFile(self.opt.hostsfile)

        host = hosts.get_host(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        self._run("virt-install -n %s -r %i --disk path=/var/vm/%s.qcow2,format=qcow2,size=2 --accelerate --vnc --noautoconsole --import --connect=qemu:///system" % (host["name"], self.opt.memory, host["name"]) )

        print "Registered host %s in libvirt" % host["name"]                
    