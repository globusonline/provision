# -------------------------------------------------------------------------- #
# Copyright 2010, University of Chicago                                      #
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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# RECIPE: Torque head node
#
# Set up a Torque head node.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

class Chef::Recipe
  include MiscHelper
end

# Although we could install entirely from scratch, the first Torque installation
# generates a set of convenient scripts that encapsulate pre-built binaries for
# distribution to nodes that will run Torque. We prepared these on an
# Ubuntu Lucid 32-bit machine, and use them to install Torque on DemoGrid.
pbs_server_sh = "torque-package-server-linux-i686.sh"
pbs_clients_sh = "torque-package-clients-linux-i686.sh"
pbs_mom_sh = "torque-package-mom-linux-i686.sh"

# Install Torque
if ! File.exists?(node[:torque][:dir])
	# Copy the server installation script
	cookbook_file "/var/tmp/#{pbs_server_sh}" do
	  source "#{pbs_server_sh}"
	  mode 0755
	  owner "root"
	  group "root"
	end

	# Copy the client tools installation script
	cookbook_file "/var/tmp/#{pbs_clients_sh}" do
	  source "#{pbs_clients_sh}"
	  mode 0755
	  owner "root"
	  group "root"
	end

  # Copy worker node installation script
   cookbook_file "/var/tmp/#{pbs_mom_sh}" do
     source "#{pbs_mom_sh}"
     mode 0755
     owner "root"
     group "root"
   end
 
   # Run worker node installation script
   execute "pbs_mom_install" do
     user "root"
     group "root"
     command "/var/tmp/#{pbs_mom_sh} --install"
     action :run
   end
	
	# Copy the setup script
	cookbook_file "/var/tmp/torque.setup" do
	  source "torque.setup"
	  mode 0755
	  owner "root"
	  group "root"
	end

	# Run the server installation script
	execute "pbs_server_install" do
	  user "root"
	  group "root"
	  command "/var/tmp/#{pbs_server_sh} --install"
	  action :run
	end

	# Run the client tools installation script
	execute "pbs_client_install" do
	  user "root"
	  group "root"
	  command "/var/tmp/#{pbs_clients_sh} --install"
	  action :run
	end

	# Make the system aware of new libraries
	execute "ldconfig" do
	  user "root"
	  group "root"
	  command "ldconfig"
	  action :run
	end
end
