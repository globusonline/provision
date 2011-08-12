from globus.provision.core.topology import Domain, User, Node, Topology
from globus.provision.common.config import Config, Section, Option, OPTTYPE_INT, OPTTYPE_FLOAT, OPTTYPE_STRING, OPTTYPE_BOOLEAN
import os.path
import getpass

class GPConfig(Config):

    sections = []    
    
    # ============================= #
    #                               #
    #        GENERAL OPTIONS        #
    #                               #
    # ============================= #    
    
    general = Section("general", required=True,
                      doc = "This section is used for general options affecting Globus Provision as a whole.")
    general.options = \
    [
     Option(name        = "ca-cert",
            getter      = "ca-cert",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            Location of CA certificate (PEM-encoded) used to generate user
            and host certificates. If blank, Globus Provision will generate a self-signed
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


class SimpleTopologyConfig(Config):
    
    sections = []    
    
    # ============================= #
    #                               #
    #        GENERAL OPTIONS        #
    #                               #
    # ============================= #    
    
    general = Section("general", required=True,
                      doc = "This section is used for general options affecting Globus Provision as a whole.")
    general.options = \
    [    
     Option(name        = "domains",
            getter      = "domains",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            TODO      
            """),    
     Option(name        = "deploy",
            getter      = "deploy",
            type        = OPTTYPE_STRING,
            required    = True,
            valid       = ["ec2", "dummy"],
            doc         = """
            TODO
            """),
     Option(name        = "ssh-pubkey",
            getter      = "ssh-pubkey",
            type        = OPTTYPE_STRING,
            required    = False,
            default     = "~/.ssh/id_rsa.pub",
            doc         = """
            TODO
            """)                                   
    ]     
    
    sections.append(general)
    
    domain = Section("domain", required=False, multiple=("general", "domains"),
                     doc = "This section is used for general options affecting Globus Provision as a whole.")
    domain.options = \
    [    
     Option(name        = "users-file",
            getter      = "users-file",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            TODO        
            """),    
     Option(name        = "users",
            getter      = "users",
            type        = OPTTYPE_INT,
            required    = False,
            default     = 0,
            doc         = """
            TODO        
            """),                             
     Option(name        = "users-no-cert",
            getter      = "users-no-cert",
            type        = OPTTYPE_INT,
            default     = 0,
            required    = False,
            doc         = """
            TODO        
            """),                   
     Option(name        = "login",
            getter      = "login",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            doc         = """
            TODO        
            """),
     Option(name        = "myproxy",
            getter      = "myproxy",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            doc         = """
            TODO        
            """),                           
     Option(name        = "gram",
            getter      = "gram",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            doc         = """
            TODO        
            """),                   
     Option(name        = "gridftp",
            getter      = "gridftp",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            doc         = """
            TODO        
            """),                   
     Option(name        = "lrm",
            getter      = "lrm",
            type        = OPTTYPE_STRING,
            valid       = ["none", "condor"],
            default     = "none",
            required    = False,
            doc         = """
            TODO        
            """),           
     Option(name        = "cluster-nodes",
            getter      = "cluster-nodes",
            type        = OPTTYPE_INT,
            required    = False,
            doc         = """
            TODO        
            """),                        
    ]     
    sections.append(domain)
    
    ec2 = Section("ec2", required=False,
                         required_if = [(("general","deploy"),"ec2")],
                         doc = "EC2 options.")    
    ec2.options = \
    [                
     Option(name        = "ami",
            getter      = "ec2-ami",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),
     Option(name        = "instance-type",
            getter      = "ec2-instance-type",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            TODO
            """),              
    ]    
    sections.append(ec2)    
  
    def __init__(self, configfile):
        Config.__init__(self, configfile, self.sections)

    def to_topology(self):
        ssh_pubkeyf = os.path.expanduser(self.get("ssh-pubkey"))
        ssh_pubkeyf = open(ssh_pubkeyf)
        ssh_pubkey = ssh_pubkeyf.read()
        ssh_pubkeyf.close()        
        
        topology = Topology()
        domains = self.get("domains").split()
        for domain_name in domains:
            domain = Domain()
            domain.set_property("id", domain_name)
            topology.add_to_array("domains", domain)

            user = User()
            user.set_property("id", getpass.getuser())
            user.set_property("password_hash", "!")
            user.set_property("certificate", "generated")
            user.set_property("admin", True)
            user.set_property("ssh_pkey", ssh_pubkey)
            domain.add_user(user)            

            usersfile = self.get((domain_name, "users-file"))
            
            if usersfile != None:                
                print domain_name, usersfile
                usersfile = open(usersfile, "r")
                
                for line in usersfile:
                    fields = line.split()
                    type = fields[0]
                    username = fields[1]
                    if len(fields) == 3:
                        user_ssh_pubkey = fields[2]
                    else:
                        user_ssh_pubkey = ssh_pubkey
                    
                    user = User()
                    user.set_property("id", username)
                    user.set_property("password_hash", "!")
                    user.set_property("ssh_pkey", user_ssh_pubkey)
                    if type == "C":
                        user.set_property("certificate", "generated")
                    else:
                        user.set_property("certificate", "none")
                        
                    domain.add_user(user)
                    
                usersfile.close()
            else:
                usernum = 1
                for i in range(self.get((domain_name, "users"))):
                    username = "%s-user%i" % (domain_name, usernum)
                    user = User()
                    user.set_property("id", username)
                    user.set_property("password_hash", "!")
                    user.set_property("ssh_pkey", ssh_pubkey)
                    user.set_property("certificate", "generated")
                    domain.add_user(user)
                    usernum += 1
    
                for i in range(self.get((domain_name, "users-no-cert"))):
                    username = "%s-user%i" % (domain_name, usernum)
                    user = User()
                    user.set_property("id", username)
                    user.set_property("password_hash", "!")
                    user.set_property("ssh_pkey", ssh_pubkey)
                    user.set_property("certificate", "none")           
                    domain.add_user(user)
                    usernum += 1
            
            server_node = Node()
            server_name = "%s-server" % domain_name
            server_node.set_property("id", server_name)
            server_node.add_to_array("run_list", "role[domain-nfsnis]")
            domain.add_node(server_node)

            if self.get((domain_name,"login")):            
                login_node = Node()
                login_node.set_property("id", "%s-login" % domain_name)
                login_node.set_property("depends", "node:%s" % server_name)
                login_node.add_to_array("run_list", "role[domain-login]")
                domain.add_node(login_node)
            else:
                server_node.add_to_array("run_list", "role[globus]")

            if self.get((domain_name,"myproxy")):
                myproxy_node = Node()
                myproxy_node.set_property("id", "%s-myproxy" % domain_name)
                myproxy_node.set_property("depends", "node:%s" % server_name)
                myproxy_node.add_to_array("run_list", "role[domain-myproxy]")
                domain.add_node(myproxy_node)

            if self.get((domain_name,"gridftp")):
                gridftp_node = Node()
                gridftp_node.set_property("id", "%s-gridftp" % domain_name)
                gridftp_node.set_property("depends", "node:%s" % server_name)
                gridftp_node.add_to_array("run_list", "role[domain-gridftp]")
                domain.add_node(gridftp_node)                
            
            lrm = self.get((domain_name,"lrm"))
            if lrm != "none":
                gram = self.get((domain_name,"gram"))
                if lrm == "condor":
                    if gram:
                        node_name = "%s-gram-condor" % domain_name
                        role = "role[domain-gram-condor]"
                    else:
                        node_name = "%s-condor" % domain_name
                        role = "role[domain-condor]"
                    workernode_role = "role[domain-clusternode-condor]"

                lrm_node = Node()
                lrm_node.set_property("id", node_name)
                lrm_node.set_property("depends", "node:%s" % server_name)
                lrm_node.add_to_array("run_list", role)
                domain.add_node(lrm_node)

                clusternode_host = 1
                for i in range(self.get((domain_name,"cluster-nodes"))):
                    wn_name = "%s-condor-wn%i" % (domain_name, i+1)

                    wn_node = Node()
                    wn_node.set_property("id", wn_name)
                    wn_node.set_property("depends", "node:%s" % node_name)
                    wn_node.add_to_array("run_list", workernode_role)
                    domain.add_node(wn_node)

                    clusternode_host += 1
            
        return topology


