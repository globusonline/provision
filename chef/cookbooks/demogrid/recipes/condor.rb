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
# RECIPE: Condor common actions
#
# This recipe is a dependency of condor_head and condor_worker, which will set
# up a Condor head node or worker node. This recipe handles all the actions
# that are common to both.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

condor_tarball = "condor-7.4.3-linux-x86-debian50-dynamic.tar.gz"

# Needed by one of the installation scripts
package "bind9-host" do
  action :install
end

# Needed to create the condor user
package "libshadow-ruby1.8" do
  action :install
end


# Create the condor group and user

group "condor" do
  gid 501
end

user "condor" do
  comment "Condor User"
  uid 501
  gid 501
  home "/var/condor"
  password "$1$mUbD74i3$NnuDAuhjlTj3tpBbaI9WM1" # Password: condor
  shell "/bin/bash"
  supports :manage_home => true
end


# If the Condor directory does not exist, then create it by un-taring the
# Condor tarball. This also sets up the init scripts, but does not set up
# Condor itself.
if ! File.exists?(node[:condor][:dir])
	cookbook_file "/tmp/#{condor_tarball}" do
	  source "#{condor_tarball}"
	  mode 0755
	  owner "root"
	  group "root"
	end

	execute "tar" do
	  user "root"
	  group "root"
	  command "tar xzf /tmp/#{condor_tarball} --directory /usr/local"
	  action :run
	end

	cookbook_file "/etc/init.d/condor" do
	  source "condor.init"
	  mode 0744
	  owner "root"
	  group "root"
	end

	execute "update-rc.d" do
	  user "root"
	  group "root"
	  command "update-rc.d condor defaults"
	  action :run
	end
end




