import textwrap
import re
import glob
import os.path

cookbooks = ["provision", "globus", "condor", "galaxy"]

def print_section(title, marker):
    print title
    print marker * len(title)

roles_files = glob.glob("../src/globus/provision/chef-files/roles/*.rb")
roles_files.sort()

print_section("Roles", "=")
for role_file in roles_files:
    f = open(role_file)
    role = {}
    for line in f:
        if len(line.strip()) > 0:
            k,v = line.split(" ", 1)
            role[k.strip()] = v.strip().replace("\"","")
        
    print "**%s**" % role["name"]
    print "  %s" % role["description"]
    print
    print "  Runs: ``%s``" % role["run_list"]
    print

for cookbook in cookbooks:
    print_section("``%s`` cookbook" % cookbook, "=")
    print
    
    files = glob.glob("../src/globus/provision/chef-files/cookbooks/%s/recipes/*.rb" % cookbook)
    files.sort()

    for file in files:
        recipe_name = os.path.basename(file).replace(".rb","")
        
        f = open(file)
        
        lines = []
        title = None
        for l in f:
            if l.startswith("## "):
                if l.startswith("## RECIPE:"):
                    title = l.replace("## RECIPE:","").strip()
                else:                
                    lines.append(l.replace("## ","").strip())
        
        description = "\n".join(lines).strip()
        
        if title != None:
            print ".. _chef_%s_%s:" % (cookbook, recipe_name)
            print
            print_section("``%s`` (%s)" % (recipe_name, title), "-")
            print description
            print
    
    print