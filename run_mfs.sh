#!/bin/bash
truncate -s 0 /var/log/mfs.log
truncate -s 0 cd /root/FyersMFS/mfs.log
cd /root/FyersMFS
source venv/bin/activate
python3.11 -u main.py run 2>&1 | tee -a mfs.log