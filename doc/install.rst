Installing Globus Provision
***************************

.. highlight:: bash

Installation options

* :ref:`Using the "easy_install" tool <easy_install>`.
* :ref:`Using a source tarball <source_tarball>`.
* :ref:`Downloading the latest code from GitHub <github_install>`. 

.. _easy_install:

Using ``easy_install``
======================

Do this::

	sudo easy_install globus-provision
	
::	

	easy_install globus-provision --user
	
.. note::
	Update PATH to include ~/.local/bin
	
	::	

		easy_install globus-provision --user -s ~/bin/
	
	
.. _source_tarball:

Using a source tarball
======================

::

	tar xvzf globus-provision-XXX.tar.gz
	cd globus-provision-XXX
	sudo python setup.py install
	
::

	python setup.py install --user
	

.. _github_install:

Tracking latest code from GitHub
================================

::

	git clone git://github.com/globusonline/provision.git
	

Same as source tarball.

If you don't want to install, remember to update PYTHONPATH


::

	python setup.py install_scripts -d ~/bin/
