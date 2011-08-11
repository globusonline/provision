'''
Created on Jun 16, 2011

@author: borja
'''
import subprocess


        
class demogrid_clone_image(Command):
    
    name = "demogrid-clone-image"
    
    def __init__(self, argv):
        Command.__init__(self, argv, root = True)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")
        
    def run(self):    
        self.parse_options()
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()        

        host = topology.get_node_by_id(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        args_newvm = ["%s/ubuntu-vm-builder/master_img.qcow2" % self.opt.dir, 
                      "/var/vm/%s.qcow2" % host.node_id, 
                      host.ip, 
                      host.node_id,
                      "%s/hosts" % self.opt.dir
                      ]
        cmd_newvm = ["%s/lib/create_from_master_img.sh" % self.dg_location] + args_newvm
        
        print "Creating VM for %s" % host.node_id
        retcode = subprocess.call(cmd_newvm)
        if retcode != 0:
            print "Error when running %s" % " ".join(cmd_newvm)
            exit(1)

        print "Created VM for host %s" % host.node_id



class demogrid_register_host_libvirt(Command):
    
    name = "demogrid-register-host-libvirt"
    
    def __init__(self, argv):
        Command.__init__(self, argv, root=True)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")

        self.optparser.add_option("-m", "--memory", 
                                  action="store", type="int", dest="memory", 
                                  default = 512,
                                  help = "Memory")        
        
    def run(self):    
        self.parse_options()
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()        

        host = topology.get_node_by_id(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        self._run("virt-install -n %s -r %i --disk path=/var/vm/%s.qcow2,format=qcow2,size=2 --accelerate --vnc --noautoconsole --import --connect=qemu:///system" % (host.node_id, self.opt.memory, host.node_id) )

        print "Registered host %s in libvirt" % host.node_id     
        
        

class demogrid_register_host_chef(Command):
    
    name = "demogrid-register-host-chef"
    
    def __init__(self, argv):
        Command.__init__(self, argv)
        
        self.optparser.add_option("-n", "--host", 
                                  action="store", type="string", dest="host", 
                                  help = "Host to clone an image for.")

        self.optparser.add_option("-g", "--generated-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.GENERATED_LOCATION,
                                  help = "Directory with generated files.")
        
    def run(self):    
        self.parse_options()
        
        f = open ("%s/topology.dat" % self.opt.dir, "r")
        topology = load(f)
        f.close()        

        host = topology.get_node_by_id(self.opt.host)
        if host == None:
            print "Host %s is not defined" % self.opt.host
            exit(1)

        retcode = self._run("knife node show %s" % host.hostname, exit_on_error = False)
        node_exists = (retcode == 0)
        retcode = self._run("knife client show %s" % host.hostname, exit_on_error = False)
        client_exists = (retcode == 0)

        if node_exists:
            self._run("knife node delete %s -y" % host.hostname)
        if client_exists:
            self._run("knife client delete %s -y" % host.hostname)
        self._run("knife node create %s -n" % host.hostname)
        self._run("knife node run_list add %s role[%s]" % (host.hostname, host.role))            
        print "Registered host %s in the Chef server" % host.node_id        
                   
