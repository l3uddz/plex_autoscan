import argparse
import json
import logging
import os
import sys
import uuid

logger = logging.getLogger("CONFIG")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


class Config(object):
    __metaclass__ = Singleton

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
        'PLEX_ANALYZE_TYPE': 'basic',
        'PLEX_ANALYZE_DIRECTORY': True,
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
        'SERVER_SCAN_PRIORITIES': {
            0: [
                '/Movies/'
            ],
            1: [
                '/TV/'
            ],
            2: [
                '/Music/'
            ]
        },
        'RCLONE_RC_CACHE_EXPIRE': {
            'ENABLED': False,
            'MOUNT_FOLDER': '/mnt/rclone',
            'RC_URL': 'http://localhost:5572'
        },
        'DOCKER_NAME': 'plex',
        'RUN_COMMAND_BEFORE_SCAN': '',
        'USE_DOCKER': False,
        'USE_SUDO': True,
        'GDRIVE': {
            'CLIENT_ID': '',
            'CLIENT_SECRET': '',
            'POLL_INTERVAL': 60,
            'ENABLED': False,
            'SCAN_EXTENSIONS': ['webm', 'mkv', 'flv', 'vob', 'ogv', 'ogg', 'drc', 'gif', 'gifv', 'mng', 'avi',
                                 'mov', 'qt', 'wmv', 'yuv', 'rm', 'rmvb', 'asf', 'amv', 'mp4', 'm4p', 'm4v',
                                 'mpg', 'mp2', 'mpeg', 'mpe', 'mpv', 'm2v', 'm4v', 'svi', '3gp', '3g2', 'mxf',
                                 'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b']
        }
    }

    base_settings = {
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
        },
        'queuefile': {
            'argv': '--queuefile',
            'env': 'PLEX_AUTOSCAN_QUEUEFILE',
            'default': os.path.join(os.path.dirname(sys.argv[0]), 'queue.db')
        },
        'tokenfile': {
            'argv': '--tokenfile',
            'env': 'PLEX_AUTOSCAN_TOKENFILE',
            'default': os.path.join(os.path.dirname(sys.argv[0]), 'token.json')
        },
        'cachefile': {
            'argv': '--cachefile',
            'env': 'PLEX_AUTOSCAN_CACHEFILE',
            'default': os.path.join(os.path.dirname(sys.argv[0]), 'cache.json')
        }
    }

    def __init__(self):
        """Initializes config"""
        # Args and settings
        self.args = self.parse_args()
        self.settings = self.get_settings()
        # Configs
        self.configs = None

    def upgrade(self, cfg):
        fields = []
        fields_env = {}

        # ENV gets priority: ENV < config.json
        for name, data in self.base_config.items():
            if name not in cfg:
                cfg[name] = data
                fields.append(name)

            if name in os.environ:
                # Use JSON decoder to get same behaviour as config file
                fields_env[name] = json.JSONDecoder().decode(os.environ[name])
                logger.info("Using ENV setting %s=%s", name, fields_env[name])

        # Only rewrite config file if new fields added
        if len(fields):
            logger.warn("Upgraded config, added %d new field(s): %r", len(fields), fields)
            self.save(cfg)

        # Update in-memory config with environment settings
        cfg.update(fields_env)

        return cfg

    def load(self):
        if not os.path.exists(self.settings['config']):
            logger.warn("No config file found, creating default config.")
            self.save(self.base_config)

        cfg = {}
        with open(self.settings['config'], 'r') as fp:
            cfg = self.upgrade(json.load(fp))

        self.configs = cfg

    def save(self, cfg):
        with open(self.settings['config'], 'w') as fp:
            json.dump(cfg, fp, indent=2, sort_keys=True)

        logger.warn(
            "Please configure/review config before running again: %r",
            self.settings['config']
        )

        exit(0)

    def get_settings(self):
        setts = {}
        for name, data in self.base_settings.items():
            # Argrument priority: cmd < environment < default
            try:
                value = None
                # Command line argument
                if self.args[name]:
                    value = self.args[name]
                    logger.info("Using ARG setting %s=%s", name, value)

                # Envirnoment variable
                elif data['env'] in os.environ:
                    value = os.environ[data['env']]
                    logger.info("Using ENV setting %s=%s" % (
                        data['env'],
                        value
                    ))

                # Default
                else:
                    value = data['default']
                    logger.info("Using default setting %s=%s" % (
                        data['argv'],
                        value
                    ))

                setts[name] = value

            except Exception:
                logger.exception("Exception retrieving setting value: %r" % name)

        return setts

    # Parse command line arguments
    def parse_args(self):
        parser = argparse.ArgumentParser(
            description=(
                'Script to assist sonarr/radarr with plex imports. Will only scan the folder \n'
                'that has been imported, instead of the whole library section.'
            ),
            formatter_class=argparse.RawTextHelpFormatter
        )

        # Mode
        parser.add_argument('cmd',
                            choices=('sections', 'server', 'authorize'),
                            help=(
                                '"sections": prints plex sections\n',
                                '"server": starts the application\n',
                                '"authorize": authorize against a google account'
                            )
                            )

        # Config file
        parser.add_argument(self.base_settings['config']['argv'],
                            nargs='?',
                            const=None,
                            help='Config file location (default: %s)' % self.base_settings['config']['default']
                            )

        # Log file
        parser.add_argument(self.base_settings['logfile']['argv'],
                            nargs='?',
                            const=None,
                            help='Log file location (default: %s)' % self.base_settings['logfile']['default']
                            )

        # Queue file
        parser.add_argument(self.base_settings['queuefile']['argv'],
                            nargs='?',
                            const=None,
                            help='Queue file location (default: %s)' % self.base_settings['queuefile']['default']
                            )

        # Token file
        parser.add_argument(self.base_settings['tokenfile']['argv'],
                            choices=('WARN', 'INFO', 'DEBUG'),
                            help='Google token file location (default: %s)' % self.base_settings['tokenfile']['default']
                            )

        # Cache file
        parser.add_argument(self.base_settings['cachefile']['argv'],
                            choices=('WARN', 'INFO', 'DEBUG'),
                            help='Google cache file location (default: %s)' % self.base_settings['cachefile']['default']
                            )

        # Logging level
        parser.add_argument(self.base_settings['loglevel']['argv'],
                            choices=('WARN', 'INFO', 'DEBUG'),
                            help='Log level (default: %s)' % self.base_settings['loglevel']['default']
                            )

        # Print help by default if no arguments
        if len(sys.argv) == 1:
            parser.print_help()

            sys.exit(0)

        else:
            return vars(parser.parse_args())
