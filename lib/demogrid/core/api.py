import os
import os.path
import sys
import shutil


from demogrid.core.topology import Topology, Domain, Node, User
from demogrid.common.certs import CertificateGenerator
from demogrid.core.instance import Instance, InstanceStore
from demogrid.common.utils import parse_extra_files_files, MultiThread,\
    SSHCommandFailureException, SIGINTWatcher
from demogrid.vm.ec2.deploy import EC2Deployer, EC2InstanceWaitThread,\
    EC2InstanceConfigureThread
from demogrid.common import log
from boto.exception import EC2ResponseError
import traceback
from copy import deepcopy
import json

try:
    from mako.template import Template
except Exception, e:
    print "Mako Templates for Python are not installed."
    print "You can download them at http://www.makotemplates.org/"
    print "or 'apt-get install python-mako' on most Debian/Ubuntu systems"
    exit(1)

class API(object):
    
    def __init__(self, demogrid_dir, instances_dir):
        self.demogrid_dir = demogrid_dir
        self.instances_dir = instances_dir

    def create(self, topology_json, config_txt):
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.create_new_instance(topology_json, config_txt)
        
        print inst.id
        

    def __allocate_vms(self, deployer, nodes):
        log.info("Allocating %i VMs." % len(nodes))
        node_vm = {}
        for n in nodes:
            try:
                vm = deployer.allocate_vm(n)
                node_vm[n] = vm
            except Exception as exc:
                raise
        
                #self.handle_unexpected_exception(exc)
        log.debug("Waiting for instances to start.")
        mt_instancewait = MultiThread()
        for node, vm in node_vm.items():
            mt_instancewait.add_thread(EC2InstanceWaitThread(mt_instancewait, "wait-%s" % str(vm), node, vm, deployer))
        
        mt_instancewait.run()
        if not mt_instancewait.all_success():
            self.handle_mt_exceptions(mt_instancewait.get_exceptions(), "Exception raised while waiting for instances.")
        
        return node_vm


    def __configure_vms(self, deployer, node_vm):
        nodes = node_vm.keys()
        mt_configure = MultiThread()
        parents = [n for n in nodes if n.depends == None]
        threads = {}
        while len(parents) > 0:
            rest = dict([(n, EC2InstanceConfigureThread(mt_configure, 
                            "configure-%s" % n.node_id, 
                            n, 
                            i, 
                            deployer, 
                            depends=threads.get(n.depends))) for (n, i) in node_vm.items() if n in parents])
            threads.update(rest)
            parents = [n for n in nodes if n.depends in parents]
        
        for thread in threads.values():
            mt_configure.add_thread(thread)
        
        mt_configure.run()
        if not mt_configure.all_success():
            self.handle_mt_exceptions(mt_configure.get_exceptions(), "DemoGrid was unable to configure the instances.")

    def start(self, inst_id, no_cleanup, extra_files):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        inst.topology.state = Topology.STATE_STARTING
        inst.topology.save()
        
        # TODO: Choose the right deployer based on config file
        deployer = EC2Deployer(self.demogrid_dir, no_cleanup, extra_files)

        deployer.set_instance(inst)    
        
        nodes = inst.topology.get_nodes()

        node_vm = self.__allocate_vms(deployer, nodes)
          
        log.info("Instances are running.")

        for node, vm in node_vm.items():
            deployer.post_allocate(node, vm)

        # Generate certificates
        inst.gen_certificates(force_certificates=False)

        for n in nodes:
            n.gen_chef_attrs()        
        
        inst.topology.gen_ruby_file(inst.instance_dir + "/topology.rb")
        inst.topology.gen_hosts_file(inst.instance_dir + "/hosts") 
        inst.topology.gen_csv_file(inst.instance_dir + "/topology.csv")                

        inst.topology.save()

        log.info("Setting up DemoGrid on instances")        
        
        self.__configure_vms(deployer, node_vm)

        inst.topology.state = Topology.STATE_RUNNING
        inst.topology.save()

        
    def add_hosts(self, inst_id, hosts_json, no_cleanup, extra_files):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        topology = inst.topology

        deployer = EC2Deployer(self.demogrid_dir, no_cleanup, extra_files)
        deployer.set_instance(inst)
                        
        # We assume there's only one domain.
        domain = inst.topology.domains.values()[0]

        json_nodes = json.loads(hosts_json)
        nodes = []
        for node in json_nodes:
            node_obj = Node.from_json(node, domain)
            node_obj.deploy_data.update(deepcopy(topology.default_deploy_data))     
            if topology.get_node_by_id(node_obj.node_id) == None:           
                topology.add_domain_node(domain, node_obj)
                nodes.append(node_obj)
            else:
                "Node %s already exists" % (node_obj.node_id)
            
        topology.save()

        node_vm = self.__allocate_vms(deployer, nodes)

        for node, vm in node_vm.items():
            deployer.post_allocate(node, vm)

        # Generate certificates
        inst.gen_certificates(force_certificates=False)

        for n in nodes:
            n.gen_chef_attrs()        
        
        inst.topology.gen_ruby_file(inst.instance_dir + "/topology.rb")
        inst.topology.gen_hosts_file(inst.instance_dir + "/hosts") 
        inst.topology.gen_csv_file(inst.instance_dir + "/topology.csv")                

        # TODO: Update hosts file on existing nodes

        log.info("Setting up DemoGrid on instances")        

        self.__configure_vms(deployer, node_vm)
                        

    def handle_unexpected_exception(self, exc, what=""):
        if what != "": what = " when " + what
        print "\033[1;31mERROR\033[0m - An unexpected '%s' exception has been raised" % what
        print "        Message: %s" % exc
        print "        Stack trace:"
        traceback.print_exc()
        self.cleanup()
        exit(1)        

    def handle_mt_exceptions(self, exceptions, what):
        print "\033[1;31mERROR\033[0m - " + what
        for name, exception in exceptions.items():
            if isinstance(exception, SSHCommandFailureException):
                print "        %s: Error while running '%s'" % (name, exception.command)
            elif isinstance(exception, EC2ResponseError):
                print "        %s: EC2 error '%s'" % (name, exception.reason)
                print "        Body: %s" % exception.body
            else:          
                print "        %s: Unexpected exception '%s'" % (name, exception.__class__.__name__)
                print "        Message: %s" % exception
            
        self.cleanup()
        exit(1)
        
        

             
    def cleanup_after_kill(self):
        print "DemoGrid has been unexpectedly killed and cannot release EC2 resources."
        print "Please make sure you manually release all DemoGrid instances and volumes."
        
        

        
        
