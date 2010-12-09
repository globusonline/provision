package "libshadow-ruby1.8" do
  action :install
end

package "nis" do
  action :install
end

package "portmap" do
  action :install
end

package "nfs-common" do
  action :install
end

package "autofs" do
  action :install
end

package "xinetd" do
  action :install
end

include_recipe "demogrid::globus"
include_recipe "demogrid::condor"

