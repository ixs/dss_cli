dss_cli
=======

Command line interface for the Open-E Data Storage Server using both the SSH
API as well as Webscraping


Audience
========

The dss_cli command line tool is targeted of owners or administrators of an
Open-E DSS server wishing to completely automate the creation of failover
volumes, something the current API does not support.


General Description
===================

The Data Storage Server (DSS) from Open-E (http://www.open-e.com) is a Linux
based storage server.

Management tasks such as initial setup but also more common tasks such as
creation of volumes, setup of replication etc. are usually performed via an
ajax web-interface.

The DSS software has a limited API for executing certain tasks via SSH
command line execution.

Unfortunately this API is not offering all the needed functionality to 
programatically create failover volumes in a cluster, something often needed
in a professional environment.

The dss_cli program is both able to access a DSS via SSH as well as
simulating a web-browser in order to complement the offered API. This way 
the following tasks not available through the regular API are now available
for automation/scripting:

   * volume_replication_remove - While the regular API offers the ability to
     add replication to an existing volume it is unable to remove the
     replication flag again. While replication is enabled, a volume cannot be
     removed.
   * volume_replication_mode - Volumes created through the web interface of
     through the API are by default created as replication sources. Before
     replication can be enabled in a failover configuration, the secondary
     volume needs to be configured as a replication destination.
   * create_volume_replication_task - After the volumes for replication have
     been created, a replication task needs to be created to configure the
     actual synchronisation of data.
   * iscsi_target_access - Configure IP Access rules for iSCSI targets.

LICENSE
=======

The code is licensed under the GNU Public License version 2.
The main points to take away from this are:

   * It is allowed to use this software both non- as well as commercially.
   * It is allowed to modify this software and use these modified versions.
   * Should a modified version be distributed, source code needs to be
     made available to the receipients of the distributed version.

CONTACT
=======

This tool was written by Andreas Thienemann <andreas@bawue.net> for use at
Bawue.Net (http://www.bawue.de).