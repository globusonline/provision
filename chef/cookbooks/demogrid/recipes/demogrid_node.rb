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
# RECIPE: DemoGrid common actions
#
# This recipe performs actions that are common to all DemoGrid nodes.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Required to create the "gridadmin" user.
package "libshadow-ruby1.8" do
  action :install
end


# Create the "gridadmin" user. This user has admin privileges,
# and can be used on any node to sudo into root.
user "gridadmin" do
  # In some cases, we may be running Chef as gridadmin. When this happens,
  # Chef will try to run usermod (since the user already exists) but will
  # fail because the user is logged in. This is not caught by Chef's
  # idempotency checks, so we tell Chef to skip this action altogether 
  # if the user already exists.
  not_if "id gridadmin" # Skip Chef's usual checks
  comment "DemoGrid administrator"
  uid 600
  gid "admin"
  home "/home/gridadmin"
  password "$1$ZFLDhbwu$5sa39wH60W/NyQYAKy2xV0" # Password: gridadmin
  shell "/bin/bash"
  supports :manage_home => true
end

# Copy the hosts file
cookbook_file "/etc/hosts" do
  source "hosts"
  mode 0644
  owner "root"
  group "root"
end

# Change the hostname
file "/etc/hostname" do
  mode 0644
  owner "root"
  group "root"
  action :create
  # The demogrid_hostname attribute is part of the generated topology.rb file,
  # and contains the FQDN of the node. In most cases, we could simply use
  # node[:name] or node[:fqdn], but this won't work with Vagrant, which
  # sets an interim hostname when the VM is being configured. So,
  # we supply the FQDN ourselves (in topology.rb when not using Vagrant,
  # and in Vagrantfile when using Vagrant).
  content node[:demogrid_hostname]
end

# Make sure the new hostname takes effect.
execute "hostname" do
 user "root"
 group "root"
 command "/etc/init.d/hostname restart"
 action :run
end

