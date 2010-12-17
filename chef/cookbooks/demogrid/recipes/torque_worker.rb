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
# RECIPE: Torque worker node
#
# Set up a Torque worker node.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Recipe
  include MiscHelper
end

# See torque_head for a description of what these ".sh" files are.
include_recipe "demogrid::torque"

# The lrm_head attribute is part of the generated topology.rb file,
# and contains the FQDN of the head node.
server_fqdn = node[:lrm_head]
server = server_fqdn.split(".")[0]

# Create configuration file. 
file "#{node[:torque][:dir]}/mom_priv/config" do
  owner "root"
  group "root"
  mode "0644"
  action :create
  # Besides telling Torque about the head node, we instruct it
  # to not use scp/rcp when copying files to/from the home directories
  # (since they're on a shared file system)
  content "pbs_server = #{server}\n$usecp *:/export  /export"
end

# Tell Torque what node is the head node.
file "#{node[:torque][:dir]}/server_name" do
  owner "root"
  group "root"
  mode "0644"
  action :create
  content "#{server}"
end

# Create init script.
cookbook_file "/etc/init.d/pbs_mom" do
  source "debian.pbs_mom"
  owner "root"
  group "root"
  mode "0755"
end

execute "update-rc.d" do
  user "root"
  group "root"
  command "update-rc.d pbs_mom defaults"
  action :run
end

# Restart Torque daemon
execute "pbs_mom_restart" do
 user "root"
 group "root"
 command "/etc/init.d/pbs_mom restart"
 action :run
end
