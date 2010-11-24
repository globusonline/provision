name "org-clusternode-condor"
description "An organization's Condor node"
run_list "role[org-client]", "recipe[demogrid::condor_worker]"

