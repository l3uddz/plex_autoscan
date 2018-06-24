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

**The user that runs plex_autoscan needs to beable to sudo without a password otherwise it cannot execute the PLEX_SCANNER as plex.
This can be disabled by config option USE_SUDO**

## Windows

1. Git clone / Download the master folder
2. Install python requirements.txt, e.g. c:\python27\scripts\pip install -r c:\plex_autoscan\requirements.txt
3. `python scan.py` to generate default config.json

**The user running plex_autoscan MUST be the same user as the one running plex, e.g. Administrator)**

# Configuration

Example configuration:
```json
{
    "DOCKER_NAME": "plex",
    "PLEX_DATABASE_PATH": "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
    "PLEX_EMPTY_TRASH": true,
    "PLEX_EMPTY_TRASH_CONTROL_FILES": [
        "/mnt/unionfs/mounted.bin"
    ],
    "PLEX_EMPTY_TRASH_MAX_FILES": 100,
    "PLEX_EMPTY_TRASH_ZERO_DELETED": false,
    "PLEX_LD_LIBRARY_PATH": "/usr/lib/plexmediaserver",
    "PLEX_LOCAL_URL": "http://localhost:32400",
    "PLEX_SCANNER": "/usr/lib/plexmediaserver/Plex\\ Media\\ Scanner",
    "PLEX_SECTION_PATH_MAPPINGS": {
        "1": [
            "/Movies/"
        ],
        "2": [
            "/TV/"
        ]
    },
    "PLEX_SUPPORT_DIR": "/var/lib/plexmediaserver/Library/Application\\ Support",
    "PLEX_TOKEN": "XXXXXXXXXX",
    "PLEX_USER": "plex",
    "PLEX_WAIT_FOR_EXTERNAL_SCANNERS": true,
    "SERVER_ALLOW_MANUAL_SCAN": false,
    "SERVER_FILE_EXIST_PATH_MAPPINGS": {
        "/home/thompsons/plexdrive": [
            "/data"
        ]
    },
    "SERVER_IP": "0.0.0.0",
    "SERVER_MAX_FILE_CHECKS": 10,
    "SERVER_PASS": "0c1fa7c986fe48b2bb3aa055cb86f533",
    "SERVER_PATH_MAPPINGS": {
        "/mnt/unionfs": [
            "/home/seed/media/fused"
        ]
    },
    "SERVER_PORT": 3468,
    "SERVER_SCAN_DELAY": 5,
    "USE_DOCKER": false,
    "USE_SUDO": true
}

```

Output:
![Config output](http://i.imgur.com/AfI0qWv.png)

## Plex

Ensure the `PLEX_LD_LIBRARY_PATH` / `PLEX_SCANNER` / `PLEX_SUPPORT_DIR` variables are the correct locations (the defaults should be preset).
You can verify this is working correctly by doing, `python scan.py sections` which will return a list of your plex library sections & id's, which we will use to setup `PLEX_SECTION_PATH_MAPPINGS`.

`PLEX_SECTION_PATH_MAPPINGS` example:

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

This tells the script that if the filepath that we have decided to scan has /Movies/ in the path, use section 1, otherwise use 2 when /TV/ is in the path. This is used when starting the plex command line scanner.

`PLEX_USER` is self explanatory, again this should be fine as the default plex. **Ignore for Windows installations**

`PLEX_TOKEN` only needs to be used in conjunction with `PLEX_EMPTY_TRASH` and `PLEX_LOCAL_URL`. For more on how to retrieve this, visit https://support.plex.tv/hc/en-us/articles/204059436-Finding-an-authentication-token-X-Plex-Token

`PLEX_LOCAL_URL` is the local url of plex server where the empty trash request is sent.

`PLEX_EMPTY_TRASH` when set to true, after a scan was performed, empty trash will also be performed for that section. `PLEX_DATABASE_PATH` and `PLEX_EMPTY_TRASH_MAX_FILES` must be set when this is enabled.

`PLEX_EMPTY_TRASH_CONTROL_FILES` is used before performing an empty trash request, this allows you to specify a list of files that must exist. If they dont then no empty trash request is sent. If this is not needed, you can leave the list empty to disable the check.

`PLEX_EMPTY_TRASH_MAX_FILES` must be set when using `PLEX_EMPTY_TRASH`, this value is the maximum deleted items to delete, so if there is more than than this amount deleted items, abort the empty trash.

`PLEX_EMPTY_TRASH_ZERO_DELETED` if set to True, will always perform an empty trash on the scanned section. If False, trash will only be emptied when the database returns more than 0 deleted items.

`PLEX_DATABASE_PATH` is the plex library database location. Make sure the user running plex_autoscan has access to this file directly, e.g. chmod -R 777 /var/lib/plexmediaserver or the empty trash will never be performed. On Windows, this database filepath can usually be found at "%LOCALAPPDATA%\Plex Media Server\Plug-in Support\Databases"

`PLEX_WAIT_FOR_EXTERNAL_SCANNERS` when set to true, the active scanner in the plex_autoscan queue will once the lock is acquired, before a plex scan is commenced, scan the process list looking for existing Plex Media Scanners. If one is found, it will sleep 60 seconds and check again in a constant loop. Once all Plex Media Scanner's are no longer in the process list, the scan will commence, thus continuing the plex_autoscan scan backlog. **Note: if USE_DOCKER is enabled, this will not work properly if there is multiple plex dockers being ran, as it will see all the plex scanners being ran in all the containers. So turn this off when using USE_DOCKER unless there is only 1 docker container**

`DOCKER_NAME` is the name of the docker container to execute the plex scanner in, if USE_DOCKER is enabled.

`USE_SUDO` is on by default. If the user that runs your plex_autoscan server is able to run the Plex CLI Scanner without sudo, you can disable the sudo requirement here. **Ignore for Windows installations**

`USE_DOCKER` is off by default. If this is enabled, then docker exec will be used to execute the plex scanner inside the DOCKER_NAME container.

## Server

`SERVER_IP` is the server IP that plex_autoscan will listen on. usually 0.0.0.0 for remote access and 127.0.0.1 for local.

`SERVER_PORT` is the port that plex_autoscan will listen on.

`SERVER_SCAN_DELAY` is the seconds that is slept before a scan request can continue.

`SERVER_MAX_FILE_CHECKS` is an additional check that is performed after the `SERVER_SCAN_DELAY`. It will check if the file that was requested to be scanned exists, if it does not then it will sleep for 1 minute and check again until this value has been reached. **This setting does not work with sonarr until https://github.com/Sonarr/Sonarr/commit/4189bc6f76347aee00db4449dba142ae04961e0a has been merged with master**

`SERVER_PASS` is a random 32 character string generated on config build. This is used in the URL given to sonarr/radarr of plex_autoscan server.

`SERVER_PATH_MAPPINGS` is a list of paths that will be remapped before being scanned. This is useful for receiving scan requests from a remote sonarr/radarr installation. Lets take for example:

```json
    "SERVER_PATH_MAPPINGS": {
        "/mnt/unionfs": [
            "/home/seed/media/fused"
        ]
    },
```

If the filepath that was reported to plex_autoscan by sonarr/radarr was `/home/seed/media/fused/Movies/Die Hard/Die Hard.mkv` then the path that would be scanned by plex would become `/mnt/unionfs/Movies/Die Hard/Die Hard.mkv`.

`SERVER_FILE_EXIST_PATH_MAPPINGS` this is exactly like the option above, but for the file exist checks. this is useful when using docker, because the folder being scanned by the plex container, may be different to the path on the host system running plex_autoscan. This config option allows you to specify a path mapping to be used exclusively for the file exist checks, and then continue using the remapped path using the setting above for the plex scanner. You can leave this empty if it is not required.

`SERVER_ALLOW_MANUAL_SCAN` when set to true will allow GET requests to the webhook URL where you can perform manual scans on a filepath. Remember all path mappings and section id mappings of server apply. So this is a good way of testing your configuration manually.
You can either visit your webhook url in a browser, or initiate a scan by curl e.g. `curl -d "eventType=Manual&filepath=/mnt/unionfs/Media/Movies/Shut In (20166f533t In (2016) - Bluray-1080p.x264.DTS-GECKOS.mkv" http://localhost:3468/0c1fa3c9867e48b1bb3aa055cb86`

## Windows

Windows installations only need to be concerned with the `PLEX_SCANNER` and `PLEX_LIBRARY_PATH` if empty trash is being used, ignore the `USE_SUDO`, `PLEX_USER`, `PLEX_SUPPORT_DIR` and `PLEX_LD_LIBRARY_PATH` variables.

`PLEX_SCANNER` can usually be found in the C:\Program Files (x86)\Plex folder.
You must use double backslashes for this path, e.g. `C:\\Program Files (x86)\\Plex\\Plex Scanner.exe`

Follow the same guidelines as above but instead of / in paths, use `\\`, so, /Movies/ becomes `\\Movies\\`.

# Sonarr/Radarr

To setup your sonarr/radarr installations to use plex_autoscan, simply go to Settings -> Connect -> Add New -> Webhook.
Untick on Grab and tick Download, Rename, Upgrade. Then enter the url to your server which is normally:

http://SERVER_IP:SERVER_PORT/SERVER_PASS

![Sonarr](http://i.imgur.com/KxaRlwo.png)

## Startup

## Linux

To start the server, simply `python scan.py server` - this will start the request server. This is good todo too grab a quick file and ensure your configuration is correct, before configuring / starting / enabling the included systemd service file.

## Windows

Follow the same steps as above to run the server. As for startup, this can be achieved using the Windows Task Scheduler. Bear in mind however you decide to get your script to startup, it must be executed as a user that has permissions to access the `PLEX_SCANNER` file, typically Administrator. If this is not the case, it will hang.
