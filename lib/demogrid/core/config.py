import ConfigParser
from demogrid.core.topology import Domain, User, Node, Topology
from demogrid.common import constants
from demogrid.common.config import Config, Section, Option, OPTTYPE_INT, OPTTYPE_FLOAT, OPTTYPE_STRING, OPTTYPE_BOOLEAN

class DemoGridConfig(Config):
    
    sections = []    
    
    # ============================= #
    #                               #
    #        GENERAL OPTIONS        #
    #                               #
    # ============================= #    
    
    general = Section("general", required=True,
                      doc = "This section is used for general options affecting DemoGrid as a whole.")
    general.options = \
    [
     Option(name        = "ca-cert",
            getter      = "ca-cert",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            Location of CA certificate (PEM-encoded) used to generate user
            and host certificates. If blank, DemoGrid will generate a self-signed
            certificate from scratch.        
            """),    
     Option(name        = "ca-key",
            getter      = "ca-key",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            Location of the private key (PEM-encoded) for the certificate
            specified in "ca-cert".
            """),
     Option(name        = "scratch-dir",
            getter      = "scratch-dir",
            type        = OPTTYPE_STRING,
            required    = False,
            default     = "/var/tmp",
            doc         = """
            Scratch directory that Chef will use (on the provisioned machines)
            while configuring them.
            """),
     Option(name        = "deploy",
            getter      = "deploy",
            type        = OPTTYPE_STRING,
            required    = True,
            valid       = ["ec2", "dummy"],
            doc         = """
            Scratch directory that Chef will use (on the provisioned machines)
            while configuring them.
            """)     
    ]

    sections.append(general)

    # ====================== #
    #                        #
    #      EC2 OPTIONS       #
    #                        #
    # ====================== #

    ec2 = Section("ec2", required=False,
                         required_if = [(("general","deploy"),"ec2")],
                         doc = "EC2 options.")
    ec2.options = \
    [                
     Option(name        = "keypair",
            getter      = "ec2-keypair",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),
     Option(name        = "keyfile",
            getter      = "ec2-keyfile",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),
     Option(name        = "username",
            getter      = "ec2-username",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),     
     Option(name        = "availability-zone",
            getter      = "ec2-availability-zone",
            type        = OPTTYPE_STRING,
            required    = False,
            default     = None,
            doc         = """
            TODO
            """),
     Option(name        = "public",
            getter      = "ec2-public",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = True,
            doc         = """
            TODO
            """),
     Option(name        = "server-hostname",
            getter      = "ec2-server-hostname",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            TODO
            """),
     Option(name        = "server-port",
            getter      = "ec2-server-port",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            TODO
            """),
     Option(name        = "server-path",
            getter      = "ec2-server-path",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            TODO
            """)                                    
    ]    
    sections.append(ec2)

    # ================================ #
    #                                  #
    #      GLOBUS ONLINE OPTIONS       #
    #                                  #
    # ================================ #

    go = Section("globusonline", required=False,
                  doc = "Globus Online options.")
    go.options = \
    [       
     Option(name        = "username",
            getter      = "go-username",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),
     Option(name        = "cert-file",
            getter      = "go-cert-file",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),         
     Option(name        = "key-file",
            getter      = "go-key-file",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),        
     Option(name        = "server-ca-file",
            getter      = "go-server-ca-file",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),           
     Option(name        = "auth",
            getter      = "go-auth",
            type        = OPTTYPE_STRING,
            required    = True,
            valid       = ["go", "myproxy"],
            doc         = """
            TODO
            """)
    ]         
    sections.append(go)
      
    def __init__(self, config_file):
        Config.__init__(self, config_file, self.sections)


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


