name "domain-hadoop-master"
description "A domain's Hadoop master node"
run_list "recipe[hadoop::hadoop-master]"

