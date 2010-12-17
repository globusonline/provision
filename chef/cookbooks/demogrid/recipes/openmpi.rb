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
# RECIPE: OpenMPI
#
# Install OpenMPI.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Recipe
  include MiscHelper
end

orgletter = node[:org]

openmpi_tarball = "openmpi-1.4.3-bin.tar.bz2"

if ! File.exists?(node[:openmpi][:dir])

	cookbook_file "/var/tmp/#{openmpi_tarball}" do
	  source "#{openmpi_tarball}"
	  mode 0644
	  owner "root"
	  group "root"
	end

	execute "tar" do
	  user "root"
	  group "root"
	  command "tar xjf /var/tmp/#{openmpi_tarball} --directory /usr/local"
	  action :run
	end

end

# OpenMPI requires passwordless SSH between the nodes. The users'
# SSH keys are already passwordless, but we need to add the hosts
# to the known_hosts file. We do this simply by making every user 
# SSH into the current node, so the host will be added
# to the known_hosts files (which is in a global home directory)
# TODO: Move all this to a "passwordless SSH" recipe, since it
# isn't strictly OpenMPI-specific.

# The org attribute is part of the generated topology.rb file,
# and contains the name of the organization this node belongs to.
org = node[:org]

# The orgusers attribute is part of the generated topology.rb file,
# and contains information on an organization's user (username,
# whether the user is a grid user or not, etc.)
users = node[:orgusers][org]

users.each do |u|
	execute "ssh" do
	  user u[:login]
	  command "ssh -o StrictHostKeychecking=no `hostname` :"
	  action :run
	end
end
