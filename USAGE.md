USAGE Examples
==============


Create failover enabled NAS volume on two filers
------------------------------------------------

$ ./dss_cli filer1 create_naslv filer1_vol000 4800
lvfiler1_vol00001

$ ./dss_cli filer2 create_naslv filer2_vol000 4800
lvfiler2_vol00001

$ ./dss_cli filer1 volume_replication add lvfiler1_vol00001

$ ./dss_cli filer2 volume_replication add lvfiler2_vol00001

$ ./dss_cli filer2 volume_replication_mode lvfiler2_vol00001 secondary

$ ./dss_cli filer1 create_volume_replication_task lvfiler1_vol00001 lvfiler2_vol00001 failover_nas_www

$ ./dss_cli filer1 task --start VREP failover_nas_www

$ ./dss_cli filer1 nas_share_create "nas_users_www" lvfiler1_vol00001

$ ./dss_cli filer1 nas_share_toggle_smb nas_users_www disabled

$ ./dss_cli filer2 nas_share_toggle_smb nas_users_www disabled

$ ./dss_cli filer1 failover --stop

$ ./dss_cli filer1 nas_share_access_nfs nas_users_www on

$ ./dss_cli filer1 activate_failover_task failover_nas_www

$ ./dss_cli filer1 failover --start

