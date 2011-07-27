name "globus"
description "A machine running Globus"
run_list "recipe[globus::client-tools]", "recipe[demogrid::ca]", "recipe[demogrid::hostcert]"

