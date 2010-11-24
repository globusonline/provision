name "org-clusternode-pbs"
description "An organization's PBS node"
run_list "role[org-client]", "recipe[demogrid::torque_worker]", "recipe[demogrid::openmpi]"

