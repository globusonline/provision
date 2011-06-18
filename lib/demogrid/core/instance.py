import shutil
import os.path
from cPickle import load
import random
from demogrid.common import DemoGridException
from demogrid.core.config import DemoGridConfig
from demogrid.core.topology import Topology
from demogrid.common.certs import CertificateGenerator

class InstanceStore(object):
    def __init__(self, instances_dir):
        self.instances_dir = instances_dir
        
    def create_new_instance(self, topology_json, config_txt):
        created = False
        while not created:
            inst_id = "xgi-" + hex(random.randint(1,2**32))[2:].rjust(8,"0")
            inst_dir = "%s/%s" % (self.instances_dir, inst_id)
            if not os.path.exists(inst_dir):
                os.makedirs(inst_dir)
                created = True
                
        configf = open("%s/demogrid.conf" % inst_dir, "w")
        configf.write(config_txt)
        configf.close()

        topology = Topology.from_json(topology_json)
        topology.save("%s/topology.dat" % inst_dir)
                                        
        inst = Instance(inst_id, inst_dir)
        
        return inst
    
    def get_instance(self, inst_id):
        inst_dir = "%s/%s" % (self.instances_dir, inst_id)

        if not os.path.exists(inst_dir):
            raise DemoGridException("Instance does not exist")
        return Instance(inst_id, inst_dir)


class Instance(object):

    # Relative to $DEMOGRID_LOCATION
    CHEF_DIR = "/chef/"  
    
    # Relative to generated dir
    CERTS_DIR = "/certs"
    CHEF_FILES_DIR = "/chef/cookbooks/demogrid/files/default/"  
    CHEF_ATTR_DIR = "/chef/cookbooks/demogrid/attributes/"

    def __init__(self, inst_id, instance_dir):
        self.instance_dir = instance_dir
        self.id = inst_id
        self.config = DemoGridConfig("%s/demogrid.conf" % instance_dir)
        self.topology = self.__load_topology()
        
    def __load_topology(self):
        f = open ("%s/topology.dat" % self.instance_dir, "r")
        topology = load(f)
        f.close()   
        return topology     



    def gen_hosts_file(self):
        hosts = """127.0.0.1    localhost

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts

"""
        
        nodes = self.topology.get_nodes()
        for n in nodes:
            hosts += " ".join((n.ip, n.hostname, n.hostname.split(".")[0], "\n"))
        
        hostsfile = open(self.generated_dir + "/hosts", "w")
        hostsfile.write(hosts)
        hostsfile.close()


    def gen_certificates(self, force_hosts = False, force_users = False, force_ca = False):
        certs_dir = self.instance_dir + self.CERTS_DIR
        if not os.path.exists(certs_dir):
            os.makedirs(certs_dir)  

        certg = CertificateGenerator()

        cert_files = []
        
        if self.config.has_ca():
            ca_cert_file, ca_cert_key = self.config.get_ca()
            ca_cert, ca_key = certg.load_certificate(ca_cert_file, ca_cert_key)
        else:
            ca_cert, ca_key = certg.gen_selfsigned_ca_cert("DemoGrid CA")
        
        certg.set_ca(ca_cert, ca_key)

        h = "%x" % ca_cert.subject_name_hash()

        hash_file = open(certs_dir + "/ca_cert.hash", "w")
        hash_file.write(h)
        hash_file.close()   

        ca_cert_file = "%s/%s.0" % (certs_dir, h)
        ca_key_file = certs_dir + "/ca_key.pem"
        cert_files.append(ca_cert_file)
        cert_files.append(ca_key_file)
        certg.save_certificate(cert = ca_cert,
                              key = ca_key,
                              cert_file = ca_cert_file,
                              key_file = ca_key_file, 
                              force = force_ca)

        users = [u for u in self.topology.get_users() if u.cert_type=="generated"]
        for user in users:        
            cert, key = certg.gen_user_cert(cn = user.description) 
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, user.login)
            key_file = "%s/%s_key.pem" % (certs_dir, user.login)
            cert_files.append(cert_file)
            cert_files.append(key_file)    
            certg.save_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file, 
                                    force = force_users)
        
        nodes = self.topology.get_nodes()
        for n in nodes:
            cert, key = certg.gen_host_cert(hostname = n.hostname) 
            
            filename = n.node_id
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, filename)
            key_file = "%s/%s_key.pem" % (certs_dir, filename)
            cert_files.append(cert_file)
            cert_files.append(key_file)          
            certg.save_certificate(cert = cert,
                                   key = key,
                                   cert_file = cert_file,
                                   key_file = key_file, 
                                   force = force_hosts)        

        return cert_files  


                 
        


        
