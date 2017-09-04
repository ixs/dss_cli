#!/bin/sh -e

pri="dss1"
sec="dss2"

if [ $# != 1 ]; then
	echo "Usage: $0 <target_name>"
	exit 1
fi

name=$1
server="$pri $sec"

echo -n Deactivating failover... 
./dss_cli $pri failover_task replication_iscsi_${name} disable
echo done

lvs=$(./dss_cli $pri volume_replication_task_status replication_iscsi_${name} | grep "Logical volume:" | awk '{ print $3}')

lv_pri=$(echo $lvs | cut -d ' ' -f 1)
lv_sec=$(echo $lvs | cut -d ' ' -f 2)

echo -n Unassigning LUN... 
./dss_cli $pri iscsi_target_unassign $name $lv_pri
./dss_cli $sec iscsi_target_unassign $name $lv_sec
echo done.

echo -n Removing iSCSI targets... 
for s in $server; do
	./dss_cli $s iscsi_target_remove $name
done
echo done.

echo -n Stopping replication...
./dss_cli $pri volume_replication_task_stop replication_iscsi_${name}
echo done.

echo -n Removing replication task... 
./dss_cli $pri volume_replication_task_remove replication_iscsi_${name}
echo done.

echo -n Removing replication from lvs... 
./dss_cli $pri volume_replication_remove $lv_pri
./dss_cli $sec volume_replication_remove $lv_sec
echo done.

echo -n Removing iSCSI logical volume... 
./dss_cli $pri volume_iscsi_remove $lv_pri
./dss_cli $sec volume_iscsi_remove $lv_sec
echo $lv removed.

