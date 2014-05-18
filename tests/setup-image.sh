#!/usr/bin/env bash
ISCSI_CONF_DIR="/etc/tgt/conf.d"
read image_server image_path image_id image_iqn < image.txt
echo "image_server" = $image_server
echo "image path = $image_path"
echo "image_id = $image_id"
echo "image_iqn = $image_iqn"

configfile="$ISCSI_CONF_DIR/$image_id.conf"
echo "output target config to file $configfile"
echo "<target $image_iqn> " > $configfile
echo "backing-store $image_path" >> $configfile
echo "</target>" >> $configfile

echo "create iscsi target for image"
tgt-admin --update $image_iqn -c $configfile
