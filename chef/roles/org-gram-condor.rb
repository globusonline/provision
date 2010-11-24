name "org-gram-condor"
description "An organization's GRAM machine (with Condor)"
run_list "role[org-gram]", "recipe[demogrid::condor_head]", "recipe[demogrid::gram-condor]"

