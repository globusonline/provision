import ConfigParser
import csv

class DemoGridConfig(object):
    
    GENERAL_SEC = "general"
    ORGANIZATIONS_OPT = "organizations"
    MYPROXY_OPT = "myproxy"
    
    ORGANIZATION_SEC = "organization-"
    GRIDUSERS_OPT = "grid-users"
    GRIDUSERS_AUTH_OPT = "grid-users-auth"
    NONGRIDUSERS_OPT = "nongrid-users"
    GRIDFTP_OPT = "gridftp"
    LRM_OPT = "lrm"
    CLUSTER_NODES_OPT = "cluster-nodes"

    EC2_SEC = "ec2"
    AMI_OPT = "ami"
    SNAP_OPT = "snap"
    KEYPAIR_OPT = "keypair"
    KEYFILE_OPT = "keyfile"
    INSTYPE_OPT = "instance_type"
    ZONE_OPT = "availability_zone"

    
    def __init__(self, configfile):
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(configfile, "r"))
        
        organizations = self.config.get(self.GENERAL_SEC, self.ORGANIZATIONS_OPT)
        self.organizations = organizations.split()

    def get_subnet(self):
        return "192.168" # This will be configurable
    
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
    
    def has_org_lrm(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        lrm = self.config.get(org_sec, self.LRM_OPT)
        return lrm != "none"

    def has_auth_node(self):
        return self.config.getboolean(self.GENERAL_SEC, self.MYPROXY_OPT)
        
    def get_org_lrm(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.get(org_sec, self.LRM_OPT)
    
    def get_org_num_clusternodes(self, org_name):
        org_sec = self.__get_org_sec(org_name)
        return self.config.getint(org_sec, self.CLUSTER_NODES_OPT)
        
    def __get_org_sec(self, org_name):
        return self.ORGANIZATION_SEC + org_name
    
    def get_ami(self):
        return self.config.get(self.EC2_SEC, self.AMI_OPT)
    
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
    

    
    
class DemoGridHostsFile(object):
    def __init__(self, file):
        self.reader = csv.DictReader(open(file))
        
    def get_host(self, hostname):
        for row in self.reader:
            if row["name"] == hostname:
                return row
        return None
            
        