#!/bin/bash

yes | mkfs -t ext3 /dev/sdh 
mkdir /chef
mount -t ext3 /dev/sdh /chef
chown -R ubuntu /chef