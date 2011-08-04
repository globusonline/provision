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
# RECIPE: NIS Server
#
# Set up an domain's NIS server.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

# The subnet attribute is part of the generated topology.rb file,
# and contains the domain's subnet IP address.
subnet = node[:subnet]


# Packages we need

package "nis"
package "portmap"


# Only allow access to the nodes in that domain's subnet

ruby_block "hosts.allow" do
  block do
    if subnet
      add_line("/etc/hosts.allow", "portmap ypserv ypbind : #{subnet}/24")
    else
      add_line("/etc/hosts.allow", "portmap ypserv ypbind : ALL")
    end
  end
end

ruby_block "hosts.deny" do
  block do
    if subnet
      add_line("/etc/hosts.deny", "portmap ypserv ypbind : ALL")
    end
  end
end

cookbook_file "/etc/default/nis" do
  source "nis"
  mode 0644
  owner "root"
  group "root"
  notifies :restart, "service[nis]"
  notifies :run, "execute[ypinit]"
end

ruby_block "yp.conf" do
  block do
    add_line("/etc/yp.conf", "domain grid.example.org server #{node[:demogrid_hostname]}")
  end
end

ruby_block "ypserv.securenets" do
  block do
    if subnet
      add_line("/etc/ypserv.securenets", "255.255.255.0 #{subnet}")
    end
  end
end


# Restart services so the changes take effect.

execute "ypinit" do
 user "root"
 group "root"
 command "echo | /usr/lib/yp/ypinit -m"
 action :nothing
end

service "nis"
