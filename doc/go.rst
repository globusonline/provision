.. _chap_go:

Adding Globus Online endpoints to your topology
***********************************************

`Globus Online <http://www.globusonline.org/>`_ (GO) is a hosted service that automates 
the tasks associated with moving files between sites, or "endpoints". If your
Globus Provision topology includes a GridFTP server, Globus Provision can
take care of setting it up as a Globus Online endpoint.

This chapter assumes that you have a GO account and that you are familiar, at least,
with GO's web interface. If this is not the case, take a look at the 
`Globus Online Quickstart Guide <https://www.globusonline.org/quickstart/>`_


.. _chap_go_sec_identity:

Authorizing an SSH or X.509 Identity in GO
==========================================

To create an endpoint in your GO account, Globus Provision will need to access
your GO account. By default, Globus Provision will do this using the 
`GO Command-Line Interface (CLI) <https://www.globusonline.org/usingcli/>`_ and,
to do so, you must authorize your SSH key in your GO profile so Globus Provision
can connect to the GO CLI server on your behalf. If you already
know how to access the GO CLI, that means that you already have an SSH key
authorized in your GO profile, and you can safely skip this section.

Globus Provision can also create the endpoint through GO's 
`Transfer API <https://transfer.api.globusonline.org/>`_. However, this requires
having an X.509 user certificate that is signed by Certificate Authority
trusted by Globus Online. If you don't have such certificate, allowing Globus
Provision to create the endpoint using the CLI will work fine. However,
if you do have a certificate, this will allow Globus Provision to use the
Transfer API, which will result in more detailed error reporting if something
goes wrong, and should be faster if you intend to create many endpoints at once.

Regardless of what option you choose, the procedure to authorize your
SSH or X.509 identity in GO is the same. `Log into Globus Online <https://www.globusonline.org/SignIn>`_,
go to *My Profile*, select *Manage Identities*, and then click on either
*Add SSH Public Key* or *Add X.509 Certificate*.


.. _sec_go_auth:

Authentication methods
======================	

When you connect to a GridFTP server (directly, not through Globus Online), you have
to *authenticate* yourself. In other words, you have to prove to the GridFTP server
that you are who you claim to be. Usually, you will do this by presenting an X.509
certificate (which the GridFTP server will validate; if it is satisfied that you
are who you claim to be, it will also check if you're actually *authorized* to 
access the server). When deploying a Globus Provision instance, all these certificates
are generated automatically for all the users in the topology so, if you're
accessing the GridFTP server from inside the domain, we can just use those.

However, when you try to access a GridFTP server through a GO endpoint, GO needs to perform
the authentication step on your behalf. To do so, we need a way to *delegate* our
identity to GO. One way of doing this is to include a MyProxy server in the domain
where we want to create an endpoint. In the simple configuration file, we do this
with the ``myproxy`` option. For example::

	[domain-simple]
	users: alice bob
	gridftp: yes
	myproxy: yes
	
If you choose MyProxy authentication in your GO endpoint, you will be able to access
the endpoint as either ``alice`` or ``bob`` (in general, as any user in that domain).
When you try to access the endpoint from GO, you will be asked for a username and
password. You must supply a valid username and password in the domain; GO will use
them when communicating with the domain's MyProxy server and, in turn, the MyProxy
server will use that username and password to verify that you are who you claim to be
(and will issue a short-term X.509 certificate, called a *proxy certificate*, that GO
can use to contact the GridFTP server).

Globus Provision does allow you to select a different type of authentication: Globus
Online authentication. Let's say your user account in GO is ``carol``. When you try
to access the endpoint from GO, it will "autoactivate" the endpoint using 
a GO certificate for user ``carol`` (you will not be asked for a username or password;
internally, GO simply contacts its own MyProxy server and requests a short-term
certificate for ``carol``; since you're logged into GO, it already trusts that you
are who you claim to be). In this case, you must make
sure that the names of the users in your domain are actual GO users (and that you
want to grant access to those users). Remember: when you try to access the endpoint,
you won't be given a choice of what username to use; GO will simply go ahead and
will "autoactivate" the endpoint using your GO identity.


Setting up a GO endpoint in a domain
====================================

To add a GO endpoint to a domain, you must supply
the name of the endpoint, and what authentication type to use. For example:

.. parsed-literal::

	[domain-simple]
	users: user1 user2
	gridftp: yes
	**go-endpoint: go-user#gp-test
	go-auth: go**
	
Notice how we've specified GO authentication. If you wanted to use MyProxy authentication,
you would have to specify ``go-auth: myproxy``, taking care that there was a MyProxy server
in your domain:

.. parsed-literal::

	[domain-simple]
	users: user1 user2
	gridftp: yes
	**myproxy: yes**
	go-endpoint: go-user#gp-test
	go-auth: **myproxy**

In either case, Globus Provision will try to contact Globus Online using the ``go-user`` account.
By default, it will do so through the GO CLI, using the SSH key in ``~/.ssh/id_rsa``. If you want
to specify a different SSH key, or want to use the Transfer API instead, you can do so in the
``[globusonline]`` section. For example, you can specify an alternate key using the
``ssh-key`` parameter::

	[globusonline]
	ssh-key = ~/.ssh/myotherkey_rsa
	
If you want to use an X.509 certificate to connect to GO through the Transfer API, then
use the ``cert-file`` and ``cert-key`` options. For example::

	[globusonline]
	cert-file = ~/.globus/usercert.pem
	key-file = ~/.globus/userkey.pem


Starting an instance with a GO endpoint
=======================================

Once you've defined the endpoint in the topology, starting an instance is no
different from what we've seen so far: Globus Provision will create the endpoints
when you run ``gp-instance-start`` and will remove them when you run
``gp-instance-terminate``.

For example, let's use this configuration file:

.. parsed-literal::

	[general]
	deploy: ec2
	domains: simple
	
	[domain-simple]
	users: go-user
	gridftp: yes
	go-endpoint: go-user#gp-test
	go-auth: go
	
	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu
	ami: |ami|
	instance-type: t1.micro

This will deploy the simplest possible endpoint: a single GridFTP server, with a
single user called ``go-user``. Since we're using GO authentication (``go-auth: go``),
make sure you replace ``go-user`` with your Globus Online username.

Just create and start the instance::

	$ gp-instance-create -c go-gridftp-ec2.conf
	Created new instance: gpi-76dd268e
	$ gp-instance-start gpi-76dd268e
	Starting instance gpi-76dd268e... done!
	Started instance in 1 minutes and 9 seconds
	
If you use the GO CLI to list your endpoints, you should see ``gp-test`` one::

	$ ssh cli.globusonline.org endpoint-list	
	gp-test     -
	home        -
	laptop      -
	go#ep1      -
	go#ep2      -
	
Now, use ``gp-instance-describe`` to get the hostname of the GridFTP server,
SSH into it, and create a file called ``gp-test.txt`` in it. If you now use
the GO CLI to check the contents of your home directory on the endpoint, you
should see that file appear::

	$ ssh cli.globusonline.org ls gp-test:/~/
	gp-test.txt
 
Once you're done with your Globus Provision instance, you can terminate it, and
the GO endpoint will be removed too:: 	

	$ gp-instance-terminate -d gpi-76dd268e
	Terminating instance gpi-76dd268e... done!
	$ ssh cli.globusonline.org endpoint-list
	home        -
	laptop      -
	go#ep1      -
	go#ep2      -
