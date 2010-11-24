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
# RECIPE: NIS client
#
# Set up node so it will have access to it's organizations NIS server, allowing
# organization users to log into it.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

# The org_server attribute is part of the generated topology.rb file,
# and contains the IP of the organization's NFS/NIS server.
server = node[:org_server]


# Packages we need

package "nis" do
  action :install
end

package "portmap" do
  action :install
end


# Modify various configuration files to enable access to the NIS server.
ruby_block "addlines" do
  block do
    add_line("/etc/hosts.allow", "portmap : #{server}")
    add_line("/etc/hosts.deny", "portmap : ALL")
    add_line("/etc/passwd", "+::::::")
    add_line("/etc/group", "+:::")
    add_line("/etc/shadow", "+::::::::")
    add_line("/etc/yp.conf", "ypserver #{server}")
  end
end


# Restart NIS
execute "nis_restart" do
 user "root"
 group "root"
 command "/etc/init.d/nis restart"
 action :run
end
