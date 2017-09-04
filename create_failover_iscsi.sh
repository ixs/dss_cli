#!/bin/sh -e

pri="dss1"
sec="dss2"

if [ $# != 3 ]; then
	echo "Usage: $0 <target_name> <size_in_GB> <volume_group>"
	exit 1
fi

name=$1
size=$2
vg=$3
server="$pri $sec"

# Get screen width
function columns() {
	set +e
	COLUMNS=$(resize2 2> /dev/null)
	if [ $? -eq 0 ]; then
		COLUMNS=$(echo "$COLUMNS" | grep -m 1 COLUMNS | cut -d = -f 2 | cut -d \; -f 1)
	else
		COLUMNS=$(stty -a | head -1 | tr ';' '\n' | awk '/columns/ { print $2 }' 2> /dev/null)
	fi
	set -e
}

echo -n Creating iSCSI logical volume... 
vol_pri=$(./dss_cli $pri create_iscsilv $vg $(( $size * 1024 / 32 )) blockio)
vol_sec=$(./dss_cli $sec create_iscsilv $vg $(( $size * 1024 / 32 )) blockio)
echo done

echo -n Adding replication to lvs... 
./dss_cli $pri volume_replication add $vol_pri
./dss_cli $sec volume_replication add $vol_sec
echo done.

echo -n Setting destination volume... 
./dss_cli $sec volume_replication_mode $vol_sec secondary
echo done.

echo -n Creating replication task... 
./dss_cli $pri volume_replication_task_create $vol_pri $vol_sec replication_iscsi_${name} 80
echo done.

echo -n Starting replication...
./dss_cli $pri task --start VREP replication_iscsi_${name}
echo done.

echo Waiting for replication to finish...
while true; do
    state=$(./dss_cli $pri volume_replication_task_status replication_iscsi_${name})
	echo $state | grep -q Inconsistent || break
	out=$(echo $(echo "$state" | egrep "Total size to replicate:|Remain to replicate:|Speed \(avg\):|Time left:"))
	columns
	pad=$(($COLUMNS - $(echo $out | wc -c)))
	i=0
    while [ $i -lt $pad ]; do
        out=$out" "
        i=$(($i + 1))
    done
	echo -ne '\b\b\b\b\b\b\b\b\b\b\b\b\b'
	echo -ne '\r'"$out"
	sleep 120
done
echo
echo done

echo -n Creating iSCSI targets... 
for s in $server; do
	./dss_cli $s iscsi_target_create $name
done
echo done.

echo -n Assigning LUN... 
lun=$(./dss_cli $pri iscsi_target_assign $name $vol_pri)
lun=$(./dss_cli $sec iscsi_target_assign $name $vol_sec -s $(echo $lun | cut -d : -f 5))
echo done.

echo -n Activating failover... 
./dss_cli $pri failover_task replication_iscsi_${name} enable
echo done.
