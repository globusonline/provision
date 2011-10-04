.. _changelog:

Changelog and Release Notes
***************************

0.3.2
=====
Released on *October 4, 2011*

* :jira:`7`: Instance stop/resume has been fixed.
* :jira:`8`: Related to the previous issue, Globus Online endpoints are now properly managed in the the stop/resume lifecycle.
  When an instance is stopped, the endpoint is associated with the "relay-disconnected.globusonline.org" server. When the
  instance is resumed, the new GridFTP server is associated with the endpoint.
* :jira:`9`: `instance_update` will now add new Globus Online endpoints.
* :jira:`11`: Updated Chef recipes so they will use the Opscode "apt" cookbook.

0.3.1
=====
Released on *September 12, 2011*

Changes:

* :jira:`2`: Access to a CA trusted by Globus Online is no longer required
  to create a GP instance with GO endpoints. When creating an endpoint, 
  GP will now dynamically request a certificate from the Globus Online CA. 
  This certificate will be used by the GridFTP server in that GP instance. 
* :jira:`3`: Added a dependency on the `globusonline-transfer-api-client <http://pypi.python.org/pypi/globusonline-transfer-api-client>`_
  package, instead of shipping our own copy of the Globus Online Transfer API client.   
* Changed the names of the commands so they will follow a more coherent naming
  convention. For example, `gp-start` has been renamed to `gp-instance-start`,
  `gp-describe-instance` has been renamed to `gp-instance-describe`, etc.
  See :ref:`chap_cli_ref` for more details. 
* Added the :ref:`barebones-nodes <SimpleTopologyConfig_barebones-nodes>` option
  to the simple topology file. This allows easy deployment of any number of "vanilla"
  nodes.
* Added a "Guides" section to the documentation. This section will include
  fairly self-contained guides, for both beginners and advanced users.
  This new section includes a guide on :ref:`guide_compute_go`.
* Added a :ref:`bash autocomplete script <guide_autocomplete>` for the GP commands
  (thanks to Mike Steder for contributing a first version of the script).
* We now provide 32-bit, 64-bit, and HVM AMIs. These are listed in the
  :ref:`ami` page.
* Bug fixes: :jira:`1`

Known issues:

* The ``instance_update`` API function will not add/remove Globus Online endpoints. 
* Resuming a stopped instance still not working properly.

0.3.0
=====
Released on *August 25, 2011*

Changes:

* "Hanging" SSH problem fixed. Also added a fix to allow the SSH
  code to connect to ``cli.globusonline.org`` (which has a restricted
  shell and, thus, won't allow SCP connections, which we try to
  connect by default).
* Polished up CLI documentation and other minor documentation fixes.

Known issues:

* Resuming a stopped instance still not working properly.

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
