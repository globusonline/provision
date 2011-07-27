name "domain-nfsnis-client"
description "An domain's client machine (any machine that is not the NFS/NIS server)"
run_list "recipe[demogrid::demogrid_node]", "recipe[demogrid::nis_client]", "recipe[demogrid::nfs_client]"

