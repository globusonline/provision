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
## RECIPE: R
##
## Installs the latest stable R
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

apt_repository "R" do
  uri "http://cran.us.r-project.org/bin/linux/ubuntu"
  distribution "#{node['lsb']['codename']}/"
  components []
  action :add
  keyserver "keyserver.ubuntu.com"
  key "E084DAB9"
end

package "r-base" do
  action :install
end

ruby_block "add_Rrepo" do
  file = "/etc/R/Rprofile.site"
  line = "options( repos= c( CRAN= \"http://cran.r-project.org/\"))"
  only_if do
    File.read(file).index(line).nil?
  end  
  block do
    open(file, 'a') do |f|
      f.puts line
    end  
  end
end