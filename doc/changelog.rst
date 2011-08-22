.. _changelog:

Changelog and Release Notes
***************************

0.3.0rc2
========
Released on *August 22, 2011*

Changes:

* Added most of the documentation that was missing.
* Added PDF version of the documentation.
* Implemented ``gp-remove-hosts`` and ``gp-remove-users``.

Known issues:

* :ref:`CLI documentation <chap_cli_ref>` is still barebones.
* SSH connections will sometimes "hang", even though it is possible to manually SSH into
  the affected machine. The Paramiko-based SSH code will be replaced with `Fabric <http://docs.fabfile.org/en/1.2.1/index.html>`_
  soon, so it is possible using a more stable SSH library will address this.
* ``gp-go-register-endpoint`` will only work with the Transfer API. Somehow, Paramiko
  can't connect to ``cli.globusonline.org``, so it will not be possible to create
  endpoints using only an authorized SSH key. Like above, this may go away when we
  switch to Fabric.
* Resuming a stopped instance takes a long time. For some reason, it takes a long time
  for a resumed instance to be receptive to an SSH connection and, even then, commands
  are run at a slow pace. It's possible something hasn't been cleaned up properly,
  and the instance is still looking for services that are no longer there. 

0.3.0rc1
========
Released on *August 18, 2011*

This is a complete redesign and reimplementation of the DemoGrid project. Even though it
evolved from the DemoGrid code, it is essentially a new project. 

0.2.0
=====
*Note:* This version was released under the name "DemoGrid"

Released on *December 21, 2010*

Changes:

* First public release.
* Added support for deploying on EC2.

0.1.0
=====
*Note:* This version was released under the name "DemoGrid"

Released on *November 24, 2010*

This was a private release for Globus developers only.