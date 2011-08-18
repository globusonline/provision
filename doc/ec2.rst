.. _chap_ec2:

Setting up Amazon EC2
*********************

* An `Access Key ID and Secret Access Key <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-credentials.html#using-credentials-access-key>`_.
  This will be used by Globus Provision to contact EC2 and request the creation of EC2 instances on
  which to deploy the topology (in this case, it will request a single EC2 instance to deploy
  a GridFTP server).
* An `SSH Keypair <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-credentials.html#using-credentials-keypair>`_.
  Globus Provision will use this to log into the EC2 instances and configure them appropriately (in this case,
  after it creates an EC2 instance, it will need to log into it using SSH to create the two
  users and set up GridFTP). We suggest that you create an keypair called ``gp-key``, and save the
  keypair file as ``~/.ec2/gp-key.pem``, since many of the sample files assume that naming.