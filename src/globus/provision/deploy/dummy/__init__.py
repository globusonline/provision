from demogrid.common.threads import DemoGridThread
import sys
from demogrid.common import log
from demogrid.core.deploy import BaseDeployer, VM, ConfigureThread, WaitThread
from demogrid.core.topology import Node

class DummyVM(VM):
    def __init__(self):
        VM.__init__(self)
        
class Deployer(BaseDeployer):
  
    def __init__(self, *args, **kwargs):
        BaseDeployer.__init__(self, *args, **kwargs)

    def set_instance(self, inst):
        self.instance = inst
        
    def allocate_vm(self, node):
        log.info("Allocated dummy VM.")     
        return DummyVM()

    def resume_vm(self, node):
        log.info("Resumed dummy VM.")     
        return DummyVM()

    def post_allocate(self, node, vm):
        node.hostname = "%s.demogrid.example.org" % node.id
        node.ip = "1.2.3.4"

    def get_node_vm(self, nodes):
        node_vm = {}
        for n in nodes:
            node_vm[n] = DummyVM()
        return node_vm

    def stop_vms(self, nodes):
        log.info("Dummy nodes terminated.")         

    def terminate_vms(self, nodes):
        log.info("Dummy nodes terminated.")               
            
    class NodeWaitThread(WaitThread):
        def __init__(self, multi, name, node, vm, deployer, state, depends = None):
            WaitThread.__init__(self, multi, name, node, vm, deployer, state, depends)
                        
        def wait(self):
            log.info("Waiting for state %s" % Node.state_str[self.state])
            
    class NodeConfigureThread(ConfigureThread):
        def __init__(self, multi, name, node, vm, deployer, depends = None, basic = True, chef = True):
            ConfigureThread.__init__(self, multi, name, node, vm, deployer, depends, basic, chef)
            
        def run2(self):
            topology = self.deployer.instance.topology
            
            self.node.state = Node.STATE_CONFIGURING
            topology.save()
    
            self.node.state = Node.STATE_RUNNING
            topology.save()            
            log.info("Dummy configure done")
            