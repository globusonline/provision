    def generate_vagrant(self, force_certificates):
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
        self.gen_vagrant_file(topology)
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mGenerating certificates... \033[0m",
        sys.stdout.flush()

        cert_files = self.gen_certificates(topology, force_certificates)
        
        print "\033[1;32mdone!\033[0m"


        print "\033[1;37mCopying chef files... \033[0m",
        sys.stdout.flush()
  
        self.copy_files(cert_files)

        print "\033[1;32mdone!\033[0m"

    def gen_vagrant_file(self, topology):
        vagrant_dir = self.generated_dir + self.VAGRANT_DIR
        if not os.path.exists(vagrant_dir):
            os.makedirs(vagrant_dir)         
        
        vagrant = "Vagrant::Config.run do |config|\n"
      
        nodes = topology.get_nodes()
        for n in nodes:
            name = n.hostname.split(".")[0].replace("-", "_")
            vagrant += "  config.vm.define :%s do |%s_config|\n" % (name, name)
            vagrant += "    %s_config.vm.box = \"lucid32\"\n" % name
            vagrant += "    %s_config.vm.provisioner = :chef_solo\n" % name
            vagrant += "    %s_config.chef.cookbooks_path = \"chef/cookbooks\"\n" % name
            vagrant += "    %s_config.chef.roles_path = \"chef/roles\"\n" % name
            # TODO: Fix
            #vagrant += "    %s_config.chef.add_role \"%s\"\n" % (name, n.role)
            vagrant += "    %s_config.vm.network(\"%s\", :netmask => \"255.255.0.0\")\n" % (name, n.ip)            
            vagrant += "    %s_config.chef.json.merge!({\n" % name         
            for k,v in n.chef_attrs.items():
                vagrant += "      :%s => %s,\n" % (k,v)
            vagrant += "    })\n"       
            vagrant += "  end\n\n"           
        vagrant += "end\n"           

        vagrantfile = open(vagrant_dir + "/Vagrantfile", "w")
        vagrantfile.write(vagrant)
        vagrantfile.close()
        
        chef_link = vagrant_dir + "/chef"
        if os.path.lexists(chef_link):
            os.remove(chef_link)            
        os.symlink(self.generated_dir + self.CHEF_DIR, chef_link)
        
        