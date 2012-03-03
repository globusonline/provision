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
## RECIPE: NFS client
##
## Set up node so it will have access to its domain's NFS server.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gp_domain = node[:topology][:domains][node[:domain_id]]
gp_node   = gp_domain[:nodes][node[:node_id]]

# Packages we need
package "nfs-common"
package "autofs"

# Set configuration options for NFSv4
cookbook_file "/etc/default/nfs-common" do
  source "nfs-common"
  mode 0644
  owner "root"
  group "root"
  notifies :run, "execute[nfs services restart]", :immediately
end


nfs_mounts = gp_domain[:filesystem][:nfs_mounts].to_a

cookbook_file "/etc/auto.master" do
  source "auto.master"
  mode 0644
  owner "root"
  group "root"
end

template "/etc/auto.nfs" do
  source "auto.nfs.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :gp_domain => gp_domain
  )
  notifies :restart, "service[autofs]", :immediately  
end

execute "nfs services restart" do
  user "root"
  group "root"
  action :nothing
  case node.platform
    when "debian"
      command "/etc/init.d/nfs-common restart"
    when "ubuntu"
      command "service idmapd --full-restart"
  end
end

service "autofs"

