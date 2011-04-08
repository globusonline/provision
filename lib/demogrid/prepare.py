import os
import os.path

import sys
import shutil
from demogrid.common.topology import DGGrid, DGOrganization, DGNode, DGOrgUser
from demogrid.common.certs import CertificateGenerator

try:
    from mako.template import Template
except Exception, e:
    print "Mako Templates for Python are not installed."
    print "You can download them at http://www.makotemplates.org/"
    print "or 'apt-get install python-mako' on most Debian/Ubuntu systems"
    exit(1)

class Preparator(object):
    
    DOMAIN = "grid.example.org"
    
    GRID_MANAGEMENT_SUBNET = 1
    GRID_AUTH_HOST = 1
    GRID_AUTH_HOSTNAME = "auth"
    GRID_AUTH_ROLE = "grid-auth"
    
    ORG_SUBNET_START = 100
    
    SERVER_HOST = 1
    SERVER_HOSTNAME = "server"
    SERVER_ROLE = "org-server"
    LOGIN_HOST = 2
    LOGIN_HOSTNAME = "login"
    LOGIN_ROLE = "org-login"
    GRIDFTP_HOST = 3
    GRIDFTP_HOSTNAME = "gridftp"
    GRIDFTP_ROLE = "org-gridftp"
    GATEKEEPER_HOST = 100
    GATEKEEPER_HOSTNAME = "gatekeeper"
    GATEKEEPER_CONDOR_ROLE = "org-gram-condor"
    GATEKEEPER_PBS_ROLE = "org-gram-pbs"
    LRM_NODE_HOST_START = 101
    LRM_NODE_HOSTNAME = "clusternode"
    LRM_NODE_CONDOR_ROLE = "org-clusternode-condor"
    LRM_NODE_PBS_ROLE = "org-clusternode-pbs"
    
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
    
    def __init__(self, demogrid_dir, config, generated_dir, force_certificates, force_chef):
        self.demogrid_dir = demogrid_dir
        self.config = config
        self.generated_dir = generated_dir
        self.force_certificates = force_certificates
        self.force_chef = force_chef
        self.certg = CertificateGenerator()
        
    def prepare(self):
        if not os.path.exists(self.generated_dir):
            os.makedirs(self.generated_dir)          
        
        print "\033[1;37mGenerating files... \033[0m",
        sys.stdout.flush()
        
        self.topology = self.generate_topology()
        self.topology.gen_hosts_file(self.generated_dir + "/hosts", 
                                     extra_entries = [("%s.0.1" % self.config.get_subnet(), "master.%s" % self.DOMAIN)])
        self.topology.gen_ruby_file(self.generated_dir + "/topology.rb")
        self.topology.gen_csv_file(self.generated_dir + "/topology.csv")
        self.gen_uvb_master_conf()
        self.gen_uvb_confs()
        self.gen_vagrant_file()

        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mGenerating certificates... \033[0m",
        sys.stdout.flush()

        cert_files = self.gen_certificates()
        
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mCopying chef files... \033[0m",
        sys.stdout.flush()

        chef_dir = self.demogrid_dir + self.CHEF_DIR
        if not os.path.exists(chef_dir):        
            print '\033[1;33mWarning\033[0m: Chef files not installed. DemoGrid will only work in EC2 mode'
        else:
            if self.copy_chef_files():
                print "\033[1;32mdone!\033[0m"
            else:
                print '\033[1;33mWarning\033[0m: Chef directory already exists. Skipping. Use --force-chef to overwrite'
        
            print "\033[1;37mCopying other files... \033[0m",
            sys.stdout.flush()
    
            self.copy_files(cert_files)

            print "\033[1;32mdone!\033[0m"

    
    def generate_topology(self):
        grid = DGGrid()
        
        if self.config.has_auth_node():
            auth_node = DGNode(role = self.GRID_AUTH_ROLE,
                               ip =   self.__gen_IP(self.GRID_MANAGEMENT_SUBNET, self.GRID_AUTH_HOST),
                               hostname = self.__gen_hostname(self.GRID_AUTH_HOSTNAME))
            grid.add_node(auth_node)
        
        org_subnet = self.ORG_SUBNET_START
        for org_name in self.config.organizations:
            org = DGOrganization(org_name, org_subnet)
            grid.add_organization(org)
            
            if self.config.has_org_users_file(org_name):
                usersfile = self.config.get_org_users_file(org_name)
                usersfile = open(usersfile, "r")
                
                for line in usersfile:
                    fields = line.split()
                    type = fields[0]
                    username = fields[1]
                    password = fields[2]
                    password_hash = fields[3]
                    
                    if type == "G":
                        user = DGOrgUser(login = username,
                                         description = "User '%s' of Organization %s" % (username, org_name),
                                         gridenabled = True, password = password, password_hash = password_hash,
                                         auth_type = self.config.get_org_user_auth(org_name))
                    else:
                        user = DGOrgUser(login = username,
                                         description = "User '%s' of Organization %s" % (username, org_name),
                                         gridenabled = False, password = password, password_hash = password_hash)
                    org.add_user(user)
                    
                usersfile.close()
            else:
                usernum = 1
                for i in range(self.config.get_org_num_gridusers(org_name)):
                    user = DGOrgUser(login = "%s-user%i" % (org_name, usernum),
                                     description = "User %i of Organization %s" % (usernum, org_name),
                                     gridenabled = True, password = self.DEFAULT_USER_PASSWD, password_hash = self.DEFAULT_USER_PASSWDHASH,
                                     auth_type = self.config.get_org_user_auth(org_name))
                    org.add_user(user)
                    usernum += 1
    
                for i in range(self.config.get_org_num_nongridusers(org_name)):
                    user = DGOrgUser(login = "%s-user%i" % (org_name, usernum),
                                     description = "User %i of Organization %s" % (usernum, org_name),
                                     gridenabled = False, password = self.DEFAULT_USER_PASSWD, password_hash = self.DEFAULT_USER_PASSWDHASH)
                    org.add_user(user)
                    usernum += 1
                
            
            server_node = DGNode(role = self.SERVER_ROLE,
                                 ip =   self.__gen_IP(org_subnet, self.SERVER_HOST),
                                 hostname = self.__gen_hostname(self.SERVER_HOSTNAME, org = org_name),
                                 org = org)            
            grid.add_org_node(org, server_node)
            org.server = server_node
            
            login_node =  DGNode(role = self.LOGIN_ROLE,
                                 ip =   self.__gen_IP(org_subnet, self.LOGIN_HOST),
                                 hostname = self.__gen_hostname(self.LOGIN_HOSTNAME, org = org_name),
                                 org = org)                        
            grid.add_org_node(org, login_node)

            if self.config.has_org_gridftp(org_name):
                gridftp_node = DGNode(role = self.GRIDFTP_ROLE,
                                      ip =   self.__gen_IP(org_subnet, self.GRIDFTP_HOST),
                                      hostname = self.__gen_hostname(self.GRIDFTP_HOSTNAME, org = org_name),
                                      org = org)                        
                grid.add_org_node(org, gridftp_node)
            
            if self.config.has_org_lrm(org_name):
                lrm_type = self.config.get_org_lrm(org_name)
                if lrm_type == "condor":
                    role = self.GATEKEEPER_CONDOR_ROLE
                    workernode_role = self.LRM_NODE_CONDOR_ROLE
                elif lrm_type == "torque":
                    role = self.GATEKEEPER_PBS_ROLE
                    workernode_role = self.LRM_NODE_PBS_ROLE
                    
                gatekeeper_node = DGNode(role = role,
                                         ip =   self.__gen_IP(org_subnet, self.GATEKEEPER_HOST),
                                         hostname = self.__gen_hostname(self.GATEKEEPER_HOSTNAME, org = org_name),
                                         org = org)                        
                grid.add_org_node(org, gatekeeper_node)
                org.lrm = gatekeeper_node

                clusternode_host = self.LRM_NODE_HOST_START
                for i in range(self.config.get_org_num_clusternodes(org_name)):
                    hostname = "%s-%i" % (self.LRM_NODE_HOSTNAME, i+1)
                    clusternode_node = DGNode(role = workernode_role,
                                              ip =   self.__gen_IP(org_subnet, clusternode_host),
                                              hostname = self.__gen_hostname(hostname, org = org_name),
                                              org = org)                        
                    grid.add_org_node(org, clusternode_node)
                    
                    clusternode_host += 1
            
            org_subnet += 1
        
        nodes = grid.get_nodes()
        for node in nodes:        
            attrs = node.attrs
            attrs["demogrid_hostname"] = "\"%s\"" % node.demogrid_hostname
            attrs["run_list"] = "[ \"role[%s]\" ]" % node.role
            if node.org != None:
                attrs["org"] = "\"%s\"" % node.org.name
                if self.config.has_org_lrm(node.org.name):
                    attrs["lrm_head"] = "\"%s\"" % self.__gen_hostname("gatekeeper", node.org.name)
                    attrs["lrm_nodes"] = "%i" % self.config.get_org_num_clusternodes(node.org.name)
            
        grid.save(self.generated_dir + "/topology.dat")
        
        nodes = grid.get_nodes()
        for n in nodes:
            if n.org != None:
                attrs = n.attrs
                attrs["subnet"] = "\"%s\"" % self.__gen_IP(n.org.subnet, 0)
                attrs["org_server"] = "\"%s\"" % self.__gen_IP(n.org.subnet, 1)
            
        return grid
        
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
                
    def gen_uvb_master_conf(self):
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
        
        
    def gen_uvb_confs(self):
        uvb_dir = self.generated_dir + self.UVB_DIR

        nodes = self.topology.get_nodes()
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
             
            
    def gen_certificates(self):
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
                                key_file = ca_key_file)

        users = [u for u in self.topology.get_users() if u.gridenabled and u.auth_type=="certs"]
        for user in users:        
            cert, key = self.certg.gen_user_cert(cn = user.description) 
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, user.login)
            key_file = "%s/%s_key.pem" % (certs_dir, user.login)
            cert_files.append(cert_file)
            cert_files.append(key_file)            
            self.__dump_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file)
        
        nodes = self.topology.get_nodes()
        for n in nodes:        
            cert, key = self.certg.gen_host_cert(hostname = n.hostname) 
            
            filename = n.demogrid_hostname + ".grid.example.org"
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, filename)
            key_file = "%s/%s_key.pem" % (certs_dir, filename)
            cert_files.append(cert_file)
            cert_files.append(key_file)                
            self.__dump_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file)        

        return cert_files  
        
        
    def gen_vagrant_file(self):
        vagrant_dir = self.generated_dir + self.VAGRANT_DIR
        if not os.path.exists(vagrant_dir):
            os.makedirs(vagrant_dir)         
        
        vagrant = "Vagrant::Config.run do |config|\n"
      
        nodes = self.topology.get_nodes()
        for n in nodes:
            name = n.hostname.split(".")[0].replace("-", "_")
            vagrant += "  config.vm.define :%s do |%s_config|\n" % (name, name)
            vagrant += "    %s_config.vm.box = \"lucid32\"\n" % name
            vagrant += "    %s_config.vm.provisioner = :chef_solo\n" % name
            vagrant += "    %s_config.chef.cookbooks_path = \"chef/cookbooks\"\n" % name
            vagrant += "    %s_config.chef.roles_path = \"chef/roles\"\n" % name
            vagrant += "    %s_config.chef.add_role \"%s\"\n" % (name, n.role)
            vagrant += "    %s_config.vm.network(\"%s\", :netmask => \"255.255.0.0\")\n" % (name, n.ip)            
            vagrant += "    %s_config.chef.json.merge!({\n" % name         
            for k,v in n.attrs.items():
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
        
        
    def copy_chef_files(self):
        src_chef = self.demogrid_dir + self.CHEF_DIR
        dst_chef = self.generated_dir + self.CHEF_DIR
        if os.path.exists(dst_chef):
            if self.force_chef:
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
        
    
    def __gen_IP(self, subnet, host):
        return "%s.%i.%i" % (self.config.get_subnet(), subnet, host)
    
    def __gen_hostname(self, name, org = None):
        if org == None:
            return "%s.%s" % (name, self.DOMAIN)
        else:
            return "%s-%s.%s" % (org, name, self.DOMAIN)
    
    def __dump_certificate(self, cert, key, cert_file, key_file):
        if os.path.exists(cert_file) and not self.force_certificates:
            print '\033[1;33mWarning\033[0m: Certificate %s already exists. Skipping. Use --force-certificates to overwrite' % cert_file.split("/")[-1]
        else:
            self.certg.save_certificate(cert, key, cert_file, key_file)     
        
