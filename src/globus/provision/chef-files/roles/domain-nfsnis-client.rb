name "domain-nfsnis-client"
description "A node with NFS/NIS"
run_list "recipe[provision::gp_node]","recipe[provision::software_path]", "recipe[provision::nis_client]", "recipe[provision::nfs_client]"

