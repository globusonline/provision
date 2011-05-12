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


# Needed to create the galaxy user
package "libshadow-ruby1.8" do
  action :install
end


# Create the galaxy group and user

group "galaxy" do
  gid 501
end

user "galaxy" do
  comment "Galaxy User"
  uid 501
  gid 501
  home "/home/galaxy"
  password "$1$rmHlRI5D$xNAqmRlrB6.P6SHOi2gpw1" # Password: globus
  shell "/bin/bash"
  supports :manage_home => true
end

if ! File.exists?(node[:galaxy][:dir])

  remote_file "/home/galaxy/galaxy-dist.tip.tar.gz" do
    source "http://dist.g2.bx.psu.edu/galaxy-dist.tip.tar.gz"
    mode "0644"
  end

  execute "tar" do
    user "galaxy"
    group "galaxy"
    cwd "/home/galaxy"
    command "tar xzf galaxy-dist.tip.tar.gz"
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

  cookbook_file "#{node[:galaxy][:dir]}/galaxy-setup.sh" do
    source "galaxy-setup.sh"
    owner "galaxy"
    group "galaxy"
    mode "0755"
  end

  execute "galaxy-setup.sh" do
    user "galaxy"
    group "galaxy"
    cwd node[:galaxy][:dir]
    command "./galaxy-setup.sh"
    action :run
  end  
end

cookbook_file "#{node[:galaxy][:dir]}/universe_wsgi.ini" do
  source "universe_wsgi.ini"
  owner "galaxy"
  group "galaxy"
  mode "0644"
end

execute "galaxy_restart" do
 user "root"
 group "root"
 command "/etc/init.d/galaxy restart"
 action :run
end



