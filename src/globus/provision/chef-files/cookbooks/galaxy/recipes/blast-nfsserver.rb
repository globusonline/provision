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

gp_domain = node[:topology][:domains][node[:domain_id]]
softdir   = gp_domain[:filesystem][:dir_software]
blast_dir = "#{softdir}/#{node[:blast][:dir]}"

if ! File.exists?(blast_dir)

  directory "#{blast_dir}" do
    owner "root"
    group "root"
    mode "0755"
    action :create
  end
  
  remote_file "#{node[:scratch_dir]}/blast.tar.gz" do
    source "http://mirrors.vbi.vt.edu/mirrors/ftp.ncbi.nih.gov/blast/executables/blast+/2.2.25/ncbi-blast-2.2.25+-ia32-linux.tar.gz"
    owner "root"
    group "root"
    mode "0644"
  end  

  execute "tar" do
    user "root"
    group "root"
    command "tar xzf #{node[:scratch_dir]}/blast.tar.gz --strip-components=1 --directory #{blast_dir}"
    action :run
  end  	
  
  link "/nfs/software/bin/blastp" do
    to "#{blast_dir}/bin/blastp"
  end

end
  
