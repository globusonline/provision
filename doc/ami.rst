.. _ami:

Amazon Machine Images for Globus Provision
==========================================

These are the AMIs currently available for use with Globus Provision.
All these images were generated using the Ubuntu 11.04 AMIs in
`Alestic <http://alestic.com>`_ 


+-----------+--------------+--------------+
| Region    | Architecture | AMI          |
+===========+==============+==============+
| us-east-1 | 32-bit       | ami-8ea37ee7 |
+-----------+--------------+--------------+
| us-east-1 | 64-bit       | ami-baa37ed3 |
+-----------+--------------+--------------+
| us-east-1 | HVM          | ami-XXXXXXXX |
+-----------+--------------+--------------+


We recommend you use these AMIs when using the EC2 deployer, as these AMIs
include most of the packages required by Globus Provision (you should be able
to use a stock Ubuntu image, but the deployment time will increase considerably,
since those packages will have to be installed before Globus Provision can configure
the instance). 

Take into account that all the sample files in the documentation use the 
32-bit AMI in the us-east-1 region. 

