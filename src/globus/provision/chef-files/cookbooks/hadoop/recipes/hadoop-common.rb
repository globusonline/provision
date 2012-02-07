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

require "fileutils"

gp_domain = node[:topology][:domains][node[:domain_id]]
gp_node   = gp_domain[:nodes][node[:node_id]]
homedirs  = gp_domain[:filesystem][:dir_homes]
softdir   = gp_domain[:filesystem][:dir_software]

hadoop_dir = "#{softdir}/hadoop"
hadoop_conf_dir = "#{homedirs}/hduser/conf"
hadoop_user = "hduser"
hadoop_rc = "#{homedirs}/hduser/.hadooprc"
bash_rc = "#{homedirs}/hduser/.bashrc"

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

auth_keys = "#{homedirs}/#{hadoop_user}/.ssh/authorized_keys"
key_file = "#{homedirs}/#{hadoop_user}/.ssh/id_rsa"
pkey_file = key_file+".pub"

# Create passwordless SSH key
execute "ssh-keygen" do
  not_if do File.exists?(key_file) end
  user hadoop_user
  command "ssh-keygen -N \"\" -f #{key_file}"
  action :run
end
		
file auth_keys do
  owner hadoop_user
  mode "0644"
  action :create
end  
    
execute "add_hadoop_rc" do
  line = "source #{hadoop_rc}"
  only_if do
      File.read(bash_rc).index(line).nil?
  end  
  user "hduser"
  group "hadoop"
  command "echo \"#{line}\" >> #{bash_rc}"
  action :run
end  

template hadoop_rc do
  source "hadooprc.erb"
  mode 0644
  owner "hduser"
  group "hadoop"
  variables(
    :hadoop_dir => hadoop_dir,
    :hadoop_conf_dir => hadoop_conf_dir
  )
end

execute "add_pkey" do
  only_if do
      pkey = File.read(pkey_file)
      File.read(auth_keys).index(pkey).nil?
  end  
  user "root"
  group "root"
  command "cat #{pkey_file} >> #{auth_keys}"
  action :run
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

if ! File.exists?(hadoop_conf_dir)

  directory "#{hadoop_conf_dir}" do
    owner "hduser"
    group "hadoop"
    mode "0755"
    action :create
  end

  ruby_block "copy_config_files" do
    block do
      FileUtils.cp_r Dir.glob("#{hadoop_dir}/conf/*"), hadoop_conf_dir
    end
  end

end


gp_nodes = gp_domain[:nodes].to_hash.values
hadoop_masters = gp_nodes.select{|n| n["run_list"].include?("role[domain-hadoop-master]")}
hadoop_masters_hosts = hadoop_masters.collect{|n| n["hostname"]}
hadoop_slaves = gp_nodes.select{|n| n["run_list"].include?("role[domain-hadoop-slave]")}
hadoop_slaves_hosts = hadoop_slaves.collect{|n| n["hostname"]}

# For now, we assume only one master
primary_master = hadoop_masters_hosts[0]

cookbook_file "#{hadoop_conf_dir}/hadoop-env.sh" do
  source "hadoop-env.sh"
  mode 0644
  owner "hduser"
  group "hadoop"
end

template "#{hadoop_conf_dir}/slaves" do
  source "hostlist.erb"
  mode 0644
  owner "hduser"
  group "hadoop"
  variables(
    :hosts => hadoop_slaves_hosts
  )
end

template "#{hadoop_conf_dir}/masters" do
  source "hostlist.erb"
  mode 0644
  owner "hduser"
  group "hadoop"
  variables(
    :hosts => hadoop_masters_hosts
  )
end

template "#{hadoop_conf_dir}/core-site.xml" do
  source "core-site.xml.erb"
  mode 0644
  owner "hduser"
  group "hadoop"
  variables(
    :primary_master => primary_master
  )
end

template "#{hadoop_conf_dir}/mapred-site.xml" do
  source "mapred-site.xml.erb"
  mode 0644
  owner "hduser"
  group "hadoop"
  variables(
    :primary_master => primary_master
  )
end

template "#{hadoop_conf_dir}/hdfs-site.xml" do
  source "hdfs-site.xml.erb"
  mode 0644
  owner "hduser"
  group "hadoop"
  variables(
    :replication => hadoop_slaves_hosts.size < 3 ? hadoop_slaves_hosts.size : 3 
  )
end

