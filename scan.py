#!/usr/bin/env python2.7
import json
import logging
import sys
from os import path
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


# Get parsed command line arguments
cmd_args = config.parse_args()

# Logging
logFormatter = logging.Formatter('%(asctime)24s - %(levelname)8s - %(name)9s [%(process)5d]: %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(config.get_setting(cmd_args, 'loglevel'))

# Console logger
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

# File logger
fileHandler = RotatingFileHandler(
    config.get_setting(cmd_args, 'logfile'),
    maxBytes=1024 * 1024 * 5,
    backupCount=5
)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

# Scan logger
logger = rootLogger.getChild("AUTOSCAN")

# Multiprocessing
scan_lock = Lock()

# Config
config = config.load(cmd_args)


############################################################
# FUNCS
############################################################


def start_scan(path, scan_for, scan_type):
    section = utils.get_plex_section(config, path)
    if section <= 0:
        return False

    scan_process = Process(target=plex.scan, args=(config, scan_lock, path, scan_for, section, scan_type))
    scan_process.start()
    return True


############################################################
# SERVER
############################################################

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route("/%s" % config['SERVER_PASS'], methods=['GET'])
def manual_scan():
    if not config['SERVER_ALLOW_MANUAL_SCAN']:
        return abort(401)
    page = '<html><body>' \
           '<form action="" method="post"> File to be scanned:<br>' \
           '<input type="text" name="filepath" value=""> ' \
           '<input type="hidden" name="eventType" value="Manual"> ' \
           '<br><br><input type="submit" value="Submit"></form> ' \
           '<p>Clicking submit will add this file to the scan backlog.</p></body></html>'
    return page, 200


@app.route("/%s" % config['SERVER_PASS'], methods=['POST'])
def client_pushed():
    if request.content_type == 'application/json':
        data = request.get_json(silent=True)
    else:
        data = request.form.to_dict()

    if not data:
        logger.error("Invalid scan request from: %r", request.remote_addr)
        abort(400)
    logger.debug("Client %r request dump:\n%s", request.remote_addr, json.dumps(data, indent=4, sort_keys=True))

    if ('eventType' in data and data['eventType'] == 'Test') or ('EventType' in data and data['EventType'] == 'Test'):
        logger.info("Client %r made a test request, event: '%s'", request.remote_addr, 'Test')
    elif 'eventType' in data and data['eventType'] == 'Manual':
        logger.info("Client %r made a manual scan request for: '%s'", request.remote_addr, data['filepath'])
        final_path = utils.map_pushed_path(config, data['filepath'])
        # ignore this request?
        ignore, ignore_match = utils.should_ignore(final_path, config)
        if ignore:
            logger.info("Ignored scan request for '%s' because '%s' was matched from SERVER_IGNORE_LIST", final_path,
                        ignore_match)
            return "Ignoring scan request because %s was matched from your SERVER_IGNORE_LIST" % ignore_match
        if start_scan(final_path, 'manual', 'Manual'):
            return "'%s' was added to scan backlog." % final_path
        else:
            return "Error adding '%s' to scan backlog." % data['filepath']

    elif 'Movie' in data:
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
        path = path.join(data['series']['path'], data['episodeFile']['relativePath'])
        logger.info("Client %r scan request for series: '%s', event: '%s'", request.remote_addr, path,
                    "Upgrade" if data['isUpgrade'] else data['eventType'])
        final_path = utils.map_pushed_path(config, path)
        start_scan(final_path, 'sonarr_dev', "Upgrade" if data['isUpgrade'] else data['eventType'])

    else:
        logger.error("Unknown scan request from: %r", request.remote_addr)
        abort(400)

    return "OK"


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    if cmd_args['cmd'] == 'sections':
        plex.show_sections(config)

    elif cmd_args['cmd'] == 'server':
        logger.info("Starting server: http://%s:%d/%s",
            config['SERVER_IP'],
            config['SERVER_PORT'],
            config['SERVER_PASS']
        )
        app.run(host=config['SERVER_IP'], port=config['SERVER_PORT'], debug=False, use_reloader=False)
        logger.info("Server stopped")

    else:
        logger.error("Unknown command...")
