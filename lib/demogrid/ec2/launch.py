from cPickle import dump, load, HIGHEST_PROTOCOL
from boto.ec2.connection import EC2Connection
from demogrid.common.utils import create_ec2_connection, SSH, MultiThread
import random
import time
import sys
from demogrid.common import log


class EC2Launcher(object):
    def __init__(self, demogrid_dir, config, generated_dir, loglevel):
        self.demogrid_dir = demogrid_dir
        self.config = config
        self.generated_dir = generated_dir
        self.loglevel = loglevel
        self.conn = None
     
        
    def launch(self):     
        t_start = time.time()
        
        ami = self.config.get_ami()
        keypair = self.config.get_keypair()
        insttype = self.config.get_instance_type()
        zone = self.config.get_ec2_zone()   
        
        log.init_logging(self.loglevel)
        
        log.debug("Connecting to EC2...")
        self.conn = create_ec2_connection()
        log.debug("Connected to EC2.")
        
        # Load topology
        log.debug("Loading topology file...")
        f = open ("%s/topology.dat" % self.generated_dir, "r")
        topology = load(f)
        f.close()
        log.debug("Loaded topology file")

        nodes = topology.get_nodes()
        num_instances = len(nodes)

        # Launch instances
        if self.loglevel == 0:
            print "\033[1;37mLaunching %i EC2 instances...\033[0m" % num_instances,
            sys.stdout.flush()
        log.info("Launching %i EC2 instances." % num_instances)        
        reservation = self.conn.run_instances(ami, 
                                         min_count=num_instances, 
                                         max_count=num_instances,
                                         instance_type=insttype,
                                         security_groups= ["default"],
                                         key_name=keypair,
                                         placement = zone)
        
        instances = reservation.instances
        
        log.debug("Instances: %s" % " ".join([i.id for i in instances]))
        log.debug("Waiting for instances to start.")
        
        mt = MultiThread(self.wait_instance, [[i] for i in instances])
        mt.run()
            
        print "\033[1;32mdone!\033[0m"            
        log.info("Instances are running.")

        # Kluge: This is because of a known bug in the stable release of boto.
        # Basically, update() won't get some of the attributes (specially
        # the private IP, which we need), and the workaround is to force
        # boto to create a new Instance object.
        # Can be removed once they push a new stable release
        r = self.conn.get_all_instances([i.id for i in instances])
        instances2 = r[0].instances

        node_instance = dict(zip(nodes,instances2))
        
        for node, instance in node_instance.items():
            node.ip = instance.private_ip_address
        
        # Update attributes and other data
        for node in nodes:        
            attrs = node.attrs
            if node.org != None:
                attrs["subnet"] = "nil" 
                attrs["org_server"] = "\"%s\"" % node.org.server.ip
        
        topology.gen_ruby_file(self.generated_dir + "/topology_ec2.rb")
        topology.gen_hosts_file(self.generated_dir + "/hosts_ec2") 

        if self.loglevel == 0:
            print "\033[1;37mConfiguring DemoGrid nodes...\033[0m (this may take a few minutes)"
        log.info("Setting up DemoGrid on instances")        
        mt = MultiThread(self.configure_instance, node_instance.items())
        mt.run()      
        
        t_end = time.time()
        
        delta = t_end - t_start
        minutes = int(delta / 60)
        seconds = int(delta - (minutes * 60))
        print "You just went \033[34mfrom zero to grid\033[0m in \033[1;37m%i minutes and %s seconds\033[0m!" % (minutes, seconds)

    def wait_state(self, obj, state, interval = 2.0):
        jitter = random.uniform(0.0, 0.5)
        while True:
            time.sleep(interval + jitter)
            newstate = obj.update()
            if newstate == state:
                return True
        # TODO: Check errors
            
    def wait_instance(self, instance):
        self.wait_state(instance, "running")
        log.info("Instance %s is running. Hostname: %s" % (instance.id,instance.public_dns_name))
        
    def configure_instance(self, node, instance):
        log.info("Setting up instance %s. Hostname: %s" % (instance.id, instance.public_dns_name), node)

        log.debug("Creating Chef volume.", node)
        vol = self.conn.create_volume(1, instance.placement, self.config.get_snap())
        log.debug("Created Chef volume %s. Attaching." % vol.id, node)
        vol.attach(instance.id, '/dev/sdh')
        log.debug("Chef volume attached. Waiting for it to become in-use.", node)
        self.wait_state(vol, "in-use")
        log.debug("Volume is in-use", node)

        if self.loglevel in (0,1):
            ssh_out = None
            ssh_err = None
        elif self.loglevel == 2:
            ssh_out = sys.stdout
            ssh_err = sys.stderr

        log.debug("Establishing SSH connection", node)
        ssh = SSH("ubuntu", instance.public_dns_name, self.config.get_keyfile(), ssh_out, ssh_err)
        ssh.open()
        log.debug("SSH connection established", node)
        
        log.debug("Mounting Chef volume", node)
        ssh.run("sudo mount -t ext3 /dev/sdh /chef")
        
        # Upload host file and update hostname
        log.debug("Uploading host file and updating hostname", node)
        ssh.scp("%s/hosts_ec2" % self.generated_dir,
                "/chef/cookbooks/demogrid/files/default/hosts")             
        ssh.run("sudo cp /chef/cookbooks/demogrid/files/default/hosts /etc/hosts")
        ssh.run("sudo bash -c \"echo %s > /etc/hostname\"" % node.hostname)
        ssh.run("sudo /etc/init.d/hostname restart")
        
        # Upload topology file
        log.debug("Uploading topology file", node)
        ssh.scp("%s/topology_ec2.rb" % self.generated_dir,
                "/chef/cookbooks/demogrid/attributes/topology.rb")             
        
        # Copy certificates
        log.debug("Copying certificates", node)
        ssh.scp_dir("%s/certs" % self.generated_dir, 
                    "/chef/cookbooks/demogrid/files/default/")
        
        # Run chef
        log.debug("Running chef", node)
        ssh.scp("%s/lib/ec2/chef.conf" % self.demogrid_dir,
                "/tmp/chef.conf")        
        
        ssh.run("echo '{ \"run_list\": \"role[%s]\" }' > /tmp/chef.json" % node.role)

        ssh.run("sudo chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    
        
        ssh.run("sudo update-rc.d nis enable")     

        log.info("Configuration done.", node)
        
        if self.loglevel == 0:
            print "   \033[1;37m%s\033[0m has been configured." % node.hostname.split(".")[0]
