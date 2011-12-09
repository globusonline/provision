# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                 #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

"""
Contains the parsers for the two configuration files used in Globus Provision:

* The instance configuration file (GPConfig): This is the configuration file
  that specifies options related to an instance's deploymenr.
  
* The simple topology file: This is a simple format for specifying topologies
  (which internally translated to the topology JSON format). It has the
  format of a configuration file although, strictly speaking, it is *not*
  a configuration file.    

"""

from globus.provision.core.topology import Domain, User, Node, Topology,\
    DeployData, EC2DeployData, GridMapEntry, GOEndpoint, FileSystem, NFSMount
from globus.provision.common.config import Config, Section, Option, OPTTYPE_INT, OPTTYPE_FLOAT, OPTTYPE_STRING, OPTTYPE_BOOLEAN, OPTTYPE_FILE
import os.path
import getpass

class GPConfig(Config):
    """
    The instance configuration file.
    """

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
            type        = OPTTYPE_FILE,
            required    = False,
            doc         = """
            Location of CA certificate (PEM-encoded) used to generate user
            and host certificates. If blank, Globus Provision will generate a self-signed
            certificate from scratch.        
            """),    
     Option(name        = "ca-key",
            getter      = "ca-key",
            type        = OPTTYPE_FILE,
            required    = False,
            doc         = """
            Location of the private key (PEM-encoded) for the certificate
            specified in ``ca-cert``.
            """),
     Option(name        = "ca-dn",
            getter      = "ca-dn",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            Distinguished Name of the certificates that will be signed with 
            the CA certificate specified in ``ca-cert``. 
            
            For example, if you set this value to ``O=Foo, OU=Bar``, the certificates
            will have subjects like ``/O=Foo/OU=Bar/CN=borja``, ``/O=Foo/OU=Bar/CN=host/foo.example.org``, etc.
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
            Globus Provision can support various "deployers" that are used to
            deploy the hosts in a topology. Two deployers are currently supported:
            
            * ``ec2``: Hosts are deployed as Amazon EC2 instances.
            * ``dummy``: Hosts are not actually deployed and are assigned dummy
              hostnames and IP addresses.
              
            See the Globus Provision documentation for more details on the
            available deployers.
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
                         doc = """
                         When the EC2 deployer is selected, Globus Provision will need certain information about
                         your EC2 account to be able to request EC2 instances on which to deploy your topology. This account
                         information is specified in this section of the configuration file. If you are unclear on what values
                         you need to specify here, see :ref:`chap_ec2` for more detailed instructions (including how to set up
                         an Amazon EC2 account)""")
    ec2.options = \
    [                
     Option(name        = "keypair",
            getter      = "ec2-keypair",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            The *name* of the Amazon EC2 keypair you will use to log into the VMs.
            See :ref:`chap_ec2` for instructions on how to obtain this keypair.
            """),
     Option(name        = "keyfile",
            getter      = "ec2-keyfile",
            type        = OPTTYPE_FILE,
            required    = True,
            doc         = """
            The actual location of the keypair on your local filesystem.
            See :ref:`chap_ec2` for instructions on how to obtain this keypair.
            """),
     Option(name        = "username",
            getter      = "ec2-username",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            The username that Globus Provision will use to connect to the EC2 instances,
            using the keypair specified in ``keypair``. If you are using one of the
            Globus Provision AMIs, you need to set this value to ``ubuntu``.
            """),     
     Option(name        = "server-hostname",
            getter      = "ec2-server-hostname",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            The hostname of the EC2 server. If you are using Amazon AWS, leave this option
            unspecified. If you are using an EC2-compatible system, such as OpenNebula, Nimbus,
            Eucalyptus, etc. set this to the server running that system's EC2 interface.
            """),
     Option(name        = "server-port",
            getter      = "ec2-server-port",
            type        = OPTTYPE_INT,
            required    = False,
            doc         = """
            The TCP port of the EC2 server. If you are using Amazon AWS, leave this option
            unspecified. If you are using an EC2-compatible system, such as OpenNebula, Nimbus,
            Eucalyptus, etc. set this to the port on which that system's EC2 interface is listening on.
            """),
     Option(name        = "server-path",
            getter      = "ec2-server-path",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            The path portion of the EC2 server. If you are using Amazon AWS, leave this option
            unspecified. If you are using an EC2-compatible system, such as OpenNebula, OpenStack,
            Eucalyptus, etc. set this to the path (in the host specified in ``server-hostname``)
            that the system's EC2 interface is available on.
            """)                                    
    ]    
    sections.append(ec2)

    # ================================ #
    #                                  #
    #      GLOBUS ONLINE OPTIONS       #
    #                                  #
    # ================================ #

    go = Section("globusonline", required=False,
                  doc = """
                  When a topology includes Globus Online transfer endpoints, Globus Provision will
                  use GO's API to set up those endpoints. To do so, it will need some information
                  about your GO account. If you are unclear on what values you need to specify here, 
                  see :ref:`chap_go` for more detailed instructions.
                  """)
    go.options = \
    [       
   
     Option(name        = "ssh-key",
            getter      = "go-ssh-key",
            type        = OPTTYPE_FILE,
            default     = "~/.ssh/id_rsa",            
            required    = False,
            doc         = """
            SSH key to use when connecting to the Globus Online CLI. The public key
            for this SSH key must have been previously added to your Globus Online
            profile.
            """),          
     Option(name        = "cert-file",
            getter      = "go-cert-file",
            type        = OPTTYPE_FILE,
            required    = False,
            doc         = """
            When this option is specified, Globus Provision will access your GO
            account using Globus Online's Transfer API (instead of sending commands
            to Globus Online's CLI via SSH). To do so, Globus Provision needs the
            location of a user certificate (PEM-encoded) that is authorized to access 
            the accounts specified in your topology's endpoints.
            
            See :ref:`chap_go` for more details on the differences between using the
            Transfer API, instead of the CLI via SSH.
            """),         
     Option(name        = "key-file",
            getter      = "go-key-file",
            type        = OPTTYPE_FILE,
            required    = False,
            doc         = """
            Location of the private key (PEM-encoded) for the certificate
            specified in ``cert-file``.
            """),        
     Option(name        = "server-ca-file",
            getter      = "go-server-ca-file",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            To verify the server certificate of the Globus Online Transfer API server,
            Globus Provision needs the certificate of the CA that signed that certificate.
            This file is already bundled with Globus Provision. The only reason for using
            this option to specify a different CA certificate is in the unlikely case that
            the API server decides to switch to a different CA (and the file bundled
            with Globus Provision has not been updated to that CA yet).
            """)
    ]         
    sections.append(go)
      
    def __init__(self, config_file):
        Config.__init__(self, config_file, self.sections)


class SimpleTopologyConfig(Config):
    """
    The simple topology file
    """    
    
    sections = []    
    
    # ============================= #
    #                               #
    #        GENERAL OPTIONS        #
    #                               #
    # ============================= #    
    
    general = Section("general", required=True,
                      doc = "This section is used for general options affecting all the topology.")
    general.options = \
    [    
     Option(name        = "domains",
            getter      = "domains",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            The names of the domains you are defining in this topology. They must each be separated by
            a single space.      
            """),    
     Option(name        = "deploy",
            getter      = "deploy",
            type        = OPTTYPE_STRING,
            required    = True,
            valid       = ["ec2", "dummy"],
            doc         = """
            See the :ref:`deploy option <GPConfig_deploy>` in :ref:`chap_config_ref` 
            """),
     Option(name        = "ssh-pubkey",
            getter      = "ssh-pubkey",
            type        = OPTTYPE_FILE,
            required    = False,
            default     = "~/.ssh/id_rsa.pub",
            doc         = """
            When creating users, an SSH public key must be added to their ``authorized_keys`` file
            to allow the creator of the topology to log in as those users. When using a topology file,
            each SSH key is specified separately for each user; in a simple topology, you can specify
            a single SSH public key for all the users (by default, the SSH key of the topology's creator 
            will be used)
            
            Take into account that you *can* specify per-user SSH keys in a simple topology by using the
            :ref:`users-file option<SimpleTopologyConfig_users-file>`.
            """)                                   
    ]     
    
    sections.append(general)
    
    domain = Section("domain", required=False, multiple=("general", "domains"),
                     doc = """
                     For each domain specified in the ``domains`` option, you will need to specify a section
                     titled ``[domain-DDD]`` where ``DD`` is the name of the domain. For example, if you specify the following::
                     
                         [general]
                         domains: foo bar
                         
                     You will need to specify the following sections::
                     
                         [domain-foo]
                         ...
                         
                         [domain-bar]
                         ...
                         
                     Each section provides a few high-level options about each domain.
                     This provides a simple, but constrained, way of specifying what services and users
                     should be created in each domain. For more complex topologies, you may have
                     to write a regular :ref:`topology file <chap_topology>`.                     
                     """)
    domain.options = \
    [    
     Option(name        = "users",
            getter      = "users",
            type        = OPTTYPE_STRING,
            required    = False,
            default     = "0",
            doc         = """
            This option can be either a number, or a list of usernames separated by spaces.
            
            If a number is specified, the users will be named ``D-userN``, where ``D`` is the
            domain name and ``N`` is a number between 1 and the number specified in this option.
            
            If a list of usernames is specified, users with those login names will be created.
            
            These users will be created with corresponding user certificates. To create users without user certificates
            use option ``users-no-cert``.        
            """),                             
     Option(name        = "users-no-cert",
            getter      = "users-no-cert",
            type        = OPTTYPE_STRING,
            default     = "0",
            required    = False,
            doc         = """
            Same as ``users`` but creating users without certificates.
            
            Note that if you specify a number for *both* the ``users`` and ``users-no-cert`` option 
            (with values N and M, respectively), the first N users will have certificates, and the 
            remaining M will not.        
            """),                   
     Option(name        = "users-file",
            getter      = "users-file",
            type        = OPTTYPE_FILE,
            required    = False,
            doc         = """
            The path to a file with a specification of the users to create in this domain. This file will have one line
            per user, each with three fields (separated by whitespace):
            
            #. A single character, ``C`` or ``N``. If ``C`` is specified, the user will have a user certificate created
               for it. Otherwise, it will nor.
            #. The user's UNIX login name.
            #. (Optional) An SSH public key to add to the user's ``authorized_keys`` file. If not specified, the public
               key specified in :ref:`option ssh-pubkey<SimpleTopologyConfig_ssh-pubkey>` will be used.
              
            For example::
            
                C borja     ssh-rsa FOOFOOFOO...BARBARBAR borja@example.org
                C childers  ssh-rsa FOOFOOFOO...BARBARBAR childers@example.org
                N foster
                N madduri
            
            """),   
     
     Option(name        = "nis",
            getter      = "nis",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = False,
            doc         = """
            Specifies whether an NIS server should be setup in this domain. When ``True``, there will be a
            user account space in the domain. When ``False``, user accounts and home directories will be 
            created on every individual host. This option can be useful if you are creating a single-host domain.       
            """),          
     
     Option(name        = "barebones-nodes",
            getter      = "barebones-nodes",
            type        = OPTTYPE_INT,
            default     = 0,
            required    = False,
            doc         = """
            A "barebones node" is a node on which no software will be installed. If ``nfs-nis`` is ``True``,
            these nodes *will* be configured as NFS/NIS clients. These nodes can be useful for testing.   
            """),            
     
     
     Option(name        = "filesystem",
            getter      = "filesystem",
            type        = OPTTYPE_STRING,
            required    = False,
            default     = "local-only",
            valid       = ["local-only", "nfs", "glusterfs"],
            doc         = """
            TODO       
            """),  

     Option(name        = "glusterfs-servers",
            getter      = "glusterfs-servers",
            type        = OPTTYPE_INT,
            required    = False,
            default     = 1,
            doc         = """
            TODO       
            """),  
     
     Option(name        = "glusterfs-type",
            getter      = "glusterfs-type",
            type        = OPTTYPE_STRING,
            valid       = ["distributed", "replicated", "striped",
                           "distributed-striped", "distributed-replicated"],
            default     = "distributed",
            required    = False,
            doc         = """
            TODO       
            """),  
     
     Option(name        = "glusterfs-setsize",
            getter      = "glusterfs-setsize",
            type        = OPTTYPE_INT,
            required    = False,
            default     = 2,
            doc         = """
            TODO       
            """),       
                  
     Option(name        = "login",
            getter      = "login",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = False,
            doc         = """
            Specifies whether a separate "login node" should be created in the topology. This option can be useful if you
            want a distinct node that users can log into but that does not host one of the topology's servers (like the NFS
            server, a GridFTP server, etc.)        
            """),
     Option(name        = "myproxy",
            getter      = "myproxy",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = False,
            doc         = """
            Specifies whether to set up a MyProxy server on this domain.        
            """),                           
     Option(name        = "gram",
            getter      = "gram",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = False,
            doc         = """
            Specifies whether to set up a GRAM5 server on this domain.             
            """),                   
     Option(name        = "gridftp",
            getter      = "gridftp",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = False,
            doc         = """
            Specifies whether to set up a GridFTP server on this domain.             
            """),                   
     Option(name        = "condor",
            getter      = "condor",
            type        = OPTTYPE_BOOLEAN,
            default     = False,
            required    = False,
            doc         = """
            Specifies whether to set up a `Condor <http://www.cs.wisc.edu/condor/>`_ cluster
            in this domain.   
            """),           
     Option(name        = "condor-nodes",
            getter      = "condor-nodes",
            type        = OPTTYPE_INT,
            required    = False,
            doc         = """
            The number of Condor worker nodes to create.        
            """),     
     Option(name        = "hadoop",
            getter      = "hadoop",
            type        = OPTTYPE_BOOLEAN,
            default     = False,
            required    = False,
            doc         = """
            Specifies whether to set up a `Hadoop <http://hadoop.apache.org/>`_ cluster
            in this domain.   
            """),           
     Option(name        = "hadoop-nodes",
            getter      = "hadoop-nodes",
            type        = OPTTYPE_INT,
            required    = False,
            doc         = """
            The number of Hadoop slave nodes to create.        
            """),     
     Option(name        = "R",
            getter      = "R",
            type        = OPTTYPE_BOOLEAN,
            default     = False,
            required    = False,
            doc         = """
            Specifies whether to install R in this domain.   
            """),        
     Option(name        = "galaxy",
            getter      = "galaxy",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = False,
            doc         = """
            Specifies whether to set up a Galaxy server on this domain.        
            """),   
              
     Option(name        = "go-endpoint",
            getter      = "go-endpoint",
            type        = OPTTYPE_STRING,
            required    = False,
            doc         = """
            If this domain has a GridFTP server, it can be configured as a GO endpoint.
            The format for this option is <username>#<name> (e.g., johnsmith#test-ep).
            Take into account that you must be authorized to use the GO account for <username>,
            and that you must specify the appropriate credentials in the 
            :ref:`[globusonline] section<GPConfig_section_globusonline>` of the configuration file.
            
            See :ref:`chap_go` for more details.    
            """),
               
     Option(name        = "go-auth",
            getter      = "go-auth",
            type        = OPTTYPE_STRING,
            required    = False,
            valid       = ["myproxy", "go"],            
            doc         = """
            The authentication method that Globus Online will use when contacting the endpoint on
            behalf of a user. The valid options are:
            
            * ``myproxy``: Contact the MyProxy server specified in the topology. Note that 
              the :ref:`myproxy option<SimpleTopologyConfig_myproxy>` must be set to ``true`` 
              for this to work
            * ``go``: Use Globus Online authentication.
              
            See :ref:`chap_go`, and specifically :ref:`Globus Online Authentication Methods <sec_go_auth>`,
            for more details on the implications of each authentication method.            
            """),
     
     Option(name        = "go-gc",
            getter      = "go-gc",
            type        = OPTTYPE_BOOLEAN,
            required    = False,
            default     = True,
            doc         = """
            If true, the endpoint will use a Globus Connect certificate.
            If not, it will use the host certificate generated by Globus Provision.
            Take into account that, for the GridFTP server to be trusted by
            Globus Online, it must use a certificate trusted by Globus Online.
            Unless you used a CA trusted by Globus Online to generate the certificates
            for the topology, you must use a Globus Connect certificate.
            """)                            
    ]     
    sections.append(domain)
    
    ec2 = Section("ec2", required=False,
                         required_if = [(("general","deploy"),"ec2")],
                         doc = """
                         When the EC2 deployer is selected, this section will allow you to
                         specify EC2 deployment options that are specific to this topology.""")    
    ec2.options = \
    [                
     Option(name        = "ami",
            getter      = "ec2-ami",
            type        = OPTTYPE_STRING,
            required    = True,
            doc         = """
            This is the AMI (`Amazon Machine Image <http://en.wikipedia.org/wiki/Amazon_Machine_Image>`_) 
            that Globus Provision will use to create each host in the domani. Any recent Ubuntu or Debian
            AMI should work. Nonetheless, take into account that we provide an AMI that has most of the
            necessary software pre-installed in it, considerably speeding up the setup of the machines. 
            The latest Globus Provision AMI is always listed in the Globus Provision website.
            """),
     Option(name        = "instance-type",
            getter      = "ec2-instance-type",
            type        = OPTTYPE_STRING,
            required    = True,
            default     = "t1.micro",
            doc         = """
            This is the `EC2 instance type <http://en.wikipedia.org/wiki/Amazon_Machine_Image>`_ that will
            be used to launch the machines in this domain. The default is to use micro-instances (t1.micro),
            which tend to be enough if you are just tinkering around.
            """),         
     Option(name        = "availability-zone",
            getter      = "ec2-availability-zone",
            type        = OPTTYPE_STRING,
            required    = False,
            default     = None,
            doc         = """
            The `availability zone <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/concepts-regions-availability-zones.html>`_ 
            you want the VMs to be deployed in. 
            Unless you have a good reason for choosing a specific availability zone,
            you should let Globus Provision choose a default zone for you.
            """)          
    ]    
    sections.append(ec2)    
  
 
    def __init__(self, configfile):
        Config.__init__(self, configfile, self.sections)

    def to_topology(self):
        ssh_pubkeyf = os.path.expanduser(self.get("ssh-pubkey"))
        ssh_pubkeyf = open(ssh_pubkeyf)
        ssh_pubkey = ssh_pubkeyf.read().strip()
        ssh_pubkeyf.close()        
        
        topology = Topology()
        
        if self.get("deploy") == "dummy":
            # No default deploy data
            pass
        elif self.get("deploy") == "ec2":
            deploy_data = DeployData()
            ec2_deploy_data = EC2DeployData()
            
            ec2_deploy_data.set_property("ami", self.get("ec2-ami"))
            ec2_deploy_data.set_property("instance_type", self.get("ec2-instance-type"))
            
            deploy_data.set_property("ec2", ec2_deploy_data)
            topology.set_property("default_deploy_data", deploy_data)
        
        domains = self.get("domains").split()
        for domain_name in domains:
            domain = Domain()
            domain.set_property("id", domain_name)
            topology.add_to_array("domains", domain)
            
            glusterfs_servers = []

            has_go_ep = self.get((domain_name,"go-endpoint")) != None

            user = User()
            user.set_property("id", getpass.getuser())
            user.set_property("password_hash", "!")
            user.set_property("certificate", "generated")
            user.set_property("admin", True)
            user.set_property("ssh_pkey", ssh_pubkey)
            domain.add_user(user)            

            usersfile = self.get((domain_name, "users-file"))
            
            if usersfile != None:
                usersfile = open(usersfile, "r")
                
                for line in usersfile:
                    fields = line.split()
                    type = fields[0]
                    username = fields[1]
                    if len(fields) >= 3:
                        user_ssh_pubkey = " ".join(fields[2:])
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
                users = self.get((domain_name, "users"))
                users_nocert = self.get((domain_name, "users-no-cert"))
                
                if users.isdigit():
                    num_users = int(users)
                    usernames = [("%s-user%i" % (domain_name, i), True) for i in range(1,num_users + 1)]
                else:
                    num_users = 0
                    usernames = [(u, True) for u in users.split() if u != getpass.getuser()]
                    
                if users_nocert.isdigit():
                    usernames += [("%s-user%i" % (domain_name, i), False) for i in range(num_users + 1,num_users + int(users_nocert) + 1)]
                else:
                    usernames += [(u, False) for u in users_nocert.split() if u != getpass.getuser()]                

                for username, cert in usernames:
                    user = User()
                    user.set_property("id", username)
                    user.set_property("password_hash", "!")
                    user.set_property("ssh_pkey", ssh_pubkey)
                    if cert:
                        user.set_property("certificate", "generated")
                    else:
                        user.set_property("certificate", "none")
                    domain.add_user(user)
                
            for user in domain.users.values():
                gme = GridMapEntry()
                gme.set_property("dn", "/O=Grid/OU=Globus Provision (generated)/CN=%s" % user.id)
                gme.set_property("login", user.id)
                domain.add_to_array("gridmap", gme)  
                if self.get((domain_name,"go-auth")) == "go":
                    gme = GridMapEntry()
                    gme.set_property("dn", "/C=US/O=Globus Consortium/OU=Globus Connect User/CN=%s" % user.id)
                    gme.set_property("login", user.id)
                    domain.add_to_array("gridmap", gme)  
                    
            nis_server = None                    
                    
            fs = FileSystem()
            domain.set_property("filesystem", fs)
                    
            fs_type = self.get((domain_name,"filesystem")) 
            fs_headnode = None
            
            if self.get((domain_name,"nis")) or fs_type == "nfs":
                # We need a server node  
                server_node = Node()
                server_name = "%s-server" % domain_name
                server_node.set_property("id", server_name)
                server_node.add_to_array("run_list", "recipe[provision::gp_node]")
                server_node.add_to_array("run_list", "recipe[provision::nis_server]")
                if not self.get((domain_name,"login")):
                    # If there is no login node, the NFS/NIS server will
                    # effectively act as one. 
                    server_node.add_to_array("run_list", "role[globus]")
                   
                fs_headnode = server_node
                
                if self.get((domain_name,"nis")):
                    nis_server = server_node
                   
                domain.add_node(server_node)
                
            if fs_type == "local-only":
                fs.set_property("dir_homes", "/home")
                fs.set_property("dir_software", "/usr/local")
                fs.set_property("dir_scratch", "/var/tmp")
            
            if fs_type == "nfs":
                fs_headnode.add_to_array("run_list", "recipe[provision::nfs_server]")
                
                fs.set_property("dir_homes", "/nfs/home")
                fs.set_property("dir_software", "/nfs/software")
                fs.set_property("dir_scratch", "/nfs/scratch")
                
                mounts = [ ("/nfs/home", "0755", "/nfs/home"), 
                           ("/nfs/software/", "0755", "/nfs/software"),
                           ("/ephemeral/0/scratch", "1777", "/nfs/scratch")]
                
                for path, mode, mountpoint in mounts:
                    mount = NFSMount()
                    mount.set_property("server", "node:%s" % fs_headnode.id)
                    mount.set_property("owner", "root")
                    mount.set_property("mode", mode)
                    mount.set_property("path", path)
                    mount.set_property("mountpoint", mountpoint)
                    fs.add_to_array("nfs_mounts", mount)
                
                
            if fs_type == "glusterfs":
                glusterfs_servers_num = self.get((domain_name, "glusterfs-servers"))
                glusterfs_type = self.get((domain_name, "glusterfs-type"))
                glusterfs_setsize = self.get((domain_name, "glusterfs-setsize"))
                
                # Kludge until we add a general Filesystem object to the topology
                domain.set_property("glusterfs_type", glusterfs_type)
                domain.set_property("glusterfs_setsize", glusterfs_setsize)
                
                glusterfs_servers = []
                
                # The first server is arbitrarily the one where we will set up GlusterFS
                name = "glusterfsd-1"
                head_node = self.__create_node(domain, name, nis_server)
                head_node.add_to_array("run_list", "recipe[glusterfs::glusterfs-server-head]")
                glusterfs_servers.append("%s-%s" % (domain_name, name))                
                
                fs_headnode = head_node
                
                for i in range(1,glusterfs_servers_num):
                    name = "glusterfsd-%i" % (i+1)
                    node = self.__create_node(domain, name, nis_server)
                    node.add_to_array("run_list", "recipe[glusterfs::glusterfs-server]")

                    node_name = "%s-%s" % (domain_name, name)
                    glusterfs_servers.append(node_name)
                    head_node.add_to_array("depends", "node:%s" % node_name)
                    
                # TODO: Add GlusterFSVols to FileSystem

            if self.get((domain_name,"nis")):
                nis_server.add_to_array("run_list", "recipe[provision::domain_users]")

            if fs_headnode != None:
                fs_headnode.add_to_array("run_list", "recipe[provision::software_path-common]")                    
                if self.get((domain_name,"R")):
                    # If R is installed in the domain, we need to setup the global
                    # Rlibs directory
                    fs_headnode.add_to_array("run_list", "recipe[R::Rlibs-dir-common]")                    
                if self.get((domain_name,"galaxy")):
                    # If there is a Galaxy server in the domain, the "common"
                    # recipe has to be installed on the NFS/NIS server
                    fs_headnode.add_to_array("run_list", "recipe[galaxy::galaxy-globus-common]")
                    fs_headnode.add_to_array("run_list", "recipe[galaxy::blast-nfsserver]")
                if self.get((domain_name,"hadoop")):
                    # If there is a Hadoop cluster in the domain, the "common"
                    # recipe has to be installed on the NFS/NIS server
                    fs_headnode.add_to_array("run_list", "recipe[hadoop::hadoop-common]")                    
                    if self.get((domain_name,"R")):
                        # If R is installed on the cluster, we'll want RHadoop
                        fs_headnode.add_to_array("run_list", "recipe[hadoop::rhadoop-common]")                    
            
            for i in range(self.get((domain_name,"barebones-nodes"))):
                self.__create_node(domain, "blank-%i" % (i+1), nis_server)

            if self.get((domain_name,"login")): 
                node = self.__create_node(domain, "login", nis_server)
                node.add_to_array("run_list", "role[globus]")
                if self.get((domain_name,"R")):
                    node.add_to_array("run_list", "recipe[R]")   
                    node.add_to_array("run_list", "recipe[R::Rlibs-dir]")
                         
            gridftp_node = None
            myproxy_node = None
                         
            if self.get((domain_name,"myproxy")) and self.get((domain_name,"gridftp")) and has_go_ep and self.get((domain_name,"go-gc")):
                node = self.__create_node(domain, "myproxy-gridftp", nis_server)
                node.add_to_array("run_list", "role[domain-myproxy-gc]")
                node.add_to_array("run_list", "role[domain-gridftp-gc]")
                gridftp_node = myproxy_node = node
            else:
                if self.get((domain_name,"myproxy")):
                    myproxy_node = self.__create_node(domain, "myproxy", nis_server)
                    
                    if has_go_ep:
                        if self.get((domain_name,"go-gc")):
                            myproxy_node.add_to_array("run_list", "role[domain-myproxy-gc]")
                        else:
                            myproxy_node.add_to_array("run_list", "recipe[globus::go_cert]")
                            myproxy_node.add_to_array("run_list", "role[domain-myproxy-default]")
                    else:                
                        myproxy_node.add_to_array("run_list", "role[domain-myproxy-default]")    
    
                if self.get((domain_name,"gridftp")):
                    gridftp_node = self.__create_node(domain, "gridftp", nis_server)
           
                    if has_go_ep:
                        if self.get((domain_name,"go-gc")):
                            gridftp_node.add_to_array("run_list", "role[domain-gridftp-gc]")
                        else:
                            gridftp_node.add_to_array("run_list", "recipe[globus::go_cert]")
                            gridftp_node.add_to_array("run_list", "role[domain-gridftp-default]")
                    else:                
                        gridftp_node.add_to_array("run_list", "role[domain-gridftp-default]")              
            
            if self.get((domain_name,"galaxy")) and not self.get((domain_name,"condor")):
                node = self.__create_node(domain, "galaxy", nis_server)

                if fs_type == "local-only":  
                    node.add_to_array("run_list", "recipe[galaxy::galaxy-globus-common]")     

                if self.get((domain_name,"go-endpoint")) != None:
                    node.add_to_array("run_list", "recipe[globus::go_cert]")

                node.add_to_array("run_list", "recipe[galaxy::galaxy-globus]")

            if self.get((domain_name,"condor")):
                galaxy = self.get((domain_name,"galaxy"))
                
                if self.get((domain_name,"gram")):
                    head_name = "gram-condor"
                    head_role = "role[domain-gram-condor]"
                else:
                    if galaxy:
                        head_name = "galaxy-condor"
                    else:
                        head_name = "condor"
                    head_role = "role[domain-condor]"
                worker_name = "condor-wn"
                worker_role = "role[domain-clusternode-condor]"
                num_workers = self.get((domain.id,"condor-nodes"))
                
                head_node, workers = self.__gen_cluster(domain, nis_server, None, head_name, head_role, worker_name, worker_role, num_workers)
                
                if self.get((domain_name,"galaxy")):
                    if fs_type == "local-only":  
                        head_node.add_to_array("run_list", "recipe[galaxy::galaxy-globus-common]")     
    
                    if self.get((domain_name,"go-endpoint")) != None:
                        head_node.add_to_array("run_list", "recipe[globus::go_cert]")
                    head_node.add_to_array("run_list", "recipe[galaxy::galaxy-globus]")                
                
            if self.get((domain_name,"hadoop")):
                head_name = "hadoop-master"
                head_role = "role[domain-hadoop-master]"
                worker_name = "hadoop-slave"
                worker_role = "role[domain-hadoop-slave]"
                num_workers = self.get((domain.id,"hadoop-nodes"))
                                
                if fs_type == "local-only":
                    common_recipe = "recipe[hadoop::hadoop-common]"
                else:
                    common_recipe = None
                    
                head_node, workers = self.__gen_cluster(domain, nis_server, common_recipe, head_name, head_role, worker_name, worker_role, num_workers, head_depends_on_workers=True)
                
                if self.get((domain_name,"R")):
                    # If R is installed in the domain, we need to make sure the worker
                    # nodes have R, and that they are aware of the global Rlibs directory
                    for n in [head_node] + workers:
                        n.add_to_array("run_list", "recipe[R]")   
                        n.add_to_array("run_list", "recipe[R::Rlibs-dir]")                 

            if has_go_ep:
                goep = GOEndpoint()
                gouser, goname = self.get((domain_name,"go-endpoint")).split("#")
                goep.set_property("user", gouser)
                goep.set_property("name", goname)
                goep.set_property("public", False)
                goep.set_property("gridftp", "node:%s" % gridftp_node.id)
                
                if self.get((domain_name,"go-auth")) == "myproxy":
                    goep.set_property("myproxy", "node:%s" % myproxy_node.id)
                else:
                    goep.set_property("myproxy", "myproxy.globusonline.org")

                goep.set_property("globus_connect_cert", self.get((domain_name,"go-gc")))
                    
                domain.add_to_array("go_endpoints", goep)
                
        return topology

    def __gen_cluster(self, domain, nis_server, common_recipe, head_name, head_role, worker_name, worker_role, num_workers, head_depends_on_workers = False):
        head_node = self.__create_node(domain, head_name, nis_server)
        if common_recipe != None:                  
            head_node.add_to_array("run_list", common_recipe)  
        head_node.add_to_array("run_list", head_role)

        workers = []
        for i in range(num_workers):
            wn_name = "%s%i" % (worker_name, i+1)
            wn_node = self.__create_node(domain, wn_name, nis_server)
            if head_depends_on_workers:
                head_node.add_to_array("depends", "node:%s" % wn_node.id)
            else:
                wn_node.add_to_array("depends", "node:%s" % head_node.id)
            
            if common_recipe != None:                  
                head_node.add_to_array("run_list", common_recipe)  
            wn_node.add_to_array("run_list", worker_role)
            
            workers.append(wn_node)
            
        return (head_node, workers)

    def __create_node(self, domain, name, nis_server):
        domain_name = domain.id
        node = Node()
        node.set_property("id", "%s-%s" % (domain_name, name))

        node.add_to_array("run_list", "recipe[provision::gp_node]")
        node.add_to_array("run_list", "recipe[provision::software_path]")
        depends = set()

        if nis_server != None:
            depends.add("node:%s" % nis_server.id)
            node.add_to_array("run_list", "recipe[provision::nis_client]")
        else:
            node.add_to_array("run_list", "recipe[provision::domain_users]")

        if domain.filesystem.has_nfs():
            nfs_servers = set([mount.server for mount in domain.filesystem.nfs_mounts])
            
            for nfs_server in nfs_servers:
                depends.add(nfs_server)
                node.add_to_array("run_list", "recipe[provision::nfs_client]")
        
        if domain.filesystem.has_glusterfs():        
            # TODO: Add depends
            node.add_to_array("run_list", "recipe[glusterfs::glusterfs-client]")
            
        for d in depends:
            node.add_to_array("depends", d)
            
        domain.add_node(node)
        
        return node

