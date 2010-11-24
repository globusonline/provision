name "org-server"
description "An organization server"
run_list "recipe[demogrid::demogrid_node]", "recipe[demogrid::nis_server]", "recipe[demogrid::nfs_server]", "recipe[demogrid::org_users]"

