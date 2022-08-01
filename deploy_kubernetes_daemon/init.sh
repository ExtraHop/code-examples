#!/bin/sh

set -eu

exec 6>&1
exec > rpcapd.ini

OLDIFS=$IFS
IFS=','
for s in ${EXTRAHOP_SENSOR_IP}
do
    echo "ActiveClient = ${s},${RPCAPD_TARGET_PORT}"
done
IFS=$OLDIFS
echo "NullAuthPermit = YES"
exec 1>&6 6>&-

# This script finds the subnets of the other nodes and pods in the cluster.
# The script then builds a BPF that sends traffic to the ExtraHop sensor
# only once.

main_dev=$(ip route list | grep default | grep -E  'dev (\w+)' -o | awk '{print $2}')
if [ "${main_dev}" = "" ]
then
    echo "Could not look up main network device, output:"
    ip route list
    exit 255
fi

subnets=$(ip route show dev "${main_dev}" scope link | grep / | cut -d' ' -f1)
if [ "${subnets}" = "" ]
then
    echo "Could not lookup primary subnet, routing table for ${main_dev}:"
    ip route show dev "${main_dev}"
    exit 255
fi

# The PODNET variable is a subnet that is a superset of all pod subnets on all nodes
if [ "${PODNET}" != "" ]
then
    subnets="${subnets},${PODNET}"
fi

servicesubnet=${SVCNET}

# Arguments: subnet, direction
# Returns: rule
compose_cluster_rule() {
    rule='( not ('
    subnets_number=0
    OLDIFS=$IFS
    IFS=','
    for subnet in $1
    do
        if [ $subnets_number -eq 0 ]
        then
            subnets_number=1
        else
            rule="${rule} or"
        fi
        rule="${rule} ip ${2} net ${subnet}"
    done
    IFS=$OLDIFS
    rule="${rule} ) )"
    echo "${rule}"
}
subnetrule=$(compose_cluster_rule "${subnets}" "src or dst")

# Arguments: direction
# Returns: rule
compose_local_rule() {
    direction=''
    addrcmp=''
    portcmp=''
    if [ "$1" = "src" ]
    then
        direction="inbound"
        addrcmp="(ip[12:4] >= ip[16:4])"
        portcmp="<"
    else
        direction="outbound"
        # For outbound, the lower address is chosen because
        # that means we should always match the IP broadcasts, which will
        # use the highest address in their subnet.
        addrcmp="(ip[12:4] <= ip[16:4])"
        portcmp=">"
    fi

    # Some packets do not have a port because they are fragments or they are not TCP.
    noportrule="((ip[6:2] & 0x1fff != 0) or ((not tcp)) and ${addrcmp})"

    tcprule="(tcp and ((tcp[0:2] ${portcmp} tcp[2:2]) or ((tcp[0:2] = tcp[2:2]) and ${addrcmp})))"

    rule="(${direction} and (${noportrule} or ${tcprule}))"

    echo "${rule}"
}

# The local rule specifies that only the side with the higher port
# number should forward the packet if the traffic is within
# the Kubernetes cluster. If the higher port is unknown, the side
# with  the higher IP address should forward the packet.
localsrcrule=$(compose_local_rule "src")
localdstrule=$(compose_local_rule "dst")

bpf_rules="not ip or (not ip proto 4) and (not ip net ${servicesubnet}) and (${subnetrule} or ${localsrcrule} or ${localdstrule})"

echo ./rpcapd -v -f rpcapd.ini -i "${INTERFACE}" -D -F "${bpf_rules}"
./rpcapd -v -f rpcapd.ini -i "${INTERFACE}" -D -F "${bpf_rules}"
