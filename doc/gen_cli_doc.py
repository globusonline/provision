import globus.provision.cli.api as api
import globus.provision.cli.ec2 as ec2
import globus.provision.cli.globusonline as globusonline
from docutils.core import publish_string
import re
import textwrap
import operator

OPTION_LEN=50
DESCRIPTION_LEN=100

commands = [api.gp_create, api.gp_start, api.gp_describe_instance,
            api.gp_update_topology, api.gp_stop, api.gp_terminate,
            api.gp_add_host, api.gp_add_user, api.gp_remove_hosts,
            api.gp_remove_users, api.gp_list_instances,
            
            ec2.gp_ec2_create_ami, ec2.gp_ec2_update_ami,
            
            globusonline.gp_go_register_endpoint
            ]

def print_section(title, marker):
    print title
    print marker * len(title)

commands.sort(key=operator.attrgetter("name"))
for command in commands:
    c = command([])
    print 
    print_section("``%s``" % command.name, "=")
    print
    doc = command.__doc__
    if doc != None:
        doc = textwrap.dedent(doc).strip()
    else:
        doc = "TODO"
    print doc
    print

    opts = c.optparser.option_list
    c.optparser.formatter.store_option_strings(c.optparser)
    
    print "+-" + ("-"*OPTION_LEN)            + "-+-" + ("-"*DESCRIPTION_LEN)                + "-+"
    print "| " + "Option".ljust(OPTION_LEN)  + " | " + "Description".ljust(DESCRIPTION_LEN) + " |"
    print "+=" + ("="*OPTION_LEN)            + "=+=" + ("="*DESCRIPTION_LEN)                + "=+"
    for opt in opts:
        if opt.action != "help":
            opt_string = "``%s``" % c.optparser.formatter.option_strings[opt]            
            opt_help = textwrap.dedent(opt.help).strip()
            
            opt_help_lines = opt_help.split("\n")
            
            # First line
            print "| " + opt_string.ljust(OPTION_LEN)  + " | " + opt_help_lines[0].ljust(DESCRIPTION_LEN) + " |"
            
            for l in opt_help_lines[1:]:
                print "| " + (" "*OPTION_LEN)  + " | " + l.ljust(DESCRIPTION_LEN) + " |"
            
            print "+-" + ("-"*OPTION_LEN)  + "-+-" + ("-"*DESCRIPTION_LEN)                + "-+"

    print
        