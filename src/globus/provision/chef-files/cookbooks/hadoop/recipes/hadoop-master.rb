# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                      #
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
## RECIPE: Hadoop master node
##
## Set up a Hadoop master node.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gp_domain = node[:topology][:domains][node[:domain_id]]

# The hadoop_master attribute is part of the generated topology.rb file,
# and contains the FQDN of the master node.
server = gp_domain[:hadoop_master]

directory "/mnt/hadoop" do
  owner "hduser"
  group "hadoop"
  mode "0750"
  recursive true
  action :create
end

# Force host key to be added to known_hosts
execute "ssh-localhost" do
  user "hduser"
  command "ssh -o StrictHostKeyChecking=no `hostname --fqdn` echo"
  action :run
end

#TODO
#export HADOOP_CONF_DIR=/nfs/home/hduser/conf/
#export HADOOP_HOME=/nfs/software/hadoop/
#/nfs/software/hadoop/bin/hdfs namenode -format
#/nfs/software/hadoop/bin/start-dfs.sh
#/nfs/software/hadoop/bin/start-mapred.sh
