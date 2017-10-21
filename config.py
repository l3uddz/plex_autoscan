import json
import logging
import os
import sys
import uuid

logger = logging.getLogger("CONFIG")
logger.setLevel(logging.DEBUG)

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
    'SERVER_FILE_EXIST_PATH_MAPPINGS': {
        '/home/thompsons/plexdrive': [
            '/data'
        ]
    },
    'SERVER_ALLOW_MANUAL_SCAN': False,
    'SERVER_IGNORE_LIST': [
        '/.grab/',
        '.DS_Store',
        'Thumbs.db'
    ],
    'DOCKER_NAME': 'plex',
    'USE_DOCKER': False,
    'USE_SUDO': True
}


def upgrade(config_path, cfg):
    fields = []
    fields_env = {}

    for name, data in base_config.items():
        if name not in cfg:
            cfg[name] = data
            fields.append(name)

        if name in os.environ:
            fields_env[name] = os.environ[name]
            logger.info("Using ENV setting %s=%s", name, os.environ[name])

    # Only rewrite config file if new fields added
    if len(fields):
        build(cfg)
        logger.info("Upgraded config, added %d new field(s): %r", len(fields), fields)

    # Update in-memory config with environment settings
    cfg.update(fields_env)

    return cfg


def load():
    config_path = get_setting(
        '--config',
        'PLEX_AUTOSCAN_CONFIG',
        os.path.join(os.path.dirname(sys.argv[0]), 'config', 'config.json')
    )

    if not os.path.exists(config_path):
        logger.info("No config file found, creating default config.")
        build(config_path)

    cfg = {}
    with open(config_path, 'r') as fp:
        cfg = upgrade(config_path, json.load(fp))

    return cfg


def build(config_path, cfg=base_config):
    with open(config_path, 'w') as fp:
        json.dump(cfg, fp, indent=4, sort_keys=True)

    logger.info("Please configure/review config before running again: %r", config_path)

    exit(0)


def get_setting(argv_name, env_name, argv_default):
    try:
        # Argrument priority: cmd < environment < default
        if argv_name in sys.argv:
            argv_value = sys.argv[sys.argv.index(argv_name) + 1]

        elif env_name in os.environ:
            argv_value = os.environ[env_name]

        else:
            argv_value = argv_default

        logger.debug("Using ARG setting %s=%s", env_name, argv_value)

    except Exception:
        logger.exception("Exception retrieving argument value: %r" % argv_name)

    return argv_value
