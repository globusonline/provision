from os import walk
from distutils.core import setup

data_files = []
for root, dirs, files in walk("chef/"):
    if len(files) > 0:
        data_files.append(("share/demogrid/" + root,[root + "/" + f for f in files]))

data_files += [('share/demogrid/etc/', ["etc/demogrid.conf.sample",
                                        "etc/uvb.template"]),
               ('share/demogrid/lib/', ["lib/chef-node.sh",
                                        "lib/create_from_master_img.sh"]),
               ('share/demogrid/lib/uvb', ["lib/uvb/files-chefserver.txt",
                                           "lib/uvb/post-install-chefserver.sh"]),
              ]

setup(name='demogrid',
      version='0.1.0',
      description='DemoGrid',
      author='University of Chicago',
      author_email='borja@cs.uchicago.edu',
      url='',
      package_dir = {'': 'lib'},
      packages=['demogrid'],
      scripts=['bin/demogrid-clone-image', 
               'bin/demogrid-prepare', 
               'bin/demogrid-register-host-chef', 
               'bin/demogrid-register-host-libvirt'],
      data_files=data_files,
      classifiers=[
          'Development Status :: 3 - Alpha',
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
