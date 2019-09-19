#! /bin/sh

if [ ! -f ${PLEX_AUTOSCAN_CONFIG} ]
then
    python /opt/plex_autoscan/scan.py sections
    echo "Default config.json generated, please configure for your environment. Exiting."
else
    server_pass=$(grep SERVER_PASS ${PLEX_AUTOSCAN_CONFIG} | awk -F '"' '{print $4}')
    server_port=$(grep SERVER_PORT ${PLEX_AUTOSCAN_CONFIG} | awk -F ': ' '{print $2}' | awk -F ',' '{print $1}')
    url="http://localhost:${server_port}/${server_pass}"
    curl --silent --show-error -f $url > /dev/null || exit 1
fi
