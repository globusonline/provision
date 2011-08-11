import glob
import os

from os import environ

from boto.ec2.connection import EC2Connection,RegionInfo
from boto import connect_ec2
       

def create_ec2_connection(hostname = None, path = None, port = None):
    if hostname == None:
        # We're using EC2.
        # Check for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY,
        # and use EC2Connection. boto will fill in all the values
        if not (environ.has_key("AWS_ACCESS_KEY_ID") and environ.has_key("AWS_SECRET_ACCESS_KEY")):
            return None
        else:
            return EC2Connection()
    else:
        # We're using an EC2-ish cloud.
        # Check for EC2_ACCESS_KEY and EC2_SECRET_KEY (these are used by Eucalyptus;
        # we will probably have to tweak this further to support other systems)
        if not (environ.has_key("EC2_ACCESS_KEY") and environ.has_key("EC2_SECRET_KEY")):
            return None
        else:
            print "Setting region"
            region = RegionInfo(name="eucalyptus", endpoint=hostname)
            return connect_ec2(aws_access_key_id=environ["EC2_ACCESS_KEY"],
                        aws_secret_access_key=environ["EC2_SECRET_KEY"],
                        is_secure=False,
                        region=region,
                        port=port,
                        path=path)            


def parse_extra_files_files(f):
    l = []
    extra_f = open(f)
    for line in extra_f:
        srcglob, dst = line.split()
        srcs = glob.glob(os.path.expanduser(srcglob))
        srcs = [s for s in srcs if os.path.isfile(s)]
        dst_isdir = (os.path.basename(dst) == "")
        for src in srcs:
            full_dst = dst
            if dst_isdir:
                full_dst += os.path.basename(src)
            l.append( (src, full_dst) )
    return l


# From http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)



