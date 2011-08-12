import subprocess
from optparse import OptionParser
import os
import os.path
import getpass
from globus.provision.common import defaults
from globus.provision.common import log

class Command(object):
    
    def __init__(self, argv, root = False):
        
        if root:
            if getpass.getuser() != "root":
                print "Must run as root"
                exit(1)
                
        self.argv = argv
        self.optparser = OptionParser()
        self.opt = None
        self.args = None
        
        self.optparser.add_option("-v", "--verbose", 
                                  action="store_true", dest="verbose", 
                                  help = "Produce verbose output.")

        self.optparser.add_option("-d", "--debug", 
                                  action="store_true", dest="debug", 
                                  help = "Write debugging information. Implies -v.")     

        self.optparser.add_option("-i", "--instances-dir", 
                                  action="store", type="string", dest="dir", 
                                  default = defaults.INSTANCE_LOCATION,
                                  help = "Location of the instance database.")              

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
        print " \033[1;31mERROR\033[0m: %s" % what
        print "\033[1;37mReason\033[0m: %s" % reason
        
    def cleanup_after_kill(self):
        print "Globus Provision has been unexpectedly killed and may have left resources"
        print "in an unconfigured state. Use gp-terminate to release resources."
        