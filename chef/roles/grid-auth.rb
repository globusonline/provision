name "grid-auth"
description "A grid's authentication/authorization server"
run_list "role[globus]", "recipe[demogrid::simpleca]", "recipe[demogrid::ca]", "recipe[demogrid::myproxy]", "recipe[demogrid::myproxy_users]"

