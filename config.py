import argparse
import json
import logging
import os
import sys
import uuid

logger = logging.getLogger("CONFIG")

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
    'PLEX_ANALYZE_FILE': False,
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
    'SERVER_USE_SQLITE': False,
    'DOCKER_NAME': 'plex',
    'USE_DOCKER': False,
    'USE_SUDO': True
}

settings = {
    'config': {
        'argv': '--config',
        'env': 'PLEX_AUTOSCAN_CONFIG',
        'default': os.path.join(os.path.dirname(sys.argv[0]), 'config', 'config.json')
    },
    'logfile': {
        'argv': '--logfile',
        'env': 'PLEX_AUTOSCAN_LOGFILE',
        'default': os.path.join(os.path.dirname(sys.argv[0]), 'plex_autoscan.log')
    },
    'loglevel': {
        'argv': '--loglevel',
        'env': 'PLEX_AUTOSCAN_LOGLEVEL',
        'default': 'INFO'
    }
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
        logger.warn("Upgraded config, added %d new field(s): %r", len(fields), fields)
        build(config_path, cfg)

    # Update in-memory config with environment settings
    cfg.update(fields_env)

    return cfg


def load(cmd_args):
    config_path = get_setting(cmd_args, 'config')

    if not os.path.exists(config_path):
        logger.warn("No config file found, creating default config.")
        build(config_path)

    cfg = {}
    with open(config_path, 'r') as fp:
        cfg = upgrade(config_path, json.load(fp))

    return cfg


def build(config_path, cfg=base_config):
    with open(config_path, 'w') as fp:
        json.dump(cfg, fp, indent=4, sort_keys=True)

    logger.warn("Please configure/review config before running again: %r", config_path)

    exit(0)


def get_setting(args, name):
    try:
        argv_value = None

        # Argrument priority: cmd < environment < default
        if args[name]:
            argv_value = args[name]
            logger.info("Using ARG setting %s=%s", name, argv_value)

        elif settings[name]['env'] in os.environ:
            argv_value = os.environ[settings[name]['env']]
            logger.info("Using ENV setting %s=%s", settings[name]['env'], argv_value)

        else:
            argv_value = settings[name]['default']
            logger.info("Using default setting %s=%s", settings[name]['argv'], argv_value)

    except Exception:
        logger.exception("Exception retrieving setting value: %r" % name)

    return argv_value


# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            'Script to assist sonarr/radarr with plex imports. Will only scan the folder \n'
            'that has been imported, instead of the whole library section.'
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Mode
    parser.add_argument('cmd',
                        choices=('sections', 'server'),
                        help=(
                            '"sections": prints plex sections\n'
                            '"server": starts the application'
                        )
                        )

    # Config file
    parser.add_argument(settings['config']['argv'],
                        nargs='?',
                        const=None,
                        help='Config file location (default: %s)' % settings['config']['default']
                        )

    # Log file
    parser.add_argument(settings['logfile']['argv'],
                        nargs='?',
                        const=None,
                        help='Log file location (default: %s)' % settings['logfile']['default']
                        )

    # Logging level
    parser.add_argument(settings['loglevel']['argv'],
                        choices=('WARN', 'INFO', 'DEBUG'),
                        help='Log level (default: %s)' % settings['loglevel']['default']
                        )

    # Print help by default if no arguments
    if len(sys.argv) == 1:
        parser.print_help()

        sys.exit(0)

    else:
        return vars(parser.parse_args())
