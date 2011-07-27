name "domain-condor"
description "A domain's Condor head node (without GRAM)"
run_list "role[domain-nfsnis-client]", "recipe[condor::condor_head]"

