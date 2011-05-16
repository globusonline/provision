import os
import os.path
import sys
import shutil
from cPickle import load

from demogrid.core.topology import Topology, Domain, Node, User
from demogrid.common.certs import CertificateGenerator

try:
    from mako.template import Template
except Exception, e:
    print "Mako Templates for Python are not installed."
    print "You can download them at http://www.makotemplates.org/"
    print "or 'apt-get install python-mako' on most Debian/Ubuntu systems"
    exit(1)

class Preparator(object):
    # Relative to $DEMOGRID_LOCATION
    UVB_TEMPLATE = "/etc/uvb.template"
    CHEF_DIR = "/chef/"  
    
    # Relative to generated dir
    CERTS_DIR = "/certs"
    UVB_DIR = "/ubuntu-vm-builder"
    VAGRANT_DIR = "/vagrant"
    CHEF_FILES_DIR = "/chef/cookbooks/demogrid/files/default/"  
    CHEF_ATTR_DIR = "/chef/cookbooks/demogrid/attributes/"

    # The default user password is "user"    
    DEFAULT_USER_PASSWD = "$6$7iad7GsKb$YOWHui2Axtah8/UyoGJ.Q0zA49osppljN2NZwN9JRJKv8pL7DdSnUxNopinBhv1kQkwmAYA5YPS54MWCScJKi0"
    
    def __init__(self, demogrid_dir, config, generated_dir):
        self.demogrid_dir = demogrid_dir
        self.config = config
        self.generated_dir = generated_dir
        #self.force_certificates = force_certificates
        #self.force_chef = force_chef
        self.certg = CertificateGenerator()
        
    def prepare(self, topology, force_chef):
        if not os.path.exists(self.generated_dir):
            os.makedirs(self.generated_dir)          
        
        print "\033[1;37mGenerating files... \033[0m",
        sys.stdout.flush()
        
        topology.save(self.generated_dir + "/topology.dat")

        print "\033[1;32mdone!\033[0m"

        print "\033[1;37mCopying chef files... \033[0m",
        sys.stdout.flush()

        chef_dir = self.demogrid_dir + self.CHEF_DIR
        if not os.path.exists(chef_dir):        
            print '\033[1;33mWarning\033[0m: Chef files not installed. DemoGrid will only work in EC2 mode'
        else:
            if self.copy_chef_files(force_chef):
                print "\033[1;32mdone!\033[0m"
            else:
                print '\033[1;33mWarning\033[0m: Chef directory already exists. Skipping. Use --force-chef to overwrite'


    def generate_vagrant(self, force_certificates):
        if not os.path.exists(self.generated_dir):
            # TODO: Substitute for more meaningful error
            print "ERROR"      
            exit(1)
        
        print "\033[1;37mGenerating files... \033[0m",
        sys.stdout.flush()
        
        topology = self.__load_topology()
        
        topology.bind_to_example()
        
        
        topology.gen_hosts_file(self.generated_dir + "/hosts")
        topology.gen_ruby_file(self.generated_dir + "/topology.rb")
        topology.gen_csv_file(self.generated_dir + "/topology.csv")
        self.gen_vagrant_file(topology)
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mGenerating certificates... \033[0m",
        sys.stdout.flush()

        cert_files = self.gen_certificates(topology, force_certificates)
        
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mCopying chef files... \033[0m",
        sys.stdout.flush()
  
        self.copy_files(cert_files)

        print "\033[1;32mdone!\033[0m"


    def generate_uvb(self, force_certificates):
        if not os.path.exists(self.generated_dir):
            # TODO: Substitute for more meaningful error
            print "ERROR"      
            exit(1)
        
        print "\033[1;37mGenerating files... \033[0m",
        sys.stdout.flush()
        
        topology = self.__load_topology()
        
        topology.bind_to_example()
        
        
        topology.gen_hosts_file(self.generated_dir + "/hosts")
        topology.gen_ruby_file(self.generated_dir + "/topology.rb")
        topology.gen_csv_file(self.generated_dir + "/topology.csv")
        #self.gen_uvb_master_conf(topology)
        #self.gen_uvb_confs(topology)
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mGenerating certificates... \033[0m",
        sys.stdout.flush()

        cert_files = self.gen_certificates(topology, force_certificates)
        
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mCopying chef files... \033[0m",
        sys.stdout.flush()
  
        self.copy_files(cert_files)

        print "\033[1;32mdone!\033[0m"


    def __load_topology(self):
        f = open ("%s/topology.dat" % self.generated_dir, "r")
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
                
    def gen_uvb_master_conf(self, topology):
        uvb_dir = self.generated_dir + self.UVB_DIR
        if not os.path.exists(uvb_dir):
            os.makedirs(uvb_dir)    
                    
        template = Template(filename=self.demogrid_dir + self.UVB_TEMPLATE)
        uvb_master = template.render(domain = self.DOMAIN,
                                     ip = self.__gen_IP(0, 2),
                                     gw = self.__gen_IP(0, 1),
                                     dgl = self.demogrid_dir,
                                     execscript = "post-install-chefsolo.sh",
                                     copy = "files-chefsolo.txt")   
        uvb_masterfile = open(uvb_dir + "/uvb-chefsolo-master.conf", "w")
        uvb_masterfile.write(uvb_master)
        uvb_masterfile.close()          
        
        uvb_master = template.render(domain = self.DOMAIN,
                                     ip = self.__gen_IP(0, 2),
                                     gw = self.__gen_IP(0, 1),
                                     dgl = self.demogrid_dir,
                                     execscript = "post-install-chefserver.sh",
                                     copy = "files-chefserver.txt")
        uvb_masterfile = open(uvb_dir + "/uvb-chefserver-master.conf", "w")
        uvb_masterfile.write(uvb_master)
        uvb_masterfile.close()     
        
        
    def gen_uvb_confs(self, topology):
        uvb_dir = self.generated_dir + self.UVB_DIR

        nodes = topology.get_nodes()
        for n in nodes:
            name = n.hostname.split(".")[0].replace("-", "_")
            
            template = Template(filename=self.demogrid_dir + self.UVB_TEMPLATE)
            uvb = template.render(domain = self.DOMAIN,
                                  ip = n.ip,
                                  gw = self.__gen_IP(0, 1),
                                  dgl = self.demogrid_dir,
                                  execscript = "post-install-chefsolo.sh",
                                  copy = "files-chefsolo.txt")   
            uvb_file = open(uvb_dir + "/uvb-chefsolo-%s.conf" % name, "w")
            uvb_file.write(uvb)
            uvb_file.close()          
            
            uvb = template.render(domain = self.DOMAIN,
                                  ip = n.ip,
                                  gw = self.__gen_IP(0, 1),
                                  dgl = self.demogrid_dir,
                                  execscript = "post-install-chefserver.sh",
                                  copy = "files-chefserver.txt")
            uvb_file = open(uvb_dir + "/uvb-chefserver-%s.conf" % name, "w")
            uvb_file.write(uvb)
            uvb_file.close()
             
            
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
        
        
    def gen_vagrant_file(self, topology):
        vagrant_dir = self.generated_dir + self.VAGRANT_DIR
        if not os.path.exists(vagrant_dir):
            os.makedirs(vagrant_dir)         
        
        vagrant = "Vagrant::Config.run do |config|\n"
      
        nodes = topology.get_nodes()
        for n in nodes:
            name = n.hostname.split(".")[0].replace("-", "_")
            vagrant += "  config.vm.define :%s do |%s_config|\n" % (name, name)
            vagrant += "    %s_config.vm.box = \"lucid32\"\n" % name
            vagrant += "    %s_config.vm.provisioner = :chef_solo\n" % name
            vagrant += "    %s_config.chef.cookbooks_path = \"chef/cookbooks\"\n" % name
            vagrant += "    %s_config.chef.roles_path = \"chef/roles\"\n" % name
            # TODO: Fix
            #vagrant += "    %s_config.chef.add_role \"%s\"\n" % (name, n.role)
            vagrant += "    %s_config.vm.network(\"%s\", :netmask => \"255.255.0.0\")\n" % (name, n.ip)            
            vagrant += "    %s_config.chef.json.merge!({\n" % name         
            for k,v in n.chef_attrs.items():
                vagrant += "      :%s => %s,\n" % (k,v)
            vagrant += "    })\n"       
            vagrant += "  end\n\n"           
        vagrant += "end\n"           

        vagrantfile = open(vagrant_dir + "/Vagrantfile", "w")
        vagrantfile.write(vagrant)
        vagrantfile.close()
        
        chef_link = vagrant_dir + "/chef"
        if os.path.lexists(chef_link):
            os.remove(chef_link)            
        os.symlink(self.generated_dir + self.CHEF_DIR, chef_link)
        
        
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
        
