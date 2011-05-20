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

if ! File.exists?(node[:blast][:dir])

  directory "#{node[:blast][:dir]}" do
    owner "root"
    group "root"
    mode "0755"
    action :create
  end
  
  cookbook_file "/var/tmp/blast.tar.gz" do
    source "ncbi-blast-2.2.25+-ia32-linux.tar.gz"
    owner "root"
    group "root"
    mode "0644"
  end  

  execute "tar" do
    user "root"
    group "root"
    command "tar xzf /var/tmp/blast.tar.gz --strip-components=1 --directory #{node[:blast][:dir]}"
    action :run
  end  	

end
  
