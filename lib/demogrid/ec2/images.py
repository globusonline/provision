'''
Created on Dec 6, 2010

@author: borja
'''
from demogrid.common.utils import create_ec2_connection, SSH
import time


class EC2ChefVolumeCreator(object):
    def __init__(self, demogrid_dir, ami, keypair, keyfile):
        self.demogrid_dir = demogrid_dir
        self.ami = ami
        self.keypair = keypair
        self.keyfile = keyfile

    def run(self):
        conn = create_ec2_connection()
        
        print "Creating instance"
        reservation = conn.run_instances(self.ami, 
                                         min_count=1, max_count=1,
                                         instance_type='t1.micro', 
                                         key_name=self.keypair)
        instance = reservation.instances[0]
        print "Instance %s created. Waiting for it to start..." % instance.id
        
        while instance.update() != "running":
            time.sleep(2)
        
        print "Instance running. Creating volume."
        
        vol = conn.create_volume(1, instance.placement)
        vol.attach(instance.id, '/dev/sdh')
        while vol.update() != "in-use":
            time.sleep(2)
        
        print "Volume created."

        ssh = SSH("ubuntu", instance.public_dns_name, self.keyfile)
        ssh.open()
        
        print "Preparing volume."
        ssh.scp("%s/lib/scripts/prepare_chef_volume.sh" % self.demogrid_dir,
                "/tmp/prepare_chef_volume.sh")
        
        ssh.run("chmod u+x /tmp/prepare_chef_volume.sh")

        ssh.run("sudo /tmp/prepare_chef_volume.sh")
        
        print "Copying Chef files."
        ssh.scp_dir("%s/chef" % self.demogrid_dir, "/chef")
                
        ssh.run("sudo umount /chef")
        
        print "Detaching volume"
        vol.detach()
        while vol.update() != "available":
            time.sleep(1)

        print "Terminating instance"
        conn.stop_instances([instance.id])
        while instance.update() != "terminated":
            time.sleep(2)
        print "Instance terminated"        
        
        print "Creating snapshot"
        snap = vol.create_snapshot("DemoGrid Chef partition 0.1")
        snap.share(groups=['all'])
        
        vol.delete()
        
        print "The snapshot ID is %s" % snap.id



class EC2AMICreator(object):
    def __init__(self, demogrid_dir, ami, snapshot, keypair, keyfile):
        self.demogrid_dir = demogrid_dir
        self.ami = ami
        self.snapshot = snapshot
        self.keypair = keypair
        self.keyfile = keyfile

    def run(self):
        conn = create_ec2_connection()

        print "Creating instance"
        reservation = conn.run_instances(self.ami, 
                                         min_count=1, max_count=1,
                                         instance_type='t1.micro', 
                                         key_name=self.keypair)
        instance = reservation.instances[0]
        print "Instance %s created. Waiting for it to start..." % instance.id
        
        while instance.update() != "running":
            time.sleep(2)
        
        print "Instance running. Creating volume + attaching."
        
        vol = conn.create_volume(1, instance.placement, self.snapshot)
        vol.attach(instance.id, '/dev/sdh')
        while vol.update() != "in-use":
            time.sleep(2)
        
        print "Volume created."        
        
        ssh = SSH("ubuntu", instance.public_dns_name, self.keyfile)
        ssh.open()
        
        print "Mounting volume."  
        
        ssh.run("sudo mkdir /chef")
        ssh.run("sudo mount -t ext3 /dev/sdh /chef")
        ssh.run("sudo chown -R ubuntu /chef")
        
        ssh.run("sudo apt-add-repository 'deb http://apt.opscode.com/ lucid main'")
        ssh.run("wget -qO - http://apt.opscode.com/packages@opscode.com.gpg.key | sudo apt-key add -")
        ssh.run("sudo apt-get update")
        ssh.run("echo 'chef chef/chef_server_url string http://127.0.0.1:4000' | sudo debconf-set-selections")
        ssh.run("sudo apt-get -q=2 install chef")
        
        ssh.scp("%s/lib/ec2/chef.conf" % self.demogrid_dir,
                "/tmp/chef.conf")        
        
        ssh.run("echo '{ \"run_list\": \"recipe[demogrid::ec2]\" }' > /tmp/chef.json")

        ssh.run("sudo chef-solo -c /tmp/chef.conf -j /tmp/chef.json")    
        
        ssh.run("sudo update-rc.d nis disable")
        ssh.run("sudo update-rc.d chef-client disable")
        
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
        ami = conn.create_image(instance.id, "DemoGrid Base AMI", description="DemoGrid Base AMI")       
        
        print "Cleaning up"
        vol.detach()
        
        print "Terminating instance"
        conn.terminate_instances([instance.id])
        while instance.update() != "terminated":
            time.sleep(2)
        print "Instance terminated"   
                
        vol.delete()     
        