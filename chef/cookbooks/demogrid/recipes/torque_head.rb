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

# The lrm_head attribute is part of the generated topology.rb file,
# and contains the FQDN of the head node.
server_fqdn = node[:lrm_head]
server = server_fqdn.split(".")[0]
clusternode = "#{node[:org]}-clusternode"

# Install Torque
if ! File.exists?(node[:torque][:dir])
	# Copy the server installation script
	cookbook_file "/tmp/#{pbs_server_sh}" do
	  source "#{pbs_server_sh}"
	  mode 0755
	  owner "root"
	  group "root"
	end

	# Copy the client tools installation script
	cookbook_file "/tmp/#{pbs_clients_sh}" do
	  source "#{pbs_clients_sh}"
	  mode 0755
	  owner "root"
	  group "root"
	end

	# Copy the setup script
	cookbook_file "/tmp/torque.setup" do
	  source "torque.setup"
	  mode 0755
	  owner "root"
	  group "root"
	end

	# Run the server installation script
	execute "pbs_server_install" do
	  user "root"
	  group "root"
	  command "/tmp/#{pbs_server_sh} --install"
	  action :run
	end

	# Run the client tools installation script
	execute "pbs_client_install" do
	  user "root"
	  group "root"
	  command "/tmp/#{pbs_clients_sh} --install"
	  action :run
	end

	# Make the system aware of new libraries
	execute "ldconfig" do
	  user "root"
	  group "root"
	  command "ldconfig"
	  action :run
	end

	# Tell torque what server is the head node
	file "#{node[:torque][:dir]}/server_name" do
	  owner "root"
	  group "root"
	  mode "0644"
	  action :create
	  content "#{server}"
	end

	# Run the setup script, and add the globus user
	# as an administrator
	execute "torque.setup" do
	  user "root"
	  group "root"
	  command "/tmp/torque.setup globus"
	  action :run
	end

	# Add init script
	cookbook_file "/etc/init.d/pbs_server" do
	  source "debian.pbs_server"
	  owner "root"
	  group "root"
	  mode "0755"
	end

	execute "update-rc.d" do
	  user "root"
	  group "root"
	  command "update-rc.d pbs_server defaults"
	  action :run
	end

	cookbook_file "/etc/init.d/pbs_sched" do
	  source "debian.pbs_sched"
	  owner "root"
	  group "root"
	  mode "0755"
	end

	execute "update-rc.d" do
	  user "root"
	  group "root"
	  command "update-rc.d pbs_sched defaults"
	  action :run
	end
end

# Tell Torque what nodes are worker nodes
# TODO: Remove hardcoded nastiness. We should provide this
# information through topology.rb
ruby_block "add_lines" do
  file = "#{node[:torque][:dir]}/server_priv/nodes"
  block do
    for worker in (1..4)      
      add_line(file, "#{clusternode}-#{worker}")
    end
  end
end


# Restart the Torque servers.
execute "pbs_server_restart" do
 user "root"
 group "root"
 command "/etc/init.d/pbs_server restart"
 action :run
end

execute "pbs_sched_restart" do
 user "root"
 group "root"
 command "/etc/init.d/pbs_sched restart"
 action :run
end

