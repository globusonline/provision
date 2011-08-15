name "domain-gridftp"
description "A domain's GridFTP machine"
run_list "role[globus]", "recipe[globus::gridftp]", "recipe[provision::gridmap]"

