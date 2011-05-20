'''
Created on Dec 7, 2010

@author: borja
'''
from cPickle import dump, load, HIGHEST_PROTOCOL
from copy import deepcopy
import json

import demogrid.common.constants as constants

class Topology(object):    
    
    
    def __init__(self):
        self.global_attributes = {}
        self.global_nodes = []
        self.domains = {}
        self.default_deploy_data = {}
        
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
            topology += "if node.name == \"%s\"\n" % n.hostname
            for k,v in n.chef_attrs.items():
                topology += "  node.normal[:%s] = %s\n" % (k,v)
            topology += "end\n\n"            

        for domain in self.domains.values():
            topology += "default[:orgusers][\"%s\"] = [\n" % domain.name
            for u in domain.users:
                topology += "{ :login       => \"%s\",\n" % u.login
                topology += "  :description => \"%s\",\n" % u.description
                topology += "  :password_hash => \"%s\",\n" % u.password_hash
                topology += "  :dn => \"%s\",\n" % u.dn
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
        
    def save(self, filename):
        f = open (filename, "w")
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
    def from_configfile(cls, config):
        topology = cls()
        
        grid_auth_node = None
        if config.has_grid_auth_node():
            grid_auth_node = DGNode(role = self.GRID_AUTH_ROLE,
                                    ip =   self.__gen_IP(self.GRID_MANAGEMENT_SUBNET, self.GRID_AUTH_HOST),
                                    hostname = self.__gen_hostname(self.GRID_AUTH_HOSTNAME))
            grid.add_node(grid_auth_node)
        
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
                    username = "%s-user%i" % (org_name, usernum)
                    user = DGOrgUser(login = username,
                                     description = "User '%s' of Organization %s" % (username, org_name),
                                     gridenabled = True, password = self.DEFAULT_USER_PASSWD, password_hash = self.DEFAULT_USER_PASSWDHASH,
                                     auth_type = self.config.get_org_user_auth(org_name))
                    org.add_user(user)
                    usernum += 1
    
                for i in range(self.config.get_org_num_nongridusers(org_name)):
                    username = "%s-user%i" % (org_name, usernum)
                    user = DGOrgUser(login = "%s-user%i" % (org_name, usernum),
                                     description = "User '%s' of Organization %s" % (username, org_name),
                                     gridenabled = False, password = self.DEFAULT_USER_PASSWD, password_hash = self.DEFAULT_USER_PASSWDHASH)
                    org.add_user(user)
                    usernum += 1
                
            
            server_node = DGNode(role = self.SERVER_ROLE,
                                 ip =   self.__gen_IP(org_subnet, self.SERVER_HOST),
                                 hostname = self.__gen_hostname(self.SERVER_HOSTNAME, org = org_name),
                                 org = org)            
            grid.add_org_node(org, server_node)
            org.server = server_node
            
            if self.config.has_org_login(org_name):            
                login_node =  DGNode(role = self.LOGIN_ROLE,
                                     ip =   self.__gen_IP(org_subnet, self.LOGIN_HOST),
                                     hostname = self.__gen_hostname(self.LOGIN_HOSTNAME, org = org_name),
                                     org = org)                        
                grid.add_org_node(org, login_node)

            if self.config.has_org_auth(org_name):
                auth_node = DGNode(role = self.MYPROXY_ROLE,
                                   ip =   self.__gen_IP(org_subnet, self.MYPROXY_HOST),
                                   hostname = self.__gen_hostname(self.MYPROXY_HOSTNAME, org = org_name),
                                   org = org)                        
                grid.add_org_node(org, auth_node)
                org.auth = auth_node
            else:
                org.auth = grid_auth_node

            if self.config.has_org_gridftp(org_name):
                gridftp_node = DGNode(role = self.GRIDFTP_ROLE,
                                      ip =   self.__gen_IP(org_subnet, self.GRIDFTP_HOST),
                                      hostname = self.__gen_hostname(self.GRIDFTP_HOSTNAME, org = org_name),
                                      org = org)                        
                grid.add_org_node(org, gridftp_node)
            
            if self.config.has_org_lrm(org_name):
                lrm_type = self.config.get_org_lrm(org_name)
                gram = self.config.has_org_gram(org_name)
                if lrm_type == "condor":
                    if gram:
                        role = self.GATEKEEPER_CONDOR_ROLE
                    else:
                        role = self.LRM_CONDOR_ROLE
                    workernode_role = self.LRM_NODE_CONDOR_ROLE
                elif lrm_type == "torque":
                    if gram:
                        role = self.GATEKEEPER_PBS_ROLE
                    else:
                        role = self.LRM_PBS_ROLE
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
        
        # Generate Chef attributes
        nodes = grid.get_nodes()
        for node in nodes:        
            attrs = node.attrs
            attrs["demogrid_hostname"] = "\"%s\"" % node.hostname
            attrs["node_id"] = "\"%s\"" % node.node_id
            attrs["run_list"] = "[ \"role[%s]\" ]" % node.role
            if node.org != None:
                attrs["org"] = "\"%s\"" % node.org.name
                if node.org.auth != None:
                    attrs["auth"] = "\"%s\"" % self.__gen_hostname("auth", node.org.name)
                if self.config.has_org_lrm(node.org.name):
                    attrs["lrm_head"] = "\"%s\"" % self.__gen_hostname("gatekeeper", node.org.name)
                    attrs["lrm_nodes"] = "%i" % self.config.get_org_num_clusternodes(node.org.name)
        
        nodes = grid.get_nodes()
        for n in nodes:
            if n.org != None:
                attrs = n.attrs
                attrs["subnet"] = "\"%s\"" % self.__gen_IP(n.org.subnet, 0)
                attrs["org_server"] = "\"%s\"" % self.__gen_IP(n.org.subnet, 1)
            
        return grid


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
                node_obj = Node(node["id"], domain = domain_obj)
                node_obj.run_list = node.get("run_list")
                node_obj.depends = node.get("depends")
                node_obj.deploy_data.update(deepcopy(topology.default_deploy_data))
                
                if node.has_key("deploy_data"):
                    for k,v in node["deploy_data"].items():
                        node_obj.deploy_data[k].update(v)
                
                topology.add_domain_node(domain_obj, node_obj)

            for node in domain_obj.nodes:
                if node.depends != None:
                    depends_node = topology.get_node_by_id(node.depends[5:])
                    node.depends = depends_node                    

            for user in domain["users"]:
                user_obj = User(user["login"], user.get("description", user["login"]), user["password_hash"], user.get("dn"), user.get("cert"))
                domain_obj.add_user(user_obj)
                
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

    def add_node(self, node):
        self.nodes.append(node)
        
    def get_nodes(self):
        return self.nodes
        
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
        self.ip = None
        self.hostname = None
        self.chef_attrs = {}
        self.deploy_data = {}
        
    def gen_chef_attrs(self):
        self.chef_attrs["demogrid_hostname"] = "\"%s\"" % self.hostname
        self.chef_attrs["node_id"] = "\"%s\"" % self.node_id
        self.chef_attrs["run_list"] = "[ %s ]" % ",".join("\"%s\"" % r for r in self.run_list)
        if self.domain != None:
            self.chef_attrs["org"] = "\"%s\"" % self.domain.name

            if self.domain.has_server(constants.DOMAIN_MYPROXY_SERVER):
                self.chef_attrs["auth"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_MYPROXY_SERVER).hostname

            if self.domain.has_server(constants.DOMAIN_LRMHEAD_SERVER):
                self.chef_attrs["lrm_head"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_LRMHEAD_SERVER).hostname

            if self.domain.subnet == None:
                self.chef_attrs["subnet"] = "nil"
            else:
                self.chef_attrs["subnet"] = "\"%s\"" % self.domain.subnet
            self.chef_attrs["org_server"] = "\"%s\"" % self.domain.get_server(constants.DOMAIN_NIS_SERVER).ip               
        
        
class User(object):
    def __init__(self, login, description, password_hash, dn, cert_type=None):
        self.login = login
        self.description = description
        self.password_hash = password_hash
        self.dn = dn
        self.cert_type = cert_type
