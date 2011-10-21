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
## RECIPE: Hadoop slave node
##
## Set up a Hadoop slave node.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gp_domain = node[:topology][:domains][node[:domain_id]]

if gp_domain[:nfs_server]
    softwaredir = "/nfs/software/"
else
    softwaredir = "/usr/local/"
end

rlibs_dir = "#{softwaredir}/Rlibs"

execute "install_RJSONIO" do
  user "root"
  group "root"
  command "Rscript -e 'install.packages( c(\"RJSONIO\"), lib = \"#{rlibs_dir}\" )'"
  action :run
  not_if "Rscript -e 'q(status=!is.element(\"RJSONIO\", installed.packages(lib.loc = \"#{rlibs_dir}\")[,\"Package\"]))'"
end  	

execute "install_itertools" do
  user "root"
  group "root"
  command "Rscript -e 'install.packages( c(\"itertools\"), lib = \"#{rlibs_dir}\" )'"
  action :run
  not_if "Rscript -e 'q(status=!is.element(\"itertools\", installed.packages(lib.loc = \"#{rlibs_dir}\")[,\"Package\"]))'"
end  	

execute "install_digest" do
  user "root"
  group "root"
  command "Rscript -e 'install.packages( c(\"digest\"), lib = \"#{rlibs_dir}\" )'"
  action :run
  not_if "Rscript -e 'q(status=!is.element(\"digest\", installed.packages(lib.loc = \"#{rlibs_dir}\")[,\"Package\"]))'"
end  	

remote_file "#{node[:scratch_dir]}/rmr.tar.gz" do
  source "https://s3.amazonaws.com/rhadoop/master/rmr_1.0.1.tar.gz"
  owner "root"
  group "root"    
  mode "0644"
  not_if "Rscript -e 'q(status=!is.element(\"rmr\", installed.packages(lib.loc = \"#{rlibs_dir}\")[,\"Package\"]))'"
end

execute "rmr_install" do
  user "root"
  group "root"
  command "R CMD INSTALL #{node[:scratch_dir]}/rmr.tar.gz -l #{rlibs_dir}"
  action :run
  not_if "Rscript -e 'q(status=!is.element(\"rmr\", installed.packages(lib.loc = \"#{rlibs_dir}\")[,\"Package\"]))'"
end  	
