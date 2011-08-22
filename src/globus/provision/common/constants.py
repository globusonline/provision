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

EXAMPLE_DOMAIN = "grid.example.org"
EXAMPLE_SUBNET = "192.168"

EXAMPLE_GLOBAL_SUBNET = 1
EXAMPLE_DOMAIN_SUBNET_START = 100

GRID_AUTH_ROLE = "grid-auth"
SERVER_ROLE = "org-server"
LOGIN_ROLE = "org-login"
MYPROXY_ROLE = "org-auth"
GRIDFTP_ROLE = "org-gridftp"
GATEKEEPER_CONDOR_ROLE = "org-gram-condor"
GATEKEEPER_PBS_ROLE = "org-gram-pbs"
LRM_CONDOR_ROLE = "org-condor"
LRM_PBS_ROLE = "org-pbs"
LRM_NODE_CONDOR_ROLE = "org-clusternode-condor"
LRM_NODE_PBS_ROLE = "org-clusternode-pbs"

DOMAIN_NFS_SERVER = "nfs_server"      
DOMAIN_NIS_SERVER = "nis_server"      
DOMAIN_GRIFTP_SERVER = "gridftp_server"
DOMAIN_MYPROXY_SERVER = "myproxy_server"      
DOMAIN_LRMHEAD_SERVER = "lrm_head"

DOMAIN_SERVERS = (DOMAIN_NFS_SERVER, DOMAIN_NIS_SERVER, DOMAIN_GRIFTP_SERVER, DOMAIN_MYPROXY_SERVER, DOMAIN_LRMHEAD_SERVER)