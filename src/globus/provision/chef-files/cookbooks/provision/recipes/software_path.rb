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
## RECIPE: Global "bin" directory 
##
## Set up a domain's NFS server and its shared directories.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gp_domain = node[:topology][:domains][node[:domain_id]]
gp_node   = gp_domain[:nodes][node[:node_id]]
softdir   = gp_domain[:filesystem][:dir_software]

# Add the "bin" directory (inside the domain's software directory) to everyone's 
# environment (we do this in /etc/enviroment instead of /etc/profile.d/ 
# (which is BASH-specific) because daemons started by init scripts don't necessarily 
# load BASH environment information.
# Note that if this file is modified and "bin" is removed from the path,
# subsequent runs of Chef will replace it will a file with just the PATH variable
file "/etc/environment" do
  bin_path = "#{softdir}/bin"
  only_if do
    File.read("/etc/environment").index(/PATH=.*#{bin_path}.*/).nil?
  end
  owner "root"
  mode "0644"
  content "PATH=\"#{bin_path}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games\"\n"
end  
