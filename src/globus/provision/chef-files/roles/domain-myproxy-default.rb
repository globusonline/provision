name "domain-myproxy-default"
description "A domain's MyProxy server"
run_list "role[globus]", "recipe[provision::simpleca]", "recipe[provision::ca]", "recipe[globus::myproxy-default]"

