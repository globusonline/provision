.. _chap_topology_ref:

Topology JSON reference
***********************

This chapter contains the specification of the :ref:`topology JSON format <chap_topology>`.
A topology in JSON format contains a single :ref:`topology_Topology` object. From that
object, you will be able to navigate to the specification of all the other objects it
contains.

The specification of each object contains a table summarizing that object's properties.
Besides the property name and type, a property has two other attributes:

* A **required** property is one that must have a value when a new Globus Provision instance
  is created with ``gp-instance-create``. 
* When an updated topology is specified with ``gp-instance-update``, you are only allowed
  to modify properties that are **editable**. If a property is a list of other values, 
  then you can only add/remove items from that list if the property is editable.  

.. toctree::
   :maxdepth: 2
   
   topology_ref.rst