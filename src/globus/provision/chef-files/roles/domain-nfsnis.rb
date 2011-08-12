name "domain-nfsnis"
description "An domain's NFS/NIS server"
run_list "recipe[demogrid::demogrid_node]", "recipe[demogrid::nis_server]", "recipe[demogrid::nfs_server]", "recipe[demogrid::domain_users]"

