from globus.provision.common.persistence import PersistentObject, PropertyTypes,\
    Property
    
class Topology(PersistentObject):
    STATE_NEW = 1
    STATE_STARTING = 2
    STATE_CONFIGURING = 3
    STATE_RUNNING = 4
    STATE_STOPPING = 5
    STATE_STOPPED = 6
    STATE_RESUMING = 7
    STATE_TERMINATING = 8
    STATE_TERMINATED = 9
    STATE_FAILED = 10
    
    # String representation of states
    state_str = {STATE_NEW : "New",
                 STATE_STARTING : "Starting",
                 STATE_CONFIGURING : "Configuring",
                 STATE_RUNNING : "Running",
                 STATE_STOPPING : "Stopping",
                 STATE_STOPPED : "Stopped",
                 STATE_RESUMING : "Resuming",
                 STATE_TERMINATING : "Terminating",
                 STATE_TERMINATED : "Terminated",
                 STATE_FAILED : "Failed"}        
    
    def get_nodes(self):
        nodes = []
        for domain in self.domains.values():
            nodes += [n for n in domain.get_nodes()]
        return nodes       
    
    def get_users(self):
        users = []
        for domain in self.domains.values():
            users += domain.get_users()
        return users    
    
    def gen_hosts_file(self, filename):
        hosts = """127.0.0.1    localhost

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts

"""
        
        nodes = self.get_nodes()
        for n in nodes:
            hosts += " ".join((n.ip, n.hostname, n.hostname.split(".")[0], "\n"))
        
        hostsfile = open(filename, "w")
        hostsfile.write(hosts)
        hostsfile.close()         
        
    def gen_chef_ruby_file(self, filename):
        
        def gen_topology_line(server_name, domain_id, recipes):
            server = domain.find_with_recipes(recipes)
            if len(server) > 0:
                server_node = server[0]
                if len(server) > 1:
                    # TODO: Print a warning saying more than one NFS server has been found
                    pass
                hostname_line = "default[:topology][:domains][\"%s\"][:%s] = \"%s\"\n" % (domain_id, server_name, server_node.hostname)
                ip_line       = "default[:topology][:domains][\"%s\"][:%s_ip] = \"%s\"\n" % (domain_id, server_name, server_node.ip)
                
                return hostname_line + ip_line
            else:
                return ""                              
        
        topology = "default[:topology] = %s\n" % self.to_ruby_hash_string()

        for domain in self.domains.values():
            topology += gen_topology_line("nfs_server", domain.id, ["recipe[provision::nfs_server]", "role[domain-nfsnis]"])
            topology += gen_topology_line("nis_server", domain.id, ["recipe[provision::nis_server]", "role[domain-nfsnis]"])
            topology += gen_topology_line("myproxy_server", domain.id, ["recipe[globus::myproxy]"])
            topology += gen_topology_line("lrm_head", domain.id, ["recipe[condor::condor_head]", "role[domain-condor]"])
        
        topologyfile = open(filename, "w")
        topologyfile.write(topology)
        topologyfile.close()        
    
    def get_depends(self, node):
        if not hasattr(node, "depends"):
            return None
        else:
            return self.get_node_by_id(node.depends[5:])
        
    def get_launch_order(self, nodes):
        order = []
        parents = [n for n in nodes if self.get_depends(n) == None or self.get_depends(n) not in nodes]
        while len(parents) > 0:
            order.append(parents)
            parents = [n for n in nodes if self.get_depends(n) in parents]   
        return order        
    
    def get_node_by_id(self, node_id):
        nodes = self.get_nodes()
        node = [n for n in nodes if n.id == node_id]
        if len(node) == 1:
            return node[0]
        else:
            return None    
        
    def get_deploy_data(self, node, deployer, p_name):
        if node.has_property("deploy_data") and node.deploy_data.has_property(deployer):
            deploy_data = node.deploy_data.get_property(deployer)
            if deploy_data.has_property(p_name):
                return deploy_data.get_property(p_name)
        
        # If node doesn't have requested deploy data, return default (if any)
        if self.has_property("default_deploy_data") and self.default_deploy_data.has_property(deployer):
            deploy_data = self.default_deploy_data.get_property(deployer)
            if deploy_data.has_property(p_name):
                return deploy_data.get_property(p_name)
            
        return None
    
    def add_domain(self, domain):
        self.add_to_array("domains", domain)
        
    
    
class Domain(PersistentObject):

    def get_nodes(self):
        return self.nodes.values()
    
    def get_users(self):
        return self.users.values()     
    
    def find_with_recipes(self, recipes):
        nodes = []
        for node in self.nodes.values():
            for r in recipes:
                if r in node.run_list:
                    nodes.append(node)
                    continue
        return nodes

    def add_user(self, user):
        self.add_to_array("users", user)
        
    def add_node(self, node):
        self.add_to_array("nodes", node)        

class DeployData(PersistentObject):
    pass

class EC2DeployData(PersistentObject):
    pass

class Node(PersistentObject):
    STATE_NEW = 0
    STATE_STARTING = 1
    STATE_RUNNING_UNCONFIGURED = 2
    STATE_CONFIGURING = 3
    STATE_RUNNING = 4
    STATE_STOPPING = 5
    STATE_STOPPED = 6
    STATE_RESUMING = 7
    STATE_TERMINATING = 8
    STATE_TERMINATED = 9
    STATE_FAILED = 10
    
    # String representation of states
    state_str = {STATE_NEW : "New",
                 STATE_STARTING : "Starting",
                 STATE_RUNNING_UNCONFIGURED : "Running (unconfigured)",
                 STATE_CONFIGURING : "Configuring",
                 STATE_RUNNING : "Running",
                 STATE_STOPPING : "Stopping",
                 STATE_STOPPED : "Stopped",
                 STATE_RESUMING : "Resuming",
                 STATE_TERMINATING : "Terminating",
                 STATE_TERMINATED : "Terminated",
                 STATE_FAILED : "Failed"}   


class User(PersistentObject):
    pass

class GridMapEntry(PersistentObject):
    pass

class GOEndpoint(PersistentObject):
    pass

Topology.properties = { 
                       "id":
                       Property(name="id",
                                proptype = PropertyTypes.STRING,
                                required = False,
                                description = """TODO"""),       
                       "state":
                       Property(name="state",
                                proptype = PropertyTypes.INTEGER,
                                required = False,
                                description = """TODO"""),                                                      
                       "domains": 
                       Property(name = "domains",
                                proptype = PropertyTypes.ARRAY,
                                items = Domain,
                                items_unique = True,
                                editable = True,
                                required = True,
                                description = """TODO"""),

                       "default_deploy_data":
                       Property(name = "default_deploy_data",
                                proptype = DeployData,
                                required = False,
                                editable = True,                                
                                description = """TODO""")          
                       }

DeployData.properties = { "ec2":
                            Property(name = "ec2",
                                     proptype = EC2DeployData,
                                     required = False,
                                     editable = True,
                                     description = """TODO""")          
                       }

EC2DeployData.properties = { 
                            "instance_type":
                                Property(name = "instance_type",
                                         proptype = PropertyTypes.STRING,
                                         required = False,
                                         editable = True,
                                         description = """TODO"""),
                            "instance_id":
                                Property(name = "instance_id",
                                         proptype = PropertyTypes.STRING,
                                         required = False,
                                         description = """TODO"""),               
                            "ami":
                                Property(name = "ami",
                                         proptype = PropertyTypes.STRING,
                                         required = False,
                                         editable = True,
                                         description = """TODO"""),
                            "security_groups":
                                Property(name = "security_groups",
                                         proptype = PropertyTypes.ARRAY,
                                         items = PropertyTypes.STRING,
                                         items_unique = True,                                         
                                         required = False,
                                         editable = True,
                                         description = """TODO""")                                
                       }


Domain.properties = {
                     "id":
                     Property(name="id",
                              proptype = PropertyTypes.STRING,
                              required = True,
                              description = """TODO"""),               
                              
                     "nodes":
                     Property(name="nodes",
                              proptype = PropertyTypes.ARRAY,
                              items = Node,
                              items_unique = True,
                              required = True,
                              editable = True,
                              description = """TODO"""),
                              
                     "go_endpoints":                    
                     Property(name="go_endpoints",
                              proptype = PropertyTypes.ARRAY,
                              items = GOEndpoint,
                              required = False,
                              editable = True,
                              description = """TODO"""),
                                    
                     "users": 
                     Property(name="users",
                              proptype = PropertyTypes.ARRAY,
                              items = User,
                              items_unique = True,
                              required = True,
                              editable = True,
                              description = """TODO"""),
                            
                     "gridmap":                                           
                     Property(name="gridmap",
                              proptype = PropertyTypes.ARRAY,
                              items = GridMapEntry,
                              required = False,
                              editable = True,
                              description = """TODO"""),
                     }

Node.properties = {
                   "id":
                   Property(name="id",
                            proptype = PropertyTypes.STRING,
                            required = True,
                            description = """TODO"""),
                   "state":
                   Property(name="state",
                            proptype = PropertyTypes.INTEGER,
                            required = False,
                            editable = False,
                            description = """TODO"""),                            
                   "run_list":
                   Property(name="run_list",
                            proptype = PropertyTypes.ARRAY,
                            items = PropertyTypes.STRING,
                            required = True,
                            editable = True,
                            description = """TODO"""),
                            
                   "depends":
                   Property(name="depends",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            editable = True,
                            description = """TODO"""),
                            
                   "hostname":
                   Property(name="hostname",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            description = """TODO"""),
                            
                   "ip":
                   Property(name="ip",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            description = """TODO"""),
                            
                   "public_ip":
                   Property(name="public_ip",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            description = """TODO"""),                            
                            
                   "deploy_data":
                   Property(name = "deploy_data",
                            proptype = DeployData,
                            required = False,
                            description = """TODO""")     
                   }          


User.properties = {
                   "id":
                   Property(name="id",                          
                            proptype = PropertyTypes.STRING,
                            required = True,
                            description = """TODO"""),
                            
                   "description":
                   Property(name="description",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            editable = True,
                            description = """TODO"""),
                            
                   "password_hash":
                   Property(name="password_hash",
                            proptype = PropertyTypes.STRING,
                            required = True,
                            editable = True,
                            description = """TODO"""),
                            
                   "ssh_pkey":
                   Property(name="ssh_pkey",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            editable = True,
                            description = """TODO"""),
                            
                   "admin":
                   Property(name="admin",
                            proptype = PropertyTypes.BOOLEAN,
                            required = False,
                            editable = True,
                            description = """TODO"""),
                            
                   "certificate":
                   Property(name = "certificate",
                            proptype = PropertyTypes.STRING,
                            required = False,
                            description = """TODO"""),           
                   }            

GridMapEntry.properties = {                   
                           "dn": 
                           Property(name="dn",
                                    proptype = PropertyTypes.STRING,
                                    required = True,
                                    description = """TODO"""),
                                   
                           "login":
                           Property(name="login",
                                    proptype = PropertyTypes.STRING,
                                    required = True,
                                    editable = True,
                                    description = """TODO"""),
                           }       

GOEndpoint.properties = {           
                         
                           "user":
                           Property(name="user",
                                    proptype = PropertyTypes.STRING,
                                    required = True,
                                    description = """TODO"""),
                           "name":
                           Property(name="name",
                                    proptype = PropertyTypes.STRING,
                                    required = True,
                                    description = """TODO"""),
                                   
                           "gridftp":
                           Property(name="gridftp",
                                    proptype = PropertyTypes.STRING,
                                    required = True,
                                    editable = True,
                                    description = """TODO"""),
                                   
                           "myproxy":
                           Property(name="myproxy",
                                    proptype = PropertyTypes.STRING,
                                    required = True,
                                    editable = True,
                                    description = """TODO""")                 
                           
                        }                                                                                                                 
