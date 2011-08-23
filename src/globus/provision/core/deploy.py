# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                 #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

from globus.provision.common.threads import GPThread
from globus.provision.common.ssh import SSH
from globus.provision.common import log
import sys
from globus.provision.core.topology import Node

class DeploymentException(Exception):
    """A simple exception class used for deployment exceptions"""
    pass

class BaseDeployer(object):
    def __init__(self, extra_files = [], run_cmds = []):
        self.instance = None
        self.extra_files = extra_files
        self.run_cmds = run_cmds
        
class VM(object):
    def __init__(self):
        pass
    
class WaitThread(GPThread):
    def __init__(self, multi, name, node, vm, deployer, state, depends):
        GPThread.__init__(self, multi, name, depends)
        self.node = node
        self.vm = vm
        self.deployer = deployer
        self.state = state

    def run2(self):
        topology = self.deployer.instance.topology
        
        self.wait()
        
        self.node.state = self.state
        topology.save()
    
class ConfigureThread(GPThread):
    def __init__(self, multi, name, node, vm, deployer, depends = None, basic = True, chef = True):
        GPThread.__init__(self, multi, name, depends)
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

        log.debug("Establishing SSH connection", node)
        ssh = SSH(username, hostname, keyfile, default_outf = None, default_errf = None)
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
                    "/chef/cookbooks/provision/files/default/hosts")             
            ssh.run("sudo cp /chef/cookbooks/provision/files/default/hosts /etc/hosts", expectnooutput=True)
    
            ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname, expectnooutput=True)
            ssh.run("sudo /etc/init.d/hostname.sh || sudo /etc/init.d/hostname restart", expectnooutput=True)
        
        self.check_continue()

        if self.chef:        
            # Upload topology file
            log.debug("Uploading topology file", node)
            ssh.scp("%s/topology.rb" % instance_dir,
                    "/chef/cookbooks/provision/attributes/topology.rb")             
            
            # Copy certificates
            log.debug("Copying certificates", node)
            ssh.scp_dir("%s/certs" % instance_dir, 
                        "/chef/cookbooks/provision/files/default/")
    
            # Upload extra files
            log.debug("Copying extra files", node)
            for src, dst in self.deployer.extra_files:
                ssh.scp(src, dst)
            
            self.check_continue()

            # Run chef
            log.debug("Running chef", node)
            ssh.run("echo -e \"cookbook_path \\\"/chef/cookbooks\\\"\\nrole_path \\\"/chef/roles\\\"\" > /tmp/chef.conf", expectnooutput=True)        
            ssh.run("echo '{ \"run_list\": [ %s ], \"scratch_dir\": \"%s\", \"domain_id\": \"%s\", \"node_id\": \"%s\"  }' > /tmp/chef.json" % (",".join("\"%s\"" % r for r in node.run_list), self.config.get("scratch-dir"), domain.id, node.id), expectnooutput=True)
            ssh.run("sudo -i chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    
    
            self.check_continue()

        if self.basic:
            ssh.run("sudo update-rc.d nis defaults")     

        for cmd in self.deployer.run_cmds:
            ssh.run(cmd)

        log.info("Configuration done.", node)
