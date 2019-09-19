#! /bin/sh

cd /opt/plex_autoscan
git pull

if [ ! -f ${PLEX_AUTOSCAN_CONFIG} ]
then
    python /opt/plex_autoscan/scan.py sections
    echo "Default ${PLEX_AUTOSCAN_CONFIG} generated, please configure for your environment. Exiting."

elif grep -q '"PLEX_TOKEN": "",' ${PLEX_AUTOSCAN_CONFIG}
then
    echo "config.json has not been configured, exiting."

else
    python /opt/plex_autoscan/scan.py server

fi
