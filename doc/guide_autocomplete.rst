.. _guide_autocomplete:

Using BASH autocomplete with Globus Provision commands
******************************************************

Most of the Globus Provision commands involve specifying a *Globus Provision instance* identifier
(e.g., ``gpi-12a63d2e``). Copy-pasting this identifier from one command to another can
be a bit tedious, so we provide a BASH autocomplete script that can make your
life easier.

This script is included in the source distribution of Globus Provision. You can also download
the file `gp-complete.sh <https://raw.github.com/globusonline/provision/dev/scripts/gp-complete.sh>`_
directly from our GitHub repository. To activate the autocomplete script, just run this::

	source gp-complete.sh
	
Include the above line in your ``~/.profile`` file if you want it to run every time you start
a BASH shell.

This will autocomplete all parameters for a Globus Provision command. Globus Provision instance
identifiers are treated in a special way. If you have written a command invocation to a point where 
it makes sense to complete it with a Globus Provision instance identifier (but have not started writing 
any part of the identifier), you can just press tab, and the *latest* identifier will be completed. 

For example, let's say you run this::

	$ gp-instance-create -c single-gridftp-ec2.conf
	Created new instance: gpi-52d4c9ec
	
If you then start writing this::

	$ gp-instance-start --debug 
	
And press tab, it will autocomplete directly to this:: 

	$ gp-instance-start --debug gpi-52d4c9ec
	
However, if you want to autocomplete with a different identifier (not the latest one), then start writing
the identifier, like this::

	$ gp-instance-start --debug gpi-2
	
Press tab, and BASH will show you all the identifiers that begin with ``gpi-2``::

	$ gp-instance-start --debug gpi-2
	gpi-217e7ab2  gpi-2c6170a7  gpi-2ff01dc6
