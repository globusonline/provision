'''
Created on Jun 17, 2011

@author: borja
'''
from demogrid.common.utils import DemoGridThread, SSH
from demogrid.common import log
import sys
from demogrid.core.topology import Node

class BaseDeployer(object):
    def __init__(self, demogrid_dir, extra_files = [], run_cmds = []):
        self.demogrid_dir = demogrid_dir
        self.instance = None
        self.extra_files = extra_files
        self.run_cmds = run_cmds
        
class VM(object):
    def __init__(self):
        pass
    
class WaitThread(DemoGridThread):
    def __init__(self, multi, name, node, vm, deployer, state, depends):
        DemoGridThread.__init__(self, multi, name, depends)
        self.node = node
        self.vm = vm
        self.deployer = deployer
        self.state = state

    def run2(self):
        topology = self.deployer.instance.topology
        
        self.wait()
        
        self.node.state = self.state
        topology.save()
    
class ConfigureThread(DemoGridThread):
    def __init__(self, multi, name, node, vm, deployer, depends = None, basic = True, chef = True):
        DemoGridThread.__init__(self, multi, name, depends)
        self.domain = node.parent_Domain
        self.node = node
        self.vm = vm
        self.deployer = deployer
        self.config = deployer.instance.config
        self.basic = basic
        self.chef = chef

    def run2(self):
        topology = self.deployer.instance.topology
        
        self.node.state = Node.STATE_CONFIGURING
        topology.save()
        
        ssh = self.connect()
        self.check_continue()
        self.pre_configure(ssh)
        self.check_continue()
        self.configure(ssh)
        self.check_continue()
        self.post_configure(ssh)
        self.check_continue()

        self.node.state = Node.STATE_RUNNING
        topology.save()

        
    def ssh_connect(self, username, hostname, keyfile):
        node = self.node
        #if self.deployer.loglevel in (0,1):
        #    ssh_out = None
        #    ssh_err = None
        #elif self.deployer.loglevel == 2:
        #   ssh_out = sys.stdout
        #    ssh_err = sys.stderr
        ssh_out = sys.stdout
        ssh_err = sys.stderr

        log.debug("Establishing SSH connection", node)
        ssh = SSH(username, hostname, keyfile, ssh_out, ssh_err)
        ssh.open()
        log.debug("SSH connection established", node)
        
        return ssh
        
    def configure(self, ssh):
        domain = self.domain
        node = self.node
        instance_dir = self.deployer.instance.instance_dir        
        
        if self.basic:
            # Upload host file and update hostname
            log.debug("Uploading host file and updating hostname", node)
            ssh.scp("%s/hosts" % instance_dir,
                    "/chef/cookbooks/demogrid/files/default/hosts")             
            ssh.run("sudo cp /chef/cookbooks/demogrid/files/default/hosts /etc/hosts", expectnooutput=True)
    
            ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname, expectnooutput=True)
            ssh.run("sudo /etc/init.d/hostname.sh || sudo /etc/init.d/hostname restart")
        
        self.check_continue()

        if self.chef:        
            # Upload topology file
            log.debug("Uploading topology file", node)
            ssh.scp("%s/topology.rb" % instance_dir,
                    "/chef/cookbooks/demogrid/attributes/topology.rb")             
            
            # Copy certificates
            log.debug("Copying certificates", node)
            ssh.scp_dir("%s/certs" % instance_dir, 
                        "/chef/cookbooks/demogrid/files/default/")
    
            # Upload extra files
            log.debug("Copying extra files", node)
            for src, dst in self.deployer.extra_files:
                ssh.scp(src, dst)
            
            self.check_continue()

        #if self.deployer.loglevel == 0:
        #    print "   \033[1;37m%s\033[0m: Basic setup is done. Installing Grid software now." % node.hostname.split(".")[0]
        
            # Run chef
            log.debug("Running chef", node)
            ssh.run("echo -e \"cookbook_path \\\"/chef/cookbooks\\\"\\nrole_path \\\"/chef/roles\\\"\" > /home/borja/test.conf")        
            ssh.run("echo '{ \"run_list\": [ %s ], \"scratch_dir\": \"%s\", \"domain_id\": \"%s\", \"node_id\": \"%s\"  }' > /tmp/chef.json" % (",".join("\"%s\"" % r for r in node.run_list), self.config.get("scratch-dir"), domain.id, node.id), expectnooutput=True)
            ssh.run("sudo -i chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    
    
            self.check_continue()

        if self.basic:
            ssh.run("sudo update-rc.d nis defaults")     

        for cmd in self.deployer.run_cmds:
            ssh.run(cmd)

        log.info("Configuration done.", node)
        
        #if self.deployer.loglevel == 0:
        #    print "   \033[1;37m%s\033[0m is ready." % node.hostname.split(".")[0]    