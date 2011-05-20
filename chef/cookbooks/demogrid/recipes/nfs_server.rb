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
# RECIPE: NFS Server
#
# Set up an organizations NFS server and its shared directories.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

# The subnet attribute is part of the generated topology.rb file,
# and contains the organization's subnet IP address.
subnet = node[:subnet]


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





# Only allow access to machines in the organization's subnet.
ruby_block "add_lines" do
  block do
    if subnet
      add_line("/etc/hosts.allow", "mountd nfsd statd lockd rquotad : #{subnet}/24")
      add_line("/etc/hosts.deny", "mountd nfsd statd lockd rquotad : ALL")
    else
      add_line("/etc/hosts.allow", "mountd nfsd statd lockd rquotad : ALL")
    end
  end
end


# Create directories

# Home directories
directory "/nfs/home" do
  owner "root"
  group "root"
  mode "0755"
  recursive true
  action :create
end

# Scratch directory
# This is a kludge: it assumes that ephemeral storage will be mounted
# on /mnt. If it is not, the recipe should still work since /mnt
# has to be empty, but keeping the scratch directory there is not ideal. 
# A more general-purpose solution would be preferable (ideally by
# specifying these shared directories in the topology)
directory "/mnt/scratch" do
  owner "root"
  group "root"
  mode 01777
  recursive true
  action :create
end


# Software directories
directory "/nfs/software" do
  owner "root"
  group "root"
  mode "0755"
  recursive true
  action :create
end

# Add exports
ruby_block "add_lines" do
  block do
    if subnet
      add_line("/etc/exports", "/nfs/home #{subnet}/24(rw,root_squash,no_subtree_check,sync)")
      add_line("/etc/exports", "/mnt/scratch #{subnet}/24(rw,root_squash,no_subtree_check,sync)")
      add_line("/etc/exports", "/nfs/software #{subnet}/24(rw,root_squash,no_subtree_check,sync)")
    else
      add_line("/etc/exports", "/nfs/home (rw,root_squash,no_subtree_check,sync)")
      add_line("/etc/exports", "/mnt/scratch (rw,root_squash,no_subtree_check,sync)")
      add_line("/etc/exports", "/nfs/software (rw,root_squash,no_subtree_check,sync)")
    end
  end
end

# Restart NFS
execute "nfs-kernel-server_restart" do
 user "root"
 group "root"
 command "/etc/init.d/nfs-kernel-server restart"
 action :run
end
