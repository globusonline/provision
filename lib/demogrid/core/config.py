import ConfigParser
from demogrid.core.topology import Domain, User, Node, Topology
from demogrid.common import constants

class DemoGridConfig(object):
    
    GENERAL_SEC = "general"
    CACERT_OPT = "ca-cert"
    CAKEY_OPT = "ca-key"
    SCRATCHDIR_OPT = "scratch-dir"
    
    EC2_SEC = "ec2"
    AMI_OPT = "ami"
    SNAP_OPT = "snap"
    KEYPAIR_OPT = "keypair"
    KEYFILE_OPT = "keyfile"
    INSTYPE_OPT = "instance_type"
    ZONE_OPT = "availability_zone"
    ACCESS_OPT = "access"
    HOSTNAME_OPT = "hostname"
    PATH_OPT = "path"
    PORT_OPT = "port"
    USERNAME_OPT = "username"

    GO_SEC = "globusonline"
    GO_USERNAME_OPT = "username"
    GO_CERT_OPT = "cert-file"
    GO_KEY_OPT = "key-file"
    GO_SERVER_CA_OPT = "server-ca-file"
    GO_AUTH_OPT = "auth"
    
    def __init__(self, configfile):
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(configfile, "r"))

    def has_ca(self):
        return self.config.has_option(self.GENERAL_SEC, self.CACERT_OPT) and self.config.has_option(self.GENERAL_SEC, self.CAKEY_OPT)
    
    def get_ca(self):
        return self.config.get(self.GENERAL_SEC, self.CACERT_OPT), self.config.get(self.GENERAL_SEC, self.CAKEY_OPT)

    def get_scratch_dir(self):
        return self.config.get(self.GENERAL_SEC, self.SCRATCHDIR_OPT)
    
    def get_ami(self):
        return self.config.get(self.EC2_SEC, self.AMI_OPT)

    def has_snap(self):
        return self.config.has_option(self.EC2_SEC, self.SNAP_OPT)
    
    def get_snap(self):
        return self.config.get(self.EC2_SEC, self.SNAP_OPT)

    def get_keypair(self):
        return self.config.get(self.EC2_SEC, self.KEYPAIR_OPT)

    def get_keyfile(self):
        return self.config.get(self.EC2_SEC, self.KEYFILE_OPT)
    
    def get_instance_type(self):
        return self.config.get(self.EC2_SEC, self.INSTYPE_OPT)
    
    def get_ec2_zone(self):
        return self.config.get(self.EC2_SEC, self.ZONE_OPT)        
    
    def get_ec2_access_type(self):
        return self.config.get(self.EC2_SEC, self.ACCESS_OPT) 

    def get_go_username(self):
        return self.config.get(self.GO_SEC, self.GO_USERNAME_OPT) 
            
    def get_go_credentials(self):
        return (self.config.get(self.GO_SEC, self.GO_CERT_OPT),self.config.get(self.GO_SEC, self.GO_KEY_OPT))
    
    def get_go_server_ca(self):
        return self.config.get(self.GO_SEC, self.GO_SERVER_CA_OPT)

    def get_go_auth(self):
        return self.config.get(self.GO_SEC, self.GO_AUTH_OPT)

    def has_ec2_hostname(self):
        return self.config.has_option(self.EC2_SEC, self.HOSTNAME_OPT)
            
    def get_ec2_hostname(self):
        return self.config.get(self.EC2_SEC, self.HOSTNAME_OPT)

    def get_ec2_path(self):
        return self.config.get(self.EC2_SEC, self.PATH_OPT)
    
    def get_ec2_port(self):
        return int(self.config.get(self.EC2_SEC, self.PORT_OPT))

    def get_ec2_username(self):
        return self.config.get(self.EC2_SEC, self.USERNAME_OPT)


class SimpleTopologyConfig(object):
    
    GENERAL_SEC = "general"
    ORGANIZATIONS_OPT = "organizations"
    
    ORGANIZATION_SEC = "organization-"
    USERSFILE_OPT = "users-file"
    GRIDUSERS_OPT = "grid-users"
    GRIDUSERS_AUTH_OPT = "grid-users-auth"
    NONGRIDUSERS_OPT = "nongrid-users"
    LOGIN_OPT = "login"
    GRAM_OPT = "gram"
    GRIDFTP_OPT = "gridftp"
    LRM_OPT = "lrm"
    CLUSTER_NODES_OPT = "cluster-nodes"
  
    def __init__(self, configfile):
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(configfile, "r"))
        
        if self.config.has_option(self.GENERAL_SEC, self.ORGANIZATIONS_OPT):
            organizations = self.config.get(self.GENERAL_SEC, self.ORGANIZATIONS_OPT)
            self.organizations = organizations.split()
        else:
            self.organizations = []

    def has_org_users_file(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.has_option(org_sec, self.USERSFILE_OPT)    

    def get_org_users_file(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.get(org_sec, self.USERSFILE_OPT)    

    def get_org_num_gridusers(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getint(org_sec, self.GRIDUSERS_OPT)    

    def get_org_num_nongridusers(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getint(org_sec, self.NONGRIDUSERS_OPT)    

    def get_org_user_auth(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.get(org_sec, self.GRIDUSERS_AUTH_OPT)    
    
    def has_org_gridftp(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getboolean(org_sec, self.GRIDFTP_OPT)

    def has_org_login(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getboolean(org_sec, self.LOGIN_OPT)

    def has_org_gram(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getboolean(org_sec, self.GRAM_OPT)

    def has_org_auth(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getboolean(org_sec, self.MYPROXY_OPT)
    
    def has_org_lrm(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        lrm = self.config.get(org_sec, self.LRM_OPT)
        return lrm != "none"
        
    def get_org_lrm(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.get(org_sec, self.LRM_OPT)
    
    def get_org_num_clusternodes(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getint(org_sec, self.CLUSTER_NODES_OPT)
        
    def __get_org_sec(self, org_name):
        return self.ORGANIZATION_SEC + org_name

    def gen_topology(self):
        topology = Topology()
        
        for domain_name in self.domains:
            domain = Domain(domain_name)
            topology.add_domain(domain)
            
            if self.has_org_users_file(domain_name):
                usersfile = self.get_org_users_file(domain_name)
                usersfile = open(usersfile, "r")
                
                for line in usersfile:
                    fields = line.split()
                    type = fields[0]
                    username = fields[1]
                    password_hash = fields[2]
                    
                    if type == "G":
                        cert_type = self.get_org_user_auth(domain_name)
                    else:
                        cert_type = None
                    
                    user = User(login = username,
                                description = "User '%s' of Organization %s" % (username, domain_name),
                                password_hash = password_hash,
                                cert_type = cert_type)
                        
                    domain.add_user(user)
                    
                usersfile.close()
            else:
                usernum = 1
                for i in range(self.get_org_num_gridusers(domain_name)):
                    username = "%s-user%i" % (domain_name, usernum)
                    user = User(login = username,
                                description = "User '%s' of Organization %s" % (username, domain_name),
                                password_hash = "TODO",
                                cert_type = self.get_org_user_auth(domain_name))
                    domain.add_user(user)
                    usernum += 1
    
                for i in range(self.get_org_num_nongridusers(domain_name)):
                    username = "%s-user%i" % (domain_name, usernum)
                    user = User(login = username,
                                description = "User '%s' of Organization %s" % (username, domain_name),
                                password_hash = "TODO",
                                cert_type = None)
                    domain.add_user(user)
                    usernum += 1
                
            
            server_node = Node(name = "%s-nfsnis" % domain_name, domain = domain)
            server_node.run_list.append("role[domain-nfsnis]")
                        
            topology.add_domain_node(domain, server_node)
            domain.servers[constants.DOMAIN_NIS_SERVER] = server_node
            domain.servers[constants.DOMAIN_NFS_SERVER] = server_node
            
            if self.has_domain_login(domain_name):            
                login_node = Node(name = "%s-login" % domain_name, domain = domain)
                login_node.run_list.append("role[domain-login]")
                                 
                topology.add_domain_node(domain, login_node)

            if self.get_org_user_auth(domain_name) == "myproxy":
                myproxy_node = Node(name = "%s-myproxy" % domain_name, domain = domain)
                myproxy_node.run_list.append("role[domain-myproxy]")
                                 
                topology.add_domain_node(domain, myproxy_node)
                domain.servers[constants.DOMAIN_MYPROXY_SERVER] = myproxy_node

            if self.has_org_gridftp(domain_name):
                gridftp_node = Node(name = "%s-gridftp" % domain_name, domain = domain)
                gridftp_node.run_list.append("role[domain-gridftp]")
                                 
                topology.add_domain_node(domain, gridftp_node)
                domain.servers[constants.DOMAIN_GRIFTP_SERVER] = gridftp_node
            
            if self.has_org_lrm(domain_name):
                lrm_type = self.get_org_lrm(domain_name)
                gram = self.has_org_gram(domain_name)
                if lrm_type == "condor":
                    if gram:
                        node_name = "%s-gram-condor" % domain_name
                        role = "role[domain-gram-condor]"
                    else:
                        node_name = "%s-condor" % domain_name
                        role = "role[domain-condor]"
                    workernode_role = "role[domain-clusternode-condor]"

                lrm_node = Node(name = node_name, domain = domain)
                lrm_node.run_list.append(role)
                                 
                topology.add_domain_node(domain, lrm_node)
                domain.servers[constants.DOMAIN_LRMHEAD_SERVER] = lrm_node

                clusternode_host = 1
                for i in range(self.get_org_num_clusternodes(domain_name)):
                    wn_name = "%s-condor-wn%i" % (domain_name, i+1)
                    wn_node = Node(name = wn_name, domain = domain)
                    wn_node.run_list.append(workernode_role)
                                     
                    topology.add_domain_node(domain, wn_node)

                    clusternode_host += 1
            
        return topology


