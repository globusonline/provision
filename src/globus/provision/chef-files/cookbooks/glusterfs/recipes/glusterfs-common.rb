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
## RECIPE: GlusterFS common actions
##
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

remote_file "#{node[:scratch_dir]}/glusterfs.deb" do
  action :create_if_missing 
  source "http://download.gluster.com/pub/gluster/glusterfs/3.2/3.2.3/Ubuntu/glusterfs_3.2.3-1_amd64.deb"
  owner "root"
  group "root"    
  mode "0644"
end

package "glusterfs" do
  action :install
  source "#{node[:scratch_dir]}/glusterfs.deb"
  provider Chef::Provider::Package::Dpkg
end
