#!/bin/bash

backup_name=TheOutcastsMC
backup_dir=$HOME/$backup_name
now=$(date +"%Y_%m_%d_%H_%M")

# Zip the server
# tar -czf $backup_name-server-$now.tar.gz $backup_dir/
tar -cf - $backup_dir/ | pv -s $(du -sb $backup_dir | awk '{print $1}') | pigz -p $(nproc) > $backup_name-server-$now.tar.gz 
