.. _chap_go:

Adding Globus Online endpoints to your topology
***********************************************



::

	[globusonline]
	username = go-user
	cert-file = ~/.globus/usercert.pem
	key-file = ~/.globus/userkey.pem
	server-ca-file = ~/.globus/certificates/gd-bundle_ca.cert
	auth = go
	
	
::

	[domain-simple]
	users: user1 user2
	gridftp: yes
	go-endpoint: go-user#gp-test
	go-auth: go
	



Globus Online 101
=================	



Setting up Globus Online
========================


.. _sec_go_auth:

Authentication methods
======================	


Setting up a GO endpoint in a domain
====================================


::

	[globusonline]
	username = go-user
	cert-file = ~/.globus/usercert.pem
	key-file = ~/.globus/userkey.pem
	server-ca-file = ~/.globus/certificates/gd-bundle_ca.cert
	auth = go
	
	
::

	[domain-simple]
	users: user1 user2
	gridftp: yes
	go-endpoint: go-user#gp-test
	go-auth: go
	
	
:: 

	gp-go-register-endpoint gpi-7a4f5ec1
	
::

	Created endpoint 'go-user#gp-test' for domain 'simple'


	
