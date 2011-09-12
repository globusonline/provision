.. _chap_instances:

Provisioning and managing a GP instance
***************************************

At this point in the documentation, you should have :ref:`installed Globus Provision <chap_install>`
and :ref:`gotten an Amazon AWS account <chap_ec2>`. If you didn't work through the 
:ref:`Quickstart Guide <chap_quickstart>`, this might be a good moment to revisit it, and work
through a simple example. If you've already read the Quickstart Guide, this chapter will
show you a more complex example, so it should still be worthwhile to read the whole thing. 

.. _sec_simple_topology:

Defining a topology
===================

As we saw in the :ref:`chap_intro` chapter, Globus Provision allows you to deploy 
fully-configured Globus systems, which we refer to as *topologies*. More specifically, 
the topology is the specification of what we want to deploy (a GridFTP server, a specific
set of users, a Condor cluster, etc.). When we deploy it, and it is running on actual
machines somewhere "in the cloud", we refer to it as a *Globus Provision instance*.

So, the first thing we need to do is to define a topology. Globus Provision actually
provides two ways of doing this:

* *The simple topology format*. This is a simple configuration file-like format where
  we define a topology by selecting some high-level options. For example, it includes options
  to declare that a topology has two domains, that each has a separate set of users,
  and that both have a GridFTP server each, but only one has a Condor cluster. Something like this 
  can be specified in just a few lines using the simple topology format.
  
  However, because this format is simple, it is also fairly constrained. You would be unable
  to specify topologies where there are two GridFTP servers in the same domain, or where
  the same machine hosts multiple servers (by default, the simple topology format
  creates a separate machine for each service, such as GridFTP, GRAM, Condor, etc.). For more
  complex topologies, you will want to use our other topology format.  
  
  You can find the full specification of the simple topology format in :ref:`chap_stopology_ref`.
* *The JSON topology format*. This is a more versatile and flexible
  format where the topology is specified using the `JSON <http://www.json.org/>`_ format.
  In fact, Globus Provision internally translates topologies specified using the simple topology format
  into this JSON format. This format is described in detail in :ref:`chap_topology`, and the full
  specification can be found in :ref:`chap_topology_ref`

In this chapter, we will use the simple topology format, although we will take a peek at the JSON
format too. More specifically, this will be our topology file:

.. parsed-literal::

	[general]
	domains: simple
	deploy: ec2
	
	[domain-simple]
	users: user1 user2
	nfs-nis: yes
	lrm: condor
	cluster-nodes: 2
	
	[ec2]
	ami: |ami|
	instance-type: t1.micro

As you can see, this looks like a simple configuration file. Let's take a look at what each option means. 

First of all, we have the ``[general]`` section. This section is used to specify options
that affect the entire topology. Most notably, it is used to specify the list of domains
in our topology. Remember that a topology can be divided into several domains, each with
its own set of users, Globus services, etc. Here, we are only defining a single domain
called ``simple``. If we wanted to define two domains called ``simple1`` and ``simple2``,
our topology file would look more like this:
	
.. parsed-literal::

	[general]
	domains: simple1 simple2
	
	[domain-simple1]
	...	

	[domain-simple2]
	...	

The ``[general]`` section also includes a ``deploy`` option that specifies *how* our topology
will be deployed. Right now, the only deployer available is ``ec2``, which means your topology
will be deployed as EC2 instances (virtual machines running on an Amazon datacenter). You can
also select the ``dummy`` deployer, which will just pretend to deploy your topology (this can
be useful for testing purposes).

Next, we have the specification of the ``simple`` domain itself. The options are fairly
self-explanatory:

::

	users: user1 user2
	
This domain will have two users with logins ``user1`` and ``user2``. When using the simple topology
format, your public SSH key (taken from ``~/.ssh/id_rsa.pub``) will be added to each user's
``authorized_keys`` file. That means you will be able to log into the domain's hosts as any of
these users. Globus Provision will also take your username, and will create a user with that
same login (so, if your UNIX username is ``jdoe``, this domain will actually have three users:
``jdoe``, ``user1``, and ``user2``). Your user will furthermore be given administrative privileges,
which means you will be able to use ``sudo`` to run commands as ``root``.

Obviously, this is not a very realistic setup and is meant to allow you to tinker around as
quickly as possible. If you want to create accounts for actual users (who will each have their
own SSH key), you can use the :ref:`users-file option <SimpleTopologyConfig_users-file>`. 	

::
	
	nfs-nis: yes
	
In this option, we are indicating that we want this domain to be set up with an NFS and NIS
server. This means that all the nodes will have access to a shared filesystem, and will be
in the same authentication domain (i.e., the home directories and passwords will be the same
in all the hosts in the domain). 

::

	lrm: condor
	cluster-nodes: 2
	
This option specifies what LRM (Local Resource Manager) should be installed on this domain, and
how many worker nodes that LRM will have.	

Finally, because we've selected the ``ec2`` deployer, there is also an ``[ec2]`` section where we have
to specify some EC2-specific options:

.. parsed-literal::

	[ec2]
	ami: |ami|
	instance-type: t1.micro

Here, we are specifying what AMI (Amazon Machine Image) we will use to deploy the hosts
in our topology. The |ami| ami is an Ubuntu 11.04 image with some software preinstalled,
which will reduce the deployment time considerably.

.. note::
	In case you're wondering, the documentation is automatically updated to reflect
	the latest version of the Globus Provision "golden AMI", so you can use the 
	configuration files shown here verbatim. 
	
	.. ifconfig:: website == "yes"
	
		The AMI used in the example files is a 32-bit AMI, but we also provide a 64-bit AMI.
		The latest versions of our AMIs are listed in the :ref:`ami` page.

	.. ifconfig:: website != "yes"

		The AMI used in the example files is a 32-bit AMI, but we also provide a 64-bit AMI.
		The latest versions of our AMIs are listed on the main Globus Provision website.
	
We are also specifying the `EC2 instance type <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/instance-types.html>`_
to use. We are using the `"micro-instance" <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/index.html?concepts_micro_instances.html>`_
type, an instance with limited memory and CPU power, but good enough for tinkering around. This is also
Amazon's cheapest instance type ($0.02/hour), which means running the example in this chapter
won't cost you more than $0.08/hour (as we'll see soon, the topology is "translated" into four
hosts).

.. note::

	The above is just a sampling of the options available in the simple topology format.
	Make sure to check out the :ref:`chap_stopology_ref` for a complete list of options.

.. _sec_create_instance:

Creating an instance
====================

Now that we've defined a topology, we can go ahead and actually deploy it. There's only one
thing missing, though: Globus Provision needs to know how to connect to EC2 on your behalf
to request EC2 instances for your topology. Before doing anything, you will have to export 
your Access Key ID and Secret Key as environment variables 
``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY``, respectively. For example:

::

	export AWS_ACCESS_KEY_ID=FOOBAR123FOOBAR123
	export AWS_SECRET_ACCESS_KEY=FoOBaZ123/FoOBaZ456FoOBaZ789FoOBaZ012FoOBaZ345

Next, Globus Provision needs to log into the EC2 instances with administrative
privileges to configure them. It can do so if we provide an EC2 keypair.

.. note::

   Access Key ID? Secret Key? Keypair? If you're confused, this might be a good
   moment to go back to the :ref:`chap_ec2` chapter.

The name and location of the keypair is provided in the Globus Provision
*configuration file*. In this case, our configuration file will look something like this:

::

	[general]
	deploy: ec2
	
	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu

Notice how we also specify the user that Globus Provision must connect as when using
the specified keypair. If you are using the Globus Provision AMI, or any Ubuntu AMI,
this value should be set to ``ubuntu``.

Finally, even though this file may look similar to the simple topology file,
*they are two separate files*. One is used to define a topology, and the other is
used to specify connection parameters. Nonetheless, it is actually possible to
merge both files. The finished file would look like this:

.. parsed-literal::

	[general]
	domains: simple
	deploy: ec2
	
	[domain-simple]
	users: user1 user2
	nfs-nis: yes
	lrm: condor
	cluster-nodes: 2
	
	[ec2]
	ami: |ami|
	instance-type: t1.micro
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu	

For the purposes of this example, we'll refer to this file as ``simple-ec2.conf``.

.. note::

	The configuration file has other options you can tweak. Take a look at
	:ref:`chap_config_ref` for a complete list of options.

Ok, now that we have a topology and a configuration file, we are ready to create
a Globus Provision instance. We do so with the :ref:`cli_gp-instance-create` command::

	gp-instance-create -c simple-ec2.conf

.. note::

	If you want to keep the configuration file and the topology file in separate
	files, you would run ``gp-instance-create`` like this::
	
		gp-instance-create -c simple-ec2-conf.conf -t simple-ec2-topology.conf
		
``gp-instance-create`` should return something like this:

::

	Created new instance: gpi-02156188

The ``gp-instance-create`` command doesn't actually deploy the topology, but simply validates that the topology 
is correct, assigns a Globus Provision Instance (or GPI) identifier to it, and saves the information
about the instance (including the topology and the configuration options) in a database. Hang on to
the GPI identifier, as we will need it in all the following commands to refer to our instance.

Starting an instance
====================

You can start an instance using the :ref:`cli_gp-instance-start` command:

::

	gp-instance-start gpi-02156188
	
You will see the following output:

::

	Starting instance gpi-02156188...

``gp-instance-start`` may take a few minutes to fully deploy the instance. The example topology in this chapter
should only take ~3 minutes:

::

	Starting instance gpi-02156188... done!
	Started instance in 2 minutes and 34 seconds

To see more detailed log messages, simply add the ``-d`` option.

::

	gp-instance-start -d gpi-02156188
		
If you don't use the ``-d`` option, you can still see the detailed log messages in
``~/.globusprovision/instances/gpi-nnnnnnnn/deploy.log`` (where ``gpi-nnnnnnnn`` is the
identifier of your instance).


Checking the status of an instance
==================================

To check the status of an instance at any point, use the :ref:`cli_gp-instance-describe` command::

	gp-instance-describe gpi-02156188
	
This is useful while running ``gp-instance-start``. For example, the output of ``gp-instance-describe``
could look like this while the instance is still being deployed::

	gpi-02156188: Configuring
	
	Domain 'simple'
	    simple-server      Running                 ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Configuring             ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn2  Running (unconfigured)  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Running (unconfigured)  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 		
	
When ``gp-instance-start`` completes, the output of ``gp-instance-describe`` should look something like this::

	gpi-02156188: Running
	
	Domain 'simple'
	    simple-server      Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Running  ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn2  Running  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Running  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 

Notice how ``gp-instance-describe`` also provides the hostnames of the machines that have been
deployed for this topology. 

For this chapter's example topology, the topology has been
"translated" into four machines: one for the NFS/NIS server, one for the Condor head node,
and two for the Condor worker nodes. You can actually do a quick test to verify that
the Condor cluster is running correctly (make sure you substitute the hostname below
for the hostname of ``simple-condor``)::

	ssh user1@ec2-M-M-M-M.compute-1.amazonaws.com condor_status	
	
You should see the following::

	Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime
	
	ec2-R-R-R-R.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:43
	ec2-S-S-S-S.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:44
	                     Total Owner Claimed Unclaimed Matched Preempting Backfill
	
	         INTEL/LINUX     2     0       0         2       0          0        0
	
	               Total     2     0       0         2       0          0        0

This shows that the Condor head node is running, and that it is aware of the two worker nodes
in our instance.

Finally, if you want to take a look at the JSON representation of your instance, you can use
the ``-v`` option:

::

	gp-instance-describe -v gpi-02156188
	
As you'll see, this provides a much more verbose output than the regular ``gp-instance-describe``.
:ref:`chap_topology` describes this JSON format in more detail. 

Modifying a running instance
============================

Once an instance is running, it is possible to do all sorts of modifications to its topology.
You can actually edit the instance's topology in JSON format (as returned by ``gp-instance-describe -v``)
and tell Globus Provision to modify the running instance so it will match the new topology.
Globus Provision will figure out whether any hosts have to be added (or removed), whether
additional software has to be installed on one of the machines, etc.

However, you won't have to descend to the level of editing JSON code for all these operations.
As a convenience, Globus Provision provides commands that allow you to easily add/remove hosts
and users from a topology.

Adding hosts
------------

Additional hosts can be added using the :ref:`cli_gp-instance-add-host` command. For example, let's
say we want to add a new worker node to the Condor pool. 

::

	gp-instance-add-host   --domain  simple \
	                           --id  simple-condor-wn3 \
	                      --depends  simple-condor \
	                     --run-list  role[domain-nfsnis-client],role[domain-clusternode-condor] \
	                     gpi-02156188

We are telling ``gp-instance-add-host`` to add a new host with id ``simple-condor-wn3`` to the ``simple`` domain.
We also tell Globus Provision that this node depends on ``simple-condor`` (this will be taken into
account if you ever want to stop and later resume this instance; that way, Globus Provision will
know not to start ``simple-condor-wn3`` until ``simple-condor`` is running).

We also need to tell Globus Provision that this new host will act as a Condor worker node in the domain.
We do so by specifying what its "run list" will be. This concept is covered in more detail in
:ref:`chap_topology`. The run list is actually passed to `Chef <http://www.opscode.com/chef/>`_,
a configuration management framework that Globus Provision uses internally to set up the individual
hosts in an instance. You can see the list of Chef "recipes" and "roles" that Globus Provision
supports in :ref:`chap_recipe_ref`.

For now, it is enough to know that we are assigning two roles to this new host: ``domain-nfsnis-client``, 
so it will be an NFS/NIS client in the domain, and ``domain-clusternode-condor``, so it will be a
worker node in the domain's Condor pool.

After running ``gp-instance-add-host``, you should see the following:  

::

	Adding new host to gpi-02156188...done!
	Added host in 1 minutes and 17 seconds
	
You can use ``gp-instance-describe`` to verify that the new host was added:	
	
::

	gpi-02156188: Running
	
	Domain 'simple'
	    simple-server      Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Running  ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn3  Running  ec2-T-T-T-T.compute-1.amazonaws.com  10.T.T.T  
	    simple-condor-wn2  Running  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Running  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 
	
In fact, if you run ``condor_status`` on the Condor head node again::

	ssh ec2-M-M-M-M.compute-1.amazonaws.com condor_status	
	
You should see the new worker node show up there too::
	
	Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime
	
	ec2-S-S-S-S.comput LINUX      INTEL  Unclaimed Idle     0.560   595  0+00:00:05
	ec2-T-T-T-T.comput LINUX      INTEL  Unclaimed Idle     1.160   595  0+00:00:04
	ec2-R-R-R-R.comput LINUX      INTEL  Unclaimed Idle     0.460   595  0+00:00:04
	                     Total Owner Claimed Unclaimed Matched Preempting Backfill
	
	         INTEL/LINUX     3     0       0         3       0          0        0
	
	               Total     3     0       0         3       0          0        0
	
	
	
Adding users
------------

Extra users can be added to a domain using the :ref:`cli_gp-instance-add-user` command. For example, let's
add a user called ``newuser``::

	gp-instance-add-user     --domain  simple \
	                     --ssh-pubkey  "`cat ~/.ssh/id_rsa.pub`" \
	                          --login  newuser \
	                     gpi-02156188

Notice how we're also providing an SSH public key (in this case, your own SSH public key). This
SSH key will be added to the new user's ``authorized_keys`` file.

After running ``gp-instance-add-user``, you should see the following::

	Adding new user to gpi-196d1660...done!
	Added user in 0 minutes and 17 seconds
	
You should now be able to log into any of the instance's hosts as the ``newuser`` user::

	ssh newuser@ec2-M-M-M-M.compute-1.amazonaws.com
	
	

Removing hosts and users
------------------------

Similarly, you can remove hosts and users using the :ref:`cli_gp-instance-remove-hosts` and :ref:`cli_gp-instance-remove-users`,
respectively. Besides providing the Globus Provision instance identifier, and the domain where
you want to remove hosts or users, you also need to provide a list of hosts/users.

For example, to remove ``simple-condor-wn3``, we could do the following::

	gp-instance-remove-hosts --domain simple \
	                         gpi-02156188 \
	                         simple-condor-wn3 simple-foo simple-bar
	
Notice how we've also specified two hosts that don't exist. In this case, ``gp-instance-remove-hosts``
will just print out a warning::

	Warning: Host simple-foo does not exist.
	Warning: Host simple-bar does not exist.
	Removing hosts ['simple-condor-wn3'] from gpi-02156188...done!
	Removed hosts in 0 minutes and 29 seconds

Be careful when using this command: the host will be irreversibly terminated.

``gp-instance-remove-users`` works in a similar fashion::

	gp-instance-remove-users --domain simple \
	                         gpi-02156188 \
	                         newuser user3 user4 

This should output the following::

	Warning: User user4 does not exist.
	Warning: User user3 does not exist.
	Removing users ['newuser'] from gpi-02156188... done!
	Removed users in 0 minutes and 12 seconds
	
.. note::

   ``gp-instance-remove-users`` currently doesn't remove the user account on the hosts themselves,
   it just removes them from the topology. This means that, if you manually remove the
   user, that user will not be automatically re-created in subsequent updates to the instance.
   In the future, ``gp-instance-remove-users`` will also take care of removing the actual user account.

Updating the topology
---------------------

As described earlier, you can actually do more complex modifications to a topology
by editing the JSON representation of the topology, and telling Globus Provision to
apply the new topology. Globus Provision will figure out exactly what changes to make,
and will prevent you from doing "impossible" changes (for example, Globus Provision
would prevent you from changing the IP address of a host, since that IP is assigned
by Amazon EC2).

For example, by editing the JSON representation of the topology directly, you
would be able to do the following changes:

* Add or remove several hosts at once (instead of one by one using ``gp-instance-add-host``).
  When adding hosts, you can also specify deployment data that differs from the
  values specified in the simple topology file (for example, instead of creating
  a ``t1.micro`` EC2 instance, you could add a few ``m1.small`` EC2 instances). 
* Add or remove several users at once (instead of one by one using ``gp-instance-add-user``).
  Furthermore, you can also modify existing users (for example, changing a user's
  password or authorized SSH public key).
* Add or remove entire domains.
* Add software to one or several hosts.

The first thing you need to do is retrieve the instance's JSON representation of the topology::

	gp-instance-describe -v gpi-02156188 > newtopology.json

In this example, we are going to make the Condor head node act as a GridFTP server too.
In the JSON file, locate the entry corresponding to the ``simple-condor`` host:
	
.. parsed-literal::

        {
          "ip": "10.M.M.M",
          "hostname": "ec2-M-M-M-M.compute-1.amazonaws.com",
          "depends": "node:simple-server",
          "public_ip": "M.M.M.M",
          "state": 4,
          **"run_list": [
            "role[domain-nfsnis-client]",
            "role[domain-condor]"
          ]**,
          "id": "simple-condor",
          "deploy_data": {
            "ec2": {
              "instance_id": "i-254a1844"
            }
          }
        }

In the ``run_list`` array, add an entry for the ``domain-gridftp-default`` role:

.. parsed-literal::

	"run_list": [
            "role[domain-nfsnis-client]",
            "role[domain-condor]",
            **"role[domain-gridftp-default]"**
          ]	

Next, we use the :ref:`cli_gp-instance-update` command to tell Globus Provision to
apply the new topology::

	gp-instance-update -t newtopology.json gpi-02156188
	
You can verify that GridFTP was correctly installed by logging into the ``simple-condor``
host::

	ssh user1@ec2-M-M-M-M.compute-1.amazonaws.com

By default, Globus Provision will create user certificates for all users, which means you 
should be able to create a proxy certificate by running the following::

	grid-proxy-init
	
You should see the following output::
	
	Your identity: /O=Grid/OU=Globus Provision (generated)/CN=user1
	Creating proxy ................................ Done
	Your proxy is valid until: Wed Aug 17 11:24:55 2011
	
Next, you can try doing a simple GridFTP transfer::

	globus-url-copy gsiftp://`hostname --fqdn`/etc/hostname ./
	

Stopping and resuming an instance
=================================

Once a Globus Provision instance is running, you may not need it to be running
continuously. For example, let's say you've deployed an instance like the one
described in this chapter, just for the purposes of experimenting with Condor,
and figuring out how you could run some existing scientific code in parallel.
You probably only want the instance to be running while you're tinkering with
it, but not at other times. Although you *could* leave the instance running
all the time, you would be paying Amazon EC2 for a set of machines that
are essentially idling most of the time.

On the other hand, it would be inconvenient to have to
create a completely new instance from scratch, transfer all your files into it,
etc., every time you wanted to tinker around. So, Globus Provision allows you
to shut down -but not *terminate*- your instance, so that you can resume it
later. You will still have to pay Amazon EC2 for the cost of storing your
instance (more specifically, each Globus Provision AMI uses an 8GB 
`EBS <http://aws.amazon.com/ebs/>`_-backed partition), but this cost
is much lower than the cost of running the EC2 instances.

To stop your Globus Provision instance, simply use the :ref:`cli_gp-instance-stop`
command::

	gp-instance-stop gpi-02156188
	
You should see the following::

	Stopping instance gpi-02156188... done!
	
And ``gp-instance-describe`` should show the following::

	gpi-02156188: Stopped
	
	Domain 'simple'
	    simple-server      Stopped  ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Stopped  ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn2  Stopped  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Stopped  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 

To resume your instance, just use the ``gp-instance-start`` command. It will realize that
your instance is stopped, and not completely new, and will resume it (instead of
requesting new EC2 instances for it)::

	gp-instance-start gpi-02156188
	
You should see the following::

	Starting instance gpi-02156188... done!	

And ``gp-instance-describe`` should report it as running again:
::

	gpi-02156188: Running
	
	Domain 'simple'
	    simple-server      Running  ec2-A-A-A-A.compute-1.amazonaws.com  10.A.A.A
	    simple-condor      Running  ec2-B-B-B-B.compute-1.amazonaws.com  10.B.B.B 
	    simple-condor-wn2  Running  ec2-C-C-C-C.compute-1.amazonaws.com  10.C.C.C  
	    simple-condor-wn1  Running  ec2-D-D-D-D.compute-1.amazonaws.com  10.D.D.D 	

When resuming an instance, Globus Provision does not just start the machines again.
Since Amazon EC2 will assign new hostnames and IPs to machines that have been stopped
and then started again, Globus Provision will also reconfigure the machines so that
services like NFS/NIS and Condor work correctly (if you simply start the machine,
it will start with configuration files that still point to the old hostnames).

So, if you run the following::

	ssh ec2-B-B-B-B.compute-1.amazonaws.com condor_status	
	
You should see that Condor is aware of its two worker nodes with their new hostnames::

	Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime
	
	ec2-C-C-C-C.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:43
	ec2-D-D-D-D.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:44
	                     Total Owner Claimed Unclaimed Matched Preempting Backfill
	
	         INTEL/LINUX     2     0       0         2       0          0        0
	
	               Total     2     0       0         2       0          0        0

Actually, the fact that you were able to log into the Condor head node (which is
an NFS/NIS *client* in the domain) also confirms that the NFS/NIS configuration
files were updated correctly.

Terminating an instance
=======================

Once you're completely done with a Globus Provision instance, you terminate all
the hosts in that instance. Be careful when doing this: unlike stopping an instance,
this action is irreversible, and the entire contents of the instance will be destroyed.

To terminate an instance, use the :ref:`cli_gp-instance-terminate` command::

	gp-instance-terminate gpi-02156188

You should see the following::

	Terminating instance gpi-02156188... done!

And you can verify that the instance was terminated by running ``gp-instance-describe``::

	gpi-02156188: Terminated
	
	Domain 'simple'
	    simple-server      Terminated  ec2-A-A-A-A.compute-1.amazonaws.com  10.A.A.A
	    simple-condor      Terminated  ec2-B-B-B-B.compute-1.amazonaws.com  10.B.B.B 
	    simple-condor-wn3  Terminated  ec2-C-C-C-C.compute-1.amazonaws.com  10.C.C.C  
	    simple-condor-wn2  Terminated  ec2-D-D-D-D.compute-1.amazonaws.com  10.D.D.D  
	    simple-condor-wn1  Terminated  ec2-E-E-E-E.compute-1.amazonaws.com  10.E.E.E 	

