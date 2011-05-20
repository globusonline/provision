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


  execute "galaxy-setup.sh" do
    user "galaxy"
    group "galaxy"
    cwd node[:galaxy][:dir]
    command "./galaxy-setup.sh"
    action :run
  end  
 
  # Add init script
  cookbook_file "/etc/init.d/galaxy" do
    source "galaxy.init"
    owner "root"
    group "root"
    mode "0755"
  end
  
  execute "update-rc.d" do
    user "root"
    group "root"
    command "update-rc.d galaxy defaults"
    action :run
  end  

execute "galaxy_restart" do
 user "root"
 group "root"
 command "/etc/init.d/galaxy restart"
 action :run
end




