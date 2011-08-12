name "domain-login"
description "A domain's login machine"
run_list "role[domain-nfsnis-client]", "role[globus]"

