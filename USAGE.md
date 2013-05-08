USAGE Examples
==============


Supported commands
------------------

```
$ ./dss_cli -l filer1
build                     - Lists and sets default build.
check_mk_agent            - Returns information from check_mk monitor
create_iscsilv            - Creates a logical iSCSI Volume.
create_naslv              - Creates a logical NAS volume.
date                      - Sets time and date; please use the following format: yyyy-mm-dd hh:mm:ss
failover                  - This function allows you to stop, run or change the operation mode for the given server.
failover_task             - Manage a failover task
get_TXbytes               - Returns total number of bytes transmitted for the given interface.
get_TXpackets             - Returns total number of packets transmitted for the given interface.
get_driveslist            - Fetches a list of drives.
get_hwstatus              - Returns information from system hardware monitor.
get_memorystatus          - Fetches memory status.
get_nichealth             - Fetches the status of the given Network Interface Card.
get_nicslist              - Lists Network Interface Cards.
get_raidstatus            - Returns information about RAID.
help                      - Lists all available methods
iscsi_target_access       - Configure Target IP access
iscsi_target_assign       - Assign lv with given name to existing iSCSI target.
iscsi_target_create       - Creates a new iSCSI target.
iscsi_target_list         - Lists iSCSI targets (syntax: alias;name).
iscsi_target_remove       - Remove an existing iSCSI target
iscsi_target_restart      - Restart iSCSI target service.
iscsi_target_sessions     - Shows and manages iSCSI target sessions.
iscsi_target_status       - Lists the parameters of the selected target.
iscsi_target_unassign     - Unassign from given iSCSI target lvname.
lv_remove                 - Remove a logical volume
nas_settings_http         - Enables and disables access to shares via HTTP.
nas_share_access_afp      - Modifies AFP share access.
nas_share_access_ftp      - Enables and disables access to shares via FTP
nas_share_access_http     - Enables and disables access to shares via HTTP.
nas_share_access_nfs      - Enables and disables access to the given share via NFS.
nas_share_access_smb      - Modifies SMB/AFP share access.
nas_share_create          - Create share on specified volume.
nas_share_details         - Display detailed configuration of share
nas_share_edit            - Changes share location or comment.
nas_share_groups          - Groups manipulation functions.
nas_share_list            - Lists shares
nas_share_remove          - Removes the given share.
nas_share_toggle_smb      - Enable or disable SMB support for a share
nas_share_users           - Users manipulation functions.
nas_user_add              - Create user in the system.
nas_user_groups           - Adding and removing users to groups.
nas_user_remove           - Removes the given user from the system.
nas_user_rename           - Rename NAS user.
ntp                       - Fetches the time and date from an NTP server.
reboot                    - Reboots the system.
set_nic                   - Configures Network Interface Cards.
set_powersettings         - Sets the power button action scheme.
shutdown                  - Shuts the system down.
snapshot_task             - Starts and stops snapshots.
task                      - This function allows you to start task.
test                      - Generates an example of a help message.
unit_manager              - Creates new volume group or adds unit(s) to existing volume group.
update                    - Initiates and checks the status of software update.
version                   - Fetches the software version.
volume_group_status       - Lists Volume Groups.
volume_iscsi_remove       - Removes a logical iSCSI volume
volume_replication        - Adds and removes replication to volume.
volume_replication_mode   - Set volume replication mode to source or destination
volume_replication_remove - Removes replication from Volume
volume_replication_task_create - Create a volume replication task
volume_replication_task_remove - Remove a replication task
volume_replication_task_stop - Stop a replication task
volume_status             - Displays storage info.

```


Create failover enabled iSCSI volume on two filers:
---------------------------------------------------

$  ./dss_cli filer1 create_iscsilv arc_vol_000 4800 blockio
lvarc_vol_00000

$ ./dss_cli filer2 create_iscsilv arc_vol_000 4800 blockio
lvarc_vol_00000

$ ./dss_cli filer1 volume_replication add lvarc_vol_00000

$ ./dss_cli filer2 volume_replication add lvarc_vol_00000

$ ./dss_cli filer1 volume_replication_task_create lvarc_vol_00000 lvarc_vol_00000 failover_iscsi_phoenix

$ ./dss_cli filer1 task --start VREP failover_iscsi_phoenix

$ ./dss_cli filer1 iscsi_target_create phoenix

$ ./dss_cli filer2 iscsi_target_create phoenix

$ ./dss_cli filer1 iscsi_target_assign phoenix lvarc_vol_00000
lvarc_vol_00000:phoenix:0:wt:Dgp5VLni08UGb5W5

$ ./dss_cli filer2 iscsi_target_assign phoenix lvarc_vol_00000 -s Dgp5VLni08UGb5W5
lvarc_vol_00000:phoenix:0:wt:Dgp5VLni08UGb5W5

$ ./dss_cli filer1 failover_task failover_iscsi_phoenix enable

$ ./dss_cli filer1 failover --start


Create failover-enabled NAS volume on two filers
------------------------------------------------

$ ./dss_cli filer1 create_naslv filer1_vol000 4800
lvfiler1_vol00001

$ ./dss_cli filer2 create_naslv filer2_vol000 4800
lvfiler2_vol00001

$ ./dss_cli filer1 volume_replication add lvfiler1_vol00001

$ ./dss_cli filer2 volume_replication add lvfiler2_vol00001

$ ./dss_cli filer2 volume_replication_mode lvfiler2_vol00001 secondary

$ ./dss_cli filer1 volume_replication_task_create lvfiler1_vol00001 lvfiler2_vol00001 failover_nas_www

$ ./dss_cli filer1 task --start VREP failover_nas_www

$ ./dss_cli filer1 nas_share_create "nas_users_www" lvfiler1_vol00001

$ ./dss_cli filer1 nas_share_toggle_smb nas_users_www disabled

$ ./dss_cli filer2 nas_share_toggle_smb nas_users_www disabled

$ ./dss_cli filer1 failover --stop

$ ./dss_cli filer1 nas_share_access_nfs nas_users_www on

$ ./dss_cli filer1 failover_task failover_nas_www enable

$ ./dss_cli filer1 failover --start

Delete failover-enabled NAS volume on two filers
------------------------------------------------

$ ./dss_cli filer1 failover --stop

$ ./dss_cli filer1 failover_task failover_nas_www disable

$ ./dss_cli filer1 volume_replication_task_stop failover_nas_www

$  ./dss_cli filer1 volume_replication_task_remove failover_nas_www

$ ./dss_cli filer2 volume_replication_mode lvfiler2_vol00001 primary

$ ./dss_cli filer1 nas_share_access_nfs nas_users_www off

$ ./dss_cli filer2 nas_share_access_nfs nas_users_www off

$ ./dss_cli filer1 nas_share_remove nas_users_www
Share removed ok.

$ ./dss_cli filer2 nas_share_remove nas_users_www
Share removed ok.

$ ./dss_cli filer1 failover --start

$ ./dss_cli filer1 volume_replication_remove lvfiler1_vol00001

$ ./dss_cli filer2 volume_replication_remove lvfiler2_vol00001

$ ./dss_cli filer1 lv_remove lvfiler1_vol00001

$ ./dss_cli filer2 lv_remove lvfiler2_vol00001
