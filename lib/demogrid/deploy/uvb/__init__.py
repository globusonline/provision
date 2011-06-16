
    def generate_uvb(self, force_certificates):
        if not os.path.exists(self.generated_dir):
            # TODO: Substitute for more meaningful error
            print "ERROR"      
            exit(1)
        
        print "\033[1;37mGenerating files... \033[0m",
        sys.stdout.flush()
        
        topology = self.__load_topology()
        
        topology.bind_to_example()
        
        
        topology.gen_hosts_file(self.generated_dir + "/hosts")
        topology.gen_ruby_file(self.generated_dir + "/topology.rb")
        topology.gen_csv_file(self.generated_dir + "/topology.csv")
        #self.gen_uvb_master_conf(topology)
        #self.gen_uvb_confs(topology)
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mGenerating certificates... \033[0m",
        sys.stdout.flush()

        cert_files = self.gen_certificates(topology, force_certificates)
        
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mCopying chef files... \033[0m",
        sys.stdout.flush()
  
        self.copy_files(cert_files)

        print "\033[1;32mdone!\033[0m"

    def gen_uvb_confs(self, topology):
        uvb_dir = self.generated_dir + self.UVB_DIR

        nodes = topology.get_nodes()
        for n in nodes:
            name = n.hostname.split(".")[0].replace("-", "_")
            
            template = Template(filename=self.demogrid_dir + self.UVB_TEMPLATE)
            uvb = template.render(domain = self.DOMAIN,
                                  ip = n.ip,
                                  gw = self.__gen_IP(0, 1),
                                  dgl = self.demogrid_dir,
                                  execscript = "post-install-chefsolo.sh",
                                  copy = "files-chefsolo.txt")   
            uvb_file = open(uvb_dir + "/uvb-chefsolo-%s.conf" % name, "w")
            uvb_file.write(uvb)
            uvb_file.close()          
            
            uvb = template.render(domain = self.DOMAIN,
                                  ip = n.ip,
                                  gw = self.__gen_IP(0, 1),
                                  dgl = self.demogrid_dir,
                                  execscript = "post-install-chefserver.sh",
                                  copy = "files-chefserver.txt")
            uvb_file = open(uvb_dir + "/uvb-chefserver-%s.conf" % name, "w")
            uvb_file.write(uvb)
            uvb_file.close()
            
    def gen_uvb_master_conf(self, topology):
        uvb_dir = self.generated_dir + self.UVB_DIR
        if not os.path.exists(uvb_dir):
            os.makedirs(uvb_dir)    
                    
        template = Template(filename=self.demogrid_dir + self.UVB_TEMPLATE)
        uvb_master = template.render(domain = self.DOMAIN,
                                     ip = self.__gen_IP(0, 2),
                                     gw = self.__gen_IP(0, 1),
                                     dgl = self.demogrid_dir,
                                     execscript = "post-install-chefsolo.sh",
                                     copy = "files-chefsolo.txt")   
        uvb_masterfile = open(uvb_dir + "/uvb-chefsolo-master.conf", "w")
        uvb_masterfile.write(uvb_master)
        uvb_masterfile.close()          
        
        uvb_master = template.render(domain = self.DOMAIN,
                                     ip = self.__gen_IP(0, 2),
                                     gw = self.__gen_IP(0, 1),
                                     dgl = self.demogrid_dir,
                                     execscript = "post-install-chefserver.sh",
                                     copy = "files-chefserver.txt")
        uvb_masterfile = open(uvb_dir + "/uvb-chefserver-master.conf", "w")
        uvb_masterfile.write(uvb_master)
        uvb_masterfile.close()                 