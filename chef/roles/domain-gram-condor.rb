name "domain-gram-condor"
description "A domain's GRAM machine (with Condor)"
run_list "role[domain-gram]", "recipe[condor::condor_head]", "recipe[globus::gram-condor]"

