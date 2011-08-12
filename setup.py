from os import walk
from setuptools import setup, find_packages

cmds = {"globus.provision.cli.api":
        ["gp-create", "gp-describe-instance", "gp-start", "gp-update-topology", "gp-stop",
         "gp-terminate", "gp-list-instances", "gp-add-user", "gp-add-host",
         "gp-remove-users", "gp-remove-hosts"],
         
        "globus.provision.cli.ec2":
        ["gp-ec2-create-ami", "gp-ec2-update-ami"],
        
        "globus.provision.cli.globusonline":
        ["gp-go-register-endpoint"]
        }

eps = []
for mod in cmds:
    for name in cmds[mod]:
        clsname = name.replace("-","_")
        eps.append("%s = %s:%s_func" % (name, mod, clsname))


setup(name='globus-provision',
      version='0.3.0rc1',
      description='Globus Provision',
      author='University of Chicago',
      author_email='borja@cs.uchicago.edu',
      url='http://globus.org/provision',
      package_dir = {'': 'src'},      
      packages=find_packages("src", exclude=["dg_paraproxy"]),
      
      install_requires = ['boto>=2.0', 'paramiko>=1.7.7.1'],
      setup_requires = [ "setuptools_git >= 0.4.2", ],
      include_package_data=True,
      
      entry_points = {
        'console_scripts': eps
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
