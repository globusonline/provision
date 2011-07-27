'''
Created on Dec 7, 2010

@author: borja
'''
from cPickle import dump, load, HIGHEST_PROTOCOL
from copy import deepcopy
import json

import demogrid.common.constants as constants
from demogrid.common import DemoGridException

class Topology(object):    
    
    STATE_NEW = 1
    STATE_STARTING = 2
    STATE_RUNNING = 3
    STATE_STOPPING = 4
    STATE_STOPPED = 5
    STATE_RESUMING = 6
    STATE_TERMINATING = 7
    STATE_TERMINATED = 8
    
    # String representation of states
    state_str = {STATE_NEW : "New",
                 STATE_STARTING : "Starting",
                 STATE_RUNNING : "Running",
                 STATE_STOPPING : "Stopping",
                 STATE_STOPPED : "Stopped",
                 STATE_RESUMING : "Resuming",
                 STATE_TERMINATING : "Terminating",
                 STATE_TERMINATED : "Terminated"}    
    
    def __init__(self):
        self.global_attributes = {}
        self.global_nodes = []
        self.domains = {}
        self.default_deploy_data = {}
        self.pickledfile = None
        self.state = Topology.STATE_NEW
        
    def add_domain(self, domain):
        self.domains[domain.name] = domain

    def add_domain_node(self, domain, node):
        domain.nodes.append(node)

    def add_global_node(self, node):
        self.global_nodes.append(node)
        
    def get_nodes(self):
        nodes = self.global_nodes[:]
        for domain in self.domains.values():
            nodes += domain.get_nodes()
        return nodes

    def remove_nodes(self, nodes):
        for n in nodes:
            if n in self.global_nodes:
                self.global_nodes.remove(n)
            
            for domain in self.domains.values():
                if n in domain.nodes:
                    domain.nodes.remove(n)
    
    def get_node_by_id(self, node_id):
        nodes = self.get_nodes()
        node = [n for n in nodes if n.node_id == node_id]
        if len(node) == 1:
            return node[0]
        else:
            return None
    
    def get_users(self):
        users = []
        for domain in self.domains.values():
            users += domain.get_users()
        return users    
    
    def gen_ruby_file(self, file):
        topology = ""

        for k,v in self.global_attributes.items():
            topology += "node.normal[:%s] = %s\n" % (k,v)
            
        topology += "\n"
      
        nodes = self.get_nodes()
        for n in nodes:
            topology += "if node[:node_id] == \"%s\"\n" % n.node_id
            for k,v in n.chef_attrs.items():
                topology += "  node.normal[:%s] = %s\n" % (k,v)
            topology += "end\n\n"            

        for domain in self.domains.values():
            topology += "default[:domains][\"%s\"][:users] = [\n" % domain.name
            for u in domain.users:
                topology += "{ :login       => \"%s\",\n" % u.login
                topology += "  :description => \"%s\",\n" % u.description
                topology += "  :password_hash => \"%s\",\n" % u.password_hash
                if u.admin:
                    topology += "  :admin => true,\n"
                else:
                    topology += "  :admin => false,\n"

                if u.ssh_pkey != None:
                    topology += "  :ssh_pkey => \"%s\",\n" % u.ssh_pkey
                    
                if u.cert_type != None:
                    if u.cert_type == "external":
                        topology += "  :gridenabled => true}"
                    else:
                        topology += "  :gridenabled => true,\n"
                        if u.cert_type == "generated":
                            topology += "  :auth_type   => :certs}"
                        elif u.cert_type == "myproxy":
                            topology += "  :auth_type   => :myproxy}"
                else:
                    topology += "  :gridenabled => false}"
                topology += ",\n"
            topology += "]\n"

            topology += "default[:domains][\"%s\"][:gridmap] = [\n" % domain.name
            for (dn,login) in domain.gridmap.items():
                topology += "{ :dn    => \"%s\",\n" % dn
                topology += "  :login => \"%s\"},\n" % login
            topology += "]\n"

        topologyfile = open(file, "w")
        topologyfile.write(topology)
        topologyfile.close()      
        
    def gen_hosts_file(self, filename, extra_entries = []):
        hosts = """127.0.0.1    localhost

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts

"""
        for ip, hostname in extra_entries:
            hosts += "%s %s %s\n" % (ip, hostname, hostname.split(".")[0])
        
        nodes = self.get_nodes()
        for n in nodes:
            hosts += " ".join((n.ip, n.hostname, n.hostname.split(".")[0], "\n"))
        
        hostsfile = open(filename, "w")
        hostsfile.write(hosts)
        hostsfile.close()        
        
    def gen_csv_file(self, filename):
        attr_names = set()
        #deploy_data = set()
        nodes = self.get_nodes()
        
        for n in nodes:
            attr_names.update(n.chef_attrs.keys())
            #deploy_data.update(n.deploy_data.keys())
            
        attr_names = list(attr_names)
        #deploy_data = list(deploy_data)
#        csv = "org,hostname,run_list,ip," + ",".join(attr_names+deploy_data) +"\n"
        csv = "org,hostname,run_list,ip," + ",".join(attr_names) +"\n"
        
        for n in nodes:
            if n.domain:
                domainname = n.domain.name
            else:
                domainname = ""
            fields = [domainname, n.hostname, ";".join(n.run_list), n.ip]
            for name in attr_names:
                fields.append(n.chef_attrs.get(name,""))
            #for name in deploy_data:    
            #    fields.append(n.deploy_data.get(name,""))
            csv += ",".join(fields) + "\n"
            
        csvfile = open(filename, "w")
        csvfile.write(csv)
        csvfile.close()                
        
    def save(self, filename = None):
        if self.pickledfile == None and filename == None:
            raise DemoGridException("Don't know where to save this topology")
        if filename != None:
            self.pickledfile = filename
        f = open (self.pickledfile, "w")
        dump(self, f, protocol = HIGHEST_PROTOCOL)
        f.close()
        
    def bind_to_example(self):
        global_node_num = 1
        for node in self.global_nodes:
            node.ip = self.__gen_example_IP(constants.EXAMPLE_GLOBAL_SUBNET, global_node_num)
            node.hostname = self.__gen_example_hostname(node.node_id)
            global_node_num += 1
            
        domain_subnet = constants.EXAMPLE_DOMAIN_SUBNET_START
        for domain in self.domains.values():
            domain_node_num = 1
            domain.subnet = self.__gen_example_IP(domain_subnet, 0)
            for node in domain.nodes:
                node.ip = self.__gen_example_IP(domain_subnet, domain_node_num)
                node.hostname = self.__gen_example_hostname(node.node_id)
                domain_node_num += 1            
                
            domain_subnet += 1
            
        for n in self.get_nodes():
            n.gen_chef_attrs()
                 

    @classmethod
    def from_json(cls, jsonstr):
        topology = cls()
        
        topology_json = json.loads(jsonstr)
        
        if topology_json.has_key("default_deploy_data"):
            topology.default_deploy_data.update(deepcopy(topology_json["default_deploy_data"]))

        for domain in topology_json["domains"]:
            domain_obj = Domain(domain["name"])
            topology.add_domain(domain_obj)
            
            for node in domain["nodes"]:
                node_obj = Node.from_json(node, domain_obj, topology.default_deploy_data)
                topology.add_domain_node(domain_obj, node_obj)

            for node in domain_obj.nodes:
                if node.depends != None:
                    depends_node = topology.get_node_by_id(node.depends[5:])
                    node.depends = depends_node                    

            for user in domain["users"]:
                user_obj = User.from_json(user) 
                domain_obj.add_user(user_obj)

            for g in domain["gridmap"]:
                domain_obj.gridmap[g["dn"]] = g["login"]
                
            for s in constants.DOMAIN_SERVERS:
                if domain.has_key(s):
                    if domain[s].startswith("node:"):
                        node = topology.get_node_by_id(domain[s][5:])
                        domain_obj.servers[s] = node
    
        return topology

   
    def __gen_example_IP(self, subnet, host):
        return "%s.%i.%i" % (constants.EXAMPLE_SUBNET, subnet, host)
    
    def __gen_example_hostname(self, name):
        return "%s.%s" % (name, constants.EXAMPLE_DOMAIN)
   
class Domain(object):    
    def __init__(self, name):
        self.name = name
        self.subnet = None
        self.nodes = []
        self.users = []
        self.servers = {}
        self.gridmap = {}

    def add_node(self, node):
        self.nodes.append(node)
        
    def get_nodes(self):
        return self.nodes[:]
        
    def add_user(self, user):
        self.users.append(user)   
        
    def get_users(self):
        return self.users
    
    def has_server(self, s):
        return self.servers.has_key(s)
    
    def get_server(self, s):
        return self.servers.get(s)
    
class Node(object):
    def __init__(self, node_id, domain = None):
        self.node_id = node_id
        self.domain = domain
        self.run_list = None
        self.depends = None
        self.ip = None
        self.hostname = None
        self.chef_attrs = {}
        self.deploy_data = {}
        
    def gen_chef_attrs(self):
        self.chef_attrs["demogrid_hostname"] = "\"%s\"" % self.hostname
        self.chef_attrs["node_id"] = "\"%s\"" % self.node_id
        self.chef_attrs["run_list"] = "[ %s ]" % ",".join("\"%s\"" % r for r in self.run_list)
        if self.domain != None:
            self.chef_attrs["demogrid_domain"] = "\"%s\"" % self.domain.name

            if self.domain.has_server(constants.DOMAIN_NIS_SERVER):
                self.chef_attrs["nis_server"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_NIS_SERVER).ip               

            if self.domain.has_server(constants.DOMAIN_NFS_SERVER):
                self.chef_attrs["nfs_server"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_NFS_SERVER).ip               

            if self.domain.has_server(constants.DOMAIN_MYPROXY_SERVER):
                self.chef_attrs["myproxy"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_MYPROXY_SERVER).hostname

            if self.domain.has_server(constants.DOMAIN_LRMHEAD_SERVER):
                self.chef_attrs["lrm_head"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_LRMHEAD_SERVER).hostname

            if self.domain.subnet == None:
                self.chef_attrs["subnet"] = "nil"
            else:
                self.chef_attrs["subnet"] = "\"%s\"" % self.domain.subnet
        

    @classmethod
    def from_json(cls, json, domain_obj, default_deploy_data):
        node = json
        node_obj = cls(node["id"], domain = domain_obj)
        node_obj.run_list = node.get("run_list")
        node_obj.depends = node.get("depends")
        
        node_obj.deploy_data.update(deepcopy(default_deploy_data))                
        
        if node.has_key("deploy_data"):
            for k,v in node["deploy_data"].items():
                node_obj.deploy_data.setdefault(k,{}).update(v)
                
        return node_obj
    
    @staticmethod
    def get_launch_order(nodes):
        order = []
        parents = [n for n in nodes if n.depends == None or n.depends not in nodes]
        threads = {}
        while len(parents) > 0:
            order.append(parents)
            parents = [n for n in nodes if n.depends in parents]    
        return order
        
        
class User(object):
    def __init__(self, login, description, password_hash, ssh_pkey = None, admin = False, cert_type=None):
        self.login = login
        self.description = description
        self.password_hash = password_hash
        self.ssh_pkey = ssh_pkey
        self.admin = admin
        self.cert_type = cert_type

    @classmethod
    def from_json(cls, json):
        admin = (json.get("admin") in ("True", "true"))
            
        return cls(json["login"], json.get("description", json["login"]), json["password_hash"], json.get("ssh_pkey"), admin, json.get("cert"))
