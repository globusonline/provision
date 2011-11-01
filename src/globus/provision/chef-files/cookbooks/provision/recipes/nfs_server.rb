# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                      #
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


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##
## RECIPE: NFS Server
##
## Set up a domain's NFS server and its shared directories.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gp_domain = node[:topology][:domains][node[:domain_id]]
gp_node   = gp_domain[:nodes][node[:node_id]]

subnet = nil

# Install the NFS server package
package "nfs-kernel-server" do
  action :install
end


# Configuration file with fixed port
cookbook_file "/etc/default/nfs-kernel-server" do
  source "nfs-kernel-server"
  mode 0644
  owner "root"
  group "root"
end

# Set configuration options for NFSv4
cookbook_file "/etc/default/nfs-common" do
  source "nfs-common"
  mode 0644
  owner "root"
  group "root"
end

template "/etc/hosts.allow" do
  source "hosts.denyallow.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :subnet => subnet,
    :type => :allow
  )
end

template "/etc/hosts.deny" do
  source "hosts.denyallow.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :subnet => subnet,
    :type => :deny
  )
end

# Create directories

nfs_mounts = gp_domain[:filesystem][:nfs_mounts].to_a

nfs_mounts.each do |m|

  directory m[:path] do
    owner m[:owner]
    mode m[:mode]
    recursive true
    action :create
  end
end

# Add exports
template "/etc/exports" do
  source "exports.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :nfs_mounts => nfs_mounts,
    :subnet => subnet
  )
  notifies :restart, "service[nfs-kernel-server]"
  notifies :run, "execute[nfs services restart]"
end


# Restart NFS
service "nfs-kernel-server"

execute "nfs services restart" do
  user "root"
  group "root"
  action :nothing
  case node.platform
    when "debian"
      command "/etc/init.d/nfs-common restart"
    when "ubuntu"
      command "service statd --full-restart; service idmapd --full-restart"
  end
end
