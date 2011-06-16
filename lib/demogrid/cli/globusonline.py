'''
Created on Jun 16, 2011

@author: borja
'''
from demogrid.cli import Command
from demogrid.common import defaults, constants
from demogrid.core.config import DemoGridConfig
from demogrid.globusonline.transfer_api import TransferAPIClient, ClientError

class demogrid_go_register_endpoint(Command):
    
    name = "demogrid-go-register-endpoint"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-c", "--conf", 
                                  action="store", type="string", dest="conf", 
                                  default = defaults.CONFIG_FILE,
                                  help = "Configuration file.")        
        
        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")        

        self.optparser.add_option("-d", "--domain", 
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
        
        config = DemoGridConfig(self.opt.conf)
        go_username = config.get_go_username()
        go_cert_file, go_key_file = config.get_go_credentials()
        go_server_ca = config.get_go_server_ca()

        api = TransferAPIClient(go_username, go_server_ca, go_cert_file, go_key_file)
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()            
        
        domain = topology.domains[self.opt.domain]
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
        
        if config.get_go_auth() == "go": 
            myproxy_server = "myproxy.globusonline.org"
        else:
            myproxy_server = gridftp.org.auth.hostname
        
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