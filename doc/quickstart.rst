Quickstart Guide
****************

::

	[general]
	deploy: ec2
	domains: simple
	
	[domain-simple]
	users: user1 user2
	gridftp: yes

	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu
	ami: ami-7d28e914
	instance-type: t1.micro


::

	gp-create -c single-gridftp-ec2.conf

::

	Created new instance: gpi-52d4c9ec


::

	gp-start gpi-52d4c9ec
	
::

	Starting instance gpi-52d4c9ec...	
	
::

	gp-describe-instance gpi-52d4c9ec
	
::
	
	gpi-52d4c9ec: Starting
	
	Domain 'simple'
	    simple-gridftp  Starting    

::

	gpi-52d4c9ec: Configuring
	
	Domain 'simple'
	    simple-gridftp  Configuring  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X

::

	Starting instance gpi-52d4c9ec... done!
	Started instance in 1 minutes and 22 seconds

::

	gpi-52d4c9ec: Running
	
	Domain 'simple'
	    simple-gridftp  Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X

::

	ssh user1@ec2-N-N-N-N.compute-1.amazonaws.com
	

::

	grid-proxy-init
	
::

	Your identity: /O=Grid/OU=Globus Provision (generated)/CN=user1
	Creating proxy ..................................................................... Done
	Your proxy is valid until: Wed Aug 17 04:30:07 2011
	
::
	
	globus-url-copy gsiftp://`hostname --fqdn`/etc/hostname ./
	
::

	gp-terminate gpi-52d4c9ec

::

	Terminating instance gpi-52d4c9ec... done!
	
