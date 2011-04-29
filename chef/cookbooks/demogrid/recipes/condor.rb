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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# RECIPE: Condor common actions
#
# This recipe is a dependency of condor_head and condor_worker, which will set
# up a Condor head node or worker node. This recipe handles all the actions
# that are common to both.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Needed by the Condor deb package
package "libc6-amd64" do
  action :install
end

cookbook_file "/var/tmp/#{node[:condor][:package]}" do
  source "#{node[:condor][:package]}"
  mode 0755
  owner "root"
  group "root"
end

package "condor" do
  action :install
  provider Chef::Provider::Package::Dpkg
  source "/var/tmp/#{node[:condor][:package]}"
end

