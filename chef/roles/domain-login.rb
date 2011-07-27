name "org-login"
description "An organization's login machine"
run_list "role[org-client]", "role[globus]"

