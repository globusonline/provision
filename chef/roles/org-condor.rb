name "org-condor"
description "An organization's Condor head node (without GRAM)"
run_list "role[org-client]", "recipe[demogrid::condor_head]"

