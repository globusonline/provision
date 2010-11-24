#!/bin/bash

chroot $1 bash -c 'echo "deb http://apt.opscode.com/ lucid main" >> /etc/apt/sources.list'
chroot $1 wget -qO - http://apt.opscode.com/packages@opscode.com.gpg.key | chroot $1 apt-key add -
chroot $1 apt-get update
echo "chef chef/chef_server_url string http://192.168.0.1:4000" | chroot $1 debconf-set-selections
chroot $1 apt-get -q=2 install chef
