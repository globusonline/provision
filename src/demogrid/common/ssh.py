import sys
import paramiko
import time
import select
import os.path
import traceback

# Try to use our patched version of paraproxy only if
# it is available. If it isn't, ProxyCommand support
# will simply be unavailable
try:
    import dg_paraproxy
except:
    pass

from Crypto.Random import atfork

from demogrid.common import log
from os import walk

class SSHCommandFailureException(Exception):
    def __init__(self, ssh, command):
        self.ssh = ssh
        self.command = command
        
        
class SSH(object):
    def __init__(self, username, hostname, key_path, default_outf = sys.stdout, default_errf = sys.stderr, port=22):
        self.username = username
        self.hostname = hostname
        self.key_path = key_path
        self.default_outf = default_outf
        self.default_errf = default_errf
        self.port = port
        
    def open(self, timeout = 180):
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        connected = False
        remaining = timeout
        while not connected:
            try:
                if remaining < 0:
                    raise Exception("SSH timeout")
                else:
                    atfork()
                    self.client = paramiko.SSHClient()
                    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self.client.connect(self.hostname, self.port, self.username, pkey=key)
                    connected = True
            except Exception, e:
                if remaining - 2 < 0:
                    raise e
                else:
                    time.sleep(2)
                    remaining -= 2

        self.sftp = paramiko.SFTPClient.from_transport(self.client.get_transport())    
        
    def close(self):
        self.client.close()
        
    def run(self, command, outf=None, errf=None, exception_on_error = True, expectnooutput=False):
        channel = self.client.get_transport().open_session()
        
        log.debug("%s - Running %s" % (self.hostname,command))
        
        if expectnooutput:
            outf = None
            errf = None
        else:
            if outf != None:
                outf = open(outf, "w")
            else:
                outf = self.default_outf
        
            if errf != None:
                errf = open(errf, "w")
            else:
                errf = self.default_errf
            
        try:
            channel.exec_command(command)
    
            if outf != None or errf != None:
                while True:
                    rl, wl, xl = select.select([channel],[],[])
                    if len(rl) > 0:
                        # Must be stdout
                        x = channel.recv(1)
                        if not x: break
                        outf.write(x)
                        outf.flush()
                
                if outf != sys.stdout:
                    outf.close()
                    
                if errf != sys.stderr:
                    outf.close()
            
            log.debug("%s - Waiting for exit status: %s" % (self.hostname,command))
            rc = channel.recv_exit_status()
            log.debug("%s - Ran %s" % (self.hostname,command))
            channel.close()
        except Exception, e:
            raise # Replace by something more meaningful
         
        if exception_on_error and rc != 0:
            raise SSHCommandFailureException(self, command)
        else:
            return rc
    

        
        
    def scp(self, fromf, tof):
        # Create directory if it does not exist
        try:
            self.sftp.stat(os.path.dirname(tof))
        except IOError, e:
            pdirs = get_parent_directories(tof)
            for d in pdirs:
                try:
                    self.sftp.stat(d)
                except IOError, e:
                    self.sftp.mkdir(d)        
        try:
            self.sftp.put(fromf, tof)
        except Exception, e:
            traceback.print_exc()
            try:
                self.close()
            except:
                pass
        log.debug("scp %s -> %s:%s" % (fromf, self.hostname, tof))
        
    def scp_dir(self, fromdir, todir):
        for root, dirs, files in walk(fromdir):
            todir_full = todir + "/" + root[len(fromdir):]
            try:
                self.sftp.stat(todir_full)
            except IOError, e:
                self.sftp.mkdir(todir_full)
            for f in files:
                fromfile = root + "/" + f
                tofile = todir_full + "/" + f
                self.sftp.put(fromfile, tofile)
                log.debug("scp %s -> %s:%s" % (fromfile, self.hostname, tofile))

def get_parent_directories(filepath):
    dir = os.path.dirname(filepath)
    dirs = [dir]
    while dir != "/":
        dir = os.path.dirname(dir)
        dirs.append(dir)
    dirs.reverse()
    return dirs
    