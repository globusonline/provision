import os
import os.path
import sys
import shutil


from demogrid.core.topology import Topology, Domain, Node, User
from demogrid.common.certs import CertificateGenerator
from demogrid.core.instance import Instance, InstanceStore
from demogrid.common.utils import parse_extra_files_files, MultiThread,\
    SSHCommandFailureException, SIGINTWatcher
from demogrid.common import log
from boto.exception import EC2ResponseError
import traceback
from copy import deepcopy
import json

import demogrid.deploy.ec2 as ec2_deploy
import demogrid.deploy.dummy as dummy_deploy

class API(object):
    
    def __init__(self, demogrid_dir, instances_dir):
        self.demogrid_dir = demogrid_dir
        self.instances_dir = instances_dir

    def create(self, topology_json, config_txt):
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.create_new_instance(topology_json, config_txt)
        
        print inst.id
        
    def start(self, inst_id, no_cleanup, extra_files, run_cmds):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        inst = istore.get_instance(inst_id)
        
        if inst.topology.state == Topology.STATE_NEW:
            resuming = False
        elif inst.topology.state == Topology.STATE_STOPPED:
            resuming = True
        else:
            resuming = True
            #print "Error, can't start"
            #exit(1)
        
        if not resuming:
            inst.topology.state = Topology.STATE_STARTING
        else:
            inst.topology.state = Topology.STATE_RESUMING
        inst.topology.save()
        
        deployer_class = self.__get_deployer_class(inst)
        
        deployer = deployer_class(self.demogrid_dir, no_cleanup, extra_files, run_cmds)
        deployer.set_instance(inst)    
        
        nodes = inst.topology.get_nodes()

        (success, message, node_vm) = self.__allocate_vms(deployer, nodes, resuming)
        
        if not success:
            deployer.cleanup()
            return (False, message)
          
        log.info("Instances are running.")

        for (domain, node), vm in node_vm.items():
            deployer.post_allocate(domain, node, vm)

        # Generate certificates
        if not resuming:
            inst.gen_certificates(force_hosts=False, force_users=False)
        else:
            inst.gen_certificates(force_hosts=True, force_users=False)    
        
        inst.topology.gen_chef_ruby_file(inst.instance_dir + "/topology.rb")
        inst.topology.gen_hosts_file(inst.instance_dir + "/hosts")               

        inst.topology.save()

        log.info("Setting up DemoGrid on instances")        
        
        (success, message) = self.__configure_vms(deployer, node_vm)
        if not success:
            deployer.cleanup()
            return (False, message)

        inst.topology.state = Topology.STATE_RUNNING
        inst.topology.save()
        
        return (True, "Success")


    def update_topology(self, inst_id, topology_json, no_cleanup, extra_files):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        inst = istore.get_instance(inst_id)
        
        inst.update_topology(topology_json)
        
        deployer_class = self.__get_deployer_class(inst)
        
        deployer = deployer_class(self.demogrid_dir, no_cleanup, extra_files)
        deployer.set_instance(inst)    
        
        nodes = inst.topology.get_nodes()

        # Generate certificates
        inst.gen_certificates()

        for n in nodes:
            n.gen_chef_attrs()        
        inst.topology.save()
        
        inst.topology.gen_ruby_file(inst.instance_dir + "/topology.rb")
        inst.topology.gen_hosts_file(inst.instance_dir + "/hosts") 
        inst.topology.gen_csv_file(inst.instance_dir + "/topology.csv")

        log.info("Setting up DemoGrid on instances")        

        node_vm = deployer.get_node_vm(nodes)
        
        self.__configure_vms(deployer, node_vm)

        inst.topology.state = Topology.STATE_RUNNING
        inst.topology.save()


    def stop(self, inst_id):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        inst.topology.state = Topology.STATE_STOPPING
        inst.topology.save()
        
        deployer_class = self.__get_deployer_class(inst)
        
        deployer = deployer_class(self.demogrid_dir)
        deployer.set_instance(inst)    
        
        nodes = inst.topology.get_nodes()

        self.__stop_vms(deployer, nodes)
          
        inst.topology.state = Topology.STATE_STOPPED
        inst.topology.save()


    def terminate(self, inst_id):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        inst.topology.state = Topology.STATE_TERMINATING
        inst.topology.save()
        
        deployer_class = self.__get_deployer_class(inst)
        
        deployer = deployer_class(self.demogrid_dir)
        deployer.set_instance(inst)    
        
        nodes = inst.topology.get_nodes()

        deployer.terminate_vms(nodes)
          
        inst.topology.state = Topology.STATE_TERMINATED
        inst.topology.save()
        
    def add_hosts(self, inst_id, hosts_json, no_cleanup, extra_files):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        topology = inst.topology

        deployer_class = self.__get_deployer_class(inst)
        
        deployer = deployer_class(self.demogrid_dir, no_cleanup, extra_files)
        deployer.set_instance(inst)

        existing_nodes = inst.topology.get_nodes()
        existing_nodes_vm = deployer.get_node_vm(existing_nodes)
                        
        # We assume there's only one domain.
        domain = inst.topology.domains.values()[0]

        json_nodes = json.loads(hosts_json)
        nodes = []
        for node in json_nodes:
            node_obj = Node.from_json(node, domain, topology.default_deploy_data)
            if topology.get_node_by_id(node_obj.node_id) == None:           
                topology.add_domain_node(domain, node_obj)
                nodes.append(node_obj)
            else:
                print "Node %s already exists" % (node_obj.node_id)
                
        for node in nodes:
            if node.depends != None:
                depends_node = topology.get_node_by_id(node.depends[5:])
                node.depends = depends_node                   

        node_vm = self.__allocate_vms(deployer, nodes, resuming=False)

        for node, vm in node_vm.items():
            deployer.post_allocate(node, vm)
        topology.save()

        # Generate certificates
        inst.gen_certificates()

        for n in nodes:
            n.gen_chef_attrs()        
        topology.save()
        
        inst.topology.gen_ruby_file(inst.instance_dir + "/topology.rb")
        inst.topology.gen_hosts_file(inst.instance_dir + "/hosts") 
        inst.topology.gen_csv_file(inst.instance_dir + "/topology.csv")                

        # TODO: Update hosts file on existing nodes
        log.info("Updating existing nodes")        
        self.__configure_vms(deployer, existing_nodes_vm, chef = False)

        log.info("Setting up DemoGrid on instances")        
        self.__configure_vms(deployer, node_vm)
        topology.save()


    def list_instances(self, inst_ids):
        istore = InstanceStore(self.instances_dir)
        
        if inst_ids == None:
            insts = istore.get_instances()
        else:
            insts = [istore.get_instance(inst_id) for inst_id in inst_ids]
                
        # TODO: Return JSON
        return insts

                        
    def remove_hosts(self, inst_id, hosts):
        SIGINTWatcher(self.cleanup_after_kill)
        
        istore = InstanceStore(self.instances_dir)
        
        inst = istore.get_instance(inst_id)
        topology = inst.topology

        deployer_class = self.__get_deployer_class(inst)
        
        deployer = deployer_class(self.demogrid_dir)
        deployer.set_instance(inst)
                        
        # We assume there's only one domain.
        domain = inst.topology.domains.values()[0]
        
        nodes = []
        for host in hosts:
            node = topology.get_node_by_id(host)
            if node == None:
                print "Warning: Node %s is not part of this topology" % host
            else:
                nodes.append(node)
        
        if len(nodes) > 0:
            deployer.terminate_vms(nodes)
            topology.remove_nodes(nodes)
        topology.save()
        
             
    def cleanup_after_kill(self):
        print "DemoGrid has been unexpectedly killed and cannot release EC2 resources."
        print "Please make sure you manually release all DemoGrid instances and volumes."
        
    def __get_deployer_class(self, inst):
        if inst.config.get("deploy") == "ec2":
            deploy_module = ec2_deploy
        elif inst.config.get("deploy") == "dummy":
            deploy_module = dummy_deploy
            
        return deploy_module.Deployer        
        
    def __allocate_vms(self, deployer, nodes, resuming):
        # TODO: Make this an option
        sequential = False
        
        if not resuming:
            log.info("Allocating %i VMs." % len(nodes))
        else:
            log.info("Resuming %i VMs" % len(nodes))
        node_vm = {}
        for (domain, n) in nodes:
            try:
                if not resuming:
                    vm = deployer.allocate_vm(n)
                else:
                    vm = deployer.resume_vm(n)
                node_vm[(domain, n)] = vm
            except Exception:
                message = self.__unexpected_exception_to_text()
                return (False, message, None)
        
            if sequential:
                log.debug("Waiting for instance to start.")
                wait = deployer.NodeWaitThread(None, "wait-%s" % str(vm), n, vm, deployer)
                wait.run2()
                
        if not sequential:        
            log.debug("Waiting for instances to start.")
            mt_instancewait = MultiThread()
            for node, vm in node_vm.items():
                mt_instancewait.add_thread(deployer.NodeWaitThread(mt_instancewait, "wait-%s" % str(vm), node, vm, deployer))
            
            mt_instancewait.run()
            if not mt_instancewait.all_success():
                message = self.__mt_exceptions_to_text(mt_instancewait.get_exceptions(), "Exception raised while waiting for instances.")
                return (False, message, None)
            
        return (True, "Success", node_vm)


    def __configure_vms(self, deployer, node_vm, basic = True, chef = True):
        nodes = node_vm.keys()
        mt_configure = MultiThread()
        topology = deployer.instance.topology
        order = topology.get_launch_order(nodes)
        
        threads = {}
        for nodeset in order:
            rest = dict([(n, deployer.NodeConfigureThread(mt_configure, 
                            "configure-%s" % n.id, 
                            d,
                            n, 
                            node_vm[(d,n)], 
                            deployer, 
                            depends=threads.get(topology.get_depends(n)),
                            basic = basic,
                            chef = chef)) for d, n in nodeset])
            threads.update(rest)
        
        for thread in threads.values():
            mt_configure.add_thread(thread)
        
        mt_configure.run()
        if not mt_configure.all_success():
            message = self.__mt_exceptions_to_text(mt_configure.get_exceptions(), "DemoGrid was unable to configure the instances.")
            return (False, message)
        
        return (True, "Success")

    def __mt_exceptions_to_text(self, exceptions, what):
        msg = "ERROR - " + what
        for thread_name in exceptions:
            msg += "\n\n"
            exception_obj, exception_trace = exceptions[thread_name]
            if isinstance(exception_obj, SSHCommandFailureException):
                msg += "        %s: Error while running '%s'\n" % (thread_name, exception_obj.command)
            elif isinstance(exception_obj, EC2ResponseError):
                msg += "        %s: EC2 error '%s'\n" % (thread_name, exception_obj.reason)
                msg += "        Body: %s\n" % exception_obj.body
            else:          
                msg += "        %s: Unexpected exception '%s'\n" % (thread_name, exception_obj.__class__.__name__)
                msg += "        Message: %s\n" % exception_obj
            for l in exception_trace:
                msg += l
        return msg

            
    def __unexpected_exception_to_text(self, what=""):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if what != "": what = " when " + what
        msg = "ERROR - An unexpected '%s' exception has been raised" % what
        msg += "        Message: %s\n" % exc_value
        msg += "        Stack trace:\n"
        trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for l in trace:
            msg += l
        return msg


    def __stop_vms(self, deployer, nodes):
        order = Node.get_launch_order(nodes)
        order.reverse()
        
        for nodeset in order:
            deployer.stop_vms(nodeset)
        
        