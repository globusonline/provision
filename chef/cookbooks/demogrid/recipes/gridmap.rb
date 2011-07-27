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
# This recipe creates a gridmap file where users with their :gridmap
# attribute set to true are added.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Chef::Resource
  include FileHelper
end

# The domain attribute is part of the generated topology.rb file,
# and contains the name of the domain this node belongs to.
domain = node[:demogrid_domain]

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
# The :users attribute is part of the generated topology.rb file,
# and contains information on a domain's users (username,
# password, etc.)
users = node[:domains][domain][:users]
users.select{|v| v[:gridmap]}.each do |u|
	ruby_block "add_lines" do
	  file = "/etc/grid-security/grid-mapfile"
	  map = "\"#{u[:dn]}\" #{u[:login]}"
	  block do
	    add_line(file, map)
	  end
	end
end
