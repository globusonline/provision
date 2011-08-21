from globus.provision.common.persistence import *
from globus.provision.core.topology import *
from globus.provision.common.utils import rest_table
import textwrap


def print_section(title, marker):
    print title
    print marker * len(title)
    
def get_ptype(p):
    p_type = pt_to_str(p.type, p.items)
    if inspect.isclass(p.type) and issubclass(p.type, PersistentObject):
        p_type = ":ref:`%s <topology_%s>`" % (p.type.__name__, p.type.__name__)
    elif p.type == PropertyTypes.ARRAY and inspect.isclass(p.items) and issubclass(p.items, PersistentObject):
        p_type = "list of :ref:`%s <topology_%s>`" % (p.items.__name__, p.items.__name__)
    return p_type

def gen_cls_doc(cls):
    print ".. _topology_%s:" %  cls.__name__
    print
    print_section("``%s`` Object" % cls.__name__, "=")
    print
    doc = cls.__doc__
    if doc != None:
        doc = textwrap.dedent(doc).strip()
    else:
        doc = ""    
    
    p_names = cls.properties.keys()
    p_names.sort()
    
    col_names = ["Property Name", "Type", "Required", "Editable"]
    rows = []
    for p_name in p_names:
        p = cls.properties[p_name]
        p_type = get_ptype(p)
            
        row = []
        
        row = [":ref:`%s <topology_%s_%s>`" % (p_name, cls.__name__, p_name), p_type]
        if p.required:
            row.append("**Yes**")
        else:
            row.append("No")

        if p.editable:
            row.append("Yes")
        else:
            row.append("No")

        rows.append(row)
        
    print ".. centered:: Summary of ``%s``'s Properties" % cls.__name__
    print
    print rest_table(col_names, rows)
    
    for p_name in p_names:
        p = cls.properties[p_name]
        description = textwrap.dedent(p.description).strip()

        p_type = get_ptype(p)

        print ".. _topology_%s_%s:" %  (cls.__name__, p_name)
        print     
        print_section(p_name,"-")
        print
        print "*Type*: %s" % p_type
        print
        print "*Required*:",
        if p.required:
            print "**Yes**"
        else:
            print "No"
        print
        print "*Editable*:",
        if p.editable:
            print "Yes"
        else:
            print "No"
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


