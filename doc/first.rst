Provisioning and managing a GP instance
***************************************



Creating an instance
====================

::

	[general]
	deploy: ec2
	domains: simple
	
	[domain-simple]
	users: user1 user2
	nfs-nis: yes
	lrm: condor
	cluster-nodes: 2
	
	[ec2]
	keypair: gp-key
	keyfile: ~/.ec2/gp-key.pem
	username: ubuntu
	ami: ami-7d28e914
	instance-type: t1.micro

::

	gp-create simple-ec2.conf

::

	Created new instance: gpi-02156188


Starting an instance
====================

::

	gp-start gpi-02156188

::

	Starting instance gpi-02156188...

::

	Starting instance gpi-02156188... done!
	Started instance in 2 minutes and 34 seconds

::

	gp-start -d gpi-02156188
		


Checking the status of an instance
==================================

::

	gp-describe-instance gpi-02156188
	
::

	gpi-02156188: Running
	
	Domain 'simple'
	    simple-server      Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Running  ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn2  Running  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Running  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 


::

	gpi-02156188: Configuring
	
	Domain 'simple'
	    simple-server      Running                 ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Configuring             ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn2  Running (unconfigured)  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Running (unconfigured)  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 	
	
::

	ssh ec2-M-M-M-M.compute-1.amazonaws.com condor_status	
	
::

	Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime
	
	ec2-R-R-R-R.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:43
	ec2-S-S-S-S.comput LINUX      INTEL  Unclaimed Idle     0.010   595  0+00:04:44
	                     Total Owner Claimed Unclaimed Matched Preempting Backfill
	
	         INTEL/LINUX     2     0       0         2       0          0        0
	
	               Total     2     0       0         2       0          0        0

::

	gp-describe-instance -v gpi-02156188
	


Modifying a running instance
============================


Adding hosts
------------

::

	gp-add-host -m simple \
	            -n simple-condor-wn3 \
	            -p simple-condor \
	            -r role[domain-nfsnis-client],role[domain-clusternode-condor] \
	            gpi-02156188


::

	Adding new host to gpi-24e1d0b0...done!
	Added host in 1 minutes and 17 seconds
	
::

	gpi-02156188: Running
	
	Domain 'simple'
	    simple-server      Running  ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Running  ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn3  Running  ec2-T-T-T-T.compute-1.amazonaws.com  10.T.T.T  
	    simple-condor-wn2  Running  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Running  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 
	
::

	ssh ec2-M-M-M-M.compute-1.amazonaws.com condor_status	

::
	
	Name               OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime
	
	ec2-S-S-S-S.comput LINUX      INTEL  Unclaimed Idle     0.560   595  0+00:00:05
	ec2-T-T-T-T.comput LINUX      INTEL  Unclaimed Idle     1.160   595  0+00:00:04
	ec2-R-R-R-R.comput LINUX      INTEL  Unclaimed Idle     0.460   595  0+00:00:04
	                     Total Owner Claimed Unclaimed Matched Preempting Backfill
	
	         INTEL/LINUX     3     0       0         3       0          0        0
	
	               Total     3     0       0         3       0          0        0
	
	
	
Adding users
------------

::

	gp-add-user -m simple \
	            -s "`cat ~/.ssh/id_rsa.pub`" \
	            -l newuser \
	            gpi-02156188

::

	Adding new user to gpi-196d1660...done!
	Added user in 0 minutes and 17 seconds
	
::

	ssh newuser@ec2-M-M-M-M.compute-1.amazonaws.com
	
	

Removing hosts and users
------------------------

TODO

Updating the topology
---------------------

::

	gp-describe-instance -v gpi-02156188 > newtopology.json
	
::

        {
          "ip": "10.M.M.M",
          "hostname": "ec2-M-M-M-M.compute-1.amazonaws.com",
          "depends": "node:simple-server",
          "public_ip": "M.M.M.M",
          "state": 4,
          "run_list": [
            "role[domain-nfsnis-client]",
            "role[domain-condor]"
          ],
          "id": "simple-condor",
          "deploy_data": {
            "ec2": {
              "instance_id": "i-254a1844"
            }
          }
        }

::

	"run_list": [
            "role[domain-nfsnis-client]",
            "role[domain-condor]",
            "role[domain-gridftp]"
          ]
          
:: 	

	gp-update-topology -t newtopology.json gpi-02156188
        
::

	ssh user1@ec2-M-M-M-M.compute-1.amazonaws.com

::

	grid-proxy-init
	
::
	
	Your identity: /O=Grid/OU=Globus Provision (generated)/CN=user1
	Creating proxy ................................ Done
	Your proxy is valid until: Wed Aug 17 11:24:55 2011
	
::

	globus-url-copy gsiftp://`hostname --fqdn`/etc/hostname ./
	

Stopping and resuming an instance
=================================

TODO

Terminating an instance
=======================

::

	gp-terminate gpi-02156188

::

	Terminating instance gpi-02156188... done!

::

	gpi-02156188: Terminated
	
	Domain 'simple'
	    simple-server      Terminated  ec2-N-N-N-N.compute-1.amazonaws.com  10.N.N.N
	    simple-condor      Terminated  ec2-M-M-M-M.compute-1.amazonaws.com  10.M.M.M 
	    simple-condor-wn3  Terminated  ec2-T-T-T-T.compute-1.amazonaws.com  10.T.T.T  
	    simple-condor-wn2  Terminated  ec2-R-R-R-R.compute-1.amazonaws.com  10.R.R.R  
	    simple-condor-wn1  Terminated  ec2-S-S-S-S.compute-1.amazonaws.com  10.S.S.S 

