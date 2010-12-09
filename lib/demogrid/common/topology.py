'''
Created on Dec 7, 2010

@author: borja
'''
from cPickle import dump, load, HIGHEST_PROTOCOL

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
    
    def gen_ruby_file(self, file):
        topology = ""
      
        nodes = self.get_nodes()
        for n in nodes:
            topology += "if node.name == \"%s\"\n" % n.hostname
            for k,v in n.attrs.items():
                topology += "  node.normal[:%s] = %s\n" % (k,v)
            topology += "end\n\n"            

        for org in self.organizations.values():
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
        
    def save(self, filename):
        f = open (filename, "w")
        dump(self, f, protocol = HIGHEST_PROTOCOL)
        f.close()

   
class DGOrganization(object):    
    def __init__(self, name, subnet):
        self.name = name
        self.subnet = subnet
        self.nodes = []
        self.users = []
        self.lrm = None
        self.server = None

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
        self.attrs = {}
        
class DGOrgUser(object):
    def __init__(self, login, description, gridenabled, auth_type=None):
        self.login = login
        self.description = description
        self.gridenabled = gridenabled
        self.auth_type = auth_type   