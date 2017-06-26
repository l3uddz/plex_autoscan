# plex_autoscan
Script to assist sonarr/radarr with plex imports. Will only scan the folder that has been import, instead of the whole library section.

# Install
## Debian/Ubuntu

1. `cd /opt`
2. `sudo git clone https://github.com/l3uddz/plex_autoscan`
3. `sudo chown -R user:user plex_autoscan`
4. `cd plex_autoscan`
5. `sudo pip install -r requirements.txt`
6. `python scan.py` to generate default config.json

## Windows

1. Git clone / Download the master folder
2. Install python requirements.txt, e.g. c:\python27\scripts\pip install -r c:\plex_autoscan\requirements.txt
3. `python scan.py` to generate default config.json

# Configure
## Debian/Ubuntu
**Note: The user that runs sonarr/radarr needs to beable to sudo without a password otherwise it cannot execute the PLEX_SCANNER as plex.**

Ensure the PLEX_LD_LIBRARY_PATH / PLEX_SCANNER / PLEX_SUPPORT_DIR variables are the correct locations (these should be the defaults).
You can verify this is working correctly by doing, `python scan.py sections` which will return a list of your plex library sections & id's, which we will use to setup PLEX_SECTION_PATH_MAPPINGS.

PLEX_SECTION_PATH_MAPPINGS example:

```json
    "PLEX_SECTION_PATH_MAPPINGS": {
        "1": [
            "/Movies/"
        ], 
        "2": [
            "/TV/"
        ]
    }, 
```

This tells the script that if the imported file has /Movies/ in the path, use section 1, otherwise use 2 if /TV/ is in the path.

PLEX_USER is self explanatory, again this should be fine as the default plex.

Your config should now be ready for local automatic plex scans on sonarr/radarr imports.

## Windows
**Note: The user running the sonarr/radarr service MUST be the same user as the one running plex, e.g. Administrator)**

Windows installations only need to be concerned with the PLEX_SCANNER and PLEX_SECTION_PATH_MAPPINGS variables.
PLEX_SCANNER can usually be found in the C:\Program Files (x86)\Plex folder.
You must use double backslashes for this path, e.g. C:\\Program Files (x86)\\Plex\\Plex Scanner.exe

Follow the same steps as above for the PLEX_SECTION_PATH_MAPPINGS but instead of / use \\, so, /Movies/ becomes \\Movies\\

## Remote Installations

plex_autoscan is capable of sending the scan request to remote installations (e.g. sonarr/radarr/downloaders on one machine, plex/plex_autoscan on another). 

```json
    "SERVER_IP": "0.0.0.0", 
    "SERVER_PASS": "0c1fa7c986fe48b2bb3aa055cb86f533", 
    "SERVER_PATH_MAPPINGS": {
        "/mnt/unionfs": [
            "/home/seed/media/fused"
        ]
    }, 
    "SERVER_PORT": 3467, 
    "SERVER_PUSH_URL": [
        "http://localhost:3467/push"
    ], 
    "USE_SERVER_PUSH": true
```

SERVER_IP / SERVER_PORT is the IP & Port for the server to listen on for incoming scan requests.

SERVER_PASS is a random 32 character key generated on config build. This must be the same for both the local/remote plex_autoscan installations so the server can verify its an authenticated scan request.

SERVER_PATH_MAPINGS is used by the server to map incoming scan request paths to their appropriate location, using the above example:

/home/seed/media/fused/Media/TV/Doctor Who/Season 1/Doctor Who - S01E01 - meh.mkv would become /mnt/unionfs/Media/TV/Doctor Who/Season 1/Doctor Who - S01E01 - meh.mkv.

This is useful for where the server/requester systems have different mount locations. If they are the same, you can leave this blank, e.g.:

```json
    "SERVER_PATH_MAPPINGS": {
    }, 
```

SERVER_PUSH_URL is used by the requester plex_autoscan installation, this is where to send the scan requests, as you can see, you could have more than one remote plex/plex_autoscan installation receive the requests.

Finally USE_SERVER_PUSH, this is the key variable that tells plex_autoscan to push the scan request instead of performing a local scan. This needs to be set to true if you wish for your scan requests to be sent to another plex_autoscan installation. 
**Note: this MUST be false on the setup running the server, otherwise it will push incoming requests to itself and repeat forever.**

To start the server, simply `python scan.py server` - this will start the request server. Alternatively you can use the systemd service included in the system folder todo this for you to keep it running & autostart on boot.

# Sonarr/Radarr
## Debian/Ubuntu

To setup your sonarr/radarr installations to use plex_autoscan, simply go to Settings -> Connect -> Add New -> Custom Script.
Untick on Grab and tick Download, Rename, Upgrade. Then choose the scan.py as the file and add either sonarr or radarr as the argument.

![Sonarr](http://i.imgur.com/SXcnvkT.png)

You should now be ready!

## Windows

Follow the same steps as above but path must be set to your python executable.

The arguments should be "PATH OF SCRIPT" sonarr OR radarr

![Sonarr Windows](http://i.imgur.com/OAcunrd.png)
