name "org-auth"
description "A single organization's authentication/authorization server"
run_list "role[org-client]", "role[globus]", "recipe[demogrid::simpleca]", "recipe[demogrid::ca]", "recipe[demogrid::myproxy_org]"

