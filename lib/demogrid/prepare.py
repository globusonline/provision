import os
import os.path

from OpenSSL import crypto, SSL
import sys
import shutil


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
    
    def __init__(self, demogrid_dir, config, generated_dir, force):
        self.demogrid_dir = demogrid_dir
        self.config = config
        self.generated_dir = generated_dir
        self.force = force
        
    def prepare(self):
        if not os.path.exists(self.generated_dir):
            os.makedirs(self.generated_dir)          
        
        print "\033[1;37mGenerating files... \033[0m",
        sys.stdout.flush()
        
        self.topology = self.generate_topology()
        self.gen_hosts_file()
        self.gen_hosts_csv_file()
        self.gen_topology_attributes_file()
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
        if self.copy_chef_files():
            print "\033[1;32mdone!\033[0m"
        else:
            print '\033[1;33mWarning\033[0m: Chef directory already exists. Skipping. Use --force to overwrite'

        
        print "\033[1;37mCopying other files... \033[0m",
        sys.stdout.flush()

        self.copy_files(cert_files)

        print "\033[1;32mdone!\033[0m"

    
    def generate_topology(self):
        grid = DGGrid()
        
        auth_node = DGNode(role = self.GRID_AUTH_ROLE,
                           ip =   self.__gen_IP(self.GRID_MANAGEMENT_SUBNET, self.GRID_AUTH_HOST),
                           hostname = self.__gen_hostname(self.GRID_AUTH_HOSTNAME))
        grid.add_node(auth_node)
        
        org_subnet = self.ORG_SUBNET_START
        for org_name in self.config.organizations:
            org = DGOrganization(org_name, org_subnet)
            grid.add_organization(org)
            
            usernum = 1
            for i in range(self.config.get_org_num_gridusers(org_name)):
                user = DGOrgUser(login = "%s-user%i" % (org_name, usernum),
                                 description = "User %i of Organization %s" % (usernum, org_name),
                                 gridenabled = True,
                                 auth_type = self.config.get_org_user_auth(org_name))
                org.add_user(user)
                usernum += 1

            for i in range(self.config.get_org_num_nongridusers(org_name)):
                user = DGOrgUser(login = "%s-user%i" % (org_name, usernum),
                                 description = "User %i of Organization %s" % (usernum, org_name),
                                 gridenabled = False)
                org.add_user(user)
                usernum += 1
                
            
            server_node = DGNode(role = self.SERVER_ROLE,
                                 ip =   self.__gen_IP(org_subnet, self.SERVER_HOST),
                                 hostname = self.__gen_hostname(self.SERVER_HOSTNAME, org = org_name),
                                 org = org)            
            grid.add_org_node(org, server_node)
            
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
        
    def gen_hosts_csv_file(self):
        hosts_csv = "fqdn,name,ip,role\n"
                
        nodes = self.topology.get_nodes()
        for n in nodes:
            hosts_csv += ",".join((n.hostname, n.hostname.split(".")[0], n.ip, n.role))
            hosts_csv += "\n"
        
        hosts_csvfile = open(self.generated_dir + "/hosts.csv", "w")
        hosts_csvfile.write(hosts_csv)
        hosts_csvfile.close()
        
    def gen_topology_attributes_file(self):
        topology = ""
      
        nodes = self.topology.get_nodes()
        for n in nodes:
            attrs = self.__gen_chef_attrs(n)
            topology += "if node.name == \"%s\"\n" % n.hostname
            for k,v in attrs.items():
                topology += "  node.normal[:%s] = %s\n" % (k,v)
            topology += "end\n\n"            

	for org in self.topology.organizations.values():
            topology += "default[:orgusers][\"%s\"] = [\n" % org.name
            for u in org.users:
                topology += "{ :login       => \"%s\",\n" % u.login
                topology += "  :description => \"%s\",\n" % u.description
                if u.gridenabled:
                    topology += "  :gridenabled => true,\n"
                    topology += "  :auth_type   => :%s}" % u.auth_type
                else:
                    topology += "  :gridenabled => false}"
                topology += ",\n"
            topology += "]\n"

        topologyfile = open(self.generated_dir + "/topology.rb", "w")
        topologyfile.write(topology)
        topologyfile.close()        
        
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

        ca_cert, ca_key = self.__gen_certificate(cn = "DemoGrid CA", 
                                                 serial = 1,
                                                 issuer_cert = None,
                                                 issuer_key = None)
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

        serial_number = 2
        users = [u for u in self.topology.get_users() if u.gridenabled and u.auth_type=="certs"]
        for user in users:        
            cert, key = self.__gen_certificate(cn = user.description, 
                                               serial = serial_number,
                                               issuer_cert = ca_cert,
                                               issuer_key = ca_key)
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, user.login)
            key_file = "%s/%s_key.pem" % (certs_dir, user.login)
            cert_files.append(cert_file)
            cert_files.append(key_file)            
            self.__dump_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file)
            serial_number += 1
        
        nodes = self.topology.get_nodes()
        for n in nodes:        
            cert, key = self.__gen_certificate(cn = "host/%s" % n.hostname, 
                                               serial = serial_number,
                                               issuer_cert = ca_cert,
                                               issuer_key = ca_key)
            
            cert_file = "%s/%s_cert.pem" % (certs_dir, n.hostname)
            key_file = "%s/%s_key.pem" % (certs_dir, n.hostname)
            cert_files.append(cert_file)
            cert_files.append(key_file)                
            self.__dump_certificate(cert = cert,
                                    key = key,
                                    cert_file = cert_file,
                                    key_file = key_file)            

            serial_number += 1          

        return cert_files  
        
        
    def gen_vagrant_file(self):
        vagrant_dir = self.generated_dir + self.VAGRANT_DIR
        if not os.path.exists(vagrant_dir):
            os.makedirs(vagrant_dir)         
        
        vagrant = "Vagrant::Config.run do |config|\n"
      
        nodes = self.topology.get_nodes()
        for n in nodes:
            attrs = self.__gen_chef_attrs(n)
            name = n.hostname.split(".")[0].replace("-", "_")
            vagrant += "  config.vm.define :%s do |%s_config|\n" % (name, name)
            vagrant += "    %s_config.vm.box = \"lucid32\"\n" % name
            vagrant += "    %s_config.vm.provisioner = :chef_solo\n" % name
            vagrant += "    %s_config.chef.cookbooks_path = \"chef/cookbooks\"\n" % name
            vagrant += "    %s_config.chef.roles_path = \"chef/roles\"\n" % name
            vagrant += "    %s_config.chef.add_role \"%s\"\n" % (name, n.role)
            vagrant += "    %s_config.vm.network(\"%s\", :netmask => \"255.255.0.0\")\n" % (name, n.ip)            
            vagrant += "    %s_config.chef.json.merge!({\n" % name         
            for k,v in attrs.items():
                vagrant += "      :%s => %s,\n" % (k,v)
            vagrant += "    })\n"       
            vagrant += "  end\n\n"           
        vagrant += "end\n"           

        vagrantfile = open(vagrant_dir + "/Vagrantfile", "w")
        vagrantfile.write(vagrant)
        vagrantfile.close()
        
        chef_link = vagrant_dir + "/chef"
        if os.path.exists(chef_link):
            os.remove(chef_link)            
        os.symlink(self.generated_dir + self.CHEF_DIR, chef_link)
        
        
    def copy_chef_files(self):
        src_chef = self.demogrid_dir + self.CHEF_DIR
        dst_chef = self.generated_dir + self.CHEF_DIR
        if os.path.exists(dst_chef):
            if self.force:
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
        
    def __gen_chef_attrs(self, node):
        attrs = {}
        attrs["demogrid_hostname"] = "\"%s\"" % node.hostname.split(".")[0]
        attrs["run_list"] = "[ \"role[%s]\" ]" % node.role
        if node.org != None:
            attrs["org"] = "\"%s\"" % node.org.name
            attrs["subnet"] = "\"%s\"" % self.__gen_IP(node.org.subnet, 0)
            attrs["org_server"] = "\"%s\"" % self.__gen_IP(node.org.subnet, 1)
            attrs["lrm_head"] = "\"%s\"" % self.__gen_hostname("gatekeeper", node.org.name)
        return attrs
    
    def __gen_certificate(self, cn, serial, issuer_cert, issuer_key):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        cert = crypto.X509()
        cert.get_subject().O = "Grid"
        cert.get_subject().OU = "DemoGrid"
        cert.get_subject().CN = cn
        cert.set_serial_number(serial)
        cert.set_version(2)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_pubkey(k)

        
        if issuer_cert == None:
            cert.set_issuer(cert.get_subject())
        else:
            cert.set_issuer(issuer_cert.get_subject())
            
        if issuer_cert == None:
            cert.sign(k, 'sha1')
        else:
            cert.sign(issuer_key, 'sha1')   
        
        return cert, k 
    
    def __dump_certificate(self, cert, key, cert_file, key_file):
        if os.path.exists(cert_file) and not self.force:
            print '\033[1;33mWarning\033[0m: Certificate %s already exists. Skipping. Use --force to overwrite' % cert_file.split("/")[-1]
        else:
            cert_file = open(cert_file, "w")
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            cert_file.close()  
        
            key_file = open(key_file, "w")
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
            key_file.close()        
    
class DGGrid(object):    
    
    def __init__(self):
        self.grid_nodes = []
        self.organizations = {}
        
    def add_organization(self, org):
        self.organizations[org.name] = org

    def add_org_node(self, org, node):
        self.grid_nodes.append(node)

    def add_node(self, node):
        self.grid_nodes.append(node)
        
    def get_nodes(self):
        nodes = self.grid_nodes[:]
        for org in self.organizations.values():
            nodes += org.get_nodes()
        return nodes
    
    def get_users(self):
        users = []
        for org in self.organizations.values():
            users += org.get_users()
        return users    
    
class DGOrganization(object):    
    def __init__(self, name, subnet):
        self.name = name
        self.subnet = subnet
        self.nodes = []
        self.users = []

    def add_node(self, node):
        self.nodes.append(node)
        
    def get_nodes(self):
        return self.nodes
        
    def add_user(self, user):
        self.users.append(user)   
        
    def get_users(self):
        return self.users
    
class DGNode(object):
    def __init__(self, role, ip, hostname, org = None):
        self.role = role
        self.ip = ip
        self.hostname = hostname
        self.org = org
        
class DGOrgUser(object):
    def __init__(self, login, description, gridenabled, auth_type=None):
        self.login = login
        self.description = description
        self.gridenabled = gridenabled
        self.auth_type = auth_type    
        
