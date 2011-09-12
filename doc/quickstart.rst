.. _chap_quickstart:

Quickstart Guide
****************

This guide is meant to get you up and running right away. It is written as a standalone document,
so we do not assume that you've read the :ref:`chap_intro` (if you have, you'll only see a few
bits of repeated content).

To get you started right away, we do make a few assumptions:

* You are using a fairly recent Linux distribution or Mac OS X.
* You must have `Python <http://www.python.org/>`_ (version 2.6 or higher) and 
  `Python Distribute <http://packages.python.org/distribute/>`_
  installed on your machine (or you must be able to install them). Most Linux distributions already
  include Python, often with the Distribute package included. Ultimately, you must be able to run the
  ``easy_install`` command.
* You must already have an `Amazon AWS <http://aws.amazon.com/>`_ account, and you should be familiar 
  with `Amazon EC2 <http://aws.amazon.com/ec2/>`_. More specifically, you should have (or know how to get) 
  a secret access key and an SSH keypair for your EC2 account.
  
If you do not meet these requirements, you may want to skip to the next chapters, which provide
much more detailed instructions on how to get started with Globus Provision (including instructions on
how to get an Amazon AWS account, and how to install Globus Provision if you don't have Python
or Setuptools installed). Nonetheless, you may still want to read through this quickstart guide, even if
you can't perform the steps yourself, to get a sense for what Globus Provision does.

If you do meet these requirements, let's dive right in! 

Installing Globus Provision
===========================

You can install Globus Provision by running the following as ``root``::

	easy_install -U globus-provision

This will install not just Globus Provision, but also all the packages it depends on.
	
.. note::
	If you are using Ubuntu or Mac OS X, you will likely just need to run this::
	
		sudo easy_install -U globus-provision
		
	If you do not have administrative privileges on your machine, you will have to install Globus
	Provision under your regular user account. You can find instructions on this in the :ref:`chap_install`
	chapter.

Defining a simple topology
==========================

Globus Provision allows you to deploy fully-configured Globus systems "in the cloud" (more specifically,
we will be deploying them on Amazon EC2). The system you deploy could be something as simple as a
single GridFTP server, or something as complicated as 20 Condor clusters, each with a GRAM and MyProxy
server (e.g., if you were teaching a workshop, and wanted to give each student access to their own
cluster to play with). 

In Globus Provision lingo, the specification of such a system is called a *topology*. As you'll see in the 
following chapters, Globus Provision allows you to define many aspects of a topology: whether it should have
a shared filesystem, what users should be created, whether those users must have X.509 certificates, 
what software should be installed on each machine, etc.

However, we'll start with the simplest possible topology: a single GridFTP server with two users 
(``user1`` and ``user2``) that are authorized to access that server. We can specify this topology
using the following file::

	[general]
	deploy: ec2
	domains: simple
	
	[domain-simple]
	users: user1 user2
	gridftp: yes

This is an example of Globus Provision's *simple topology* file format. It provides a simple and
high-level format for specifying topologies. In this particular case, we are doing the following:

* We are specifying a single *domain* called ``simple``. A topology can be divided into multiple
  domains, each with its own set of users, Globus services, etc. For example, if we wanted to deploy
  20 separate Condor clusters (each with its own GRAM and MyProxy server), we would need to define
  20 separate domains.
* The ``simple`` domain is configured to have two users (``user1`` and ``user2``) and a GridFTP server.

The simple topology format is a good way of getting started, but it can be too constrained for more
complex topologies. As you'll see in the following chapters, Globus Provision also provides a much 
richer and versatile JSON format for specifying topologies (in fact, the simple topology format
gets translated internally into the JSON format).


Setting the EC2 parameters
==========================

The topology file shown above specifies that the topology must be deployed using Amazon EC2 (``deploy: ec2``),
so we need to provide some EC2 parameters that will allow Globus Provision to use your Amazon EC2
account to deploy this topology. More specifically, you will need an 
`Access Key ID and Secret Access Key <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-credentials.html#using-credentials-access-key>`_
and an `SSH Keypair <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-credentials.html#using-credentials-keypair>`_.
We suggest that you create a keypair called ``gp-key``, and save the keypair file as ``~/.ec2/gp-key.pem``, since many of the sample files assume that naming.

You will need to add the following to the topology file:

.. parsed-literal::

	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu
	ami: |ami|
	instance-type: t1.micro

Notice how we are telling Globus Provision to use your ``gp-key`` keypair, to use ``t1.micro`` instances
(which only cost $0.02 per hour), and to use Globus Provision's AMI (|ami|). This is an Ubuntu
11.04 AMI that we provide with many software packages preinstalled, which considerably speeds up
the deployment of topologies. The latest AMI is always listed on the Globus Provision website.

Finally, save the entire topology file (with the ``[general]`` and ``[domain-simple]`` sections shown
earlier *and* the ``[ec2]`` section shown above) as ``single-gridftp-ec2.conf``. You will also need
to export your Access Key ID and Secret Key as environment variables 
``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``, respectively. For example:

::

	export AWS_ACCESS_KEY_ID=FOOBAR123FOOBAR123
	export AWS_SECRET_ACCESS_KEY=FoOBaZ123/FoOBaZ456FoOBaZ789FoOBaZ012FoOBaZ345

.. _chap_quickstart_sec_create:

Creating and launching a Globus Provision instance
==================================================

Ok, we're ready to actually launch this topology. The first step is to create a *Globus Provision instance*
with that topology:

::

	gp-instance-create -c single-gridftp-ec2.conf

This should immediately return the following:

::

	Created new instance: gpi-52d4c9ec

The ``gp-instance-create`` command doesn't actually deploy the topology, but simply validates that the topology 
is correct, and creates an entry for it in a database. This entry is called an *instance*. You can think
of the topology as a specification of what you want to deploy and the instance as one particular
deployment of that topology.

To actually launch this instance, we use the ``gp-instance-start`` command (make sure you use the identifier
returned by ``gp-instance-create``, not the one used in these examples):

::

	gp-instance-start gpi-52d4c9ec
	
This command will take a few minutes to do its job and, for a while, all you will see is the following:	

::

	Starting instance gpi-52d4c9ec...
	
.. note:

   Did you get an error message instead? You can debug the problem by looking at the
   instance's log in ``~/.globusprovision/instances/gpi-nnnnnnnn/``, or by running
   the Globus Provision commands with the ``--debug`` option, which will print
   the log to the console as the command runs. 
   
   If you need any help, don't hesitate to :ref:`contact us <support>`. Make sure you
   include the error message and the part of the log related to that error.	
	
In a separate console, you can track the progress of the deployment using this command:	
	
::

	gp-instance-describe gpi-52d4c9ec
	
You should first see something like this:	
	
::
	
	gpi-52d4c9ec: Starting
	
	Domain 'simple'
	    simple-gridftp  Starting    
	    
This command is telling us not just the status of the entire instance (``Starting``) but also of 
each individual host in the topology's domains. In this case, Globus Provision "translated" our
topology into a single host called ``simple-gridftp``.

After a while, the output of ``gp-instance-describe`` will look like this:

::

	gpi-52d4c9ec: Configuring
	
	Domain 'simple'
	    simple-gridftp  Configuring  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X

At this point, the ``simple-gridftp`` host has started, and Globus Provision is in the process of
configuring it. Since the host has started, we now know what its actual hostname is. We will
use this later to connect to that host.

When ``gp-instance-start`` finishes deploying the instance, it will show the following:

::

	Starting instance gpi-52d4c9ec... done!
	Started instance in 1 minutes and 22 seconds

And ``gp-instance-describe`` will look like this:

::

	gpi-52d4c9ec: Running
	
	Domain 'simple'
	    simple-gridftp  Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X

Now that the instance is running, we are going to connect to the GridFTP server host as one
of the users we defined in the topology. When using the simple topology file, your public
SSH key will be authorized by default in all the users (in fact, their passwords will be
disabled, and using an SSH key will be the only way of logging into the hosts).

So, you should be able to log into the GridFTP host like this (make sure you substitute the hostname
with the one returned by ``gp-instance-describe``):

::

	ssh user1@ec2-N-N-N-N.compute-1.amazonaws.com
	
Once you've logged in, you will actually be able to play around with some Globus tools. By default,
Globus Provision will create user certificates for all users, which means you should be able to
create a proxy certificate by running the following:

::

	grid-proxy-init
	
You should see the following output:	
	
::

	Your identity: /O=Grid/OU=Globus Provision (generated)/CN=user1
	Creating proxy ..................................................................... Done
	Your proxy is valid until: Wed Aug 17 04:30:07 2011
	
Next, you can try doing a simple GridFTP transfer:

::
	
	globus-url-copy gsiftp://`hostname --fqdn`/etc/hostname ./
	
Once you're done, just log out of the host, and terminate your instance like this:
	
::

	gp-instance-terminate gpi-52d4c9ec

You will see the following:

::

	Terminating instance gpi-52d4c9ec... done!
	

What's next?
============

In this quickstart guide, you have created a simple topology and deployed it on EC2 using Globus
Provision. Although this topology only had two users and a single GridFTP server, Globus Provision
allows you to define and deploy much more complex topologies. Now that you've done this Quickstart,
you may want to read the following parts of the documentation:

* If you arrived at this Quickstart directly from our main page, you may want to read the :ref:`chap_intro`
  chapter of the documentation. It provides a more detailed explanation of what Globus Provision can
  do, and introduces much of the terminology used in the documentation.
* If you want to get your hands dirty, you can also skip directly to the :ref:`chap_instances` chapter
  (since you've already installed Globus Provision and set up Amazon EC2 in this guide, you can safely
  skip chapters :ref:`chap_install` and :ref:`chap_ec2`). That chapter will provide a more in-depth look at the simple topology file,
  and uses a more complex example, where you will deploy a topology with four hosts, including a
  Condor pool and a shared filesystem. You will also see how you can add and remove worker nodes
  from the Condor pool.
* Globus Provision also offers integration with Globus Online. If you want to turn the GridFTP server
  from this quickstart guide into a Globus Online endpoint, take a look at the :ref:`chap_go` chapter
  or the :ref:`guide_compute_go` guide.
* If you want to learn how to define more complex topologies, take a look at the :ref:`chap_topology`
  chapter. In it, you will see how you can customize many aspects of your topology, such as defining 
  hosts with multiple services on them, giving each user a distinct password, customizing what users
  are allowed to access Globus services in each domain, etc. 

