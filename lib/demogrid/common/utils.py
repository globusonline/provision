'''
Created on Dec 6, 2010

@author: borja
'''

import threading
import paramiko
import traceback
import select
import sys
import time
from boto.ec2.connection import EC2Connection
from os import walk, environ
import socket    
from demogrid.common import log
        
        
class MultiThread(object):
    def __init__(self, func, funcargs):
        self.num_threads = len(funcargs)
        self.done_threads = 0
        self.func = func
        self.threads = [threading.Thread(target = self.run_func, args = args) for args in funcargs]    
        self.semaphore = threading.Semaphore()
        self.done = threading.Event()

    def run_func(self, *args):
        self.func(*args)
        with self.semaphore:
            self.done_threads += 1
            if self.done_threads == self.num_threads:
                self.done.set()

    def run(self):
        self.done_threads = 0
        for t in self.threads:
            t.start()
        self.done.wait()
        
class SSH(object):
    def __init__(self, username, hostname, key_path, default_outf = sys.stdout, default_errf = sys.stderr, port=22):
        self.username = username
        self.hostname = hostname
        self.key_path = key_path
        self.default_outf = default_outf
        self.default_errf = default_errf
        self.port = port
        
    def open(self):
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connected = False
        while not connected:
            try:
                self.client.connect(self.hostname, self.port, self.username, pkey=key)
                connected = True
            except socket.error, e:
                if e.errno == 111: # Connection refused
                    time.sleep(2)
                else:
                    time.sleep(2)
            except EOFError, e:
                time.sleep(2)
        self.sftp = paramiko.SFTPClient.from_transport(self.client.get_transport())    
        
    def close(self):
        self.client.close()
        
    def run(self, command, outf=None, errf=None):
        channel = self.client.get_transport().open_session()
        
        log.debug("%s - Running %s" % (self.hostname,command))
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
                        x = channel.recv(128)
                        if not x: break
                        outf.write(x)
                        outf.flush()
                
                if outf != sys.stdout:
                    outf.close()
                    
                if errf != sys.stderr:
                    outf.close()

            rc = channel.recv_exit_status()
            log.debug("%s - Ran %s" % (self.hostname,command))
            channel.close()
            return rc
    
        except Exception, e:
            traceback.print_exc()
            try:
                channel.close()
            except:
                pass      
        
        
    def scp(self, fromf, tof):
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

    
def create_ec2_connection():
    if not (environ.has_key("AWS_ACCESS_KEY_ID") and environ.has_key("AWS_SECRET_ACCESS_KEY")):
        return None
    else:
        return EC2Connection()