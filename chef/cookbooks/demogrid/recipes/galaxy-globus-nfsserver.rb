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

group "galaxy" do
  gid 4000
end

user "galaxy" do
  comment "Globus User"
  uid 4000
  gid 4000
  home "/nfs/home/galaxy"
  password "$1$rmHlRI5D$xNAqmRlrB6.P6SHOi2gpw1" # Password: globus
  shell "/bin/bash"
  supports :manage_home => true
end

# We need to run this for changes to take effect in the NIS server.
execute "ypinit" do
 user "root"
 group "root"
 command "echo | /usr/lib/yp/ypinit -m"
 action :run
end

if ! File.exists?(node[:galaxy][:dir])

  directory "#{node[:galaxy][:dir]}" do
    owner "galaxy"
    group "galaxy"
    mode "0755"
    action :create
  end
  
  remote_file "/var/tmp/galaxy-dist.tip.tar.bz2" do
    source "https://bitbucket.org/steder/galaxy-globus/get/tip.tar.bz2"
    owner "root"
    group "root"    
    mode "0644"
  end
  
  #cookbook_file "/var/tmp/galaxy-dist.tip.tar.bz2" do
  #  source "galaxy-globus.tip.tar.bz2"
  #  owner "root"
  #  group "root"
  #  mode "0644"
  #end  

  execute "tar" do
    user "galaxy"
    group "galaxy"
    command "tar xjf /var/tmp/galaxy-dist.tip.tar.bz2 --strip-components=1 --directory #{node[:galaxy][:dir]}"
    action :run
  end  	

  directory "#{node[:galaxy][:dir]}/eggs" do
    owner "galaxy"
    group "galaxy"
    mode "0755"
    action :create
  end

  cookbook_file "#{node[:galaxy][:dir]}/eggs/galaxy-eggs.tgz" do
    source "galaxy-eggs.tgz"
    owner "galaxy"
    group "galaxy"
    mode "0644"
  end  

  execute "tar" do
    user "galaxy"
    group "galaxy"
    cwd "#{node[:galaxy][:dir]}/eggs"
    command "tar xzf galaxy-eggs.tgz"
    action :run
  end  	

  cookbook_file "#{node[:galaxy][:dir]}/galaxy-setup.sh" do
    source "galaxy-setup.sh"
    owner "galaxy"
    group "galaxy"
    mode "0755"
  end
  
  cookbook_file "#{node[:galaxy][:dir]}/universe_wsgi.ini" do
    source "universe_wsgi-globus.ini"
    owner "galaxy"
    group "galaxy"
    mode "0644"
  end

end
  
