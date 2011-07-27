name "domain-gridftp"
description "A domain's GridFTP machine"
run_list "role[domain-nfsnis-client]", "role[globus]", "recipe[globus::gridftp]", "recipe[demogrid::gridmap]"

