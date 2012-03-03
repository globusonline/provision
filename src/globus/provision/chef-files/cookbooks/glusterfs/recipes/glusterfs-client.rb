# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                 #
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
## RECIPE: GlusterFS client
##
## Set up a GlusterFS client node.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# The "glusterfs-common" recipe handles actions that are common to
# both servers and clients
include_recipe "glusterfs::glusterfs-common"

gp_domain = node[:topology][:domains][node[:domain_id]]
head_server = gp_domain[:glusterfs_head]
peer_servers = gp_domain[:glusterfs_servers]
glusterfs_servers = [head_server] + peer_servers


directory "/glusterfs" do
  owner "root"
  group "root"
  mode "0755"
  action :create
end

execute "mount_glusterfs" do
  user "root"
  group "root"
  command "mount -t glusterfs #{head_server}:/gp-vol /glusterfs"
  action :run
end   
