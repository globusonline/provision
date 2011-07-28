package "libshadow-ruby1.8"
package "nis"
package "portmap"
package "nfs-common"
package "autofs"
package "xinetd"
package "libssl0.9.8"

include_recipe "globus::client-tools"
package "globus-simple-ca"
package "myproxy-server"
package "globus-gridftp-server-progs"
package "libglobus-xio-gsi-driver-dev"

include_recipe "condor::condor"


