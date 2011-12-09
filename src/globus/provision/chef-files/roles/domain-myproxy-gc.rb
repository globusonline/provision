name "domain-myproxy-gc"
description "A domain's MyProxy server (using a Globus Connect certificate)"
run_list "role[globus]", "recipe[provision::simpleca]", "recipe[provision::ca]", "recipe[globus::myproxy-gc]"

