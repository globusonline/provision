name "org-pbs"
description "An organization's Torque/Maui head node (without GRAM)"
run_list "recipe[demogrid::torque_head]", "recipe[demogrid::openmpi]"

