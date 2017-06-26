#!/usr/bin/env python2.7
import json
import logging
import os
import sys
import uuid
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask
from flask import abort
from flask import request

############################################################
# INIT
############################################################

# Setup logging
logFormatter = logging.Formatter('%(asctime)24s - %(funcName)17s() :: %(message)s')
rootLogger = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

fileHandler = RotatingFileHandler(os.path.join(os.path.dirname(sys.argv[0]), 'plex_autoscan.log'),
                                  maxBytes=1024 * 1024 * 5, backupCount=5)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

logger = rootLogger.getChild("PLEX_AUTOSCAN")
logger.setLevel(logging.DEBUG)

############################################################
# CONFIG
############################################################

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
    'SERVER_IP': '0.0.0.0',
    'SERVER_PORT': 3467,
    'SERVER_PASS': uuid.uuid4().hex,
    'SERVER_PATH_MAPPINGS': {
        '/mnt/unionfs': [
            '/home/seed/media/fused'
        ]
    },
    'SERVER_PUSH_URL': [
        'http://localhost:3467/push'
    ],
    'USE_SERVER_PUSH': False
}
config = None
config_path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')


def upgrade_config(cfg):
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
        logger.debug("Upgraded config.json, added %d new field(s): %r", added_fields, fields)
    return new_config


if not os.path.exists(config_path):
    # Create default config
    with open(config_path, 'w') as fp:
        json.dump(base_config, fp, indent=4, sort_keys=True)
        fp.close()
    logger.debug("Created default config.json: '%s'", config_path)
    logger.debug("Please configure it before running me again.")
    exit(0)
else:
    # Load config
    with open(config_path, 'r') as fp:
        config = upgrade_config(json.load(fp))
        fp.close()


############################################################
# FUNCS
############################################################

def radarr(path):
    section = get_plex_section(path)
    if section <= 0:
        return
    if config['USE_SERVER_PUSH']:
        return push_to_server(path, 'radarr')

    logger.info("Scanning '%s'", path)
    plex(path, section)


def sonarr(path):
    section = get_plex_section(path)
    if section <= 0:
        return
    if config['USE_SERVER_PUSH']:
        return push_to_server(path, 'sonarr')

    logger.info("Scanning '%s'", path)
    plex(path, section)


def plex(path, id):
    if os.name == 'nt':
        final_cmd = '"%s" --scan --refresh --section %s --directory "%s"' \
                    % (config['PLEX_SCANNER'], str(id), os.path.dirname(path))
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] \
              + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
              + config['PLEX_SUPPORT_DIR'] + ';' + config['PLEX_SCANNER'] + ' --scan --refresh --section ' \
              + str(id) + ' --directory \\"' + os.path.dirname(path) + '\\"'
        final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
    return os.system(final_cmd)


def get_plex_section(path):
    for section, mappings in config['PLEX_SECTION_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping.lower() in path.lower():
                return section
    logger.debug("Unable to map '%s' to a section id....", path)
    return -1


def push_to_server(path, path_type):
    for server in config['SERVER_PUSH_URL']:
        logger.debug("Pushing '%s' to server: '%s'", path, server)
        payload = {
            'type': path_type,
            'path': path,
            'pass': config['SERVER_PASS']
        }
        resp = requests.post(server, payload)
        if resp.status_code == 200 and resp.text == "OK":
            logger.debug("Server accepted push")
        else:
            logger.debug("Server declined push with status code: %d", resp.status_code)


def map_pushed_path(path):
    for mapped_path, mappings in config['SERVER_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping in path:
                logger.debug("Mapping '%s' to '%s'", mapping, mapped_path)
                return path.replace(mapping, mapped_path)
    return path


############################################################
# SERVER
############################################################

app = Flask(__name__)


@app.route("/push", methods=['POST'])
def client_pushed():
    if 'pass' not in request.form or 'path' not in request.form or 'type' not in request.form:
        logger.debug("Invalid push request from: %r", request.remote_addr)
        return abort(400)
    if request.form['type'] != 'sonarr' and request.form['type'] != 'radarr':
        logger.debug("Invalid push request type: '%s' from: %r", type, request.remote_addr)
        return abort(400)
    if request.form['pass'] != config['SERVER_PASS']:
        logger.debug("Unauthorized push request from: %r", request.remote_addr)
        return abort(401)
    logger.debug("Client: %r requested scan: '%s', type: '%s'", request.remote_addr, request.form['path'],
                 request.form['type'])

    final_path = map_pushed_path(request.form['path'])
    if request.form['type'] == 'sonarr':
        sonarr(final_path)
    else:
        radarr(final_path)
    return "OK"


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        logger.error("You must pass an argument, sonarr, radarr, sections or server...")
        sys.exit(0)
    else:
        if sys.argv[1].lower() == 'sections':
            if os.name == 'nt':
                final_cmd = '"%s" --list' % config['PLEX_SCANNER']
            else:
                cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] \
                      + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
                      + config['PLEX_SUPPORT_DIR'] + ';' + config['PLEX_SCANNER'] + ' --list'
                final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
            os.system(final_cmd)

        elif sys.argv[1].lower() == 'radarr':
            file_path = os.environ.get('radarr_moviefile_path')
            if file_path:
                radarr(file_path)
            else:
                logger.error("Problem retrieving radarr_moviefile_path")

        elif sys.argv[1].lower() == 'sonarr':
            file_path = os.environ.get('sonarr_episodefile_path')
            if file_path:
                sonarr(file_path)
            else:
                logger.error("Problem retrieving sonarr_episodefile_path")
        elif sys.argv[1].lower() == 'server':
            logger.debug("Starting server: http://%s:%d/push", config['SERVER_IP'], config['SERVER_PORT'])
            app.run(host=config['SERVER_IP'], port=config['SERVER_PORT'], debug=False, use_reloader=False)
            logger.debug("Server stopped")
        else:
            logger.error("You must pass an argument of either sonarr, radarr, sections or server...")
