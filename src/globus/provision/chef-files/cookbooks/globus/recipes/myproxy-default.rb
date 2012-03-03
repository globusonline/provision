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
## RECIPE: Globus Toolkit 5.1.1 MyProxy
##
## Installs a MyProxy server, and sets is up as a xinetd service.
##
## For authentication, the MyProxy server will use the local UNIX accounts
## through PAM. If the node this recipe is applied to is part of a NIS
## domain, then the global NIS accounts will be used.
##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

include_recipe "globus::repository"
include_recipe "globus::myproxy-common"

template "/etc/xinetd.d/myproxy" do
  source "xinetd.myproxy.erb"
  mode 0644
  owner "root"
  group "root"
  variables(
    :gc        => false
  )
  notifies :restart, "service[xinetd]"
end

service "xinetd"
