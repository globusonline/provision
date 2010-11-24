name "org-gram-pbs"
description "An organization's GRAM machine (with Torque/Maui)"
run_list "role[org-gram]", "recipe[demogrid::torque_head]", "recipe[demogrid::gram-pbs]", "recipe[demogrid::openmpi]"

