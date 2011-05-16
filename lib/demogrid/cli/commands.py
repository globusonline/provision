'''
Created on Nov 1, 2010

@author: borja
'''

#!/usr/bin/python

import demogrid.common.defaults as defaults
from demogrid.core.prepare import Preparator
from demogrid.core.config import DemoGridConfig
from demogrid.ec2.images import EC2ChefVolumeCreator, EC2AMICreator
from demogrid.ec2.launch import EC2Launcher

import os
import getpass
import subprocess
from cPickle import load
from optparse import OptionParser
from demogrid.globusonline.transfer_api import TransferAPIClient
from demogrid.core.topology import Topology

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
        
        self.optparser.add_option("-t", "--topology", 
                                  action="store", type="string", dest="topology",
                                  help = "Topology file.")        
        
        self.optparser.add_option("-d", "--dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory to generate files in.")            

        self.optparser.add_option("-e", "--force-chef", 
                                  action="store_true", dest="force_chef", 
                                  help = "Overwrite existing Chef files.")        

                
    def run(self):    
        self.parse_options()
        
        config = DemoGridConfig(self.opt.conf)

        if self.opt.topology.endswith(".json"):
            jsonfile = open(self.opt.topology)
            json = jsonfile.read()
            jsonfile.close()
            topology = Topology.from_json(json)            

        p = Preparator(self.dg_location, config, self.opt.dir)
        p.prepare(topology, self.opt.force_chef)        
        
class demogrid_vagrant_generate(Command):
    
    name = "demogrid-vagrant-generate"

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
        
        self.optparser.add_option("-r", "--force-certificates", 
                                  action="store_true", dest="force_certificates", 
                                  help = "Overwrite existing certificates.")                       

    def run(self):    
        self.parse_options()
        
        config = DemoGridConfig(self.opt.conf)

        p = Preparator(self.dg_location, config, self.opt.dir)
        p.generate_vagrant(self.opt.force_certificates)                

class demogrid_uvb_generate(Command):
    
    name = "demogrid-uvb-generate"

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
        
        self.optparser.add_option("-r", "--force-certificates", 
                                  action="store_true", dest="force_certificates", 
                                  help = "Overwrite existing certificates.")                       

    def run(self):    
        self.parse_options()
        
        config = DemoGridConfig(self.opt.conf)

        p = Preparator(self.dg_location, config, self.opt.dir)
        p.generate_uvb(self.opt.force_certificates)            

        
class demogrid_clone_image(Command):
    
    name = "demogrid-clone-image"
    
    def __init__(self, argv):
        Command.__init__(self, argv, root = True)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")
        
    def run(self):    
        self.parse_options()
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()        

        host = topology.get_node_by_id(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        args_newvm = ["%s/ubuntu-vm-builder/master_img.qcow2" % self.opt.dir, 
                      "/var/vm/%s.qcow2" % host.node_id, 
                      host.ip, 
                      host.node_id,
                      "%s/hosts" % self.opt.dir
                      ]
        cmd_newvm = ["%s/lib/create_from_master_img.sh" % self.dg_location] + args_newvm
        
        print "Creating VM for %s" % host.node_id
        retcode = subprocess.call(cmd_newvm)
        if retcode != 0:
            print "Error when running %s" % " ".join(cmd_newvm)
            exit(1)

        print "Created VM for host %s" % host.node_id
        

class demogrid_register_host_chef(Command):
    
    name = "demogrid-register-host-chef"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")
        
    def run(self):    
        self.parse_options()
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()        

        host = topology.get_node_by_id(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        retcode = self._run("knife node show %s" % host.hostname, exit_on_error = False)
        node_exists = (retcode == 0)
        retcode = self._run("knife client show %s" % host.hostname, exit_on_error = False)
        client_exists = (retcode == 0)

        if node_exists:
            self._run("knife node delete %s -y" % host.hostname)
        if client_exists:
            self._run("knife client delete %s -y" % host.hostname)
        self._run("knife node create %s -n" % host.hostname)
        self._run("knife node run_list add %s role[%s]" % (host.hostname, host.role))            
        print "Registered host %s in the Chef server" % host.node_id        
        

class demogrid_register_host_libvirt(Command):
    
    name = "demogrid-register-host-libvirt"
    
    def __init__(self, argv):
        Command.__init__(self, argv, root=True)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")

        self.optparser.add_option("-m", "--memory", 
                                  action="store", type="int", dest="memory", 
                                  default = 512,
                                  help = "Memory")        
        
    def run(self):    
        self.parse_options()
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()        

        host = topology.get_node_by_id(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        self._run("virt-install -n %s -r %i --disk path=/var/vm/%s.qcow2,format=qcow2,size=2 --accelerate --vnc --noautoconsole --import --connect=qemu:///system" % (host.node_id, self.opt.memory, host.node_id) )

        print "Registered host %s in libvirt" % host.node_id        
        
        
class demogrid_ec2_launch(Command):
    
    name = "demogrid-ec2-launch"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.")
        
        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")

        self.optparser.add_option("-v", "--verbose", 
                                  action="store_true", dest="verbose", 
                                  help = "Produce verbose output.")

        self.optparser.add_option("-d", "--debug", 
                                  action="store_true", dest="debug", 
                                  help = "Write debugging information. Implies -v.")

        self.optparser.add_option("-n", "--no-cleanup", 
                                  action="store_true", dest="no_cleanup", 
                                  help = "Don't release resources on failure.")

        self.optparser.add_option("-u", "--upload-recipes", 
                                  action="store_true", dest="upload_recipes", 
                                  help = "Upload Chef recipes.")
                
    def run(self):    
        self.parse_options()

        config = DemoGridConfig(self.opt.conf)
        
        if self.opt.debug:
            loglevel = 2
        elif self.opt.verbose:
            loglevel = 1
        else:
            loglevel = 0
        
        c = EC2Launcher(self.dg_location, config, self.opt.dir, loglevel, self.opt.no_cleanup, self.opt.upload_recipes)
        c.launch()          
        
class demogrid_ec2_create_chef_volume(Command):
    
    name = "demogrid-ec2-create-chef-volume"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-a", "--ami", 
                                  action="store", type="string", dest="ami", 
                                  help = "AMI to use to create the volume.")

        self.optparser.add_option("-k", "--keypair", 
                                  action="store", type="string", dest="keypair", 
                                  help = "EC2 keypair")
        
        self.optparser.add_option("-f", "--keypair-file", 
                                  action="store", type="string", dest="keyfile", 
                                  help = "EC2 keypair file")
                
    def run(self):    
        self.parse_options()
        
        c = EC2ChefVolumeCreator(self.dg_location, self.opt.ami, self.opt.keypair, self.opt.keyfile)
        c.run()  
        

class demogrid_ec2_create_ami(Command):
    
    name = "demogrid-ec2-create-ami"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-a", "--ami", 
                                  action="store", type="string", dest="ami", 
                                  help = "AMI to use to create the volume.")

        self.optparser.add_option("-s", "--snapshot", 
                                  action="store", type="string", dest="snap", 
                                  help = "Snapshot with Chef files")

        self.optparser.add_option("-n", "--name", 
                                  action="store", type="string", dest="aminame", 
                                  help = "Name of AMI to create")

        self.optparser.add_option("-k", "--keypair", 
                                  action="store", type="string", dest="keypair", 
                                  help = "EC2 keypair")
        
        self.optparser.add_option("-f", "--keypair-file", 
                                  action="store", type="string", dest="keyfile", 
                                  help = "EC2 keypair file")
                
    def run(self):    
        self.parse_options()
        
        c = EC2AMICreator(self.dg_location, self.opt.ami, self.opt.aminame, self.opt.snap, self.opt.keypair, self.opt.keyfile)
        c.run()
        
# Warning: Lot's of hard-coded kludginess
class demogrid_go_register_endpoints(Command):
    
    name = "demogrid-go-register-endpoints"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.")        
        
        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")        
                
    def run(self):    
        self.parse_options()
        
        config = DemoGridConfig(self.opt.conf)
        go_username = config.get_go_username()
        go_cert_file, go_key_file = config.get_go_credentials()
        go_server_ca = config.get_go_server_ca()

        api = TransferAPIClient(go_username, go_server_ca, go_cert_file, go_key_file)
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()            
        
        # TODO: Check each organization, and see if they need an endpoint or not.
        for org in topology.organizations.values():
            # Find the GridFTP server
            gridftp = [n for n in org.get_nodes() if n.role=="org-gridftp"][0]
             
            api.endpoint_create("demogrid", gridftp.hostname, description="DemoGrid endpoint",
                       scheme="gsiftp", port=2811, subject="/O=Grid/OU=DemoGrid/CN=host/%s" % gridftp.hostname,
                       myproxy_server=gridftp.org.auth.hostname)
             
        
        
        
        
