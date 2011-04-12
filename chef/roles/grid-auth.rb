name "grid-auth"
description "A grid's authentication/authorization server"
run_list "role[globus]", "recipe[demogrid::simpleca]", "recipe[demogrid::ca]", "recipe[demogrid::myproxy_grid]", "recipe[demogrid::myproxy_users]"

