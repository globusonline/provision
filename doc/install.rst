.. _chap_install:

Installing Globus Provision
***************************

.. highlight:: bash

You can install Globus Provision using one of the following procedures.

* :ref:`Using the "easy_install" tool <easy_install>`. This is the simplest option, as ``easy_install``
  will take care of downloading and installing not just Globus Provision but also all its dependencies.
  You must already have `Python <http://www.python.org/>`_ (version 2.6 or higher) and 
  `Python Distribute <http://packages.python.org/distribute/>`_ (version 0.6.15 or higher)
  installed on your machine (or you must be able to install them). To check if both are installed,
  try running ``easy_install --version`` from the command line. If the command is available, and it
  prints out a version number equal or higher than 0.6.15, you will be able to install Globus Provision 
  using ``easy_install``.
* :ref:`Using a source tarball <source_tarball>`. If you are unable to install Globus Provision using
  ``easy_install``, you can download a tarball with the Globus Provision source code. Your machine must
  have Python installed on it, but not the Python Distribute package (the tarball includes a setup
  script that will automatically download and install Python Distribute for you).
* :ref:`Downloading the latest code from GitHub <github_install>`. Choose this option if you want to track 
  the latest code in our GitHub repository, 

.. _easy_install:

Using ``easy_install``
======================

This option has the following prerequisites:

* `Python <http://www.python.org/>`_ 2.6 or higher. If Python is not available on your machine, 
  you can find installation instructions here: http://www.python.org/getit/. Take into account that,
  if you are using a Linux distribution, you should be able to install it using your distribution's
  package manager (e.g., ``apt-get install python`` on Debian and Ubuntu). If you are using a Mac,
  Python is included by default; however, if your version is too old, take a look at the following
  instructions: http://www.python.org/getit/mac/
* `Python Distribute <http://packages.python.org/distribute/>`_ 0.6.15 or higher. As noted above,
  you can verify if this package is installed by running ``easy_install --version``. If it is not
  available, you can find installation instructions here: http://pypi.python.org/pypi/distribute#installation-instructions.
  Take into account that, although Python Distribute is included as an optional package in most 
  Linux distributions, it is sometimes available under the name "Setuptools" (e.g., ``python-setuptools`` 
  in Debian and Ubuntu systems), since Python Distribute is a fork of the Setuptools project.

If you meet these prerequisites, you should be able to
install Globus Provision simply by running this as ``root``::

	easy_install -U globus-provision	
	
If you are using Ubuntu or Mac OS X, you will likely just need to run this::
	
	sudo easy_install -U globus-provision
		
If you do not have administrative privileges on your machine, you will have to install Globus
Provision under your regular user account::

	easy_install -U globus-provision --user
	
.. note::
	Installing Globus Provision in your home directory will install the Globus Provision commands
	in ``~/.local/bin``, which may not be in your PATH environment variable. If not, make sure to
	update the definition of your PATH environment variable (e.g., in the ``~/.profile`` file if
	you are using a BASH shell).
	
	Alternatively, you can also request that the commands be installed in a directory that is
	already in your $PATH. You may want to use ``~/bin/``, as most Linux distributions will
	automatically include that directory in your PATH.
	
	::	

		easy_install -U globus-provision --user -s ~/bin/
	
	
.. _source_tarball:

Using a source tarball
======================

If you do not have Python Distribute, or are unable to install it, you can still install Globus
Provision by downloading a source tarball yourself. This tarball contains an installation script
that will install and setup Python Distribute, and then proceed to install Globus Provision.

You will first have to download the latest source tarball from the Python Package Index: 
http://pypi.python.org/pypi/globus-provision

Next, untar the tarball and run the installation script as ``root``:

.. parsed-literal::

	tar xvzf globus-provision-|release|.tar.gz
	cd globus-provision-|release|
	python setup.py install
	
.. note::
	If you are using Ubuntu or Mac OS X, you will likely just need to run this::
	
		sudo python setup.py install
		
If you do not have administrative privileges on your machine, you can choose to install
everything inside your home directory:
	
::

	python setup.py install --user
	

.. _github_install:

Tracking latest code from GitHub
================================

If you want to use the latest version of our code from our GitHub repository, the steps
are similar to installing a source tarball. However, instead of downloading a tarball, you
will use git to clone our repository on your machine. Simply run the following::

	git clone git://github.com/globusonline/provision.git
	
This will create a directory called ``provision``. In it, you will find the same ``setup.py``
script described in the previous section. If you want to install Globus Provision, and not
make any modifications to the code, you should run ``python setup.py install`` as described
in the previous section.

If you intend to modify the code, and want the Globus Provision commands to use the code
in the git repository you've created on your machine, you can instead install Globus
Provision in "developer" mode::

	python setup.py develop

This will install Globus Provision but, instead of copying the Python source code
to a system directory, it will create a pointer to the source directory you checked out.
That way, any changes you make to the source code will take effect immediately
(without having to reinstall Globus Provision).

Take into account that there are, at least, two branches in our GitHub repository: ``master``
and ``dev``. The former always contains the latest stable release, including bug fixes, and
the former contains the very latest version of our code (which may not work as reliably
as the code in the ``master`` branch). By default, your repository will track the ``master``
branch. To switch to the ``dev`` branch, run the following::

	git checkout dev
	
To pull the latest changes from our GitHub repository, run the following::

	git pull origin
	
 
