.. _chap_topology:

The JSON topology format
************************

Up to this point, we've been specifying our topologies using the *simple topology format*
introduced in :ref:`chap_instances` (and also used in the :ref:`chap_quickstart`). This
format is simple but also fairly constrained. Thus, Globus Provision also allows you
to specify your topology using `JSON <http://www.json.org/>`_, a lightweight format
for data exchange that includes primitive types found in most programming languages
(integers, strings, etc.), lists, and objects.

If you've never used JSON before, you'll notice it is a fairly intuitive format, since it 
was designed to mimic the syntax shared by many programming languages. For example,
this is a list of strings in JSON::

	[ "one", "two", "three" ]
	
JSON objects are represented as collections of name/value pairs (they are akin to
dictionaries and hashes). For example, an "object" intended to represent a person
and with three properties (*name*, *phone*, *active*) could look like this in
JSON::

	{
		"name": "J. Random Hacker",
		"phone": 5551234,
		"active": true
	}
	
Notice, though, that this "object" includes no indication that it is a "person object".
It is up to the application reading that JSON code to treat it as such. In particular,
Globus Provision expects a JSON topology to have certain objects representing domains,
users, hosts, etc. 


A simple JSON topology file
===========================

To familiarize ourselves with the JSON topology format, let's take a look at a simple
topology file, step by step.

When we specify a topology using JSON, Globus Provision expects to find a single object,
which will represent the topology. This object must have, at least, a property called
``domains`` and one called ``default_deploy_data``:

.. parsed-literal::

	{
	  "domains": *domains*
	  "default_deploy_data": *deployer-specific data*
	}	
	
The ``domains`` property must have a list of domains:

.. parsed-literal::

	{
	  "domains": [ *domain_1*, *domain_2*, ... , *domain_N*]
	}	

Each domain will be a a Domain object.
We are going to define a single domain. A domain must, at the very least, have three properties,
``id``, ``users``, and ``nodes``:

.. parsed-literal::

	{
	  "domains": [ 
	  	{
	  		"id": *identifier*,
	  
	  		"users": *users*,
	  		
	  		"nodes": *nodes*
	  	}
	  ]
	}	

The Domain object actually has more properties you can specify. The full specification
of what JSON will be accepted by Globus Provision can be found in the :ref:`chap_topology_ref`.
For example, to find out what other attributes can be specified, take a look at the
:ref:`Domain object reference <topology_Domain>`.

The ``id`` property will simply be a string with a unique identifier for this domain.
``users`` and ``nodes``, on the other hand, will be lists of :ref:`User <topology_User>`
and :ref:`Node <topology_Node>`, respectively:

.. parsed-literal::

	{
	  "domains": [ 
	  	{
	  		"id": "simple",
	  
	  		"users": [ *user1*, *user2*, ..., *userN* ],
	  		
	  		"nodes": [ *node1*, *node2*, ..., *nodeN* ]
	  	}
	  ]
	}	
	
We are going to define a single user. The User object must have, at the very least,
an ``id`` property, with a unique identifier for the user, and a ``password_hash``
property, with the password hash of the user (as it will appear in ``/etc/shadow``
when the user is created). For now, don't worry about the actual value of this
property (see :ref:`topology_User_password_hash` in the :ref:`chap_topology_ref`
for more details).

So, the user object would look like this::

    {
      "id": "borja", 
      "password_hash": "$6$3DSIAVhnk4dK1b$NaoCO3q6i..."
    }

We will also define a single host (or *node*). A host object must, at the very
least, have an ``id`` property, with a unique identifier for the host, and a ``run_list``
property, with the list of "roles" and "recipes" to apply to that host::

    {
      "id": "simple-gridftp", 
      "run_list": [ "role[domain-gridftp-default]" ]
    }

We will revisit the ``run_list`` attribute soon. For now, just trust that the value shown
above will result in a host that is configured as a GridFTP server.

That is all we need for the Domain, object which will look like this::

    {
      "id": "simple",
      "users": [
        {
          "id": "borja", 
          "password_hash": "$6$3DSIAVhnk4dK1b$NaoCO3q6i..."
        }
      ], 
      "nodes": [
        {
          "id": "simple-gridftp", 
          "run_list": [ "role[domain-gridftp-default]" ]
        }
      ], 
    }


Don't forget there was another property, ``default_deploy_data``, in the Topology object.
The value of this property must be a :ref:`DeployData <topology_DeployData>` object which, 
in turn, has an ``ec2`` property which must have an :ref:`EC2DeployData <topology_EC2DeployData>`
object. This object is used to specify
the same EC2 parameters which we specified in the ``[ec2]`` section of the 
:ref:`simple topology format <sec_simple_topology>`. So, the ``default_deploy_data``
property could look like this:

.. parsed-literal::

  "default_deploy_data": {
    "ec2": {
      "ami": "|ami|", 
      "instance_type": "t1.micro"
    }
  }


And the whole topology JSON file will look like this:

.. parsed-literal::

	{
	
	  "default_deploy_data": {
	    "ec2": {
	      "ami": "|ami|", 
	      "instance_type": "t1.micro"
	    }
	  },	
	
	  "domains": [
	    {
	    
	      "id": "simple",

	      "users": [
	        {
	          "id": "borja", 
	          "password_hash": "$6$3DSIAVhnk4dK1b$NaoCO3q6i..."
	        }
	      ], 
	      
	      "nodes": [
	        {
	          "id": "simple-gridftp", 
	          "run_list": [ "role[domain-gridftp]" ]
	        }
	      ], 
	      
	    }
	  ]
	}	
	
The above is essentially the same as the following in the simple topology format::

	[general]
	domains: simple
	deploy: ec2
	
	[domain-simple]
	users: borja
	gridftp: yes

	[ec2]
	ami: ami-ff76b796
	instance-type: t1.micro

So, why would we want to use the much more verbose JSON format instead of this simple,
much more human-readable, format? The main reason is that the JSON format gives you
a lot more control over the topology. For example, the simple topology format
allows you to say ``gridftp: yes`` and ``lrm: condor``, but that will get translated
into two separate hosts (one for the GridFTP server and another for the Condor head node).
If you want to specify that you want both servers in a single host, the simple
topology format will not allow you to do this. In the topology JSON, on the other hand,
you simply define single Node in the domain, and set its ``run_list`` to
``[ "role[domain-condor]", "role[domain-gridftp-default]" ]``.

To put it another way, the JSON format allows you to specify *exactly* what you want
your topology to look like. The simple topology format, on the other hand, will take
the high-level description of your topology and will translate it into a specific
topology (it actually translates it to the JSON format internally) using some reasonable
defaults, like putting the GridFTP server and the Condor head node on separate domains.


Using a JSON topology file
==========================

So, if you've written your topology in JSON, you can no longer merge it with the
Globus Provision configuration file, as we've done in previous examples. Instead,
you must specify the configuration file and the topology separately, like this::
	
	gp-instance-create -c ec2.conf -t topology.json
	
In this case, ``ec2.conf`` could contain the following::

	[general]
	deploy: ec2
	
	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu

Notice how this configuration file (which was explained in detail in :ref:`sec_create_instance`)
contains connection-specific information, while the EC2 parameters included in the
``default_deploy_data`` of the topology is information specific to the topology: what
AMI will be used to create the hosts, and what EC2 instance type will be used.

.. _sec_runlist:

Specifying the "run list" of a host
===================================

The "run list" of a host, which we specified in the ``run_list`` property of a
:ref:`Node <topology_Node>` object is something we saw briefly in :ref:`chap_instances`. 
Globus Provision uses `Chef <http://www.opscode.com/chef/>`_,
a configuration management framework, to install and configure software on the hosts that
make up a Globus Provision instance. In Chef, a "recipe" is a specification of
how to install and configure a piece of software. 

So, if we want a host to be
a GridFTP server, we would tell Chef to apply the "GridFTP recipe" to it. In this case,
we're actually selecting a "role", which is simply a convenient way of specifying
that multiple recipes must be run (e.g., in this case, besides installing the GridFTP
server itself, we also need to install a host certificate; the "host certificate recipe"
is included in ``role[domain-gridftp-default]``, as is the "GridFTP recipe"). So, while in the simple 
topology format we could get away with using simple options like 
``gridftp: yes`` (which Globus Provision translated into the specific "run list" necessary 
to set up a GridFTP server), in the JSON format we will have to specify precisely what roles
or recipes must be applied.
 
This means that any piece of software you want to install must have a Chef recipe written
for it. Globus Provision already includes several recipes to install various pieces of software.
The roles and recipes that you can choose from are listed in the :ref:`chap_recipe_ref`.
The :ref:`chap_developer` chapter also includes instructions on how to write your own
recipes.


Specifying per-host deployment data
===================================

As we saw earlier, we can specify deployment-specific parameters in the topology
using the ``default_deploy_data`` property::

  "default_deploy_data": {
    "ec2": {
      "ami": "ami-ff76b796", 
      "instance_type": "t1.micro"
    }
  }

However, it is also possible to specify per-host deployment data. Node objects
also have a ``deploy_data`` property, which must contain a DeployData object. So,
we could define the following two nodes::

  "nodes": [
    {
      "id": "simple-gridftp", 
      "run_list": [ "role[domain-gridftp-default]" ],
      "deploy_data": { "ec2": {"instance_type": "m1.small" } }
    },
    {
      "id": "simple-condor", 
      "run_list": [ "role[domain-condor]" ],
    }
  ] 

``simple-condor`` does not have a ``deploy_data`` property, so it will
simply use the values defined in the topology's ``default_deploy_data``.
``simple-gridftp``, on the other hand, will use the value for ``ami``,
but overrides the value for ``instance_type``.


Checking deployment data of a running instance
==============================================

Knowing your way around the JSON topology format can also come in handy
when checking on the status of a running instance. For example,
let's say we use the following simple topology (notice how we're using
the ``dummy`` deployer)::

	[general]
	domains: simple
	deploy: dummy
	
	[domain-simple]
	users: user1 user2
	nfs-nis: yes
	lrm: condor
	cluster-nodes: 2

Next, we create the instance::

	$ gp-instance-create -c samples/simple-dummy.conf
	Created new instance: gpi-4bb1aefa

If we run ``gp-instance-describe -v``, we will get the raw JSON representation of the
topology::

	$ gp-instance-describe -v gpi-4bb1aefa
	{
	  "domains": [
	    {
	    
	      "users": [
	        {
	          "ssh_pkey": "ssh-rsa ...", 
	          "id": "user1", 
	          "certificate": "generated", 
	          "password_hash": "!"
	        }, 
	        {
	          "ssh_pkey": "ssh-rsa ...", 
	          "id": "user2", 
	          "certificate": "generated", 
	          "password_hash": "!"
	        }, 
	        {
	          "admin": true, 
	          "ssh_pkey": "ssh-rsa ...", 
	          "id": "borja", 
	          "certificate": "generated", 
	          "password_hash": "!"
	        }
	      ], 
	      
	      "nodes": [
	        {
	          "depends": "node:simple-server", 
	          "id": "simple-condor", 
	          "run_list": [
	            "role[domain-nfsnis-client]", 
	            "role[domain-condor]"
	          ]
	        }, 
	        {
	          "id": "simple-server", 
	          "run_list": [
	            "role[domain-nfsnis]", 
	            "role[globus]"
	          ]
	        }, 
	        {
	          "depends": "node:simple-condor", 
	          "id": "simple-condor-wn2", 
	          "run_list": [
	            "role[domain-nfsnis-client]", 
	            "role[domain-clusternode-condor]"
	          ]
	        }, 
	        {
	          "depends": "node:simple-condor", 
	          "id": "simple-condor-wn1", 
	          "run_list": [
	            "role[domain-nfsnis-client]", 
	            "role[domain-clusternode-condor]"
	          ]
	        }
	      ], 
	      
	      "gridmap": [
	        {
	          "dn": "/O=Grid/OU=Globus Provision (generated)/CN=user1", 
	          "login": "user1"
	        }, 
	        {
	          "dn": "/O=Grid/OU=Globus Provision (generated)/CN=user2", 
	          "login": "user2"
	        }, 
	        {
	          "dn": "/O=Grid/OU=Globus Provision (generated)/CN=borja", 
	          "login": "borja"
	        }
	      ], 
	      
	      "id": "simple"
	    }
	  ], 
	  
	  "state": 1, 
	  "id": "gpi-4bb1aefa"
	}	
	
Now, let's start this instance::

	$ gp-instance-start gpi-4bb1aefa
	Starting instance gpi-4bb1aefa... done!
	Started instance in 0 minutes and 0 seconds

If you look at the instance's topology JSON again, you'll notice that
it has now been furnished with more properties (highlighted in bold):
	
.. parsed-literal::

	{
	  "domains": [
	    {
	      "users": [
	        {
	          "admin": true, 
	          "ssh_pkey": "ssh-rsa ...", 
	          "id": "borja", 
	          "certificate": "generated", 
	          "password_hash": "!"
	        }, 
	        {
	          "ssh_pkey": "ssh-rsa ...", 
	          "id": "user2", 
	          "certificate": "generated", 
	          "password_hash": "!"
	        }, 
	        {
	          "ssh_pkey": "ssh-rsa ...", 
	          "id": "user1", 
	          "certificate": "generated", 
	          "password_hash": "!"
	        }
	      ], 
	      "nodes": [
	        {
	          **"ip": "1.2.3.4", 
	          "hostname": "simple-condor.gp.example.org",** 
	          "depends": "node:simple-server", 
	          "state": **4**, 
	          "run_list": [
	            "role[domain-nfsnis-client]", 
	            "role[domain-condor]"
	          ], 
	          "id": "simple-condor"
	        }, 
	        {
	          **"ip": "1.2.3.4"**, 
	          "state": **4**, 
	          **"hostname": "simple-server.gp.example.org"**, 
	          "id": "simple-server", 
	          "run_list": [
	            "role[domain-nfsnis]", 
	            "role[globus]"
	          ]
	        }, 
	        {
	          **"ip": "1.2.3.4"**, 
	          **"hostname": "simple-condor-wn2.gp.example.org"**, 
	          "depends": "node:simple-condor", 
	          "state": **4**, 
	          "run_list": [
	            "role[domain-nfsnis-client]", 
	            "role[domain-clusternode-condor]"
	          ], 
	          "id": "simple-condor-wn2"
	        }, 
	        {
	          **"ip": "1.2.3.4"**, 
	          **"hostname": "simple-condor-wn1.gp.example.org"**, 
	          "depends": "node:simple-condor", 
	          "state": 4, 
	          "run_list": [
	            "role[domain-nfsnis-client]", 
	            "role[domain-clusternode-condor]"
	          ], 
	          "id": "simple-condor-wn1"
	        }
	      ], 
	      "gridmap": [
	        {
	          "dn": "/O=Grid/OU=Globus Provision (generated)/CN=user1", 
	          "login": "user1"
	        }, 
	        {
	          "dn": "/O=Grid/OU=Globus Provision (generated)/CN=user2", 
	          "login": "user2"
	        }, 
	        {
	          "dn": "/O=Grid/OU=Globus Provision (generated)/CN=borja", 
	          "login": "borja"
	        }
	      ], 
	      "id": "simple"
	    }
	  ], 
	  "state": 4, 
	  "id": "gpi-4bb1aefa"
	}
	
These are properties that are added by Globus Provision at deploy-time, and which
you cannot specify or edit (the :ref:`chap_topology_ref` specifies what properties
are editable and which ones are not). 

If we were using the EC2 deployer, we would get similar information:

.. parsed-literal::

        {
          **"ip": "10.X.X.X", 
          "hostname": "ec2-107-X-X-X.compute-1.amazonaws.com",** 
          "depends": "node:simple-condor", 
          **"public_ip": "107.X.X.X",** 
          "state": **4**, 
          "run_list": [
            "role[domain-nfsnis-client]", 
            "role[domain-clusternode-condor]"
          ], 
          "id": "simple-condor-wn1", 
          **"deploy_data": {
            "ec2": {
              "instance_id": "i-374a1856"
            }
          }**
        }
        
Notice, though, how Globus Provision also adds a ``deploy_data`` property with
information that's specific to the EC2 deployer (in this case, the EC2 instance id).
