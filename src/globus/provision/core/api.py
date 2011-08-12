import sys
import traceback

from boto.exception import EC2ResponseError

import globus.provision.deploy.ec2 as ec2_deploy
import globus.provision.deploy.dummy as dummy_deploy

from globus.provision.core.topology import Topology, Node
from globus.provision.core.instance import InstanceStore, InstanceException
from globus.provision.common.threads import MultiThread
from globus.provision.common.ssh import SSHCommandFailureException
from globus.provision.common import log
from globus.provision.common.config import ConfigException
from globus.provision.common.persistence import ObjectValidationException

class API(object):
    
    STATUS_SUCCESS = 0
    STATUS_FAIL = 1
    
    def __init__(self, instances_dir):
        self.instances_dir = instances_dir
        
    def instance_create(self, topology_json, config_txt):
        try:
            istore = InstanceStore(self.instances_dir)
            inst = istore.create_new_instance(topology_json, config_txt)
        except ConfigException, cfge:
            message = "Error in configuration file: %s" % cfge
            return (API.STATUS_FAIL, message, None)
        except ObjectValidationException, ove:
            message = "Error in topology file: %s" % ove
            return (API.STATUS_FAIL, message, None)        
        except:
            message = self.__unexpected_exception_to_text(what = "creating a new instance.")
            return (API.STATUS_FAIL, message, None)
        
        return (API.STATUS_SUCCESS, "Success", inst.id)

    def instance(self, inst_id):
        (success, message, inst) = self.__get_instance(inst_id)
        
        if not success:
            return (API.STATUS_FAIL, message)
                
        try:
            json_string = inst.topology.to_json_string()
        except:
            message = self.__unexpected_exception_to_text(what = "accessing the instance's topology.")
            return (API.STATUS_FAIL, message, None)
        
        return (API.STATUS_SUCCESS, "Success", json_string)
        
    def instance_start(self, inst_id, extra_files, run_cmds):
        
        (success, message, inst) = self.__get_instance(inst_id)
        
        if not success:
            return (API.STATUS_FAIL, message)
            
        try:
            if inst.topology.state == Topology.STATE_NEW:
                resuming = False
            elif inst.topology.state == Topology.STATE_STOPPED:
                resuming = True
            else:
                message = "Cannot start an instance that is in state '%s'" % (Topology.state_str[inst.topology.state])
                return (API.STATUS_FAIL, message)
            
            if not resuming:
                inst.topology.state = Topology.STATE_STARTING
            else:
                inst.topology.state = Topology.STATE_RESUMING
    
            inst.topology.save()
            
            deployer_class = self.__get_deployer_class(inst)
            deployer = deployer_class(extra_files, run_cmds)
            deployer.set_instance(inst)    
            
            nodes = inst.topology.get_nodes()
    
            (success, message, node_vm) = self.__allocate_vms(deployer, nodes, resuming)
            
            if not success:
                inst.topology.state = Topology.STATE_FAILED
                inst.topology.save()
                return (API.STATUS_FAIL, message)
    
            inst.topology.state = Topology.STATE_CONFIGURING
            inst.topology.save()
                          
            log.info("Instances are running.")
    
            for node, vm in node_vm.items():
                deployer.post_allocate(node, vm)

            inst.topology.save()
    
            # Generate certificates
            if not resuming:
                inst.gen_certificates(force_hosts=False, force_users=False)
            else:
                inst.gen_certificates(force_hosts=True, force_users=False)    
            
            inst.topology.gen_chef_ruby_file(inst.instance_dir + "/topology.rb")
            inst.topology.gen_hosts_file(inst.instance_dir + "/hosts")               
    
            log.info("Setting up Globus Provision on instances")        
            
            (success, message) = self.__configure_vms(deployer, node_vm)
            if not success:
                inst.topology.state = Topology.STATE_FAILED
                inst.topology.save()
                return (API.STATUS_FAIL, message)
    
            inst.topology.state = Topology.STATE_RUNNING
            inst.topology.save()
            
            return (API.STATUS_SUCCESS, "Success")
        except:
            message = self.__unexpected_exception_to_text(what = "starting the instance.")
            try:
                if inst != None:
                    inst.topology.state = Topology.STATE_FAILED
                    inst.topology.save()
            except:
                message += "\nNote: Unable to update instance's state to 'Failed'"
            return (API.STATUS_FAIL, message)


    def instance_update(self, inst_id, topology_json, extra_files, run_cmds):
        try:
            (success, message, inst) = self.__get_instance(inst_id)
            
            if not success:
                return (API.STATUS_FAIL, message)
                
            if inst.topology.state != Topology.STATE_RUNNING:
                message = "Cannot update the topology of an instance that is in state '%s'" % (Topology.state_str[inst.topology.state])
                return (API.STATUS_FAIL, message)        
    
            old_topology = inst.topology
            try:
                (success, message, create_hosts, destroy_hosts) = inst.update_topology(topology_json)
            except ObjectValidationException, ove:
                message = "Error in topology file: %s" % ove
                return (API.STATUS_FAIL, message)   

            deployer_class = self.__get_deployer_class(inst)
            deployer = deployer_class(extra_files, run_cmds)
            deployer.set_instance(inst)            

            nodes = inst.topology.get_nodes()

            if len(destroy_hosts) > 0:
                old_nodes = old_topology.get_nodes()
                log.info("Terminating hosts %s" % destroy_hosts)   
                old_nodes = [n for n in old_nodes if n.id in destroy_hosts]
                (success, message) = self.__terminate_vms(deployer, old_nodes)
                
                if not success:
                    inst.topology.state = Topology.STATE_FAILED
                    inst.topology.save()
                    return (API.STATUS_FAIL, message)       
                
                inst.topology.save()         
                  
            if len(create_hosts) > 0:
                nodes = inst.topology.get_nodes()
                log.info("Allocating VMs for hosts %s" % create_hosts)   
                new_nodes = [n for n in nodes if n.id in create_hosts]
                (success, message, node_vm) = self.__allocate_vms(deployer, new_nodes, resuming = False)
        
                if not success:
                    inst.topology.state = Topology.STATE_FAILED
                    inst.topology.save()
                    return (API.STATUS_FAIL, message)
            
                inst.topology.save()
                
                for node, vm in node_vm.items():
                    deployer.post_allocate(node, vm)

                inst.topology.save()

            # Generate certificates
            inst.gen_certificates()

            inst.topology.gen_chef_ruby_file(inst.instance_dir + "/topology.rb")
            inst.topology.gen_hosts_file(inst.instance_dir + "/hosts")               

            log.info("Setting up Globus Provision on instances")        
            
            # Right now we reconfigure all nodes. It shouldn't be hard to follow
            # the dependency tree to make sure only the new nodes and "ancestor"
            # nodes are updated
            node_vm = deployer.get_node_vm(nodes)
            (success, message) = self.__configure_vms(deployer, node_vm)
            if not success:
                inst.topology.state = Topology.STATE_FAILED
                inst.topology.save()
                return (API.STATUS_FAIL, message)
    
            inst.topology.state = Topology.STATE_RUNNING
            inst.topology.save()
            
            return (API.STATUS_SUCCESS, "Success")
        except:
            message = self.__unexpected_exception_to_text(what = "starting the instance.")
            try:
                if inst != None:
                    inst.topology.state = Topology.STATE_FAILED
                    inst.topology.save()
            except:
                message += "\nNote: Unable to update instance's state to 'Failed'"
            return (API.STATUS_FAIL, message)


    def instance_stop(self, inst_id):
        (success, message, inst) = self.__get_instance(inst_id)
        
        if not success:
            return (API.STATUS_FAIL, message)
        
        try:
            if inst.topology.state != Topology.STATE_RUNNING:
                message = "Cannot start an instance that is in state '%s'" % (Topology.state_str[inst.topology.state])
                return (API.STATUS_FAIL, message)
        
            inst.topology.state = Topology.STATE_STOPPING
            inst.topology.save()
            
            deployer_class = self.__get_deployer_class(inst)
            deployer = deployer_class()
            deployer.set_instance(inst)    
            
            nodes = inst.topology.get_nodes()            
    
            (success, message) = self.__stop_vms(deployer, nodes)
            
            if not success:
                inst.topology.state = Topology.STATE_FAILED
                inst.topology.save()
                return (API.STATUS_FAIL, message)            
        
            inst.topology.state = Topology.STATE_STOPPED
            inst.topology.save()
              
            log.info("Instances have been stopped running.")
            return (API.STATUS_SUCCESS, "Success")
        except:
            message = self.__unexpected_exception_to_text(what = "starting the instance.")
            try:
                if inst != None:
                    inst.topology.state = Topology.STATE_FAILED
                    inst.topology.save()
            except:
                message += "\nNote: Unable to update instance's state to 'Failed'"
            return (API.STATUS_FAIL, message)


    def instance_terminate(self, inst_id):
        (success, message, inst) = self.__get_instance(inst_id)
        
        if not success:
            return (API.STATUS_FAIL, message)
        
        try:
            if inst.topology.state in [Topology.STATE_NEW]:
                message = "Cannot terminate an instance that is in state '%s'" % (Topology.state_str[inst.topology.state])
                return (API.STATUS_FAIL, message)
        
            inst.topology.state = Topology.STATE_TERMINATING
            inst.topology.save()
            
            deployer_class = self.__get_deployer_class(inst)
            deployer = deployer_class()
            deployer.set_instance(inst)    
            
            nodes = inst.topology.get_nodes()            
    
            (success, message) = self.__terminate_vms(deployer, nodes)
            
            if not success:
                inst.topology.state = Topology.STATE_FAILED
                inst.topology.save()
                return (API.STATUS_FAIL, message)            
        
            inst.topology.state = Topology.STATE_TERMINATED
            inst.topology.save()
              
            log.info("Instances have been stopped running.")
            return (API.STATUS_SUCCESS, "Success")
        except:
            message = self.__unexpected_exception_to_text(what = "starting the instance.")
            try:
                if inst != None:
                    inst.topology.state = Topology.STATE_FAILED
                    inst.topology.save()
            except:
                message += "\nNote: Unable to update instance's state to 'Failed'"
            return (API.STATUS_FAIL, message)


    def instance_list(self, inst_ids):
        istore = InstanceStore(self.instances_dir)
        
        if inst_ids == None:
            insts = istore.get_instances()
        else:
            insts = [istore.get_instance(inst_id) for inst_id in inst_ids]
                
        # TODO: Return JSON
        return insts

        
    def __get_instance(self, inst_id):
        try:
            istore = InstanceStore(self.instances_dir)
            inst = istore.get_instance(inst_id)
            return (True, "Success", inst)
        except ConfigException, cfge:
            message = "Error in configuration file: %s" % cfge
            return (False, message, None)
        except ObjectValidationException, ove:
            message = "Error in topology file: %s" % ove
            return (False, message, None)        
        except InstanceException, ie:
            return (False, str(ie), None)
        except:
            message = self.__unexpected_exception_to_text(what = "accessing the instance.")
            return (False, message, None)    
        
    def __get_deployer_class(self, inst):
        if inst.config.get("deploy") == "ec2":
            deploy_module = ec2_deploy
        elif inst.config.get("deploy") == "dummy":
            deploy_module = dummy_deploy
            
        return deploy_module.Deployer        
        
    def __allocate_vms(self, deployer, nodes, resuming):
        # TODO: Make this an option
        sequential = False
        topology = deployer.instance.topology
        
        if not resuming:
            log.info("Allocating %i VMs." % len(nodes))
        else:
            log.info("Resuming %i VMs" % len(nodes))
        node_vm = {}
        for n in nodes:
            try:
                if not resuming:
                    n.set_property("state", Node.STATE_STARTING)
                    topology.save()
                    vm = deployer.allocate_vm(n)
                else:
                    n.set_property("state", Node.STATE_RESUMING)
                    topology.save()
                    vm = deployer.resume_vm(n)
                node_vm[n] = vm
            except Exception:
                message = self.__unexpected_exception_to_text()
                return (False, message, None)
        
            if sequential:
                log.debug("Waiting for instance to start.")
                wait = deployer.NodeWaitThread(None, "wait-%s" % str(vm), n, vm, deployer, state = Node.STATE_RUNNING_UNCONFIGURED)
                wait.run2()
                
        if not sequential:        
            log.debug("Waiting for instances to start.")
            mt_instancewait = MultiThread()
            for node, vm in node_vm.items():
                mt_instancewait.add_thread(deployer.NodeWaitThread(mt_instancewait, "wait-%s" % str(vm), node, vm, deployer, state = Node.STATE_RUNNING_UNCONFIGURED))

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
                            n, 
                            node_vm[n], 
                            deployer, 
                            depends=threads.get(topology.get_depends(n)),
                            basic = basic,
                            chef = chef)) for n in nodeset])
            threads.update(rest)
        
        for thread in threads.values():
            mt_configure.add_thread(thread)
        
        mt_configure.run()
        if not mt_configure.all_success():
            message = self.__mt_exceptions_to_text(mt_configure.get_exceptions(), "Globus Provision was unable to configure the instances.")
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
        msg = "An unexpected '%s' exception has been raised%s\n\n" % (exc_type.__name__, what)
        msg += "Message: %s\n\n" % exc_value
        trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for l in trace:
            msg += l
        return msg


    def __stop_vms(self, deployer, nodes):
        topology = deployer.instance.topology
        order = topology.get_launch_order(nodes)
        order.reverse()
        
        for nodeset in order:
            deployer.stop_vms(nodeset)
        
        node_vm = deployer.get_node_vm(nodes)
        
        log.debug("Waiting for instances to stop.")
        mt_instancewait = MultiThread()
        for node, vm in node_vm.items():
            mt_instancewait.add_thread(deployer.NodeWaitThread(mt_instancewait, "wait-%s" % str(vm), node, vm, deployer, state = Node.STATE_STOPPED))
        
        mt_instancewait.run()
        if not mt_instancewait.all_success():
            message = self.__mt_exceptions_to_text(mt_instancewait.get_exceptions(), "Exception raised while waiting for instances.")
            return (False, message)
            
        return (True, "Success")
        
    def __terminate_vms(self, deployer, nodes):
        topology = deployer.instance.topology

        deployer.terminate_vms(nodes)
        
        node_vm = deployer.get_node_vm(nodes)
        
        log.debug("Waiting for instances to terminate.")
        mt_instancewait = MultiThread()
        for node, vm in node_vm.items():
            mt_instancewait.add_thread(deployer.NodeWaitThread(mt_instancewait, "wait-%s" % str(vm), node, vm, deployer, state = Node.STATE_TERMINATED))
        
        mt_instancewait.run()
        if not mt_instancewait.all_success():
            message = self.__mt_exceptions_to_text(mt_instancewait.get_exceptions(), "Exception raised while waiting for instances.")
            return (False, message)
            
        return (True, "Success")
        
        