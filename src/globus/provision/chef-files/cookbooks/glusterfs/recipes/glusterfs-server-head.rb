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
## RECIPE: GlusterFS server
##
## Set up a GlusterFS server
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

require 'pp'


include_recipe "glusterfs::glusterfs-server"

gp_domain = node[:topology][:domains][node[:domain_id]]
head_server = gp_domain[:glusterfs_head]
peer_servers = gp_domain[:glusterfs_servers]
glusterfs_servers = [head_server] + peer_servers
glusterfs_type = gp_domain[:glusterfs_type]
glusterfs_setsize = gp_domain[:glusterfs_setsize]


peer_servers.each do |s|

  execute "add_glusterfs_peer" do
    user "root"
    group "root"
    command "gluster peer probe #{s}"
    action :run
  end   

end

brick_list =  glusterfs_servers.map{|s| s+":/ephemeral/0/glusterfs"}
brick_list += glusterfs_servers.map{|s| s+":/ephemeral/1/glusterfs"}

num_bricks = brick_list.size

brick_list = brick_list.join(" ")

case glusterfs_type
when "distributed"
    opt = ""
when "replicated"
    opt = "replica #{num_bricks}"
when "striped"
    opt = "stripe #{num_bricks}"
when "distributed-striped"
    opt = "stripe #{glusterfs_setsize}"
when "distributed-replicated"
    opt = "replica #{glusterfs_setsize}"
end

vol_create = "gluster volume create gp-vol #{opt} transport tcp #{brick_list}"

execute "create_glusterfs_volume" do
  not_if "gluster volume info gp-vol"
  brick_list = glusterfs_servers.map{|s| s+":/mnt/glusterfs"}.join(" ")
  user "root"
  group "root"
  command "#{vol_create} && gluster volume start gp-vol"
  action :run
end   
