from demogrid.common.persistence import *
from demogrid.core.topology import *
import textwrap


def print_section(title, marker):
    print title
    print marker * len(title)

print_section("Topology", "*")

def gen_cls_doc(cls):
    print_section("``%s``" % cls.__name__, "=")
    
    doc = cls.__doc__
    if doc != None:
        doc = textwrap.dedent(doc).strip()
    else:
        doc = "TODO"    
    
    p_names = cls.properties.keys()
    p_names.sort()
    
    for p_name in p_names:
        p = cls.properties[p_name]
        
        description = textwrap.dedent(p.description).strip()
        #print "**%s**" % p_name
        print_section(p_name,"-")
        print
        print description
        print

gen_cls_doc(Topology)
gen_cls_doc(Domain)
gen_cls_doc(Node)
gen_cls_doc(User)
gen_cls_doc(GridMapEntry)
gen_cls_doc(GOEndpoint)
gen_cls_doc(DeployData)
gen_cls_doc(EC2DeployData)


