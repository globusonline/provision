import demogrid.cli.api as api
import demogrid.cli.ec2 as ec2
from docutils.core import publish_string
import re
import textwrap

OPTION_LEN=50
DESCRIPTION_LEN=50

commands = [api.demogrid_create, api.demogrid_start, ec2.demogrid_ec2_create_ami]

def print_section(title, marker):
    print title
    print marker * len(title)

print_section("Command-line Interface", "*")

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
        