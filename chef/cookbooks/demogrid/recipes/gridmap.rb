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
# RECIPE: Gridmap file
#
# This recipe creates a gridmap file where all grid users are authorized.
# Local users are mapped to their local account. Remote users are mapped to
# their "grid account" on that site (e.g., "b-user1" running on organization "a"
# would run under account "dg-b-user1").
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

# The org attribute is part of the generated topology.rb file,
# and contains the name of the organization this node belongs to.
org = node[:org]

# Create grid-security directory.
directory "/etc/grid-security" do
  owner "root"
  group "root"
  mode "0755"
  action :create
end

# If it does not exist, create an empty gridmap file.
file "/etc/grid-security/grid-mapfile" do
  owner "root"
  group "root"
  mode "0644"
  action :create
end

# Add entries for local users.
# The orgusers attribute is part of the generated topology.rb file,
# and contains information on an organization's user (username,
# whether the user is a grid user or not, etc.)
users = node[:orgusers][org]
users.select{|v| v[:gridenabled]}.each do |u|
	ruby_block "add_lines" do
	  file = "/etc/grid-security/grid-mapfile"
	  map = "\"#{u[:dn]}\" #{u[:login]}"
	  block do
	    add_line(file, map)
	  end
	end
end

# Entries for remote ("grid") users
# We check all the other organizations, and add an entry for
# each grid user we encounter there.
other_orgs = node[:orgusers].select{|k,v| k != org}
other_orgs.each do |other_org,users|
	users.select{|v| v[:gridenabled]}.each do |u|
		username = "dg-#{u[:login]}"

		ruby_block "add_lines" do
		  file = "/etc/grid-security/grid-mapfile"
		  map = "\"#{u[:dn]}\" #{username}"
		  block do
		    add_line(file, map)
		  end
		end
	end
end
