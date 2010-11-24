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
# RECIPE: Add users to MyProxy server
#
# An organization can be configured so that users don't have certificates
# in their home directories and, instead, get their proxy certificates from
# MyProxy. This recipe adds these users to MyProxy, so they can just
# run myproxy-logon.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# We need this package to run myproxy-admin-adduser
package "expect" do
  action :install
end


# The orgusers attribute is part of the generated topology.rb file,
# and contains information on an organization's user (username,
# whether the user is a grid user or not, etc.)
#
# In this loop, we iterate over each organization and the users in that organization.
# If the user's authorization method is set to "myproxy", we add that user to the
# MyProxy server
node[:orgusers].each_pair do |org, users|
	users.select{|u| u[:auth_type] == :myproxy}.each do |u|
		# Only add the user if it hasn't been created yet.
		if ! File.exists?("/var/myproxy/#{u[:login]}.creds")
			# I haven't found a way of running myproxy-admin-adduser in a completely unattended
			# manner. So, we have to use expect to supply the passphrase for the user's certificate.
			cmd = "expect -c \"spawn #{node[:globus][:dir]}/sbin/myproxy-admin-adduser -c \\\"#{u[:description]}\\\" -l #{u[:login]} -p pass:gridca; expect \\\"Enter PEM pass phrase:\\\"; send \\\"griduser\r\\\"; expect \\\"Verifying - Enter PEM pass phrase:\\\"; send \\\"griduser\r\\\"; expect eof\""
			execute "myproxy-admin-adduser #{u[:login]}" do
			  user "root"
			  command ". #{node[:globus][:dir]}/etc/globus-user-env.sh; #{cmd}"
			  action :run
			  environment(
			    "GLOBUS_LOCATION" => node[:globus][:dir],
			    # expect, myproxy, or some combination of both barfs if this is not included.
			    # Only happens when running under chef. 
			    "HOME" => "/root" 
			  )
			end
		end
	end
end

