name "globus"
description "A machine running Globus"
run_list "recipe[demogrid::globus]", "recipe[demogrid::ca]", "recipe[demogrid::hostcert]"

