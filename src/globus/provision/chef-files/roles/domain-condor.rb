name "domain-condor"
description "A domain's Condor head node (without GRAM)"
run_list "recipe[condor::condor_head]"

