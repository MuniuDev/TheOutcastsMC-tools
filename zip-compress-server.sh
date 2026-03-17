#!/bin/bash

backup_name=TheOutcastsMC
backup_dir=$HOME/$backup_name
now=$(date +"%Y_%m_%d_%H_%M")

# Zip the server
tar \
	--exclude=$backup_dir/plugins/dynmap/web/tiles \
	--exclude=$backup_dir/plugins/CoreProtect/database.db \
	-czf $backup_name-server-$now.tar.gz $backup_dir/
