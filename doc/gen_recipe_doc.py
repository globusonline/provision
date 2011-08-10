import textwrap
import re
import glob
import os.path

cookbooks = ["demogrid", "globus", "condor"]

def print_section(title, marker):
    print title
    print marker * len(title)

print_section("Chef recipe reference", "*")
print

for cookbook in cookbooks:
    print_section("``%s`` cookbook" % cookbook, "=")
    print
    
    files = glob.glob("../chef/cookbooks/%s/recipes/*.rb" % cookbook)
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
            print_section("``%s`` (%s)" % (recipe_name, title), "-")
            print description
            print
    
    print