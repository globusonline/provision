#!/bin/bash

NODE=$1
ROLE=$2

knife node delete $NODE -y
knife client delete $NODE -y
knife node create $NODE -n
knife node run_list add $NODE role[$ROLE]
