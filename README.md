# Plex Autoscan

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%203-blue.svg)](https://github.com/l3uddz/plex_autoscan/blob/master/LICENSE.md)
[![Discord](https://img.shields.io/discord/381077432285003776.svg?colorB=177DC1&label=Discord)](https://discord.io/cloudbox)
[![Feature Requests](https://img.shields.io/badge/Requests-Feathub-blue.svg)](http://feathub.com/l3uddz/plex_autoscan)

---
<!-- TOC depthFrom:1 depthTo:2 withLinks:1 updateOnSave:0 orderedList:0 -->

- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
	- [Example](#example)
	- [Basics](#basics)
	- [Docker](#docker)
	- [Plex Media Server](#plex-media-server)
	- [Plex Autoscan Server](#plex-autoscan-server)
	- [Google Drive Monitoring](#google-drive-monitoring)
	- [Rclone Remote Control](#rclone-remote-control)
- [Setup](#setup)
	- [Sonarr](#sonarr)
	- [Radarr](#radarr)
	- [Lidarr](#lidarr)

<!-- /TOC -->

---


# Introduction

Plex Autoscan is a python script that assists in the importing of Sonarr, Radarr, and Lidarr dowloads into Plex Media Server.

It does this by creating a webserver to accept webhook requests from these apps, and in turn, sends a scan request to Plex. Plex will then only scan the parent folder (i.e. season folder for TV shows, movie folder for movies, and album folders for music) of the media file (versus scanning the entire library folder).

In addition to the above, Plex Autoscan can also monitor Google Drive for updates. When a new file is detected, it is checked against the Plex database and if this file is missing, a new scan request is sent to Plex (see section [below](README.md#google-drive-monitoring)).

Plex Autoscan is installed on the same server as the Plex Media Server.

# Requirements

1. Ubuntu/Debian

2. Python 2.7 or higher (`sudo apt install python python-pip`).

3. requirements.txt modules (see below).

# Installation

1. `cd /opt`

1. `sudo git clone https://github.com/l3uddz/plex_autoscan`

1. `sudo chown -R user:group plex_autoscan` - Run `id` to find your user / group.

1. `cd plex_autoscan`

1. `sudo python -m pip install -r requirements.txt`

1. `python scan.py` - Run once to generate a default config.json file.

1. `/opt/plex_autoscan/config/config.json` - Configure settings (do this before moving on).

1. `sudo cp /opt/plex_autoscan/system/plex_autoscan.service /etc/systemd/system/`

1. `sudo systemctl daemon-reload`

1. `sudo systemctl enable plex_autoscan.service`

1. `sudo systemctl start plex_autoscan.service`


# Configuration

_Note: Changes to config file require a restart of the Plex Autoscan service: `sudo systemctl restart plex_autoscan.service`._

## Example

```json
{
  "DOCKER_NAME": "plex",
  "GDRIVE": {
    "CLIENT_ID": "",
    "CLIENT_SECRET": "",
    "ENABLED": false,
    "POLL_INTERVAL": 60,
    "SCAN_EXTENSIONS":[
      "webm","mkv","flv","vob","ogv","ogg","drc","gif",
      "gifv","mng","avi","mov","qt","wmv","yuv","rm",
      "rmvb","asf","amv","mp4","m4p","m4v","mpg","mp2",
      "mpeg","mpe","mpv","m2v","m4v","svi","3gp","3g2",
      "mxf","roq","nsv","f4v","f4p","f4a","f4b","mp3",
      "flac","ts"
    ]
  },
  "PLEX_ANALYZE_DIRECTORY": true,
  "PLEX_ANALYZE_TYPE": "basic",
  "PLEX_DATABASE_PATH": "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
  "PLEX_EMPTY_TRASH": false,
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
  "PLEX_TOKEN": "",
  "PLEX_USER": "plex",
  "PLEX_WAIT_FOR_EXTERNAL_SCANNERS": true,
  "RCLONE_RC_CACHE_EXPIRE": {
    "ENABLED": false,
    "MOUNT_FOLDER": "/mnt/rclone",
    "RC_URL": "http://localhost:5572"
  },
  "RUN_COMMAND_BEFORE_SCAN": "",
  "SERVER_ALLOW_MANUAL_SCAN": false,
  "SERVER_FILE_EXIST_PATH_MAPPINGS": {
      "/mnt/unionfs/media": [
          "/data"
      ]
  },
  "SERVER_IGNORE_LIST": [
    "/.grab/",
    ".DS_Store",
    "Thumbs.db"
  ],
  "SERVER_IP": "0.0.0.0",
  "SERVER_MAX_FILE_CHECKS": 10,
  "SERVER_FILE_CHECK_DELAY": 60,
  "SERVER_PASS": "9c4b81fe234e4d6eb9011cefe514d915",
  "SERVER_PATH_MAPPINGS": {
      "/mnt/unionfs": [
          "/home/seed/media/fused"
      ]
  },
  "SERVER_PORT": 3468,
  "SERVER_SCAN_DELAY": 180,
  "SERVER_SCAN_FOLDER_ON_FILE_EXISTS_EXHAUSTION": false,
  "SERVER_SCAN_PRIORITIES": {
    "1": [
      "/Movies/"
    ],
    "2": [
      "/TV/"
    ]
  },
  "SERVER_USE_SQLITE": true,
  "USE_DOCKER": false,
  "USE_SUDO": false
}

```
## Basics


```json
"USE_SUDO": true
```

`USE_SUDO` - This option is typically used in conjunction with `PLEX_USER` (e.g. `sudo -u plex`).

  - If the user that runs your Plex Autoscan server is able to run the Plex Media Scanner CLI command without sudo, or is installed with the same user account (e.g. `plex`), you can you can set this to `false`.

  - The user that runs plex_autoscan needs to beable to sudo, without a password otherwise, it cannot execute the PLEX_SCANNER as `plex`. This can be disabled by config option USE_SUDO.

 - Default is `true`.

## Docker

Docker specific options.


_Note: Docker examples used below are based on the image by [plexinc/pms-docker](https://hub.docker.com/r/plexinc/pms-docker/), with `/config/` in the container path mapped to `/opt/plex/` on the host._

```json
"USE_DOCKER": true,
"DOCKER_NAME": "plex",
```

`USE_DOCKER` - Set to `true` when Plex is in a Docker container. Default is `false`.

`DOCKER_NAME` - Name of the Plex docker container. Default is `"plex"`.


## Plex Media Server

Plex Media Server options.


### Plex Basics

```json
"PLEX_USER": "plex",
"PLEX_WAIT_FOR_EXTERNAL_SCANNERS": true,
"PLEX_ANALYZE_TYPE": "basic",
"PLEX_ANALYZE_DIRECTORY": true,
```

`PLEX_USER` - User account that Plex runs as.

  - Native Install: `"plex"`

  - Docker Install: `"plex"` (user account within the container).

`PLEX_WAIT_FOR_EXTERNAL_SCANNERS` - When set to `true`, wait for other Plex Media Scanner processes to finish, before launching a new one.

  - For hosts running a single Plex Docker instance, this can be left as `true`. For multiple Plex Docker instances on a host, set this as `false`.

`PLEX_ANALYZE_TYPE` - How Plex will analyze the media files that are scanned. Options are `off`, `basic`, `deep`. `off` will disable analyzing. Default is `basic`.

`PLEX_ANALYZE_DIRECTORY` - When set to `true`, Plex will analyze all the media files in the parent folder (e.g. movie folder, season folder) vs just the newly added file. Default is `true`.


### Plex File Locations

_Note: Verify the settings below by running the Plex Section IDs command (see below)._


```json
"PLEX_LD_LIBRARY_PATH": "/usr/lib/plexmediaserver",

"PLEX_SCANNER": "/usr/lib/plexmediaserver/Plex\\ Media\\ Scanner",

"PLEX_SUPPORT_DIR": "/var/lib/plexmediaserver/Library/Application\\ Support",

"PLEX_DATABASE_PATH": "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
```

`PLEX_LD_LIBRARY_PATH`

  - Native Install: `"/usr/lib/plexmediaserver"`

  - Docker Install: `"/usr/lib/plexmediaserver"` (path within the container).

`PLEX_SCANNER` - Location of Plex Media Scanner binary.

  - Native Install: `"/usr/lib/plexmediaserver/Plex\\ Media\\ Scanner"`

  - Docker Install: `"/usr/lib/plexmediaserver/Plex\\ Media\\ Scanner"` (path within the container).

`PLEX_SUPPORT_DIR` - Location of Plex "Application Support" path.

  - Native Install: `"/var/lib/plexmediaserver/Library/Application\\ Support"`

  - Docker Install: `"/var/lib/plexmediaserver/Library/Application\\ Support"` (path within the container).

`PLEX_DATABASE_PATH` - Location of Plex library database.

  - Native Install: `"/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"`

  - Docker Install: `"/opt/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"` (path on the host)



### Plex Section IDs

Running the following command, will return a list of Plex Library Names and their corresponding Section IDs (sorted by alphabetically Library Name):

```shell
python scan.py sections
```

This will be in the format of:

```
SECTION ID #: LIBRARY NAME
```

Sample output:

```
 2018-06-23 08:28:26,910 -     INFO -    CONFIG [140425529542400]: Using default setting --loglevel=INFO
 2018-06-23 08:28:26,910 -     INFO -    CONFIG [140425529542400]: Using default setting --cachefile=cache.db
 2018-06-23 08:28:26,910 -     INFO -    CONFIG [140425529542400]: Using default setting --tokenfile=token.json
 2018-06-23 08:28:26,910 -     INFO -    CONFIG [140425529542400]: Using default setting --queuefile=queue.db
 2018-06-23 08:28:26,910 -     INFO -    CONFIG [140425529542400]: Using default setting --logfile=plex_autoscan.log
 2018-06-23 08:28:26,910 -     INFO -    CONFIG [140425529542400]: Using default setting --config=config/config.json
 2018-06-23 08:28:27,069 -     INFO -  AUTOSCAN [140425529542400]:
        _                         _
  _ __ | | _____  __   __ _ _   _| |_ ___  ___  ___ __ _ _ __
 | '_ \| |/ _ \ \/ /  / _` | | | | __/ _ \/ __|/ __/ _` | '_ \
 | |_) | |  __/>  <  | (_| | |_| | || (_) \__ \ (_| (_| | | | |
 | .__/|_|\___/_/\_\  \__,_|\__,_|\__\___/|___/\___\__,_|_| |_|
 |_|

#########################################################################
# Author:   l3uddz                                                      #
# URL:      https://github.com/l3uddz/plex_autoscan                     #
# --                                                                    #
# Part of the Cloudbox project: https://cloudbox.works                  #
#########################################################################
# GNU General Public License v3.0                                       #
#########################################################################

 2018-06-23 08:28:27,070 -     INFO -      PLEX [140425529542400]: Using Plex Scanner
  1: Movies
  2: TV
```

### Plex Section Mappings

This tells Plex what library sections to map the media paths to when the Plex Scanner command is ran.

Format:


```json
"PLEX_SECTION_PATH_MAPPINGS": {
  "SECTION ID #": [
    "/path/to/library/"
  ]
},
```

For example, if a request is sent to scan a filepath with `/Movies/` in it, then to map it to Section ID 1, and to map filepath `/TV` to Section ID 2.


Example:

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


If you have a complex library setup, you will need to specfiy the child paths as well:

Example:

```json
"PLEX_SECTION_PATH_MAPPINGS": {
  "1": [
    "/Movies/Movies/"
  ],
  "2": [
    "/Movies/Movies-4K/"
  ],
  "3": [
    "/Movies/Movies-Foreign/"
  ],
  "4": [
    "/TV/"
  ]
},
```

### Plex Emptying Trash

When media is upgraded by Sonarr/Radarr/Lidarr, the previous files are then deleted. When Plex gets the scan request after the upgrade, the new media is added in to the library, but the previous media files would still be listed there but labeled as "unavailable".

To remedy this, a trash emptying command needs to be sent to Plex to get rid of these missing files from the library. The options below enable that to happen.


```json
"PLEX_TOKEN": "abcdefghijkl",
"PLEX_LOCAL_URL": "http://localhost:32400",
"PLEX_EMPTY_TRASH": true,
"PLEX_EMPTY_TRASH_CONTROL_FILES": [
  "/mnt/unionfs/mounted.bin"
],
"PLEX_EMPTY_TRASH_MAX_FILES": 100,
"PLEX_EMPTY_TRASH_ZERO_DELETED": true,
```

`PLEX_TOKEN` - Plex Access Token.

  - Run the Plex Token script by [Werner Beroux](https://github.com/wernight): `/opt/plex_autoscan/scripts/plex_token.sh`, or

  - Visit https://support.plex.tv/hc/en-us/articles/204059436-Finding-an-authentication-token-X-Plex-Token


`PLEX_LOCAL_URL` - Local URL of the Plex Media Server.

  - Native Install: `"http://localhost:32400"`

  - Docker Install: `"http://localhost:32400"` (open port)

`PLEX_EMPTY_TRASH` - When set to `true`, empty trash of a section after a scan.

`PLEX_EMPTY_TRASH_CONTROL_FILES` - Only empty trash when this file exists. Useful when media files, located elsewhere, is mounted on the Plex Server host. Can be left blank if not needed.

`PLEX_EMPTY_TRASH_MAX_FILES` - The maximum amount of missing files to remove from Plex at one emptying trash request.  If there are more missing files than the number listed, the emptying trash request is aborted. This is particularly useful when externally mounted media temporarily dismounts and a ton of files go "missing" in Plex. Default is `100`.

`PLEX_EMPTY_TRASH_ZERO_DELETED` - When set to `true`, will always empty the trash on the scanned section, even if there are 0 missing files. If `false`, trash will only be emptied when the database returns more than 0 deleted items. Default is `false`.


## Plex Autoscan Server

### Basics

```json
"SERVER_IP": "0.0.0.0",
"SERVER_PASS": "9c4b81fe234e4d6eb9011cefe514d915",
"SERVER_PORT": 3468,
"SERVER_SCAN_DELAY": 180,
```

`SERVER_IP` -  Server IP that Plex Autoscan will listen on. Default is `0.0.0.0`.

  - `0.0.0.0` - Allow remote access (e.g. Sonarr/Radarr/Lidarr running on another/remote server).

  - `127.0.0.1` - Local access only.

`SERVER_PORT` - Port that Plex Autoscan will listen on.

`SERVER_PASS` - Plex Autoscan password. Used to authenticate requests from Sonarr/Radarr/Lidarr. Default is a random 32 character string generated during config build.

  - Your webhook URL will look like: http://ipaddress:3468/server_pass (or http://localhost:3468/server_pass if local only).

`SERVER_SCAN_DELAY` - How long (in seconds) Plex Autoscan will wait before sending a scan request to Plex.

  - This is useful, for example, when you want Plex Autoscan to wait for more episodes of the same TV show to come in before scanning the season folder, resulting in less work for Plex to do by not scannin the same folder multiple times. This works especially well with `SERVER_USE_SQLITE` enabled.


### Server - Path Mappings

List of paths that will be remapped before being scanned by Plex.

This is particularly useful when receiving scan requests, from a remote Sonarr/Radarr/Lidarr installation, that has different paths for the media.

#### Native Install

Format:
```json
"SERVER_PATH_MAPPINGS": {
    "/path/on/local/host": [
        "/path/on/sonarr/host"
    ]
},
```

Example:

```json
"SERVER_PATH_MAPPINGS": {
    "/mnt/unionfs": [
        "/home/seed/media/fused"
    ]
},
```

#### Docker Install

Format:

```json
"SERVER_PATH_MAPPINGS": {
    "/path/in/plex/container": [
        "/path/from/sonarr/container"
    ]
},
```

Example:

```json
"SERVER_PATH_MAPPINGS": {
  "/data/Movies/": [
    "/movies/"
  ]
}
```



If the filepath that was reported to Plex Autoscan by Radarr was `/home/seed/media/fused/Movies/Die Hard/Die Hard.mkv` then the path that would be scanned by Plex would be `/mnt/unionfs/Movies/Die Hard/Die Hard.mkv`.


#### Multiple paths

You can also have more than one folder paths pointing to a single one.

Example:

```json
"SERVER_PATH_MAPPINGS": {
  "/data/Movies/": [
    "/media/movies/",
    "/local/movies/"
  ]
}
```


### Server File Checks

After a `SERVER_SCAN_DELAY`, Plex Autoscan will check to see if file exists before sending a scan request to Plex.


```json
"SERVER_MAX_FILE_CHECKS": 10,
"SERVER_FILE_CHECK_DELAY": 60,
"SERVER_SCAN_FOLDER_ON_FILE_EXISTS_EXHAUSTION": false,
```

`SERVER_MAX_FILE_CHECKS` -  The number specifies how many times this check will occur, before giving up. If set to `0`, this check will not occur, and Plex Autoscan will simply send the scan request after the `SERVER_SCAN_DELAY`. Default is `10`.

`SERVER_FILE_CHECK_DELAY` - Delay in seconds between two file checks. Default is `60`.

`SERVER_SCAN_FOLDER_ON_FILE_EXISTS_EXHAUSTION` - Plex Autoscan will scan the media folder when the file exist checks (as set above) are exhausted. Default is `false`.

### Server File Exists - Path Mappings

List of paths that will be remapped before file exist checks are done.

This is particularly useful when using Docker, since the folder being scanned by the Plex container, may be different to the path on the host system running Plex Autoscan.


Format:
```json
"SERVER_FILE_EXIST_PATH_MAPPINGS": {
    "/actual/path/on/host": [
        "/path/from/plex/container"
    ]
},
```


Example:
```json
"SERVER_FILE_EXIST_PATH_MAPPINGS": {
    "/mnt/unionfs/media": [
        "/data"
    ]
},
```


You can leave this empty if it is not required:
```json
"SERVER_FILE_EXIST_PATH_MAPPINGS": {
},
```

### Scan Queue Database

```json
"SERVER_USE_SQLITE": true,
```

Plex Autoscan can use an optionally use a database to store queue requests. The benefits to using this are 1) Queue will be restored on Plex Autoscan restart, and 2) Multiple requests to the same folder can be merged into a single folder scan.

This would look like:

```
Already processing '/data/TV/TV-Anime/Persona 5 the Animation/Season 1/Persona 5 the Animation - s01e01 - I am thou, thou art I.mkv' from same folder, aborting adding an extra scan request to the queue.
Scan request from Sonarr for '/data/TV/TV-Anime/Persona 5 the Animation/Season 1/Persona 5 the Animation - s01e01 - I am thou, thou art I.mkv', sleeping for 180 seconds...
```

The `180` seconds in the example above are from the `SERVER_SCAN_DELAY`, if any more requests come in during this time, the scan request will be delayed by another `180` seconds.

### Misc

```json
"SERVER_ALLOW_MANUAL_SCAN": false,
"SERVER_IGNORE_LIST": [
  "/.grab/",
  ".DS_Store",
  "Thumbs.db"
],
"SERVER_SCAN_PRIORITIES": {
  "1": [
    "/Movies/"
  ],
  "2": [
    "/TV/"
  ]
},
```


`SERVER_ALLOW_MANUAL_SCAN` - When enabled, allows GET requests to the webhook URL to allow manual scans on a specific filepath. Default is `false`.

  - All path mappings and section ID mappings, of the server, apply.

  - This is also a good way of testing your configuration, manually.

  - To send a manual scan, you can either:

    - Visit your webhook url in a browser (e.g. http://ipaddress:3468/0c1fa3c9867e48b1bb3aa055cb86), and fill in the path to scan.

      ![](https://i.imgur.com/s92pdIR.png)

      or

    - Initiate a scan via curl:

      ```shell
      curl -d "eventType=Manual&filepath=/mnt/unionfs/Media/Movies/Shut In (2016)/Shut In (2016) - Bluray-1080p.x264.DTS-GECKOS.mkv" http://ipaddress:3468/0c1fa3c9867e48b1bb3aa055cb86`
      ```

`SERVER_IGNORE_LIST` - List of paths or filenames to ignore when a requests is sent to Plex Autoscan manually (see above). Case senstive.

  - For example, `curl -d "eventType=Manual&filepath=/mnt/unionfs/Media/Movies/Thumbs.db" http://ipaddress:3468/0c1fa3c9867e48b1bb3aa055cb86` would be ignored if `Thumbs.db` was in the ignore list.


`SERVER_SCAN_PRIORITIES` - What paths are picked first when multiple scan requests are being processed.

  - This section is similar to `PLEX_SECTION_PATH_MAPPINGS` mentioned earlier.

  - Format:
    ```json
    "SERVER_SCAN_PRIORITIES": {
      "PRIORITY LEVEL#": [
        "/path/to/library/in/Plex"
      ],
    },
    ```

## Google Drive Monitoring

As mentioned earlier, Plex Autoscan can monitor Google Drive for changes. It does this by utilizing a proactive cache (vs building a cache from start to end).

Once a change is detected, the file will be checked against the Plex database to make sure this is not already there. If this match comes back negative, a scan request for the parent folder is added into the process queue, and if that parent folder is already in the process queue, the duplicate request will be ignored.

_Note: Google Drive Monitoring is not compatible with Teamdrive or encrypted files._

```json
"GDRIVE": {
  "CLIENT_ID": "",
  "CLIENT_SECRET": "",
  "ENABLED": false,
  "POLL_INTERVAL": 60,
  "SCAN_EXTENSIONS":[
    "webm","mkv","flv","vob","ogv","ogg","drc","gif",
    "gifv","mng","avi","mov","qt","wmv","yuv","rm",
    "rmvb","asf","amv","mp4","m4p","m4v","mpg","mp2",
    "mpeg","mpe","mpv","m2v","m4v","svi","3gp","3g2",
    "mxf","roq","nsv","f4v","f4p","f4a","f4b","mp3",
    "flac","ts"
  ]
},
```

`ENABLED` - Enable or Disable Google Drive Monitoring. Requires one time authorization, see below.

`CLIENT_ID` - Google Drive API Client ID.

`CLIENT_SECRET` - Google Drive API Client Secret.

`POLL_INTERVAL` - How often to check for Google Drive changes (in seconds).

`SCAN_EXTENSIONS` - File files to be monitored via their file extensions.

---

To set this up:

1. Edit `config.json `file, to enable the Google Drive monitoring and fill in your Google Drive API Client ID and Secret.

    ```json
    "CLIENT_ID": "yourclientid",
    "CLIENT_SECRET": "yourclientsecret",
    "ENABLED": true,
    ```

1. Next, you will need to authorize Google Drive.

   ```shell
   scan.py authorize
   ```

1. Visit the link shown to get the authorization code and paste that in and hit `enter`.

    ```
    2018-06-24 05:50:14,945 -     INFO -    CONFIG [140446220769088]: Using default setting --loglevel=INFO
    2018-06-24 05:50:14,945 -     INFO -    CONFIG [140446220769088]: Using default setting --cachefile=/opt/plex_autoscan/cache.db
    2018-06-24 05:50:14,945 -     INFO -    CONFIG [140446220769088]: Using default setting --tokenfile=/opt/plex_autoscan/token.json
    2018-06-24 05:50:14,946 -     INFO -    CONFIG [140446220769088]: Using default setting --queuefile=/opt/plex_autoscan/queue.db
    2018-06-24 05:50:14,946 -     INFO -    CONFIG [140446220769088]: Using default setting --logfile=/opt/plex_autoscan/plex_autoscan.log
    2018-06-24 05:50:14,946 -     INFO -    CONFIG [140446220769088]: Using default setting --config=/opt/plex_autoscan/config/config.json
    2018-06-24 05:50:15,222 -     INFO -  AUTOSCAN [140446220769088]:
          _                         _
    _ __ | | _____  __   __ _ _   _| |_ ___  ___  ___ __ _ _ __
    | '_ \| |/ _ \ \/ /  / _` | | | | __/ _ \/ __|/ __/ _` | '_ \
    | |_) | |  __/>  <  | (_| | |_| | || (_) \__ \ (_| (_| | | | |
    | .__/|_|\___/_/\_\  \__,_|\__,_|\__\___/|___/\___\__,_|_| |_|
    |_|

    #########################################################################
    # Author:   l3uddz                                                      #
    # URL:      https://github.com/l3uddz/plex_autoscan                     #
    # --                                                                    #
    # Part of the Cloudbox project: https://cloudbox.works                  #
    #########################################################################
    # GNU General Public License v3.0                                       #
    #########################################################################

    Visit https://accounts.google.com/o/oauth2/v2/auth?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&client_id=&access_type=offline and authorize against the account you wish to use
    Enter authorization code:
    ```
1. When access token retrieval is successfull, you'll see this:

   ```
   2018-06-24 05:57:58,252 -     INFO -    GDRIVE [140007964366656]: Requesting access token for auth code '4/AAAfPHmX9H_kMkMasfdsdfE4r8ImXI_BddbLF-eoCOPsdfasdfHBBzffKto'
   2018-06-24 05:57:58,509 -     INFO -    GDRIVE [140007964366656]: Retrieved first access token!
   2018-06-24 05:57:58,511 -     INFO -  AUTOSCAN [140007964366656]: Access tokens were successfully retrieved!
   ```

1. You will now need to add in your Google Drive paths into `SERVER_PATH_MAPPINGS`.

    For example, if you store your files under My Drive's Media folder, it would look like this:

    ```json
    "SERVER_PATH_MAPPINGS": {
      "/mnt/unionfs/Media/Movies/": [
        "/home/seed/media/fused"
        "My Drive/Media/Movies/"
      ],
    },
    ```

    For Plex in a docker container, this would look like this:

    ```json
    "SERVER_PATH_MAPPINGS": {
      "/data/Movies/": [
        "/movies/",
        "My Drive/Media/Movies/"
      ]
    }
    ```

1. Google Drive Monitoring is now setup.

---


## Rclone Remote Control

For users of Rclone cache mounts.


```json
"RCLONE_RC_CACHE_EXPIRE": {
  "ENABLED": false,
  "MOUNT_FOLDER": "/mnt/rclone",
  "RC_URL": "http://localhost:5572"
},
```


When `RCLONE_RC_CACHE_EXPIRE` is enabled, if a file exist check fails, Plex Autoscan will keep sending an Rclone cache clear request for that files parent folder until the file check succeeds.

  - For example, `/Media/Movies/Movie/Movie.mkv`, sends clear for `Movie` folder. But if a file exist checks fails (because it's not cached yet), so clears `Movies` folder again, and so on, until a file check exists comes back positive or checks count reaches `SERVER_MAX_FILE_CHECKS`.

`MOUNT_FOLDER` - Path on the host where Rclone cache is mounted.

`RC_URL` - URL and Port Rclone RC is set to.

# Setup

Setup instructions to connect Sonarr/Radarr/Lidarr to Plex Autoscan.

## Sonarr

1. Sonarr -> "Settings" -> "Connect".

1. Add a new "Webhook".

1. Add the following:

   1. Name: Plex Autoscan

   1. On Grab: `No`

   1. On Download: `Yes`

   1. On Upgrade:  `Yes`

   1. On Rename: `Yes`

   1. Filter Series Tags: _Leave Blank_

   1. URL: _Your Plex Autoscan Webhook URL_

   1. Method:`POST`

   1. Username: _Leave Blank_

   1. Password: _Leave Blank_

1. The settings will look like this:

    ![Sonarr Plex Autoscan](https://i.imgur.com/F8L8R3a.png)

1. Click "Save" to add Plex Autoscan.

## Radarr

1. Radarr -> "Settings" -> "Connect".

1. Add a new "Webhook".

1. Add the following:

   1. Name: Plex Autoscan

   1. On Grab: `No`

   1. On Download: `Yes`

   1. On Upgrade:  `Yes`

   1. On Rename: `Yes`

   1. Filter Movie Tags: _Leave Blank_

   1. URL: _Your Plex Autoscan Webhook URL_

   1. Method:`POST`

   1. Username: _Leave Blank_

   1. Password: _Leave Blank_

1. The settings will look like this:

    ![Radarr Plex Autoscan](https://i.imgur.com/jQJyvMA.png)

1. Click "Save" to add Plex Autoscan.


## Lidarr

1. Lidarr -> "Settings" -> "Connect".

1. Add a new "Webhook" Notification.

1. Add the following:

   1. Name: Plex Autoscan

   1. On Grab: `No`

   1. On Album Import: `No`

   1. On Track Import: `Yes`

   1. On Track Upgrade:  `Yes`

   1. On Rename: `Yes`

   1. Tags: _Leave Blank_

   1. URL: _Your Plex Autoscan Webhook URL_

   1. Method:`POST`

   1. Username: _Leave Blank_

   1. Password: _Leave Blank_

1. The settings will look like this:

    ![Radarr Plex Autoscan](https://i.imgur.com/43uZloh.png)

1. Click "Save" to add Plex Autoscan.
