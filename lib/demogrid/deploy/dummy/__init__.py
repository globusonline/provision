from demogrid.common.utils import DemoGridThread
import sys
from demogrid.common import log
from demogrid.core.deploy import BaseDeployer, VM, ConfigureThread

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

    def post_allocate(self, domain, node, vm):
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

    def cleanup(self):
        log.info("Dummy cleanup is done.")        
            
    class NodeWaitThread(DemoGridThread):
        def __init__(self, multi, name, node, vm, deployer, depends = None):
            DemoGridThread.__init__(self, multi, name, depends)
            self.deployer = deployer
                        
        def run2(self):
            log.info("Dummy node is running.")
            
    class NodeConfigureThread(ConfigureThread):
        def __init__(self, multi, name, domain, node, vm, deployer, depends = None, basic = True, chef = True):
            ConfigureThread.__init__(self, multi, name, domain, node, vm, deployer, depends, basic, chef)
            
        def run2(self):
            log.info("Dummy configure done")
            