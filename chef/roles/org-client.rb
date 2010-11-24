name "org-client"
description "An organization client machine (any machine that is not the server)"
run_list "recipe[demogrid::demogrid_node]", "recipe[demogrid::nis_client]", "recipe[demogrid::nfs_client]"

