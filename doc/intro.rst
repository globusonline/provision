.. _chap_intro:

Introduction
************

Welcome to the Globus Provision documentation! This is the primary source of documentation for 
the `Globus Provision <http://globus.org/provision>`_ project. This documentation is meant as both
a tutorial introduction to Globus Provision and a reference guide. To read it as a tutorial, 
just read this chapter and the next ones sequentially until you hit the reference chapters.
Throughout the text, we'll tell you what chapters or sections you can safely skip.

.. ifconfig:: website == "yes"

	If you need any help while using Globus Provision, or need additional information on any of the 
	contents of this documentation, please don't hesitate to contact us through our mailing list. 
	You can find instructions on how to subscribe on the :ref:`support` page. 

.. ifconfig:: website == "no"

	If you need any help while using Globus Provision, or need additional information on any of the 
	contents of this documentation, please don't hesitate to contact us through our mailing list. 
	You can find instructions on how to subscribe on the Support page of the
	`Globus Provision website <http://globus.org/provision>`_.

What is Globus Provision?
=========================

.. ifconfig:: website == "yes"

   .. note::
   	  If you've already read the :ref:`whatis` page on the Globus Provision
   	  website, you can skip this section and go straight to :ref:`sec_terminology` 

.. include:: intro_common.rst

.. _sec_terminology:

Some terminology
================

Before we move on to the rest of the documentation, let's get some terminology
out of the way:

**Topology**
	Earlier, we said that Globus Provision can deploy fully-configured "Globus systems".
	Throughout the documentation, we'll refer to the *specification* of such a system
	as a *topology*. For example, the "My Cluster" topology includes a GridFTP server,
	a Condor cluster, four users, etc.
	
**Domains**
	A topology can be composed of one or more domains. The "My Cluster" topology has
	a single domain, whereas the "Mini-clusters" topology has multiple domains
	(one for each mini-cluster). The main distinguishing characteristic of a domain
	is that it has its own set of users, and that only the users in a given domain
	will be able to access the resources in that domain.

**Host (or Node)**
	A domain contains one or more hosts (which we will occasionally refer to
	as *nodes*). Take into account that, when using the simple configuration file
	format shown earlier, you don't specify the domain's hosts directly (for example,
	we specified options ``gram: yes`` and ``condor: yes``, and Globus Provision
	allocated a single host for both). Globus Provision's lower-level interface does
	allow you to specify each individual host, and what software and services must
	run in each of them.

**Instance**
	When a topology is actually deployed, we refer to it as a *Globus Provision instance*.
	You can think of the topology as the specification of what you want to run,
	and an instance as the actual running system. Notice how the commands shown above
	perform operations on your instance: starting it, adding a new host to it, etc.


