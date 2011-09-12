Welcome to Globus Provision!
============================

Globus Provision is a tool for deploying fully-configured `Globus <http://www.globus.org/>`_ systems 
on `Amazon EC2 <http://aws.amazon.com/ec2/>`_. It is designed to 
be simple to use, and will allow you to deploy common Globus services, such as GridFTP and GRAM, 
in just minutes. Globus Provision will also take care of 
generating user accounts, certificates, setting up NFS/NIS, etc.  

Globus Provision currently supports the following Globus software:

* `GridFTP 5.1.1 <http://dev.globus.org/wiki/GridFTP>`_
* `MyProxy 5.1.1 <http://grid.ncsa.illinois.edu/myproxy/>`_
* `GRAM <http://dev.globus.org/wiki/GRAM>`_ (coming soon; will be included once version 5.2 
  of the Globus Toolkit is released)

Globus Provision can also set up the following software:

* A `Condor <http://www.cs.wisc.edu/condor/>`_ pool with any number of worker nodes. The number 
  of worker nodes can be dynamically increased and decreased.
* `Galaxy <http://galaxy.psu.edu/>`_, with experimental integration with Globus Online Transfer

Globus Provision can deploy these services in any combination you need. For example,
you could deploy a single GridFTP server, a Condor pool with ten worker nodes and a GRAM server, 
or 30 GridFTP servers to teach a tutorial where each student needs their own GridFTP server to 
play around with. Once these services are deployed, you can dynamically add and remove software,
hosts, and user accounts.

Additionally, Globus Provision has experimental support for the `Globus Online <https://www.globusonline.org/>`_
Transfer service. Once you've deployed a GridFTP server on the cloud, you can register that
server as a Globus Online Transfer endpoint.

For more details on what Globus Provision can do, take a look at :ref:`whatis`, or
get started right away with our :ref:`Quickstart Guide <chap_quickstart>`.

.. toctree::
   :hidden:

   whatis
   download
   ami
   support
   docs
   intro_common



