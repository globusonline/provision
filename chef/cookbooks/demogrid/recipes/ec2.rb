package "libshadow-ruby1.8"
package "nis"
package "portmap"
package "nfs-common"
package "autofs"
package "xinetd"
package "gcc"
package "libssl0.9.8"
package "libssl-dev"
package "expect"

include_recipe "demogrid::globus"
include_recipe "demogrid::condor"
include_recipe "demogrid::torque"
include_recipe "demogrid::gram-condor"
include_recipe "demogrid::gram-pbs"
