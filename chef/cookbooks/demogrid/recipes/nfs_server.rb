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
# Set up an organizations NFS server. Currently, the only shared directory
# is the one containing the home directories of the organization's users.
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


# Create the directory for the home directories
directory "/export/home" do
  owner "root"
  group "root"
  mode "0755"
  recursive true
  action :create
end


# Only allow access to machines in the organization's subnet.
ruby_block "add_lines" do
  block do
    add_line("/etc/hosts.allow", "mountd nfsd statd lockd rquotad : #{subnet}/24")
    add_line("/etc/hosts.deny", "mountd nfsd statd lockd rquotad : ALL")
    add_line("/etc/exports", "/export/home #{subnet}/24(rw,no_subtree_check,sync)")
  end
end


# Restart NFS
execute "nfs-kernel-server_restart" do
 user "root"
 group "root"
 command "/etc/init.d/nfs-kernel-server restart"
 action :run
end
