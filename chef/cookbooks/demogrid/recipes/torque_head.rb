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

# The "torque" recipe handles actions that are common to
# both head and worker nodes.
include_recipe "demogrid::torque"

# The lrm_head attribute is part of the generated topology.rb file,
# and contains the FQDN of the head node.
server_fqdn = node[:lrm_head]
server = server_fqdn.split(".")[0]
clusternodes = (1..node[:lrm_nodes]).map{|n| "#{node[:org]}-clusternode-#{n}"}

if ! File.exists?("/etc/init.d/pbs_server") 
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
    command "/var/tmp/torque.setup globus"
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
template "#{node[:torque][:dir]}/server_priv/nodes" do
  source "torque_nodes.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :clusternodes => clusternodes
  )
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

