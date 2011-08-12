from os import walk
from setuptools import setup, find_packages

import inspect

import demogrid.cli.api
import demogrid.cli.ec2
import demogrid.cli.globusonline

def gen_entrypoints(module):
    members = dict([(name,cmd) for name, cmd in inspect.getmembers(module)])
    cmd_names = [name for name, cmd in members.items() 
                 if inspect.isclass(cmd) and issubclass(cmd, demogrid.cli.Command) and cmd != demogrid.cli.Command]
    eps = []
    for name in cmd_names:
        if "%s_func" % name in members:
            cmd = members[name]
            eps.append("%s = %s:%s_func" % (cmd.name, module.__name__, name))

    return eps

setup(name='globus-provision',
      version='0.3.0rc1',
      description='Globus Provision',
      author='University of Chicago',
      author_email='borja@cs.uchicago.edu',
      url='http://globus.org/provision',
      package_dir = {'': 'src'},      
      packages=find_packages("src", exclude=["dg_paraproxy"]),
      
      install_requires = ['boto>=2.0', 'pycrypto>=2.3', 'paramiko>=1.7.7.1'],
      setup_requires = [ "setuptools_git >= 0.4.2", ],
      include_package_data=True,
      
      entry_points = {
        'console_scripts': gen_entrypoints(demogrid.cli.api) + 
                           gen_entrypoints(demogrid.cli.ec2) +
                           gen_entrypoints(demogrid.cli.globusonline)
        },

      package_data = {"chef":["*"]},
      zip_safe = False,
      #eager_resources=["chef/"],
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
