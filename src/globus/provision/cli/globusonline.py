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
Commands related to Globus Online endpoint management, but which do not require access to the API
"""

import sys
import os.path
from pkg_resources import resource_filename
from globus.provision.common.ssh import SSH

from globus.provision.cli import Command
from globus.transfer.transfer_api import TransferAPIClient, ClientError
from globus.provision.core.instance import InstanceStore

def gp_go_register_endpoints_func():
    return gp_go_register_endpoints(sys.argv).run()     

class gp_go_register_endpoints(Command):
    """
    Creates the Globus Online endpoints specified in an instance's topology.
    
    The instance identifier must be specified after all other parameters. For example::
    
        gp-go-register-endpoints --public gpi-12345678    
    """     
    
    name = "gp-go-register-endpoints"
    
    def __init__(self, argv):
        Command.__init__(self, argv)    

        self.optparser.add_option("-m", "--domain", 
                                  action="store", type="string", dest="domain", 
                                  help = "Register only the endpoints in this domain")
        
        self.optparser.add_option("-p", "--public", 
                                  action="store_true", dest="public", 
                                  help = "Create public endpoints")           

        self.optparser.add_option("-r", "--replace", 
                                  action="store_true", dest="replace", 
                                  help = "If an endpoint already exists, replace it")           
                
    def run(self):    
        self.parse_options()
        inst_id = self.args[1]
        
        istore = InstanceStore(self.opt.dir)
        inst = istore.get_instance(inst_id)        
        
        if inst.config.get("go-cert-file") == None:
            # Use SSH
            use_ssh = True
            ssh_key = os.path.expanduser(inst.config.get("go-ssh-key"))
        else:
            # Use Transfer API
            use_ssh = False
            go_cert_file = os.path.expanduser(inst.config.get("go-cert-file"))
            go_key_file = os.path.expanduser(inst.config.get("go-key-file"))
            go_server_ca = resource_filename("globus.provision", "chef-files/cookbooks/globus/files/default/gd-bundle_ca.cert")



        for domain_name, domain in inst.topology.domains.items():
            for ep in domain.go_endpoints:
                if ep.gridftp.startswith("node:"):
                    gridftp = inst.topology.get_node_by_id(ep.gridftp[5:]).hostname
                else:
                    gridftp = ep.gridftp
    
                ca_dn = inst.config.get("ca-dn")
                if ca_dn == None:
                    ca_dn = "/O=Grid/OU=Globus Provision (generated)"
                else:
                    ca_dn = [x.split("=") for x in ca_dn.split(",")]
                    ca_dn = "".join(["/%s=%s" % (n.upper().strip(), v.strip()) for n,v in ca_dn])

                gridftp_subject = "%s/CN=host/%s" % (ca_dn, gridftp)
    
                if ep.myproxy.startswith("node:"):
                    myproxy = inst.topology.get_node_by_id(ep.myproxy[5:])
                else:
                    myproxy = ep.myproxy
    
                if use_ssh:
                    print ep.user, ssh_key
                    ssh = SSH(ep.user, "cli.globusonline.org", ssh_key, default_outf = None, default_errf = None)
                    ssh.open()
                    rc = ssh.run("endpoint-list %s" % (ep.name), exception_on_error=False)
                    if rc == 0:
                        if not self.opt.replace:
                            print "An endpoint called '%s' already exists. Please choose a different name." % ep.name
                            exit(1)
                        else:
                            rc = ssh.run("endpoint-remove %s" % (ep.name), exception_on_error=False)

                    rc = ssh.run("endpoint-add %s -p %s -s \"%s\"" % (ep.name, gridftp, gridftp_subject), exception_on_error=False)
                    if rc != 0:
                        print "Could not create endpoint."
                        exit(1)
                    rc = ssh.run("endpoint-modify --myproxy-server=%s %s" % (myproxy, ep.name), exception_on_error=False)
                    if rc != 0:
                        print "Could not set endpoint's MyProxy server."
                        exit(1)
                    if self.opt.public:
                        rc = ssh.run("endpoint-modify --public %s" % (ep.name), exception_on_error=False)
                        if rc != 0:
                            print "Could not make the endpoint public."
                            exit(1)
                    ssh.close()
                else:
                    api = TransferAPIClient(ep.user, go_server_ca, go_cert_file, go_key_file)
    
                    try:
                        (code, msg, data) = api.endpoint(ep.name)
                        ep_exists = True
                    except ClientError as ce:
                        if ce.status_code == 404:
                            ep_exists = False
                        else:
                            print ce
                            exit(1)
                
                
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