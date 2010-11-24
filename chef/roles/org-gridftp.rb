name "org-gridftp"
description "An organization's GridFTP machine"
run_list "role[org-client]", "role[globus]", "recipe[demogrid::gridftp]", "recipe[demogrid::gridmap]"

