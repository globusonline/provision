from globus.provision import AMI
import os

ami = AMI["us-east-1"]["32-bit"]

sample_files = os.listdir("../samples/")

for fname in sample_files:
    fname1 = "../samples/" + fname
    fname2 = "./_build/samples/" + fname

    f1 = open(fname1, "r")
    f2 = open(fname2, "w")
    
    for l in f1:
        f2.write(l.replace("%AMI%", ami))
    
    f1.close()
    f2.close()
