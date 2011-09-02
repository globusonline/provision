# -------------------------------------------------------------------------- #
# Copyright 2010-2011, University of Chicago                                 #
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

from distribute_setup import use_setuptools
use_setuptools(version="0.6.15")
from setuptools import setup, find_packages
import sys

sys.path.insert(0, './src')
from globus.provision import RELEASE

cmds = {"globus.provision.cli.api":
        ["gp-instance-create", "gp-instance-describe", "gp-instance-start", "gp-instance-update", 
         "gp-instance-stop", "gp-instance-terminate", "gp-instance-list", "gp-instance-add-user", "gp-instance-add-host",
         "gp-instance-remove-users", "gp-instance-remove-hosts"],
         
        "globus.provision.cli.ec2":
        ["gp-ec2-create-ami", "gp-ec2-update-ami"],
        
        "globus.provision.cli.globusonline":
        ["gp-go-register-endpoints"]
        }

eps = []
for mod in cmds:
    for name in cmds[mod]:
        clsname = name.replace("-","_")
        eps.append("%s = %s:%s_func" % (name, mod, clsname))


setup(name='globus-provision',
      version=RELEASE,
      description='A tool for deploying fully-configured Globus systems on Amazon EC2',
      author='University of Chicago',
      author_email='borja@cs.uchicago.edu',
      url='http://globus.org/provision',
      package_dir = {'': 'src'},      
      packages=find_packages("src", exclude=["dg_paraproxy"]),
      
      install_requires = ['boto>=2.0', 'paramiko>=1.7.7.1', 'colorama>=0.2.4', 'pyOpenSSL>=0.10',
                          'globusonline-transfer-api-client>=0.10.7'],
      setup_requires = [ "setuptools_git >= 0.4.2", ],
      include_package_data=True,
      
      entry_points = {
        'console_scripts': eps
        },

      zip_safe = False,

      license="Apache Software License",
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Education',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering',
          'Topic :: System :: Distributed Computing'
          ]
     )
