name "domain-clusternode-condor"
description "A domain's Condor node"
run_list "role[domain-nfsnis-client]", "recipe[condor::condor_worker]"

