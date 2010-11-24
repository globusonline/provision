name "org-gram"
description "An organization's GRAM machine"
run_list "role[org-client]", "role[globus]", "recipe[demogrid::gram]", "recipe[demogrid::gridmap]"

