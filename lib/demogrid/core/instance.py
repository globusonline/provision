import shutil
import os.path
from cPickle import load
import random
from demogrid.common import DemoGridException
from demogrid.core.config import DemoGridConfig
from demogrid.core.topology import Topology

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

    def __init__(self, inst_id, instances_dir):
        self.id = inst_id
        self.__instances_dir = instances_dir
        self.__topology = self.__load_topology()
        self.__config = DemoGridConfig("%s/demogrid.conf" % instances_dir)
        


    def __load_topology(self):
        f = open ("%s/topology.dat" % self.__instances_dir, "r")
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
        hosts += "%s.0.1 master.%s master\n" % (self.config.get_subnet(), self.DOMAIN)
        
        nodes = self.topology.get_nodes()
        for n in nodes:
            hosts += " ".join((n.ip, n.hostname, n.hostname.split(".")[0], "\n"))
        
        hostsfile = open(self.generated_dir + "/hosts", "w")
        hostsfile.write(hosts)
        hostsfile.close()


    def gen_certificates(self, topology, force_certificates):
        certs_dir = self.generated_dir + self.CERTS_DIR
        if not os.path.exists(certs_dir):
            os.makedirs(certs_dir)  

        cert_files = []
        
        if self.config.has_ca():
            ca_cert_file, ca_cert_key = self.config.get_ca()
            ca_cert, ca_key = self.certg.load_certificate(ca_cert_file, ca_cert_key)
        else:
            ca_cert, ca_key = self.certg.gen_selfsigned_ca_cert("DemoGrid CA")
        
        self.certg.set_ca(ca_cert, ca_key)

        h = "%x" % ca_cert.subject_name_hash()

        hash_file = open(certs_dir + "/ca_cert.hash", "w")
        hash_file.write(h)
        hash_file.close()   

        ca_cert_file = "%s/%s.0" % (certs_dir, h)
        ca_key_file = certs_dir + "/ca_key.pem"
        cert_files.append(ca_cert_file)
        cert_files.append(ca_key_file)
        self.__dump_certificate(cert = ca_cert,
                                key = ca_key,
                                cert_file = ca_cert_file,
                                key_file = ca_key_file, force_certificates = force_certificates)

        users = [u for u in topology.get_users() if u.cert_type=="generated"]
        for user in users:        
            cert, key = self.certg.gen_user_cert(cn = user.description) 
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, user.login)
            key_file = "%s/%s_key.pem" % (certs_dir, user.login)
            cert_files.append(cert_file)
            cert_files.append(key_file)            
            self.__dump_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file, force_certificates = force_certificates)
        
        nodes = topology.get_nodes()
        for n in nodes:
            cert, key = self.certg.gen_host_cert(hostname = n.hostname) 
            
            filename = n.node_id
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, filename)
            key_file = "%s/%s_key.pem" % (certs_dir, filename)
            cert_files.append(cert_file)
            cert_files.append(key_file)                
            self.__dump_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file, force_certificates = force_certificates)        

        return cert_files  


    def copy_files(self, cert_files):
        chef_files_dir = self.generated_dir + self.CHEF_FILES_DIR
        for f in cert_files:
            shutil.copy(f, chef_files_dir)
            
        shutil.copy(self.generated_dir + "/hosts", chef_files_dir)
        
        shutil.copy(self.generated_dir + "/topology.rb", self.generated_dir + self.CHEF_ATTR_DIR)
    
    def __dump_certificate(self, cert, key, cert_file, key_file, force_certificates):
        if os.path.exists(cert_file) and not force_certificates:
            print '\033[1;33mWarning\033[0m: Certificate %s already exists. Skipping. Use --force-certificates to overwrite' % cert_file.split("/")[-1]
        else:
            self.certg.save_certificate(cert, key, cert_file, key_file)     
        

    def copy_chef_files(self, force_chef):
        src_chef = self.demogrid_dir + self.CHEF_DIR
        dst_chef = self.generated_dir + self.CHEF_DIR
        if os.path.exists(dst_chef):
            if force_chef:
                shutil.rmtree(dst_chef)
            else:
                return False
              
        if not os.path.exists(dst_chef):
            shutil.copytree(src_chef, dst_chef)            
            
        return True
        
