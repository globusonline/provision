.. _chap_ec2:

Setting up Amazon EC2
*********************

Before you can start defining and deploying topologies, you will need an Amazon EC2 account.
If you are already familiar with Amazon EC2, you can safely skip this chapter. If you have
never used Amazon EC2, read on.

What is Amazon EC2?
===================

Amazon EC2 is an "Infrastructure-as-a-Service" (or IaaS) cloud. This means that you can pay
Amazon to provide you with IT infrastructure using a pay-as-you-go model. For example,
if you need 10 machines right now, Amazon EC2 can provide them to you (for a price) in just 
a few minutes, and will charge you on a per-hour basis.

From the user's perspective, all you do is request the number and type of machines (or 
"EC2 instances") through a web console or a command-line interface, and Amazon EC2 reports 
back to you a few minutes later with the hostnames and IP addresses of your EC2 instances. 
You can then log into them and do whatever you want with them. Once you're done with them, 
you just use EC2's interface to shut down your instances. 

Plus, you only pay for as long as those machines are running,
and there are different tiers of service. The cheapest machine type (or "EC2 instance type")
costs $0.02/hour, but only provides 613 MB of memory and very little compute muscle. One of
their higher-end instance types costs $1.60/hour and comes with 23GB of memory, and has
a performance equivalent to two quad-core processors.

Globus Provision uses Amazon EC2 to provision the machines that are required by your
topology. So, to use Globus Provision, you must have an Amazon EC2 account.


What you need from Amazon EC2
=============================

First of all, if you don't have an account, you will have to 
`get one <http://aws-portal.amazon.com/gp/aws/developer/subscription/index.html?productCode=AmazonEC2>`_.
Consider that you may be able to you can take advantage of their 
`Free Usage Tier <http://aws.amazon.com/free/>`_ and get 750 hours on EC2 completely free.

If you are completely new to EC2, it may be worthwhile to read through their
`Getting Started Guide <http://docs.amazonwebservices.com/AWSEC2/latest/GettingStartedGuide/>`_.
You should also familiarize yourself with their web console (a web interface that allows
you to monitor your EC2 instances). Although Globus Provision takes care of managing
the EC2 instances for you, you may still need to log into the web console occasionally
to monitor your EC2 instances.

Once you have an account, Globus Provision will need the following information:

* Globus Provision needs to request EC2 instances on your behalf. To do this, you need to
  get an `Access Key ID and Secret Access Key <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-credentials.html#using-credentials-access-key>`_
  from Amazon EC2 (follow the link for instructions on how to do this). These keys will
  *only* reside on your own computer. The Globus Provision commands will contact EC2
  directly using those keys, and the keys are *never* sent through any intermediate Globus servers.
  
* Globus Provision needs to log into the EC2 instances it creates, so it can configure them
  according to the topology you specified. You will need to obtain an 
  `SSH Keypair <http://docs.amazonwebservices.com/AWSEC2/latest/UserGuide/using-credentials.html#using-credentials-keypair>`_
  from Amazon EC2 (follow the link for instructions on how to do this). We suggest that you 
  create a keypair called ``gp-key``, and save the keypair file as ``~/.ec2/gp-key.pem``, since 
  many of the sample files assume that naming.
  
For now, just hold on to your access keys and your keypair. In the next chapter, we will see
how to configure Globus Provision to use them.

