# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                 #
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

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##
## RECIPE: Hadoop common actions
##
## This recipe is a dependency of ``hadoop-master`` and ``hadoop-slave``, which will set
## up a Hadoop master node or slave node. This recipe handles all the actions
## that are common to both.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gp_domain = node[:topology][:domains][node[:domain_id]]

if gp_domain[:nfs_server]
    hadoop_dir = "/nfs/software/hadoop"
    homedirs = "/nfs/home"
else
    hadoop_dir = "/usr/local/hadoop"
    homedirs = "/home"
end

group "hadoop" do
  gid 4001
end

user "hduser" do
  comment "Hadoop User"
  uid 4001
  gid 4001
  home "#{homedirs}/hduser"
  password "!"
  shell "/bin/bash"
  supports :manage_home => true
  notifies :run, "execute[ypinit]"
end

# We need to run this for changes to take effect in the NIS server.
execute "ypinit" do
 only_if do gp_domain[:nis_server] end
 user "root"
 group "root"
 command "make -C /var/yp"
 action :nothing
end

# Hadoop common
if ! File.exists?(hadoop_dir)

  directory "#{hadoop_dir}" do
    owner "hduser"
    group "hadoop"
    mode "0755"
    action :create
  end

  remote_file "#{node[:scratch_dir]}/hadoop.tar.gz" do
    source "http://mirrors.kahuki.com/apache/hadoop/core/hadoop-0.21.0/hadoop-0.21.0.tar.gz"
    owner "root"
    group "root"    
    mode "0644"
  end

  execute "tar" do
    user "hduser"
    group "hadoop"
    command "tar xzf #{node[:scratch_dir]}/hadoop.tar.gz --strip-components=1 --directory #{hadoop_dir}"
    action :run
  end  	

end

# Configuration files

directory "#{homedirs}/hduser/conf" do
  owner "hduser"
  group "hadoop"
  mode "0755"
  action :create
end


