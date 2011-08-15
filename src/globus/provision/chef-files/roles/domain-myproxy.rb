name "domain-myproxy"
description "A single organization's MyProxy server"
run_list "role[globus]", "recipe[provision::simpleca]", "recipe[provision::ca]", "recipe[globus::myproxy]"

