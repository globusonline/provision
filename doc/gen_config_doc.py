from demogrid.core.config import DemoGridConfig
from demogrid.common.config import OPTTYPE_INT, OPTTYPE_FLOAT, OPTTYPE_STRING, OPTTYPE_BOOLEAN
import textwrap
import re

def print_section(title, marker):
    print title
    print marker * len(title)

print_section("Configuration File", "*")

for s in DemoGridConfig.sections:
    print_section("Section ``[%s]``" % s.name, "=")
    print
    print s.get_doc()
    print
    if s.required:
        print "*This section is required*"
    else:
        if s.required_if:
            print "This section is required when:"
            for r in s.required_if:
                sec,opt = r[0]
                val = r[1]
                print "* Option ``%s`` (in section ``[%s]``)" % (opt,sec)
                print "  is set to ``%s``" % val
            print
        else:
            print "This section is optional."
    print
    
    for opt in s.options:
        print_section("Option ``%s``" % opt.name, "-")
        print "**Type:**",
        if opt.valid:
            print "  " + ", ".join(["``%s``" % v for v in opt.valid])
        else:
            if opt.type == OPTTYPE_INT:
                print "Integer number"
            elif opt.type == OPTTYPE_FLOAT:
                print "Real number"
            elif opt.type == OPTTYPE_STRING:
                print "String"
            elif opt.type == OPTTYPE_BOOLEAN:
                print "``True`` or ``False``"
        print
        print "**Required:**",
        if opt.required:
            print "Yes"
        else:
            if opt.required_if:
                print "Only if"
                print "\\begin{itemize}"
                for r in opt.required_if:
                    sec,o = r[0]
                    val = r[1]
                    print "\\item"
                    print "Option \\texttt{%s} (in section \\texttt{[%s]})" % (o,sec)
                    print "is set to \\texttt{%s}" % val
                print "\\end{itemize}"
            else:
                txt = "No "
                if opt.default:
                    txt += "(default is ``%s``)" % opt.default
                print txt
        print
        optdoc = opt.get_doc()
        print optdoc
        print 
        