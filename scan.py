#!/usr/bin/env python2.7
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Lock

from flask import Flask
from flask import abort
from flask import request

import config
import plex
import utils

############################################################
# INIT
############################################################

# Logging
logFormatter = logging.Formatter('%(asctime)24s - %(levelname)8s - %(name)9s :: %(message)s')
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

logger = rootLogger.getChild("AUTOSCAN")
logger.setLevel(logging.DEBUG)

# Multiprocessing
scan_lock = Lock()

# Config
config = config.load()


############################################################
# FUNCS
############################################################

def start_scan(path, scan_for, scan_type):
    section = utils.get_plex_section(config, path)
    if section <= 0:
        return

    scan_process = Process(target=plex.scan, args=(config, scan_lock, path, scan_for, section, scan_type))
    scan_process.start()
    return


############################################################
# SERVER
############################################################

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route("/%s" % config['SERVER_PASS'], methods=['POST'])
def client_pushed():
    data = request.get_json(silent=True)
    if not data:
        logger.error("Invalid scan request from: %r", request.remote_addr)
        abort(400)
    logger.debug("Client %r request dump:\n%s", request.remote_addr, json.dumps(data, indent=4, sort_keys=True))
    if 'Movie' in data:
        logger.info("Client %r scan request for movie: '%s', event: '%s'", request.remote_addr,
                    data['Movie']['FilePath'], data['EventType'])
        final_path = utils.map_pushed_path(config, data['Movie']['FilePath'])
        start_scan(final_path, 'radarr', data['EventType'])
    elif 'Series' in data:
        logger.info("Client %r scan request for series: '%s', event: '%s'", request.remote_addr, data['Series']['Path'],
                    data['EventType'])
        final_path = utils.map_pushed_path(config, data['Series']['Path'])
        start_scan(final_path, 'sonarr', data['EventType'])
    elif 'series' and 'episodeFile' in data:
        # new sonarr webhook
        path = os.path.join(data['series']['path'], data['episodeFile']['relativePath'])
        logger.info("Client %r scan request for series: '%s', event: '%s'", request.remote_addr, path,
                    "Upgrade" if data['isUpgrade'] else data['eventType'])
        final_path = utils.map_pushed_path(config, path)
        start_scan(final_path, 'sonarr_dev', "Upgrade" if data['isUpgrade'] else data['eventType'])
    elif 'eventType' == 'Test' or 'EventType' == 'Test':
        logger.info("Client %r made a test request, event: '%s'", request.remote_addr, 'Test')
        return "OK"

    else:
        logger.error("Unknown scan request from: %r", request.remote_addr)
        abort(400)

    return "OK"


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        logger.error("You must pass an argument, sections or server...")
        sys.exit(0)
    else:
        if sys.argv[1].lower() == 'sections':
            plex.show_sections(config)
        elif sys.argv[1].lower() == 'server':
            logger.info("Starting server: http://%s:%d/%s", config['SERVER_IP'], config['SERVER_PORT'],
                        config['SERVER_PASS'])
            app.run(host=config['SERVER_IP'], port=config['SERVER_PORT'], debug=False, use_reloader=False)
            logger.info("Server stopped")
        else:
            logger.error("You must pass an argument of either sections or server...")
