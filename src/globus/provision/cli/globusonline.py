import sys
import os.path

from globus.provision.cli import Command
from globus.transfer.transfer_api import TransferAPIClient, ClientError
from globus.provision.core.instance import InstanceStore

def gp_go_register_endpoint_func():
    return gp_go_register_endpoint(sys.argv).run()     

class gp_go_register_endpoint(Command):
    
    name = "gp-go-register-endpoint"
    
    def __init__(self, argv):
        Command.__init__(self, argv)    

        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain", 
                                  help = "Only this domain")
        
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

        go_cert_file = os.path.expanduser(inst.config.get("go-cert-file"))
        go_key_file = os.path.expanduser(inst.config.get("go-key-file"))
        go_server_ca = os.path.expanduser(inst.config.get("go-server-ca-file"))

        for domain_name, domain in inst.topology.domains.items():
            for ep in domain.go_endpoints:

                api = TransferAPIClient(ep.user, go_server_ca, go_cert_file, go_key_file)

                if ep.gridftp.startswith("node:"):
                    gridftp = inst.topology.get_node_by_id(ep.gridftp[5:]).hostname
                else:
                    gridftp = ep.gridftp
    
                ca_dn = inst.config.get("ca-dn")
                if ca_dn == None:
                    ca_dn = "/O=Grid/OU=Globus Provision (generated)" % inst_id
                else:
                    ca_dn = [x.split("=") for x in ca_dn.split(",")]
                    ca_dn = "".join(["/%s=%s" % (n.upper().strip(), v.strip()) for n,v in ca_dn])

                gridftp_subject = "%s/CN=host/%s" % (ca_dn, gridftp)
    
                try:
                    (code, msg, data) = api.endpoint(ep.name)
                    ep_exists = True
                except ClientError as ce:
                    if ce.status_code == 404:
                        ep_exists = False
                    else:
                        print ce
                        exit(1)
                
                if ep.myproxy.startswith("node:"):
                    myproxy = inst.topology.get_node_by_id(ep.myproxy[5:])
                else:
                    myproxy = ep.myproxy
                
                if ep_exists:
                    if not self.opt.replace:
                        print "An endpoint called '%s' already exists. Please choose a different name." % ep.name
                        exit(1)
                    else:
                        (code, msg, data) = api.endpoint_delete(ep.name)
                    
                (code, msg, data) = api.endpoint_create(ep.name, gridftp, description="Globus Provision endpoint",
                                                        scheme="gsiftp", port=2811, subject=gridftp_subject,
                                                        myproxy_server=myproxy)
                if code >= 400:
                    print code, msg
                    exit(1)        
        
                if self.opt.public:
                    (code, msg, data) = api.endpoint(ep.name)
                    if code >= 400:
                        print code, msg
                        exit(1)
                    data["public"] = True
                    (code, msg, data) = api.endpoint_update(ep.name, data)
                    if code >= 400:
                        print code, msg
                        exit(1)
                        
                print "Created endpoint '%s#%s' for domain '%s'" % (ep.user, ep.name, domain_name)