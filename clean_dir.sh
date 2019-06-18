#!/bin/bash
passwd=$1
res=$(pwd)/../$2/results/
cd ${res}
echo '${passwd}\r' | sudo ls > /dev/null
sudo mv * $(pwd)/../bak_results/
