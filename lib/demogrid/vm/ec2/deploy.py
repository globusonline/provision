from cPickle import load
from boto.exception import BotoClientError, EC2ResponseError
from demogrid.common.utils import create_ec2_connection, SSH, MultiThread,\
    DemoGridThread, SSHCommandFailureException, SIGINTWatcher
import random
import time
import sys
import traceback
from demogrid.common import log
from demogrid.common.certs import CertificateGenerator
from demogrid.core.deploy import Deployer, VM, ConfigureThread

class EC2VM(VM):
    def __init__(self, ec2_instance):
        self.ec2_instance = ec2_instance
        
    def __str__(self):
        return self.ec2_instance.id

class EC2Deployer(Deployer):
  
    def __init__(self, *args, **kwargs):
        Deployer.__init__(self, *args, **kwargs)
        self.conn = None
        self.instances = None
        self.vols = []
        self.supports_create_tags = True

    def set_instance(self, inst):
        self.instance = inst
        self.__connect()
        if inst.config.get_ec2_access_type() == "public":
            inst.topology.global_attributes["ec2_public"] = "true"
        else:
            inst.topology.global_attributes["ec2_public"] = "false"            
    
    def __connect(self):
        config = self.instance.config
        keypair = config.get_keypair()
        zone = config.get_ec2_zone()
        
        try:
            log.debug("Connecting to EC2...")
            if config.has_ec2_hostname():
                self.conn = create_ec2_connection(config.get_ec2_hostname(),
                                                  config.get_ec2_path(),
                                                  config.get_ec2_port()) 
            else:
                self.conn = create_ec2_connection()
            
            if self.conn == None:
                print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are not set."
                exit(1)
            log.debug("Connected to EC2.")
        except BotoClientError, exc:
            print "\033[1;31mERROR\033[0m - Could not connect to EC2."
            print "        Reason: %s" % exc.reason
            exit(1)
        except Exception, exc:
            self.handle_unexpected_exception(exc)    
        
    def allocate_vm(self, node):
        instance_type = node.deploy_data["ec2"]["instance_type"]
        ami = node.deploy_data["ec2"]["ami"]

        image = self.conn.get_image(ami)
        if image == None:
            # Workaround for this bug:
            # https://bugs.launchpad.net/eucalyptus/+bug/495670
            image = [i for i in self.conn.get_all_images() if i.id == ami][0]
        
        log.info(" |- Launching a %s instance for %s." % (instance_type, node.node_id))
        reservation = image.run(min_count=1, 
                                max_count=1,
                                instance_type=instance_type,
                                security_groups= ["default"],
                                key_name=self.instance.config.get_keypair(),
                                placement = None)
        instance = reservation.instances[0]
        
        return EC2VM(instance)

    def resume_vm(self, node):
        ec2_instance_id = node.deploy_data["ec2_instance"]

        log.info(" |- Resuming instance %s for %s." % (ec2_instance_id, node.node_id))
        started = self.conn.start_instances([ec2_instance_id])            
        log.info(" |- Resumed instance %s." % ",".join([i.id for i in started]))
        
        return EC2VM(started[0])

    def post_allocate(self, node, vm):
        instance = vm.ec2_instance
        config = self.instance.config
        
        try:
            if self.supports_create_tags:
                self.conn.create_tags([instance.id], {"Name": "%s_%s" % (self.instance.id, node.node_id)})
        except:
            # Some EC2-ish systems don't support the create_tags call.
            # If it fails, we just silently ignore it, as it is not essential,
            # but make sure not to call it again, as EC2-ish systems will
            # timeout instead of immediately returning an error
            self.supports_create_tags = False

        if instance.private_ip_address != None:
            # A correct EC2 system should return this
            node.ip = instance.private_ip_address
        else:
            # Unfortunately, some EC2-ish systems won't return the private IP address
            # We fall back on the private_dns_name, which should still work
            # (plus, some EC2-ish systems actually set this to the IP address)
            node.ip = instance.private_dns_name
        node.deploy_data["ec2_instance"] = instance.id
        node.deploy_data["public_hostname"] = "\"%s\"" % instance.public_dns_name
        # TODO: The following won't work on EC2-ish systems behind a firewall.
        node.deploy_data["public_ip"] = "\"%s\"" % ".".join(instance.public_dns_name.split(".")[0].split("-")[1:])
        if config.get_ec2_access_type() == "public":
            node.hostname = instance.public_dns_name
            node.chef_attrs["demogrid_hostname"] = "\"%s\"" % node.hostname
            node.chef_attrs["public_ip"] = "\"%s\"" % ".".join(instance.public_dns_name.split(".")[0].split("-")[1:])
        elif config.get_ec2_access_type() == "private":
            node.hostname = "%s.demogrid.example.org" % node.node_id
            node.chef_attrs["demogrid_hostname"] = "\"%s\"" % node.hostname
            node.chef_attrs["public_ip"] = "nil"

    def get_node_vm(self, nodes):
        ec2_instance_ids = [n.deploy_data["ec2_instance"] for n in nodes]
        reservations = self.conn.get_all_instances(ec2_instance_ids)
        node_vm = {}
        for r in reservations:
            instance = r.instances[0]
            node = [n for n in nodes if n.deploy_data["ec2_instance"]==instance.id][0]
            node_vm[node] = EC2VM(instance)
        return node_vm

    def stop_vms(self, nodes):
        ec2_instance_ids = [n.deploy_data["ec2_instance"] for n in nodes]
        log.info("Stopping EC2 instances %s." % ", ".join(ec2_instance_ids))
        stopped = self.conn.stop_instances(ec2_instance_ids)
        log.info("Stopped EC2 instances %s." % ", ".join([i.id for i in stopped]))

    def terminate_vms(self, nodes):
        ec2_instance_ids = [n.deploy_data["ec2_instance"] for n in nodes]
        log.info("Terminating EC2 instances %s." % ", ".join(ec2_instance_ids))
        terminated = self.conn.terminate_instances(ec2_instance_ids)
        log.info("Terminated EC2 instances %s." % ", ".join([i.id for i in terminated]))
        
    def wait_state(self, obj, state, interval = 2.0):
        jitter = random.uniform(0.0, 0.5)
        while True:
            time.sleep(interval + jitter)
            newstate = obj.update()
            if newstate == state:
                return True
        # TODO: Check errors    
        

    def cleanup(self):
        if self.no_cleanup:
            print "--no-cleanup has been specified, so DemoGrid will not release EC2 resources."
            print "Remember to do this manually"
        else:
            print "DemoGrid is attempting to release all EC2 resources..."
            try:
                if self.conn != None:
                    for v in self.vols:
                        if v.attachment_state == "attached":
                            v.detach()
                    if self.instances != None:
                        self.conn.terminate_instances([i.id for i in self.instances])
                    for v in self.vols:
                        self.wait_state(v, "available")        
                        v.delete()
                    print "DemoGrid has released all EC2 resources."
            except:
                traceback.print_exc()
                print "DemoGrid was unable to release all EC2 resources."
                if self.instances != None:
                    print "Please make sure the following instances have been terminated: " % [i.id for i in self.instances]
                if len(self.vols) > 0:
                    print "Please make sure the following volumes have been deleted: " % [v.id for v in self.vols]
        
            
class EC2InstanceWaitThread(DemoGridThread):
    def __init__(self, multi, name, node, vm, deployer, depends = None):
        DemoGridThread.__init__(self, multi, name, depends)
        self.ec2_instance = vm.ec2_instance
        self.deployer = deployer
                    
    def run2(self):
        self.deployer.wait_state(self.ec2_instance, "running")
        log.info("Instance %s is running. Hostname: %s" % (self.ec2_instance.id, self.ec2_instance.public_dns_name))
        
class EC2InstanceConfigureThread(ConfigureThread):
    def __init__(self, multi, name, node, vm, deployer, depends = None, basic = True, chef = True):
        ConfigureThread.__init__(self, multi, name, node, vm, deployer, depends, basic, chef)
        self.ec2_instance = self.vm.ec2_instance
        
    def connect(self):
        return self.ssh_connect(self.config.get_ec2_username(), self.ec2_instance.public_dns_name, self.config.get_keyfile())
    
    def pre_configure(self, ssh):
        node = self.node
        instance = self.ec2_instance
        
        log.info("Setting up instance %s. Hostname: %s" % (instance.id, instance.public_dns_name), node)
        if self.chef and self.config.has_snap():
            log.debug("Creating Chef volume.", node)
            self.vol = self.deployer.conn.create_volume(1, instance.placement, self.config.get_snap())
            log.debug("Created Chef volume %s. Attaching." % self.vol.id, node)
            self.vol.attach(instance.id, '/dev/sdh')
            log.debug("Chef volume attached. Waiting for it to become in-use.", node)
            self.deployer.wait_state(self.vol, "in-use")
            log.debug("Volume is in-use", node)
    
            self.deployer.vols.append(self.vol)

            log.debug("Mounting Chef volume", node)
            ssh.run("sudo mount -t ext3 /dev/sdh /chef", expectnooutput=True)
            
    def post_configure(self, ssh):
        if self.chef and self.config.has_snap():
            ssh.run("sudo umount /chef", expectnooutput=True)
            self.vol.detach()
            self.deployer.wait_state(self.vol, "available")        
            self.vol.delete()
            
            self.deployer.vols.remove(self.vol)
            