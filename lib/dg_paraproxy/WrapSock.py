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

import socket

class WrapSock(object):
	"""
	Wrap a unix domain socket into a file-like object.
	"""
	def __init__(self, sock):
		self._sock = sock
		
	def __getattribute__(self, attr):
#		print 'getattr %s' % attr
		try:
			return super(WrapSock, self).__getattribute__(attr)
		except AttributeError:
			return super(WrapSock, self).__getattribute__('_sock').__getattribute__(attr)
	
	def dup(self):
		return WrapSock(self._sock.dup())
	
	def read(self, *args):
		return self._sock.recv(*args)
	
	def write(self, *args):
		return self._sock.send(*args)

