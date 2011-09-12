from globus.provision.common.utils import rest_table
from globus.provision import AMI, RELEASE

print ".. _ami:"
print

print "Amazon Machine Images for Globus Provision"
print "=========================================="

print """
These are the AMIs currently available for use with Globus Provision.
All these images were generated using the Ubuntu 11.04 AMIs in
`Alestic <http://alestic.com>`_ 

"""

col_names = ["Region", "Architecture", "AMI"]
rows = []
for region in AMI:
    archs = AMI[region].keys()
    archs.sort()
    for arch in archs:
        rows.append((region, arch, AMI[region][arch]))

print rest_table(col_names, rows)

print """
We recommend you use these AMIs when using the EC2 deployer, as these AMIs
include most of the packages required by Globus Provision (you should be able
to use a stock Ubuntu image, but the deployment time will increase considerably,
since those packages will have to be installed before Globus Provision can configure
the instance). 

Take into account that all the sample files in the documentation use the 
32-bit AMI in the us-east-1 region. 
"""
        