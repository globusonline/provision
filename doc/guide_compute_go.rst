.. _guide_compute_go:

Launching a Condor cluster with a Globus Online endpoint
********************************************************

This guide explains how to launch a Globus Provision instance with a Condor cluster and a
Globus Online (GO) transfer endpoint. As an example, we will use Globus Online to transfer 
a set of `Project Gutenberg <http://www.gutenberg.org/>`_ texts into the cluster, do
some simple processing on them using the Condor cluster, and transfer the result out
with Globus Online.

In general, the setup described in this guide may of interest if you have a dataset that
you want to do some processing on and want compute resources right away to do that
processing (e.g., to test your code interactively, without having your compute jobs
waiting in a queue on your organization's local cluster). This is also an example 
where Globus Provision and Globus Online complement
each other nicely: Globus Provision can set up a compute cluster for you on EC2 in
just a few minutes, and Globus Online provides a hassle-free way of getting data
in and out of the cluster. Plus, Globus Provision takes care of setting up the
endpoint on the cluster for you; no need to worry about GridFTP, certificates, etc. 

If you are starting from scratch, you will need to install Globus Provision first,
and make sure you have the necessary EC2 account information. Just read our main
:ref:`chap_quickstart`, and stop right before section :ref:`chap_quickstart_sec_create`
(although, if you have time, it doesn't hurt to work through the entire Quickstart) 

This guide also assumes that you have a GO account and that you are familiar, at least,
with GO's web interface. If this is not the case, `sign up for a GO account <https://www.globusonline.org/SignUp>`_ 
and take a look at the `Globus Online Quickstart Guide <https://www.globusonline.org/quickstart/>`_


The topology file
=================

Let's start by taking a look at the topology file we will be using (save this file
as ``go-condor-ec2.conf``):

.. parsed-literal::

	[general]
	deploy: ec2
	domains: simple
	
	[domain-simple]
	users: gp-user
	gridftp: yes
	nfs-nis: yes
	lrm: condor
	cluster-nodes: 4
	go-endpoint: go-user#gp-test
	go-auth: go
	
	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu
	ami: |ami|
	instance-type: t1.micro
	
	[globusonline]
	ssh-key: ~/.ssh/id_rsa

As you can see, this file is similar to the Quickstart's example file, except for
a couple extra options. First of all, make sure the ``[ec2]`` options have valid values
for your EC2 account. 

Next, we specify that we want this Globus Provision
instance to include a Condor cluster::

	lrm: condor
	cluster-nodes: 4

Since we'll have multiple hosts in our topology, it will be convenient for them to
have shared accounts and a shared filesystem. We do this with the following option::

	nfs-nis: yes
	
Finally, we need to specify a few Globus Online options::

	[domain-simple]
	go-endpoint: go-user#gp-test
	go-auth: go

	[globusonline]
	ssh-key: ~/.ssh/id_rsa_nopass

The ``go-endpoint`` option specifies the name of the endpoint that will be created
for the instance's GridFTP server (notice how, as we did in the Quickstart, we've specified
``gridftp: yes``). Make sure you replace ``go-user`` with the name of *your*
Globus Online user.

The ``go-auth`` option specifies that Globus Online will use your GO identity when
accessing this endpoint. In other words, if you are logged into a GO interface
(such as the GO website, or the GO CLI), GO will not ask you for any additional
account information or passwords; it will simply contact the endpoint with your
GO identity. To specify what GO users should be authorized to access the endpoint, just
specify them in the ``users`` option (make sure you, at least, add your GO user;
otherwise, you will not be able to work through the remainder of the guide).

Finally, since Globus Provision will be contacting GO to create an endpoint
on your behalf, you must authorize an SSH key in your GO account, and
specify the path of that SSH key in the ``ssh-key`` option. If you have not authorized
your SSH key in Globus Online, take a quick detour to :ref:`chap_go_sec_identity` to
learn how to do this.

Launching the instance
======================

Ok, we're ready to actually launch this topology. The first step is to create a *Globus Provision instance*
with that topology::

	gp-instance-create -c go-condor-ec2.conf

This should immediately return the following::

	Created new instance: gpi-65f00474

The ``gp-instance-create`` command doesn't actually deploy the topology, or create the
associated Globus Online endpoints, but simply validates that the topology 
is correct, and creates an entry for it in a database. This entry is called an *instance*. You can think
of the topology as a specification of what you want to deploy and the instance as one particular
deployment of that topology.

To actually launch this instance, we use the ``gp-instance-start`` command (make sure you use the identifier
returned by ``gp-instance-create``, not the one used in these examples)::

	gp-instance-start gpi-65f00474
	
This command will take a few minutes to do its job and, for a while, all you will see is the following::

	Starting instance gpi-65f00474...
	
.. note:

   Did you get an error message instead? You can debug the problem by looking at the
   instance's log in ``~/.globusprovision/instances/gpi-nnnnnnnn/``, or by running
   the Globus Provision commands with the ``--debug`` option, which will print
   the log to the console as the command runs. 
   
   If you need any help, don't hesitate to :ref:`contact us <support>`. Make sure you
   include the error message and the part of the log related to that error.	
	
In a separate console, you can track the progress of the deployment using this command::

	gp-instance-describe gpi-65f00474
	
You should first see something like this::
	
	gpi-65f00474: Starting
	
	Domain 'simple'
	    simple-condor      Starting
	    simple-server      Starting
	    simple-condor-wn4  Starting
	    simple-condor-wn3  Starting
	    simple-condor-wn2  Starting
	    simple-condor-wn1  Starting
	    simple-gridftp     Starting
	    
This command is telling us not just the status of the entire instance (``Starting``) but also of 
each individual host in the topology's domains. Notice how we have a host for the Condor head node
(``simple-condor``), four Condor worker nodes (``simple-condor-wn1``, etc.), a GridFTP server
(``simple-gridftp``), and an NFS/NIS server (``simple-server``). Since we're using EC2 micro-instance
(notice how we specified ``instance-type: t1.micro`` in the topology file), this example will
only cost $0.14 per hour to run. In fact, if you have a new Amazon Web Services account,
you may be able to take advantage of their 
`Free Usage Tier <http://aws.amazon.com/free/>`_ and get 750 hours on EC2 completely free.

After a short while, the output of ``gp-instance-describe`` will look like this:

::

	gpi-65f00474: Configuring
	
	Domain 'simple'
	    simple-condor      Running (unconfigured)  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-server      Configuring             ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn4  Running (unconfigured)  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn3  Running (unconfigured)  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn2  Running (unconfigured)  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn1  Running (unconfigured)  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-gridftp     Running (unconfigured)  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X


At this point, all the hosts have started, and Globus Provision is in the process of
configuring the ``simple-server`` host (Globus Provision can configure multiple hosts
at the same time but, in this case, it cannot do so because we can't configure the
other hosts until the NFS/NIS server is runnign). Notice how, since all the hosts
have started, we now know what their actual hostnames are. We will
use this later to connect to that host.

When ``gp-instance-start`` finishes deploying the instance, it will show the following::

	Starting instance gpi-65f00474... done!
	Started instance in 2 minutes and 31 seconds

And ``gp-instance-describe`` will look like this::

	gpi-65f00474: Running
	
	Domain 'simple'
	    simple-condor      Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-server      Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn4  Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn3  Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn2  Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-condor-wn1  Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X
	    simple-gridftp     Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.X.X.X

You can use the Globus Online CLI to verify that the "gp-test" endpoint was correctly
created::

	$ ssh cli.globusonline.org endpoint-list -v gp-test
	Name              : gp-test
	Host(s)           : gsiftp://ec2-N-N-N-N.compute-1.amazonaws.com:2811
	Subject(s)        : /C=US/O=Globus Consortium/OU=Globus Connect Service/CN=f6ec9304-dc84-11e0-bc85-12313804ec2a
	MyProxy Server    : myproxy.globusonline.org
	Credential Status : n/a
	Credential Expires: n/a
	Credential Subject: n/a

The host for the endpoint should match that of the ``simple-gridftp`` host.

Transferring the data with Globus Online
========================================

Now, we will use Globus Online to transfer a dataset into the cluster we have just
launched on EC2. You can transfer any dataset from an existing Globus Online
endpoint, or transfer data from your laptop or other local machine
using `Globus Connect <https://www.globusonline.org/globus_connect/>`_. As an example,
we will use a collection of ebooks from `Project Gutenberg <http://www.gutenberg.org/>`_.
If you'd like to follow the example with the exact same dataset, you can download
`a tarball <http://globus.org/provision/example-gutenberg.tar.gz>`_ (31MB) with all the ebooks.

Once the dataset is available on a GO endpoint, you can transfer it to the cluster using the
GO web interface or the CLI::

	$ ssh cli.globusonline.org scp -r my-gc-endpoint:/~/ebooks/ gp-test:/nfs/scratch/
	Task ID: 74f43426-dc8c-11e0-bc85-12313804ec2a
	Type <CTRL-C> to cancel or bg<ENTER> to background
	[XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX] 94/94 2.14 mbps

Notice how we're transferring the entire ``ebooks`` directory into the ``/nfs/scratch`` directory. 
This is a shared scratch directory that can be accessed from any of the hosts in the cluster. 

.. note::
	Because of the way that NFS directories are mounted on Globus Provision instances,
	and the way Globus Online's ``scp`` commands checks if a directory exists, the above CLI
	command may fail. If so, do the transfer using the GO web interface, which will first try
	to list the contents of ``/nfs/scratch``, ensuring that it will be mounted before the
	transfer. 
	
	Another quick workaround, in case you want to use the CLI command, is to
	run ``ls /nfs/scratch`` on the ``simple-gridftp`` node. This will force the
	scratch directory to be mounted before the transfer.

Processing the data with Globus Online
======================================

To process the data, we will need to log into the Condor hear node to launch a series of jobs.
When using the simple topology file, your public SSH key will be authorized by default in all 
the users specified in the ``users`` option (in fact, their passwords will be
disabled, and using an SSH key will be the only way of logging into the hosts).

So, you should be able to log into the Condor head node like this (make sure you substitute the hostname
with the one returned by ``gp-instance-describe``, and ``myuser`` with the username you specified
in ``users``)::

	ssh myuser@ec2-N-N-N-N.compute-1.amazonaws.com
	
Once you've logged in, run the following::

	condor_status
	
You should see the following output::

	Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime
	
	ec2-R-R-R-R.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:43
	ec2-S-S-S-S.comput LINUX      INTEL  Unclaimed Idle     0.000   595  0+00:04:44
	ec2-T-T-T-T.comput LINUX      INTEL  Unclaimed Idle     0.000   595  0+00:04:42
	ec2-U-U-U-U.comput LINUX      INTEL  Unclaimed Idle     0.000   595  0+00:04:42
	                     Total Owner Claimed Unclaimed Matched Preempting Backfill
	
	         INTEL/LINUX     4     0       0         4       0          0        0
	
	               Total     4     0       0         4       0          0        0

This shows that the Condor head node is running, and that it is aware of the four worker nodes
in our instance.

Now, we need to specify what jobs we're going to run on the cluster. We're going to do
some simple processing: for each ebook, count the number of words and report the wordcount
and the title of the book. To do so, save the following as ``wc.sh`` in your home directory
(on the cluster)::

	#!/bin/bash
	
	FILE=$1
	TITLE="`grep -m1 "Title:"  $FILE | cut -f2- -d" "`"
	WORDS=`wc --words $FILE | cut -f1 -d" "`
	echo $WORDS $TITLE

Make it executable::

	chmod u+x wc.sh	

Next, we need to prepare a Condor submission file. Since we have to process nearly 100 files,
we'll use a simple script to generate the submission file. Save the following as ``gen_condor.sh``::

	echo 'Universe   = vanilla'
	echo 'Executable = wc.sh'
	echo 'transfer_executable = false'
	echo 'Log        = wc.log'
	echo 'Output     = wc.$(Process).out'
	echo 'Error      = wc.$(Process).error'
	
	
	for f in `ls /nfs/scratch/ebooks/`;
	do
		echo "Arguments = /nfs/scratch/ebooks/$f"
		echo 'Queue'
	done

And run the following::

	bash gen_condor.sh > wc.submit

Now, let's submit the jobs to the Condor cluster:: 

	condor_submit wc.submit
	
You can use the ``condor_q`` command to track the progress of the jobs:: 

	$ condor_q

	-- Submitter: ec2-N-N-N-N.compute-1.amazonaws.com : <10.X.X.X:PPPPP> : ec2-N-N-N-N.compute-1.amazonaws.com
	 ID      OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD               
	   4.40  borja           9/11 16:57   0+00:00:00 R  0   0.0  wc.sh /nfs/scratch
	   4.41  borja           9/11 16:57   0+00:00:00 R  0   0.0  wc.sh /nfs/scratch
	   4.42  borja           9/11 16:57   0+00:00:00 R  0   0.0  wc.sh /nfs/scratch
	   4.43  borja           9/11 16:57   0+00:00:00 R  0   0.0  wc.sh /nfs/scratch
	   4.44  borja           9/11 16:57   0+00:00:00 I  0   0.0  wc.sh /nfs/scratch
	   4.45  borja           9/11 16:57   0+00:00:00 I  0   0.0  wc.sh /nfs/scratch
	   4.46  borja           9/11 16:57   0+00:00:00 I  0   0.0  wc.sh /nfs/scratch
	   4.47  borja           9/11 16:57   0+00:00:00 I  0   0.0  wc.sh /nfs/scratch
	   4.48  borja           9/11 16:57   0+00:00:00 I  0   0.0  wc.sh /nfs/scratch
	
	   [etc.]

After a short while, ``condor_q`` will report that there are no jobs running. That means the
jobs have completed. We just need to concatenate the output of all the jobs to form the
list of titles and wordcounts::

	$ cat *.out | sort -gr > wc.txt
	
Let's take a peek::

	$ head wc.txt
	1665403 The 2010 CIA World Factbook
	904087 The Complete Works of William Shakespeare
	824146 The King James Bible
	568531 Les Miserables
	565450 War and Peace
	462169 The Count of Monte Cristo
	428901 Don Quixote
	383599 An Inquiry into the Nature and Causes of the Wealth of Nations
	353778 The Brothers Karamazov
	352684 Anna Karenina

Of course, the result file is small enough that you could just copy-paste it somewhere else, but you
can also try transferring out of the cluster using Globus Online.


What's next?
============

In this guide, you have launched a compute cluster on EC2 using Globus Provision,
and staged data in and out with Globus Online. However, the kind of processing we've done
is very simple, and could easily be done without the need for a Condor cluster. However,
this guide lays the groundwork for you to experiment with other datasets, and with more
complex forms of processing. Globus Provision and Globus Online take care of provisioning
resources and moving data, so you can focus on your work!

If you'd like to learn more about Globus Provision, you may want to do the following:

* If this guide was your first contact with Globus Provision, you may want to read the :ref:`chap_intro`
  chapter of the documentation. It provides a more detailed explanation of what Globus Provision can
  do, and introduces much of the terminology used in the documentation.
* If you want to learn about Globus Provision's other features, head over to the :ref:`chap_instances` chapter
  (since you've already installed Globus Provision and set up Amazon EC2 in this guide, you can safely
  skip chapters :ref:`chap_install` and :ref:`chap_ec2`). That chapter will provide a more in-depth look at the simple topology file,
  and uses a similar example, but also explains how you can add and remove worker nodes dynamically
  from the Condor pool.
* To read about other Globus Online configuration options, take a look at the :ref:`chap_go` chapter.
* If you want to learn how to define more complex topologies, take a look at the :ref:`chap_topology`
  chapter. In it, you will see how you can customize many aspects of your topology, such as defining 
  hosts with multiple services on them, giving each user a distinct password, customizing what users
  are allowed to access Globus services in each domain, etc. 


Terminating the instance
========================
	
Once you're done tinkering, just log out of the Condor head node, and terminate your instance like this:
	
::

	gp-instance-terminate gpi-65f00474

You will see the following:

::

	Terminating instance gpi-65f00474... done!
	



