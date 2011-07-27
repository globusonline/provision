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
# RECIPE: NFS client
#
# Set up node so it will have access to its domain's NFS server.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

# The nfs_server attribute is part of the generated topology.rb file,
# and contains the IP of the domain's NFS server.
server = node[:nfs_server]


# Packages we need

package "nfs-common" do
  action :install
end

package "autofs" do
  action :install
end

# Set configuration options for NFSv4
cookbook_file "/etc/default/nfs-common" do
  source "nfs-common"
  mode 0644
  owner "root"
  group "root"
end


# Set up the home directories so they will be automounted.

if ! File.exists?("/nfs")
	# Create the directory where the NFS directories will be mounted
	directory "/nfs" do
	  owner "root"
	  group "root"
	  mode "0755"
	  action :create
	  recursive true
	end
	
	# Create the directory where home directories will be mounted
	directory "/nfs/home" do
	  owner "root"
	  group "root"
	  mode "0755"
	  action :create
	  recursive true
	end
end

ruby_block "addlines" do
  block do
    add_line("/etc/auto.master", "/nfs              /etc/auto.nfs")
  end
end

template "/etc/auto.home" do
  source "auto.home.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :server => server
  )
end

template "/etc/auto.nfs" do
  source "auto.nfs.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :server => server
  )
end

execute "portmap_restart" do
 user "root"
 group "root"
 command "/etc/init.d/portmap restart"
 action :run
end

case node.platform
  when "debian"
    execute "nfs_common_restart" do
      user "root"
      group "root"
      command "/etc/init.d/nfs-common restart"
      action :run
    end
  when "ubuntu"
    execute "idmapd_restart" do
      user "root"
      group "root"
      command "service idmapd --full-restart"
      action :run
    end
end


# Restart autofs

execute "autofs_restart" do
 user "root"
 group "root"
 command "/etc/init.d/autofs restart"
 action :run
end

ruby_block "addlines" do
  block do
    add_line("/etc/profile", "export PATH=/nfs/software/bin:$PATH")
  end
end
