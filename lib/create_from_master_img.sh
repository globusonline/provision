#!/bin/bash

MASTER=$1
NEWIMG=$2
IP=$3
HOSTNAME=$4
HOSTSFILE=$5

cp $MASTER $NEWIMG

MNTDIR=`mktemp -d`

qemu-nbd -c /dev/nbd0 $NEWIMG
sleep 2
mount /dev/nbd0p1 $MNTDIR

cp $HOSTSFILE $MNTDIR/etc/hosts
echo $HOSTNAME > $MNTDIR/etc/hostname
TMP_FILE=`mktemp`
cp $MNTDIR/etc/network/interfaces $TMP_FILE
sed s/192.168.0.2$/$IP/g $TMP_FILE > $MNTDIR/etc/network/interfaces

umount $MNTDIR
nbd-client -d /dev/nbd0 > /dev/null

rm $TMP_FILE
rmdir $MNTDIR
