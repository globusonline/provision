name "domain-gram"
description "A domain's GRAM machine"
run_list "role[domain-nfsnis-client]", "role[globus]", "recipe[demogrid::gram]", "recipe[demogrid::gridmap]"

