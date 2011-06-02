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
from demogrid.core.prepare import Preparator


class EC2Launcher(object):
    def __init__(self, demogrid_dir, config, generated_dir, loglevel, no_cleanup, extra_files):
        self.demogrid_dir = demogrid_dir
        self.config = config
        self.generated_dir = generated_dir
        self.loglevel = loglevel
        self.extra_files = extra_files
        self.conn = None
        self.instances = None
        self.vols = []
        self.no_cleanup = no_cleanup
     
    def run(self):
        # This try-except will catch anything that isn't
        # caught in launch() (which should handle all
        # exceptions)
        try:
            self.launch()
        except Exception, exc:
            self.handle_unexpected_exception(exc)
            
        
    def launch(self):     
        SIGINTWatcher(self.cleanup_after_kill)
        t_start = time.time()
        
        keypair = self.config.get_keypair()
        zone = self.config.get_ec2_zone()
        
        log.init_logging(self.loglevel)
        
        try:
            log.debug("Connecting to EC2...")
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
            
        
        # Load topology
        log.debug("Loading topology file...")
        f = open ("%s/topology.dat" % self.generated_dir, "r")
        topology = load(f)
        f.close()
        log.debug("Loaded topology file")

        if self.config.get_ec2_access_type() == "public":
            topology.global_attributes["ec2_public"] = "true"
        else:
            topology.global_attributes["ec2_public"] = "false"
            topology.bind_to_example()

        nodes = topology.get_nodes()
        num_instances = len(nodes)

        # Launch instances
        if self.loglevel == 0:
            print "\033[1;37mLaunching %i EC2 instances...\033[0m" % num_instances,
            sys.stdout.flush()

        log.info("Launching a total of %i EC2 instances." % num_instances)
        node_instance = {}       
        self.instances = [] 
        for n in nodes:     
            try:   
                instance_type = n.deploy_data["ec2"]["instance_type"]
                ami = n.deploy_data["ec2"]["ami"]
                
                image = self.conn.get_image(ami)
                
                log.info(" |- Launching a %s instance for %s." % (instance_type, n.node_id))
                reservation = image.run(min_count=1, 
                                        max_count=1,
                                        instance_type=instance_type,
                                        security_groups= ["default"],
                                        key_name=keypair,
                                        placement = zone)
                instance = reservation.instances[0]
                node_instance[n] = instance
                self.instances.append(instance)
            except EC2ResponseError, exc:
                self.handle_ec2response_exception(exc, "requesting instances")
            except Exception, exc:
                self.handle_unexpected_exception(exc)
        
        log.debug("Waiting for instances to start.")
        
        mt_instancewait = MultiThread()
        
        for i in node_instance.values():
            mt_instancewait.add_thread(InstanceWaitThread(mt_instancewait, "wait-%s" % i.id, i, self))
        mt_instancewait.run()
        
        if not mt_instancewait.all_success():
            self.handle_mt_exceptions(mt_instancewait.get_exceptions(), "Exception raised while waiting for instances.")
            
        if self.loglevel == 0:
            print "\033[1;32mdone!\033[0m"            
        log.info("Instances are running.")

        for node, instance in node_instance.items():
            node.ip = instance.private_ip_address
            node.deploy_data["ec2_instance"] = instance.id
            node.deploy_data["public_hostname"] = "\"%s\"" % instance.public_dns_name
            node.deploy_data["public_ip"] = "\"%s\"" % ".".join(instance.public_dns_name.split(".")[0].split("-")[1:])
            if self.config.get_ec2_access_type() == "public":
                node.hostname = instance.public_dns_name
                node.chef_attrs["demogrid_hostname"] = "\"%s\"" % node.hostname
                node.chef_attrs["public_ip"] = "\"%s\"" % ".".join(instance.public_dns_name.split(".")[0].split("-")[1:])
        
        for n in topology.get_nodes():
            n.gen_chef_attrs()        
        
        topology.gen_ruby_file(self.generated_dir + "/topology.rb")
        topology.gen_hosts_file(self.generated_dir + "/hosts") 
        topology.gen_csv_file(self.generated_dir + "/topology.csv")

        # Use Preparator to generate certificates and Chef files
        p = Preparator(self.demogrid_dir, self.config, self.generated_dir)
        cert_files = p.gen_certificates(topology, force_certificates=True)
        p.copy_files(cert_files)
        
        if self.config.get_ec2_access_type() == "public":
            self.__gen_public_host_certificates(node_instance)
        
        topology.save("%s/topology.dat" % self.generated_dir)
        
        if self.loglevel == 0:
            print "\033[1;37mConfiguring DemoGrid nodes...\033[0m (this may take a few minutes)"
        log.info("Setting up DemoGrid on instances")        
        
        mt_configure = MultiThread()

        parents = [n for n in topology.get_nodes() if n.depends == None]
        threads = {}
        while len(parents) > 0:
            rest = dict([(n,InstanceConfigureThread(mt_configure, 
                                                      "configure-%s" % n.node_id, 
                                                      n, 
                                                      i, 
                                                      self,
                                                      depends = threads.get(n.depends))) 
                                                      for n,i in node_instance.items()
                                                      if n in parents])
            threads.update(rest)
            parents = [n for n in topology.get_nodes() if n.depends in parents]
            

        for thread in threads.values():
            mt_configure.add_thread(thread)
        mt_configure.run()        
        
        if not mt_configure.all_success():
            self.handle_mt_exceptions(mt_configure.get_exceptions(), "DemoGrid was unable to configure the instances.")

        t_end = time.time()
        
        delta = t_end - t_start
        minutes = int(delta / 60)
        seconds = int(delta - (minutes * 60))
        print "You just went \033[1;34mfrom zero to grid\033[0m in \033[1;37m%i minutes and %s seconds\033[0m!" % (minutes, seconds)

        #print "Your login nodes are:"
        #for node, instance in node_instance.items():
        #    if node.role == "org-login":
        #        print "%s: %s" % (node.hostname.split(".")[0], instance.public_dns_name)


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
        
    def cleanup_after_kill(self):
        print "DemoGrid has been unexpectedly killed and cannot release EC2 resources."
        print "Please make sure you manually release all DemoGrid instances and volumes."

    def __gen_public_host_certificates(self, node_instance):
        log.info("Generating host certificates for public hosts")
        
        certs_dir = "%s/certs" % self.generated_dir
        
        certg = CertificateGenerator()
        
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
            
class InstanceWaitThread(DemoGridThread):
    def __init__(self, multi, name, instance, launcher, depends = None):
        DemoGridThread.__init__(self, multi, name, depends)
        self.instance = instance
        self.launcher = launcher
                    
    def run2(self):
        self.launcher.wait_state(self.instance, "running")
        log.info("Instance %s is running. Hostname: %s" % (self.instance.id, self.instance.public_dns_name))
        
class InstanceConfigureThread(DemoGridThread):
    def __init__(self, multi, name, node, instance, launcher, depends = None):
        DemoGridThread.__init__(self, multi, name, depends)
        self.node = node
        self.instance = instance
        self.launcher = launcher
        
    def run2(self):
        node = self.node
        instance = self.instance
        
        log.info("Setting up instance %s. Hostname: %s" % (instance.id, instance.public_dns_name), node)

        if self.launcher.config.has_snap():
            log.debug("Creating Chef volume.", node)
            vol = self.launcher.conn.create_volume(1, instance.placement, self.launcher.config.get_snap())
            log.debug("Created Chef volume %s. Attaching." % vol.id, node)
            vol.attach(instance.id, '/dev/sdh')
            log.debug("Chef volume attached. Waiting for it to become in-use.", node)
            self.launcher.wait_state(vol, "in-use")
            log.debug("Volume is in-use", node)
    
            self.launcher.vols.append(vol)

        self.check_continue()

        if self.launcher.loglevel in (0,1):
            ssh_out = None
            ssh_err = None
        elif self.launcher.loglevel == 2:
            ssh_out = sys.stdout
            ssh_err = sys.stderr

        log.debug("Establishing SSH connection", node)
        ssh = SSH("ubuntu", instance.public_dns_name, self.launcher.config.get_keyfile(), ssh_out, ssh_err)
        ssh.open()
        log.debug("SSH connection established", node)

        self.check_continue()
        
        if self.launcher.config.has_snap():
            log.debug("Mounting Chef volume", node)
            ssh.run("sudo mount -t ext3 /dev/sdh /chef", expectnooutput=True)
        
        # Upload host file and update hostname
        log.debug("Uploading host file and updating hostname", node)
        ssh.scp("%s/hosts" % self.launcher.generated_dir,
                "/chef/cookbooks/demogrid/files/default/hosts")             
        ssh.run("sudo cp /chef/cookbooks/demogrid/files/default/hosts /etc/hosts", expectnooutput=True)
        ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname, expectnooutput=True)
        ssh.run("sudo /etc/init.d/hostname restart")
        
        self.check_continue()
        
        # Upload topology file
        log.debug("Uploading topology file", node)
        ssh.scp("%s/topology.rb" % self.launcher.generated_dir,
                "/chef/cookbooks/demogrid/attributes/topology.rb")             
        
        # Copy certificates
        log.debug("Copying certificates", node)
        ssh.scp_dir("%s/certs" % self.launcher.generated_dir, 
                    "/chef/cookbooks/demogrid/files/default/")

        # Upload extra files
        log.debug("Copying extra files", node)
        for src, dst in self.launcher.extra_files:
            ssh.scp(src, dst)
        
        self.check_continue()

        if self.launcher.loglevel == 0:
            print "   \033[1;37m%s\033[0m: Basic setup is done. Installing Grid software now." % node.hostname.split(".")[0]
        
        # Run chef
        log.debug("Running chef", node)
        ssh.scp("%s/lib/ec2/chef.conf" % self.launcher.demogrid_dir,
                "/tmp/chef.conf")        
        
        ssh.run("echo '{ \"run_list\": [ %s ] }' > /tmp/chef.json" % ",".join("\"%s\"" % r for r in node.run_list), expectnooutput=True)

        ssh.run("sudo chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    

        self.check_continue()

        # The Chef recipes will overwrite the hostname, so
        # we need to set it again.
        ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname, expectnooutput=True)
        ssh.run("sudo /etc/init.d/hostname restart")
        
        if self.launcher.config.has_snap():
            ssh.run("sudo umount /chef", expectnooutput=True)
            vol.detach()
            self.launcher.wait_state(vol, "available")        
            vol.delete()
            
            self.launcher.vols.remove(vol)
        
        ssh.run("sudo update-rc.d nis enable")     

        log.info("Configuration done.", node)
        
        if self.launcher.loglevel == 0:
            print "   \033[1;37m%s\033[0m is ready." % node.hostname.split(".")[0]
