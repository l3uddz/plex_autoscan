import json
import logging
import os
import sys
import uuid

logger = logging.getLogger("CONFIG")
logger.setLevel(logging.DEBUG)

config_path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')

base_config = {
    'PLEX_USER': 'plex',
    'PLEX_SECTION_PATH_MAPPINGS': {
        '1': [
            '/Movies/'
        ],
        '2': [
            '/TV/'
        ]
    },
    'PLEX_SCANNER': '/usr/lib/plexmediaserver/Plex\\ Media\\ Scanner',
    'PLEX_SUPPORT_DIR': '/var/lib/plexmediaserver/Library/Application\ Support',
    'PLEX_LD_LIBRARY_PATH': '/usr/lib/plexmediaserver',
    'PLEX_DATABASE_PATH': '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server'
                          '/Plug-in Support/Databases/com.plexapp.plugins.library.db',
    'PLEX_LOCAL_URL': 'http://localhost:32400',
    'PLEX_EMPTY_TRASH': False,
    'PLEX_EMPTY_TRASH_MAX_FILES': 100,
    'PLEX_EMPTY_TRASH_CONTROL_FILES': [
        '/mnt/unionfs/mounted.bin'
    ],
    'PLEX_EMPTY_TRASH_ZERO_DELETED': False,
    'PLEX_WAIT_FOR_EXTERNAL_SCANNERS': True,
    'PLEX_TOKEN': '',
    'SERVER_IP': '0.0.0.0',
    'SERVER_PORT': 3467,
    'SERVER_PASS': uuid.uuid4().hex,
    'SERVER_PATH_MAPPINGS': {
        '/mnt/unionfs': [
            '/home/seed/media/fused'
        ]
    },
    'SERVER_SCAN_DELAY': 5,
    'SERVER_MAX_FILE_CHECKS': 10,
    'SERVER_ALLOW_MANUAL_SCAN': False,
    'USE_SUDO': True,
    'USE_QUOTED_SCAN_DIRECTORY': True
}


def upgrade(cfg):
    new_config = {}
    added_fields = 0
    fields = []

    for name, data in base_config.items():
        if name not in cfg:
            new_config[name] = data
            fields.append(name)
            added_fields += 1
        else:
            new_config[name] = cfg[name]

    with open(config_path, 'w') as fpc:
        json.dump(new_config, fpc, indent=4, sort_keys=True)
        fpc.close()

    if added_fields and len(fields):
        logger.info("Upgraded config.json, added %d new field(s): %r", added_fields, fields)
    return new_config


def load():
    if not os.path.exists(config_path):
        build()
        exit(0)
    cfg = {}
    with open(config_path, 'r') as fp:
        cfg = upgrade(json.load(fp))
        fp.close()
    return cfg


def build():
    with open(config_path, 'w') as fp:
        json.dump(base_config, fp, indent=4, sort_keys=True)
        fp.close()
    logger.info("Created default config.json: '%s'", config_path)
    logger.info("Please configure it before running me again.")
    exit(0)
