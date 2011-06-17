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
from demogrid.core.deploy import Deployer, VM

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
        try:
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
        except EC2ResponseError, exc:
            self.handle_ec2response_exception(exc, "requesting instances")
        
        return EC2VM(instance)

    def post_allocate(self, node, vm):
        instance = vm.ec2_instance
        config = self.instance.config
        
        try:
            if self.supports_create_tags:
                self.conn.create_tags([instance.id], {"Name": node.node_id})
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


    def wait_state(self, obj, state, interval = 2.0):
        jitter = random.uniform(0.0, 0.5)
        while True:
            time.sleep(interval + jitter)
            newstate = obj.update()
            if newstate == state:
                return True
        # TODO: Check errors

    def handle_ec2response_exception(self, exc, what=""):
        if what != "": what = " when " + what
        print "\033[1;31mERROR\033[0m - EC2 returned an error when %s." % what
        print "        Reason: %s" % exc.reason
        print "        Body: %s" % exc.body
        self.cleanup()
        exit(1)        
        

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
        


    def __gen_public_host_certificates(self, node_instance):
        log.info("Generating host certificates for public hosts")
        
        certs_dir = "%s/certs" % self.generated_dir
        
        
        if self.config.has_ca():
            ca_cert_file, ca_cert_key = self.config.get_ca()
            ca_cert, ca_key = certg.load_certificate(ca_cert_file, ca_cert_key)
        else:
            print "To use host certificates with public hostnames, you need to supply a CA certificate."
            self.cleanup()
            exit(1)
            
        certg.set_ca(ca_cert, ca_key)

        for node, instance in node_instance.items():        
            cert, key = certg.gen_host_cert(hostname= instance.public_dns_name) 
            
            filename = node.node_id
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, filename)
            key_file = "%s/%s_key.pem" % (certs_dir, filename)             
            certg.save_certificate(cert, key, cert_file, key_file)            

        log.info("Generated host certificates for public hosts")
            
class EC2InstanceWaitThread(DemoGridThread):
    def __init__(self, multi, name, node, vm, deployer, depends = None):
        DemoGridThread.__init__(self, multi, name, depends)
        self.ec2_instance = vm.ec2_instance
        self.deployer = deployer
                    
    def run2(self):
        self.deployer.wait_state(self.ec2_instance, "running")
        log.info("Instance %s is running. Hostname: %s" % (self.ec2_instance.id, self.ec2_instance.public_dns_name))
        
class EC2InstanceConfigureThread(DemoGridThread):
    def __init__(self, multi, name, node, vm, deployer, depends = None):
        DemoGridThread.__init__(self, multi, name, depends)
        self.node = node
        self.ec2_instance = vm.ec2_instance
        self.deployer = deployer
        self.config = deployer.instance.config
        
    def run2(self):
        node = self.node
        instance = self.ec2_instance
        instance_dir = self.deployer.instance.instance_dir
        
        log.info("Setting up instance %s. Hostname: %s" % (instance.id, instance.public_dns_name), node)

        if self.config.has_snap():
            log.debug("Creating Chef volume.", node)
            vol = self.deployer.conn.create_volume(1, instance.placement, self.config.get_snap())
            log.debug("Created Chef volume %s. Attaching." % vol.id, node)
            vol.attach(instance.id, '/dev/sdh')
            log.debug("Chef volume attached. Waiting for it to become in-use.", node)
            self.deployer.wait_state(vol, "in-use")
            log.debug("Volume is in-use", node)
    
            self.deployer.vols.append(vol)

        self.check_continue()

        #if self.deployer.loglevel in (0,1):
        #    ssh_out = None
        #    ssh_err = None
        #elif self.deployer.loglevel == 2:
        #   ssh_out = sys.stdout
        #    ssh_err = sys.stderr

        ssh_out = sys.stdout
        ssh_err = sys.stderr

        log.debug("Establishing SSH connection", node)
        ssh = SSH(self.config.get_ec2_username(), instance.public_dns_name, self.config.get_keyfile(), ssh_out, ssh_err)
        ssh.open()
        log.debug("SSH connection established", node)

        self.check_continue()
        
        if self.config.has_snap():
            log.debug("Mounting Chef volume", node)
            ssh.run("sudo mount -t ext3 /dev/sdh /chef", expectnooutput=True)
        
        # Upload host file and update hostname
        log.debug("Uploading host file and updating hostname", node)
        ssh.scp("%s/hosts" % instance_dir,
                "/chef/cookbooks/demogrid/files/default/hosts")             
        ssh.run("sudo cp /chef/cookbooks/demogrid/files/default/hosts /etc/hosts", expectnooutput=True)

        ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname, expectnooutput=True)
        ssh.run("sudo /etc/init.d/hostname.sh || sudo /etc/init.d/hostname restart")
        
        self.check_continue()
        
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
        ssh.scp("%s/lib/ec2/chef.conf" % self.deployer.demogrid_dir,
                "/tmp/chef.conf")        
        
        ssh.run("echo '{ \"run_list\": [ %s ], \"scratch_dir\": \"%s\", \"node_id\": \"%s\"  }' > /tmp/chef.json" % (",".join("\"%s\"" % r for r in node.run_list), self.config.get_scratch_dir(), node.node_id), expectnooutput=True)

        ssh.run("sudo chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    

        self.check_continue()

        # The Chef recipes will overwrite the hostname, so
        # we need to set it again.
        ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname, expectnooutput=True)
        ssh.run("sudo /etc/init.d/hostname.sh || sudo /etc/init.d/hostname restart")
        
        if self.config.has_snap():
            ssh.run("sudo umount /chef", expectnooutput=True)
            vol.detach()
            self.deployer.wait_state(vol, "available")        
            vol.delete()
            
            self.deployer.vols.remove(vol)
        
        ssh.run("sudo update-rc.d nis defaults")     

        log.info("Configuration done.", node)
        
        #if self.deployer.loglevel == 0:
        #    print "   \033[1;37m%s\033[0m is ready." % node.hostname.split(".")[0]
