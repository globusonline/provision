name "domain-myproxy"
description "A single organization's MyProxy server"
run_list "role[domain-nfsnis-client]", "role[globus]", "recipe[demogrid::simpleca]", "recipe[demogrid::ca]", "recipe[globus::myproxy]"

