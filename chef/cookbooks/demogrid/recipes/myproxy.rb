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
# RECIPE: MyProxy server
#
# Sets up a MyProxy server. It assumes that the "globus" recipe has been run, 
# so it just involves setting up MyProxy as a xinetd service.
#
# Users are added in a separate recipe, "myproxy_users"
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

package "xinetd" do
  action :install
end

cookbook_file "#{node[:globus][:dir]}/etc/myproxy-server.config" do
  source "myproxy-server.config"
  mode 0644
  owner "globus"
  group "globus"
end

template "/etc/xinetd.d/myproxy" do
  source "xinetd.myproxy.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :globus_location => node[:globus][:dir]
  )
end

ruby_block "add_lines" do
  block do
    add_line("/etc/services", "myproxy-server  7512/tcp                        # Myproxy server")
  end
end


execute "xinetd_restart" do
 user "root"
 group "root"
 command "/etc/init.d/xinetd restart"
 action :run
end
