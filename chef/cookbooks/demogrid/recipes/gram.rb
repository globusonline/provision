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
# RECIPE: Globus Toolkit 5.0.3 GRAM
#
# This recipe performs a barebones install of GRAM. It assumes that the
# "globus" recipe has been run, so it just involves setting up GRAM
# as a xinetd service.
#
# This doesn't set up GRAM to work with a specific LRM, which is handled 
# in other recipes.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

package "xinetd" do
  action :install
end

template "/etc/xinetd.d/gram" do
  source "xinetd.gram.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :globus_location => node[:globus][:dir]
  )
end

execute "xinetd_restart" do
 user "root"
 group "root"
 command "/etc/init.d/xinetd restart"
 action :run
end
