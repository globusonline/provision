import globus.provision.cli.api as api
import globus.provision.cli.ec2 as ec2
import globus.provision.cli.globusonline as globusonline
from globus.provision.cli import Command
from globus.provision.common.utils import rest_table

from docutils.core import publish_string
import re
import textwrap
import operator

OPTION_LEN=50
DESCRIPTION_LEN=100

commands = [api.gp_instance_create, api.gp_instance_start, api.gp_instance_describe,
            api.gp_instance_update, api.gp_instance_stop, api.gp_instance_terminate,
            api.gp_instance_add_host, api.gp_instance_add_user, api.gp_instance_remove_hosts,
            api.gp_instance_remove_users, api.gp_instance_list,
            
            ec2.gp_ec2_create_ami, ec2.gp_ec2_update_ami,
            
            globusonline.gp_go_register_endpoints
            ]

def print_section(title, marker):
    print title
    print marker * len(title)

commands.sort(key=operator.attrgetter("name"))
commands.insert(0, Command)
common_options = Command([]).optparser.option_list
common_options = [str(opt) for opt in common_options]

for command in commands:
    c = command([])
    print 
    if command == Command:
        print ".. _cli_common:"
        print
        print_section("Common options", "=")
        print
        print "These are the options common to all Globus Provision commands."
        print
    else:
        print ".. _cli_%s:" % command.name
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
    if command != Command:
        opts = [opt for opt in opts if str(opt) not in common_options]
    c.optparser.formatter.store_option_strings(c.optparser)
    
    if len(opts) > 0:
        col_names = ["Option", "Description"]
        rows = []
        
        for opt in opts:
            if opt.action != "help":
                opt_string = "``%s``" % c.optparser.formatter.option_strings[opt]            
                opt_help = textwrap.dedent(opt.help).strip()                
                
                rows.append([opt_string, opt_help])
                
        print rest_table(col_names, rows)
    
    else:
        print "This command has no options (besides the :ref:`common options <cli_common>`)"    



    print
        