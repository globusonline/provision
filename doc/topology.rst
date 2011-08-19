.. _chap_topology:

The JSON topology format
************************

Using a JSON topology file
==========================

::
	
	gp-create -c simple-ec2.conf
	

::
	
	gp-create -c ec2.conf -t topology.json
	
	
An overview of the JSON topology format
=======================================


::

	gp-create -c samples/simple-dummy.conf
	
	
::

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
	
::

	$ gp-start gpi-4bb1aefa
	Starting instance gpi-4bb1aefa... done!
	Started instance in 0 minutes and 0 seconds

	
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
