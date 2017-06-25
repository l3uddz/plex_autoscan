#!/usr/bin/env python2.7
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask
from flask import abort
from flask import request

############################################################
# CONFIG
############################################################

PLEX_USER = "plex"
PLEX_MOVIE_SECTION = 1
PLEX_TV_SECTION = 2
PLEX_SCANNER = "/usr/lib/plexmediaserver/Plex\\ Media\\ Scanner"
PLEX_SUPPORT_DIR = "/var/lib/plexmediaserver/Library/Application\ Support"
PLEX_LD_LIBRARY_PATH = "/usr/lib/plexmediaserver"
SERVER_IP = "0.0.0.0"
SERVER_PORT = 3467
SERVER_PASS = "password"
SERVER_PATH_MAPPINGS = {
    '/mnt/unionfs': [
        '/home/seed/media/fused'
    ]
}
SERVER_PUSH_URL = "http://localhost:3467/push"
USE_SERVER_PUSH = False

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
# FUNCS
############################################################

def radarr(path):
    if USE_SERVER_PUSH:
        return push_to_server(path, 'radarr')

    logger.info("Scanning '%s'", path)
    plex(path, PLEX_MOVIE_SECTION)


def sonarr(path):
    if USE_SERVER_PUSH:
        return push_to_server(path, 'sonarr')

    logger.info("Scanning '%s'", path)
    plex(path, PLEX_TV_SECTION)


def plex(path, id):
    cmd = 'export LD_LIBRARY_PATH=' + PLEX_LD_LIBRARY_PATH + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
          + PLEX_SUPPORT_DIR + ';' + PLEX_SCANNER + ' --scan --refresh --section ' \
          + str(id) + ' --directory \\"' + os.path.dirname(path) + '\\"'
    final_cmd = 'sudo -u %s bash -c "%s"' % (PLEX_USER, cmd)
    return os.system(final_cmd)


def push_to_server(path, path_type):
    logger.debug("Pushing '%s' to server: '%s'", path, SERVER_PUSH_URL)
    payload = {
        'type': path_type,
        'path': path,
        'pass': SERVER_PASS
    }
    resp = requests.post(SERVER_PUSH_URL, payload)
    if resp.status_code == 200 and resp.text == "OK":
        logger.debug("Server accepted push")
        return True
    else:
        logger.debug("Server declined push with status code: %d", resp.status_code)
        return False


def map_pushed_path(path):
    for mapped_path, mappings in SERVER_PATH_MAPPINGS.items():
        for mapping in mappings:
            if mapping in path:
                logger.debug("Mapping %r to %r", mapping, mapped_path)
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
    if request.form['pass'] != SERVER_PASS:
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
            cmd = 'export LD_LIBRARY_PATH=' + PLEX_LD_LIBRARY_PATH + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
                  + PLEX_SUPPORT_DIR + ';' + PLEX_SCANNER + ' --list'
            final_cmd = 'sudo -u %s bash -c "%s"' % (PLEX_USER, cmd)
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
            logger.debug("Starting server on port: %d", SERVER_PORT)
            app.run(host=SERVER_IP, port=SERVER_PORT, debug=False, use_reloader=False)
            logger.debug("Server stopped")
        else:
            logger.error("You must pass an argument of either sonarr, radarr, sections or server...")
