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

"""
The CLI: A console frontend to Globus Provision that allows a user to request instances, 
start them, etc.
"""

import subprocess
from optparse import OptionParser, OptionGroup
import os
import os.path
import getpass
import colorama
from globus.provision.common import defaults
from globus.provision.common import log
from globus.provision import RELEASE

class Command(object):
    """Base class for all Globus Provisioning commands"""
    
    def __init__(self, argv, root = False):
        
        if root:
            if getpass.getuser() != "root":
                print "Must run as root"
                exit(1)
                
        self.argv = argv
        self.optparser = OptionParser(version = RELEASE)
        self.opt = None
        self.args = None
        
        common_opts = OptionGroup(self.optparser, "Common options", "These options are common to all Globus Provision commands")
        self.optparser.add_option_group(common_opts)
        
        common_opts.add_option("-v", "--verbose", 
                                  action="store_true", dest="verbose", 
                                  help = "Produce verbose output.")

        common_opts.add_option("-d", "--debug", 
                                  action="store_true", dest="debug", 
                                  help = "Write debugging information. Implies -v.")     

        common_opts.add_option("-i", "--instances-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.INSTANCE_LOCATION,
                                  help = "Use this directory to store information about the instances "
                                         "(instead of the default ~/.globusprovision/instances/)")
        
        colorama.init(autoreset = True)
                

    def parse_options(self):
        opt, args = self.optparser.parse_args(self.argv)

        self.opt = opt
        self.args = args
        
        if self.opt.debug:
            loglevel = 2
        elif self.opt.verbose:
            loglevel = 1
        else:
            loglevel = 0
            
        log.init_logging(loglevel)
        
    def _run(self, cmd, exit_on_error=True, silent=True):
        if silent:
            devnull = open("/dev/null")
        cmd_list = cmd.split()
        if silent:
            retcode = subprocess.call(cmd_list, stdout=devnull, stderr=devnull)
        else:
            retcode = subprocess.call(cmd_list)
        if silent:
            devnull.close()
        if retcode != 0 and exit_on_error:
            print "Error when running %s" % cmd
            exit(1)        
        return retcode
    
    def _check_exists_file(self, filename):
        if not os.path.exists(filename):
            print "File %s does not exist" % filename
            exit(1)
            
    def _print_error(self, what, reason):
        print colorama.Fore.RED + colorama.Style.BRIGHT + " \033[1;31mERROR\033[0m",
        print ": %s" % what
        print colorama.Fore.WHITE + colorama.Style.BRIGHT + "\033[1;37mReason\033[0m",
        print ": %s" % reason
        
    def cleanup_after_kill(self):
        print "Globus Provision has been unexpectedly killed and may have left resources"
        print "in an unconfigured state. Use gp-terminate to release resources."
        