'''
Created on Jun 16, 2011

@author: borja
'''
from demogrid.cli import Command
from demogrid.common import defaults, constants
from demogrid.core.config import DemoGridConfig
from demogrid.globusonline.transfer_api import TransferAPIClient, ClientError
from demogrid.core.instance import InstanceStore

class demogrid_go_register_endpoint(Command):
    
    name = "demogrid-go-register-endpoint"
    
    def __init__(self, argv):
        Command.__init__(self, argv)    

        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain", 
                                  help = "Only this domain")   

        self.optparser.add_option("-n", "--name", 
                                  action="store", type="string", dest="name", 
                                  help = "Endpoint name")   
        
        self.optparser.add_option("-p", "--public", 
                                  action="store_true", dest="public", 
                                  help = "Create a public endpoint")           

        self.optparser.add_option("-r", "--replace", 
                                  action="store_true", dest="replace", 
                                  help = "If the endpoint already exists, replace it")           
                
    def run(self):    
        self.parse_options()
        inst_id = self.args[1]
        
        istore = InstanceStore(self.opt.dir)
        inst = istore.get_instance(inst_id)        

        go_username = inst.config.get_go_username()
        go_cert_file, go_key_file = inst.config.get_go_credentials()
        go_server_ca = inst.config.get_go_server_ca()

        api = TransferAPIClient(go_username, go_server_ca, go_cert_file, go_key_file)
                
        domain = inst.topology.domains[self.opt.domain]
        ep_name = self.opt.name
                
        # Find the GridFTP server
        gridftp = domain.servers[constants.DOMAIN_GRIFTP_SERVER]
        
        
        try:
            (code, msg, ep) = api.endpoint(ep_name)
            ep_exists = True
        except ClientError as ce:
            if ce.status_code == 404:
                ep_exists = False
            else:
                print ce
                exit(1)
        
        if inst.config.get_go_auth() == "go": 
            myproxy_server = "myproxy.globusonline.org"
        else:
            myproxy_server = domain.servers[constants.DOMAIN_GRIFTP_SERVER].hostname
        
        if ep_exists:
            if not self.opt.replace:
                print "An endpoint called '%s' already exists. Please choose a different name." % ep_name
                exit(1)
            else:
                (code, msg, data) = api.endpoint_delete(ep_name)
            
        (code, msg, data) = api.endpoint_create(ep_name, gridftp.hostname, description="DemoGrid endpoint",
                                                scheme="gsiftp", port=2811, subject="/O=Grid/OU=DemoGrid/CN=host/%s" % gridftp.hostname,
                                                myproxy_server=myproxy_server)
        if code >= 400:
            print code, msg
            exit(1)        

        if self.opt.public:
            (code, msg, ep) = api.endpoint(ep_name)
            if code >= 400:
                print code, msg
                exit(1)
            ep["public"] = True
            (code, msg, data) = api.endpoint_update(ep)
            if code >= 400:
                print code, msg
                exit(1)
                
        print "Endpoint created successfully"