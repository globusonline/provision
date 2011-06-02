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

# Default attributes.
# For now, only directories where software is going to be installed.

default[:globus][:dir] = "/usr/local/globus-5.0.3"
default[:galaxy][:dir] = "/nfs/software/galaxy"
default[:blast][:dir] = "/nfs/software/blast"
default[:globus][:srcdir] = "/var/tmp/gt5.0.3-all-source-installer"
default[:globus][:simpleCA] = "/home/globus/.globus/simpleCA"
default[:globus][:rootsimpleCA] = "/root/.globus/simpleCA"
default[:condor][:package32] = "condor-7.6.0-1-deb_5.0_i386.deb"
default[:condor][:package64] = "condor-7.6.0-1-deb_5.0_amd64.deb"
default[:torque][:dir] = "/var/spool/torque"
default[:openmpi][:dir] = "/usr/local/openmpi-1.4.3"


