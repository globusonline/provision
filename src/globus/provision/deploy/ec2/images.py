'''
Created on Dec 6, 2010

@author: borja
'''
from globus.provision.common.utils import create_ec2_connection
from globus.provision.common.ssh import SSH
from globus.provision.common import log
import time

class EC2AMICreator(object):
    def __init__(self, chef_dir, base_ami, ami_name, config):
        self.chef_dir = chef_dir
        self.base_ami = base_ami
        self.ami_name = ami_name
        self.config = config

        self.keypair = config.get("ec2-keypair")
        self.keyfile = config.get("ec2-keyfile")
        self.hostname = config.get("ec2-server-hostname")
        self.port = config.get("ec2-server-port")
        self.path = config.get("ec2-server-path")
        self.username = config.get("ec2-username")
        self.scratch_dir = config.get("scratch-dir")

    def run(self):
        log.init_logging(2)

        conn = create_ec2_connection(hostname=self.hostname, path=self.path, port=self.port)

        print "Creating instance"
        reservation = conn.run_instances(self.base_ami, 
                                         min_count=1, max_count=1,
                                         instance_type='m1.small', 
                                         key_name=self.keypair)
        instance = reservation.instances[0]
        print "Instance %s created. Waiting for it to start..." % instance.id
        
        while instance.update() != "running":
            time.sleep(2)
        
        print "Instance running"
        print self.username, instance.public_dns_name, self.keyfile
        ssh = SSH(self.username, instance.public_dns_name, self.keyfile, None, None)
        try:
            ssh.open()
        except Exception, e:
            print e.message
            exit(1)
        
        print "Copying Chef files"
        ssh.run("sudo mkdir /chef")
        ssh.run("sudo chown -R %s /chef" % self.username)
        ssh.scp_dir("%s" % self.chef_dir, "/chef")
        
        # Some VMs don't include their hostname
        ssh.run("echo \"%s `hostname`\" | sudo tee -a /etc/hosts" % instance.private_ip_address)

        ssh.run("sudo apt-get install lsb-release")
        ssh.run("echo \"deb http://apt.opscode.com/ `lsb_release -cs` main\" | sudo tee /etc/apt/sources.list.d/opscode.list")
        ssh.run("wget -qO - http://apt.opscode.com/packages@opscode.com.gpg.key | sudo apt-key add -")
        ssh.run("sudo apt-get update")
        ssh.run("echo 'chef chef/chef_server_url string http://127.0.0.1:4000' | sudo debconf-set-selections")
        ssh.run("sudo apt-get -q=2 install chef")
        
        ssh.run("echo -e \"cookbook_path \\\"/chef/cookbooks\\\"\\nrole_path \\\"/chef/roles\\\"\" > /tmp/chef.conf")        
        ssh.run("echo '{ \"run_list\": \"recipe[provision::ec2]\", \"scratch_dir\": \"%s\" }' > /tmp/chef.json" % self.scratch_dir)

        ssh.run("sudo chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    
        
        ssh.run("sudo update-rc.d -f nis remove")
        ssh.run("sudo update-rc.d -f condor remove")
        ssh.run("sudo update-rc.d -f chef-client remove")
        
        print "Removing private data and authorized keys"
        ssh.run("sudo find /root/.*history /home/*/.*history -exec rm -f {} \;", exception_on_error = False)
        ssh.run("sudo find / -name authorized_keys -exec rm -f {} \;")            
            
        # Apparently instance.stop() will terminate
        # the instance (this is a known bug), so we 
        # use stop_instances instead.
        print "Stopping instance"
        conn.stop_instances([instance.id])
        while instance.update() != "stopped":
            time.sleep(2)
        print "Instance stopped"
        
        print "Creating AMI"
        # Doesn't actually return AMI. Have to make it public manually.
        ami = conn.create_image(instance.id, self.ami_name, description=self.ami_name)       
        
        print "Cleaning up"

        
        print "Terminating instance"
        #conn.terminate_instances([instance.id])
        #while instance.update() != "terminated":
        #    time.sleep(2)
        print "Instance terminated"   

        

class EC2AMIUpdater(object):
    def __init__(self, chef_dir, base_ami, ami_name, files, config):
        self.chef_dir = chef_dir
        self.base_ami = base_ami
        self.ami_name = ami_name
        self.files = files
        
        self.config = config

        self.keypair = config.get("ec2-keypair")
        self.keyfile = config.get("ec2-keyfile")
        self.hostname = config.get("ec2-server-hostname")
        self.port = config.get("ec2-server-port")
        self.path = config.get("ec2-server-path")
        self.username = config.get("ec2-username")

    def run(self):
        log.init_logging(2)
        
        conn = create_ec2_connection(hostname=self.hostname, path=self.path, port=self.port)

        print "Creating instance"
        reservation = conn.run_instances(self.base_ami, 
                                         min_count=1, max_count=1,
                                         instance_type='m1.small', 
                                         key_name=self.keypair)
        instance = reservation.instances[0]
        print "Instance %s created. Waiting for it to start..." % instance.id
        
        while instance.update() != "running":
            time.sleep(2)
        
        print "Instance running."

        print "Opening SSH connection."
        ssh = SSH(self.username, instance.public_dns_name, self.keyfile)
        ssh.open()
        
        print "Copying files"        
        for src, dst in self.files:
            ssh.scp(src, dst)
                  
        print "Removing private data and authorized keys"
        ssh.run("sudo find /root/.*history /home/*/.*history -exec rm -f {} \;")
        ssh.run("sudo find / -name authorized_keys -exec rm -f {} \;")
                  
        # Apparently instance.stop() will terminate
        # the instance (this is a known bug), so we 
        # use stop_instances instead.
        print "Stopping instance"
        conn.stop_instances([instance.id])
        while instance.update() != "stopped":
            time.sleep(2)
        print "Instance stopped"
        
        print "Creating AMI"
        
        # Doesn't actually return AMI. Have to make it public manually.
        ami = conn.create_image(instance.id, self.ami_name, description=self.ami_name)       
        
        if ami != None:
            print ami
        print "Cleaning up"

        
        print "Terminating instance"
        conn.terminate_instances([instance.id])
        while instance.update() != "terminated":
            time.sleep(2)
        print "Instance terminated"   

                
