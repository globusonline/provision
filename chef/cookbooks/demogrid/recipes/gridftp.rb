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
# RECIPE: Globus Toolkit 5.0.2 GridFTP
#
# This recipe performs a barebones install of GridFTP. It assumes that the
# "globus" recipe has been run, so it just involves setting up GridFTP
# as a xinetd service.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

globus_location = "/usr/local/globus-5.0.2"

package "xinetd" do
  action :install
end

cookbook_file "#{globus_location}/etc/gridftp.conf" do
  source "gridftp.conf"
  mode 0644
  owner "globus"
  group "globus"
end

template "/etc/xinetd.d/gsiftp" do
  source "xinetd.gridftp.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :globus_location => globus_location,
    :ec2_public => node[:ec2_public],
    :public_ip => node[:public_ip]
  )
end

execute "xinetd_restart" do
 user "root"
 group "root"
 command "/etc/init.d/xinetd restart"
 action :run
end
