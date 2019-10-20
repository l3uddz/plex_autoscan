#! /bin/sh

if [ ! -f ${PLEX_AUTOSCAN_CONFIG} ]
then
    python /opt/plex_autoscan/scan.py sections
    echo "Default config.json generated, please configure for your environment. Exiting."
else
    server_ip=$(grep SERVER_IP ${PLEX_AUTOSCAN_CONFIG} | awk -F '"' '{print $4}')
    if [ $server_ip -eq "0.0.0.0"]
    then
        server_ip="127.0.0.1"
    fi

    server_port=$(grep SERVER_PORT ${PLEX_AUTOSCAN_CONFIG} | awk -F ': ' '{print $2}' | awk -F ',' '{print $1}')
    server_pass=$(grep SERVER_PASS ${PLEX_AUTOSCAN_CONFIG} | awk -F '"' '{print $4}')

    url="http://${server_ip}:${server_port}/${server_pass}"
    curl --silent --show-error -f $url > /dev/null || exit 1
fi
