name "domain-gram"
description "A domain's GRAM machine"
run_list "role[globus]", "recipe[globus::gram]", "recipe[provision::gridmap]"

