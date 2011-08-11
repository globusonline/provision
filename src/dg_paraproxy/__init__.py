# -*- encoding: utf-8
# Copyright (C) 2009-2011  Rene Koecher <shirk@bitspin.org>
#
# This file is part of paraproxy.
#
# Paraproxy is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paraproxy is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with paraproxy; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import paramiko

import re
import os
import time
import socket
import signal
import thread
import fnmatch
import getpass
import subprocess
import shlex
import StringIO

from WrapSock import WrapSock

# for  debugging
__paramiko_SSHClient_connect_verbose = os.getenv('PARAMIKO_SSH_HOOK_VERBOSE', False)

# hook for original SSHClient.connect function
__paramiko_SSHClient_connect_hook = globals()['paramiko'].SSHClient.connect
# hook for original SSHClient.close function
__paramiko_SSHClient_close_hook = globals()['paramiko'].SSHClient.close
# hook for original SSHClient.__del__ function (if any)
try:
	__paramkio_SSHClient_delete_hook = globals()['paramiko'].SSHClient.__del__
except AttributeError:
	__paramiko_SSHClient_delete_hook = None

# list with configured proxy-commands / ssh option etc.
__paramiko_SSHClient_proxy_config = paramiko.SSHConfig()

# Import paramiko internals with prefix (__.*)
from paramiko.hostkeys import HostKeys as __HostKeys
from paramiko.resource import ResourceManager as __ResourceManager
from paramiko.transport import Transport as __Transport
from paramiko.ssh_exception import SSHException, BadHostKeyException

def __paramiko_SSHClient_debug(msg):
	if __paramiko_SSHClient_connect_verbose:
		print '[%s] %s' % (os.getpid(), msg)

def __paramiko_SSHClient_proxy_cmdchain(self, hostname, rec=0):
	"""
	Resolver used to detect multi-layer ProxyCommand chains

	This will search for hostname in proxy_list, if found
	add the assigned ProxyCommand to the chain and check if it it turn
	requires a ProxyCommand

	Chain detection depends on the command to be 'ssh'/'ssh.exe' (absolute paths are supported)
	"""
	chain = []
	command = __paramiko_SSHClient_proxy_config.lookup(hostname).get('proxycommand')
	port = __paramiko_SSHClient_proxy_config.lookup(hostname).get('port', '22')
	hostname = __paramiko_SSHClient_proxy_config.lookup(hostname).get('hostname', hostname)
	if not command:
		if rec != 0:
			__paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): hop_%d: %s:%s, DIRECT' % (rec,hostname,port))
			return [(hostname, 'DIRECT', None)]
		return []

	# command found
	try:
		#__paramiko_SSHClient_debug('processing "%s"' % command)
		command_args = [] + shlex.split(command)

		exe = os.path.basename(command_args[0].lower())
		if exe.lower() == 'ssh' or exe.lower() == 'ssh.exe':
			# command is SSH, extract the host and the remote command
			remote_cmd = command_args.pop()
			remote_host = command_args.pop()
			if '@' in remote_host:
			    proxyuser, remote_host = remote_host.split("@")
			else:
			    proxyuser = None

			chain = [(remote_host, remote_cmd.replace('%h', hostname).replace('%p', port), proxyuser)]
			next_hop = __paramiko_SSHClient_proxy_cmdchain(self, remote_host, rec+1)

			if next_hop:
				chain = next_hop + chain
		else:
			# a regular command like netcat
			chain = [(hostname, command.replace('%h', hostname).replace('%p', port), None)]
			if rec != 0:
			    __paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): WARNING: regular command "%s" for "%s" will be run in hop_%d'  % (command, hostname, rec))
			    __paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): WARNING: paraproxy doesn\'t know how to chain further from here.')
			return chain
	except Exception,e:
		#FIXME: propper handling!
		 __paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): ERROR: failed to parse ProxyCommand for host "%s" - abort!' % (hostname))
		 raise

	if rec != 0:
		__paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): hop_%d: %s:%s' % (rec,hostname, port))
	else:
		__paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): target: %s:%s' % (hostname, port))
		__paramiko_SSHClient_debug('__paramiko_SSHClient_proxy_cmdchain(): final chain: %s' % (' => '.join([('(%s, %s)' % (x[0],x[1])) for x in chain])))

	return chain

def __paramiko_SSHClient_proxy_thread(self, ip, port, command):
	"""
	Proxy thread used to establish a connection using a ssh ProxyCommand.
	
	This will open a unix-domain-socket and listen for one incomming connection.
	After this it will spawn the proxy command an wrap the open socket to act
	as stdin and stdout for the new process.
	"""
	__paramiko_SSHClient_debug('proxy_thread(%s,%s)' % (ip, port))
	self._sock_name = os.path.join(os.path.sep,'tmp', '.paramiko_proxy_%s_%s_%s' % (ip, port, os.getpid()))
	self._should_terminate = False

	try:
		os.unlink(self._sock_name)
	except OSError:
		pass
	
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	sock.bind(self._sock_name)
	sock.listen(1)
	__paramiko_SSHClient_debug('proxy: bound to `%s` and listening' % self._sock_name)
	
	(stmp, addr) = sock.accept()
	__paramiko_SSHClient_debug('proxy: incomming connection')
	
	cmd_str = str(command) # copy
	self._proc_id = None
	wrap_sock = WrapSock(stmp)

	try:
		__paramiko_SSHClient_debug('proxy: executing command "%s"' % cmd_str.replace('%h', str(ip)).replace('%p', str(port)))

		proc = subprocess.Popen(cmd_str.replace('%h', str(ip)).replace('%p', str(port)),
								shell=True,
								stdin=wrap_sock,
								stdout=wrap_sock,
								close_fds=True)
	
		self._proc_id = proc.pid
		self._sock_state = 1

		# warten auf Beendigung der Verbindung
		while proc.poll() == None \
		      and not self._should_terminate:
			time.sleep(0.5)

		if self._should_terminate:
			__paramiko_SSHClient_debug('proxy: termination requested..')
		else:
			__paramiko_SSHClient_debug('proxy: ProxyCommand terminated, exit code: %s' % proc.returncode)

		del proc

	except OSError, e:
		__paramiko_SSHClient_debug('proxy: OSError in Popen: %s' % e)
	
	except ValueError, e:
		__paramiko_SSHClient_debug('proxy: ValueError in Popen: %s' % e)

	wrap_sock.close()
	sock.close()
	
	try:
		os.unlink(self._sock_name)
	except OSError,e:
		__paramiko_SSHClient_debug('proxy: error unlinking %s: %s' % (self._sock_name, str(e)))
	
	self._proc_id = None
	__paramiko_SSHClient_debug('proxy: ~proxy_thread()')


def __paramiko_SSHClient_connect(self, hostname, port=22, username=None,
				 password=None, pkey=None, key_filename=None,
				 timeout=None, allow_agent=True, look_for_keys=True):
	"""
	Hook function to enable Paramiko's SSHClient to work with ssh ProxyCommand.
	This will only hook into connections matching one of the ProxyRules.
	"""

	def __create_and_connect_transport(self, _hostname, _transport_sock, _username=None, _password=None):
		"""
		Helper function to create a new Transport and perform the required SSH authentication
		-- just here to keep the code more readable
		"""
		#print 'Create transport on: %s' % _transport_sock
		t = self._transport = __Transport(_transport_sock)
		self._chained_transports.append(t)

		if self._log_channel is not None:
			t.set_log_channel(self._log_channel)

		t.start_client()
		__ResourceManager.register(self, t)
		
		server_key = t.get_remote_server_key()
		keytype = server_key.get_name()
		
		our_server_key = self._system_host_keys.get(_hostname, {}).get(keytype, None)
		if our_server_key is None:
			our_server_key = self._host_keys.get(_hostname, {}).get(keytype, None)
		if our_server_key is None:
			# will raise exception if the key is rejected; let that fall out
			self._policy.missing_host_key(self, _hostname, server_key)
			# if the callback returns, assume the key is ok
			our_server_key = server_key
	
		if server_key != our_server_key:
			raise BadHostKeyException(_hostname, server_key, our_server_key)
	
		if _username is None:
			_username = getpass.getuser()
	
		if key_filename is None:
			key_filenames = []
		elif isinstance(key_filename, (str, unicode)):
			key_filenames = [ key_filename ]
		else:
			key_filenames = key_filename

		self._auth(_username, _password, pkey, key_filenames, allow_agent, look_for_keys)
	#---

	__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(%s, %s)' % (hostname, port))
	command = __paramiko_SSHClient_proxy_config.lookup(hostname).get('proxycommand')
	
	if not command:
		__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): direct connection.')
		return __paramiko_SSHClient_connect_hook(self, hostname, port, username, password, pkey,
							 key_filename, timeout, allow_agent, look_for_keys)

	command_chain = __paramiko_SSHClient_proxy_cmdchain(self, hostname)

	if len(command_chain) > 1:
		__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): using multi-layer chain with %d hops' % (len(command_chain) - 1))
	else:
		__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): using ProxyCommand `%s`' % command)

	self._sock_name = ''
	self._sock_state = 0
	self._proc_id = 0
	self._should_terminate = False
	self._chained_transports = []

	if not command_chain:
		thread.start_new(__paramiko_SSHClient_proxy_thread, (self, hostname, port, command))
		time.sleep(1)
		
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		if timeout is not None:
			try:
				sock.settimeout(timeout)
			except:
				pass

		try:
			sock.connect(self._sock_name) # set by proxy_thread
			__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): connected to proxy thread on `%s`' % self._sock_name)
			while self._sock_state == 0:
				time.sleep(0.5)

		except Exception, e:
			# except *anything* to be able to remove the proxy thread.
			__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): caught %s - closing threads.' % e.__class__.__name__)

			try:
				if (self._proc_id):
					__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): requesting thread shutdown')
					self._should_terminate = True
				else:
					__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): os._proc_id <= 0, nothing to do.')
			except OSError:
				pass

			raise

	else:
		(proxy_host, proxy_command, proxy_username) = command_chain.pop(0)
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if timeout is not None:
			try:
				sock.settimeout(timeout)
			except:
				pass

		# no try: except: here - just raise any socke errors
		proxy_port = long(__paramiko_SSHClient_proxy_config.lookup(proxy_host).get('port', '22'))
		sock.connect((proxy_host, proxy_port))
		__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): connected to `%s:%s`' % (proxy_host, proxy_port))

	try:
		transport_sock = sock
		while command_chain:
			if command_chain[0][2] == None:
				proxy_user = username
			else:
				proxy_user = command_chain[0][2]
			__create_and_connect_transport(self, command_chain[0][0], transport_sock, proxy_user, password)
			# this hop is now valid, execute the ProxyCommand
			(proxy_host, proxy_command, proxy_username) = command_chain.pop(0)

			__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): connected to %s, sending command: %s' % (proxy_host, proxy_command))
			transport_sock = self._transport.open_session()
			__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): next transport_sock: %s' % transport_sock)
			transport_sock.exec_command(proxy_command)

		# final connection, always executed
		__create_and_connect_transport(self, hostname, transport_sock, username, password)
	except Exception, e:
		# except *anything* to be able to remove the proxy thread.
		__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): caught %s - closing threads.' % e.__class__.__name__)

		try:
			if (self._proc_id):
				__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): requesting thread shutdown')
				self._should_terminate = True
			else:
				__paramiko_SSHClient_debug('__paramiko_SSHClient_connect(): os._proc_id <= 0, nothing to do.')
		except OSError:
			pass

		raise

	__paramiko_SSHClient_debug('~__paramiko_SSHClient_connect()')

def __paramiko_SSHClient_close(self):
	__paramiko_SSHClient_debug('__paramiko_SSHClient_close(): begin closing.')
	try:
		if self._chained_transports:
			self._transport = None
			while self._chained_transports:
				__paramiko_SSHClient_debug('__paramiko_SSHClient_close(): remove hop transport..')
				t = self._chained_transports.pop(0).close()
				del t
	except AttributeError:
	    pass

	__paramiko_SSHClient_close_hook(self)
	try:
		while self._proc_id:
			self._should_terminate = True
			time.sleep(0.5)
		
	except AttributeError:
		pass
	
	try:
		if os.path.exists(self._sock_name):
			os.unlink(self._sock_name)
			__paramiko_SSHClient_debug('~__paramiko_SSHClient_close(): unlink %s successful.' % self._sock_name)
	except OSError,e:
		__paramiko_SSHClient_debug('~__paramiko_SSHClient_close(): error unlinking %s: %s' % (self._sock_name, str(e)))
	except AttributeError:
		pass

	__paramiko_SSHClient_debug('__paramiko_SSHClient_close(): finished closing.')

def __paramiko_SSHClient_delete(self):
	__paramiko_SSHClient_debug('__paramiko_SSHClient_delete(): begin destruction.')
	try:
		if self._chained_transports:
			self._transport = None
			while self._chained_transports:
				__paramiko_SSHClient_debug('__paramiko_SSHClient_delete(): remove hop transport..')
				t = self._chained_transports.pop(0).close()
				del t
	except AttributeError:
	    pass

	try:
		while self._proc_id:
			self._should_terminate = True
			time.sleep(0.5)
		
	except AttributeError:
		pass
	
	try:
		if os.path.exists(self._sock_name):
			os.unlink(self._sock_name)
			__paramiko_SSHClient_debug('~__paramiko_SSHClient_delete(): unlink %s successful.' % self._sock_name)
	except OSError,e:
		__paramiko_SSHClient_debug('__paramiko_SSHClient_delete(): error unlinking %s: %s' % (self._sock_name, str(e)))
	except AttributeError:
		pass
	
	if __paramiko_SSHClient_delete_hook:
		__paramiko_SSHClient_delete_hook(self)

	__paramiko_SSHClient_debug('~__paramiko_SSHClient_delete(): finished destruction.')

# parse ssh_config
merged_config = StringIO.StringIO()
for conf_file in [os.path.join(os.path.sep, 'etc', 'ssh', 'ssh_config'),
			       os.path.join(os.getenv('HOME','/tmp'), '.ssh', 'config')]:
	try:
		config = open(conf_file)
		merged_config.write(config.read())
		merged_config.write('\n')
		config.close()
		del config

	except IOError,e:
		pass

merged_config.seek(0,0)
__paramiko_SSHClient_proxy_config.parse(merged_config)
del merged_config

# finally modify SSHClient to use our connect hook
setattr(globals()['paramiko'].SSHClient, 'connect', __paramiko_SSHClient_connect)
setattr(globals()['paramiko'].SSHClient, 'close'  , __paramiko_SSHClient_close)
setattr(globals()['paramiko'].SSHClient, '__del__', __paramiko_SSHClient_delete)

__paramiko_SSHClient_debug('Hookhookhook')

