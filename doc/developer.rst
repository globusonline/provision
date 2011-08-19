.. _chap_developer:

Developer Documentation
***********************

Globus Provision Architecture
=============================

.. image:: arch.png
   :width: 90%
   :align: center

Command-Line Interface
----------------------


Core Packages
--------------

Common Packages
---------------


Deployers
---------


Chef Cookbooks
--------------


Adding and Testing Chef Recipes
===============================

::

		gp-start --extra-files files.txt gpi-02156188
		
::

	./src/globus/provision/chef-files/cookbooks/globus/files/default/*		/chef/cookbooks/globus/files/default/
	./src/globus/provision/chef-files/cookbooks/globus/templates/default/*	/chef/cookbooks/globus/templates/default/
	./src/globus/provision/chef-files/cookbooks/globus/recipes/*		    /chef/cookbooks/globus/recipes/
		

The Globus Provision AMI
========================

Creating an AMI
---------------

::

	gp-ec2-create-ami --chef-directory  ./src/globus/provision/chef-files
	                            --conf  ec2.conf
	                             --ami  AMI
	                            --name  "My Globus Provision AMI v1"
	                           
Runs "ec2" recipe
	

Updating an AMI
---------------
::

	gp-ec2-update-ami --conf  ec2.conf
	                   --ami  AMI
	                  --name  "My Globus Provision AMI v2"


