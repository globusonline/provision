# -------------------------------------------------------------------------- #
# Copyright 2010, University of Chicago                                      #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# RECIPE: Globus Toolkit 5.0.3 basic install
#
# This recipe performs a barebones install of Globus. Users on a node where this
# recipe has been run will have access to Globus command-line utilities,
# but little else. GridFTP, GRAM, etc. are set up in separate recipes.
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Globus Toolkit 5.0.3 only provides a source tarball. Installing from scratch
# would involve compiling the toolkit on each VM, which would take too long.
# So, we use a "precompiled" version prepared on Ubuntu Lucid 32-bit and 64-bit machines.
# Since making GT 5.0.3 creates files in both the source tree and in
# GLOBUS_LOCATION, we have tarballs for both.
#
# This is a terrible kluge, and will be removed once we have a binary distribution
# of the toolkit that we can use.
if node[:kernel][:machine] == "i686" then
  gl_tarball = "gt5.0.3-globus_location_i686.tgz"
  install_tarball = "gt5.0.3-source-install_i686.tgz"
elsif node[:kernel][:machine] == "x86_64" then
  gl_tarball = "gt5.0.3-globus_location_x86_64.tgz"
  install_tarball = "gt5.0.3-source-install_x86_64.tgz"
end

# Needed to create the globus user
package "libshadow-ruby1.8" do
  action :install
end


# Create the globus group and user

group "globus" do
  gid 500
end

user "globus" do
  comment "Globus User"
  uid 500
  gid 500
  home "/home/globus"
  password "$1$rmHlRI5D$xNAqmRlrB6.P6SHOi2gpw1" # Password: globus
  shell "/bin/bash"
  supports :manage_home => true
end


# If GLOBUS_LOCATION doesn't exist, then do the following:
#  - un-tar the pre-compiled GLOBUS_LOCATION tarball in GLOBUS_LOCATION
#  - un-tar the pre-compiled source tree, and run "make install" to
#    complete the installation
if ! File.exists?(node[:globus][:dir])

  if ! File.exists?(node[:globus][:srcdir])
  	cookbook_file "/var/tmp/#{install_tarball}" do
  	  source "#{install_tarball}"
  	  mode 0755
  	  owner "globus"
  	  group "globus"
  	end
  	
    execute "tar" do
      user "globus"
      group "globus"
      cwd "/var/tmp"
      command "tar xzf /var/tmp/#{install_tarball}"
      action :run
    end  	
    
    # Cleanup
    file "/var/tmp/#{install_tarball}" do
      action :delete
    end       
  end
  
  directory node[:globus][:dir] do
    owner "globus"
    group "globus"
    mode "0755"
    action :create
  end
  
  cookbook_file "/var/tmp/#{gl_tarball}" do
    source "#{gl_tarball}"
    mode 0755
    owner "globus"
    group "globus"
  end

  execute "tar" do
	  user "globus"
	  group "globus"
	  command "tar xzf /var/tmp/#{gl_tarball} --directory #{node[:globus][:dir]}"
	  action :run
	end

  file "/var/tmp/#{gl_tarball}" do
    action :delete
  end       
	
	execute "make install" do
	  user "globus"
	  group "globus"
	  cwd node[:globus][:srcdir]
	  command "make install 2>&1 | tee build.log"
	  action :run
	  environment(
	    "GLOBUS_LOCATION" => node[:globus][:dir]
	  )
	end

end

# Add the Bash profile file in the globus user's home directory,
# so it will have GLOBUS_LOCATION, PATH, etc. properly set up.
template "/home/globus/.profile" do
  source "profile.erb"
  mode 0644
  owner "globus"
  group "globus"
  variables(
    :globus_location => node[:globus][:dir]
  )
end



