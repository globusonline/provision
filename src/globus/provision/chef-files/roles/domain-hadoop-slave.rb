name "domain-hadoop-slave"
description "A domain's Hadoop slave node"
run_list "recipe[hadoop::hadoop-slave]"

