#!/bin/bash

backup_name=TheOutcastsMC-backup
backup_dir=$HOME/$backup_name
now=$(date +"%Y_%m_%d_%H_%M")

# Zip the server
tar \
	--exclude=$backup_dir/rdiff-backup-data \
	--exclude=$backup_dir/plugins/dynmap/web/tiles \
	-czf $backup_name-$now.tar.gz $backup_dir/
