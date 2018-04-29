#!/usr/bin/env python2.7
import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask import abort
from flask import jsonify
from flask import request

# Get config
import config
import threads

############################################################
# INIT
############################################################

# Logging
logFormatter = logging.Formatter('%(asctime)24s - %(levelname)8s - %(name)9s [%(thread)5d]: %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

# Decrease modules logging
logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger("peewee").setLevel(logging.ERROR)

# Console logger, log to stdout instead of stderr
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

# Load initial config
conf = config.Config()

# File logger
fileHandler = RotatingFileHandler(
    conf.settings['logfile'],
    maxBytes=1024 * 1024 * 5,
    backupCount=5
)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

# Set configured log level
rootLogger.setLevel(conf.settings['loglevel'])
# Load config file
conf.load()

# Scan logger
logger = rootLogger.getChild("AUTOSCAN")

# Multiprocessing
thread = threads.Thread()
scan_lock = threads.PriorityLock()
resleep_paths = []

# local imports
import db
import plex
import utils


############################################################
# QUEUE PROCESSOR
############################################################


def queue_processor():
    logger.info("Starting queue processor in 10 seconds")
    try:
        time.sleep(10)
        logger.info("Queue processor started")
        db_scan_requests = db.get_all_items()
        items = 0
        for db_item in db_scan_requests:
            thread.start(plex.scan, args=[conf.configs, scan_lock, db_item['scan_path'], db_item['scan_for'],
                                          db_item['scan_section'],
                                          db_item['scan_type'], resleep_paths])
            items += 1
            time.sleep(2)
        logger.info("Restored %d scan requests from database", items)
    except Exception:
        logger.exception("Exception while processing scan requests from database: ")
    return


############################################################
# FUNCS
############################################################


def start_scan(path, scan_for, scan_type):
    section = utils.get_plex_section(conf.configs, path)
    if section <= 0:
        return False
    else:
        logger.debug("Using section id: %d for '%s'", section, path)

    if conf.configs['SERVER_USE_SQLITE']:
        db_exists, db_file = db.exists_file_root_path(path)
        if not db_exists and db.add_item(path, scan_for, section, scan_type):
            logger.info("Added '%s' to database, proceeding with scan", path)
        else:
            logger.info(
                "Already processing '%s' from same folder, aborting adding an extra scan request to the queue", db_file)
            resleep_paths.append(db_file)
            return False

    thread.start(plex.scan, args=[conf.configs, scan_lock, path, scan_for, section, scan_type, resleep_paths])
    return True


def start_queue_reloader():
    thread.start(queue_processor)
    return True


############################################################
# SERVER
############################################################

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route("/api/%s" % conf.configs['SERVER_PASS'], methods=['GET', 'POST'])
def api_call():
    data = {}
    try:
        if request.content_type == 'application/json':
            data = request.get_json(silent=True)
        elif request.method == 'POST':
            data = request.form.to_dict()
        else:
            data = request.args.to_dict()

        # verify cmd was supplied
        if 'cmd' not in data:
            logger.error("Unknown %s API call from %r", request.method, request.remote_addr)
            return jsonify({'error': 'No cmd parameter was supplied'})
        else:
            logger.info("Client %s API call from %r, type: %s", request.method, request.remote_addr, data['cmd'])

        # process cmds
        cmd = data['cmd'].lower()
        if cmd == 'queue_count':
            # queue count
            if not conf.configs['SERVER_USE_SQLITE']:
                # return error if SQLITE db is not enabled
                return jsonify({'error': 'SERVER_USE_SQLITE must be enabled'})
            return jsonify({'queue_count': db.get_queue_count()})

        else:
            # unknown cmd
            return jsonify({'error': 'Unknown cmd: %s' % cmd})

    except Exception:
        logger.exception("Exception parsing %s API call from %r: ", request.method, request.remote_addr)

    return jsonify({'error': 'Unexpected error occurred, check logs...'})


@app.route("/%s" % conf.configs['SERVER_PASS'], methods=['GET'])
def manual_scan():
    if not conf.configs['SERVER_ALLOW_MANUAL_SCAN']:
        return abort(401)
    page = '<html><body>' \
           '<form action="" method="post"> Path to be scanned:<br>' \
           '<input type="text" name="filepath" value=""> ' \
           '<input type="hidden" name="eventType" value="Manual"> ' \
           '<br><br><input type="submit" value="Submit"></form> ' \
           '<p>Clicking submit will add this path to the scan backlog.</p></body></html>'
    return page, 200


@app.route("/%s" % conf.configs['SERVER_PASS'], methods=['POST'])
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
        final_path = utils.map_pushed_path(conf.configs, data['filepath'])
        # ignore this request?
        ignore, ignore_match = utils.should_ignore(final_path, conf.configs)
        if ignore:
            logger.info("Ignored scan request for '%s' because '%s' was matched from SERVER_IGNORE_LIST", final_path,
                        ignore_match)
            return "Ignoring scan request because %s was matched from your SERVER_IGNORE_LIST" % ignore_match
        if start_scan(final_path, 'Manual', 'Manual'):
            return "'%s' was added to scan backlog." % final_path
        else:
            return "Error adding '%s' to scan backlog." % data['filepath']

    elif 'series' in data and 'eventType' in data and data['eventType'] == 'Rename' and 'path' in data['series']:
        # sonarr Rename webhook
        logger.info("Client %r scan request for series: '%s', event: '%s'", request.remote_addr, data['series']['path'],
                    "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])
        final_path = utils.map_pushed_path(conf.configs, data['series']['path'])
        start_scan(final_path, 'Sonarr',
                   "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])

    elif 'movie' in data and 'eventType' in data and data['eventType'] == 'Rename' and 'folderPath' in data['movie']:
        # radarr Rename webhook
        logger.info("Client %r scan request for movie: '%s', event: '%s'", request.remote_addr,
                    data['movie']['folderPath'],
                    "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])
        final_path = utils.map_pushed_path(conf.configs, data['movie']['folderPath'])
        start_scan(final_path, 'Radarr',
                   "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])

    elif 'movie' in data and 'movieFile' in data and 'folderPath' in data['movie'] and \
            'relativePath' in data['movieFile'] and 'eventType' in data:
        # radarr download/upgrade webhook
        path = os.path.join(data['movie']['folderPath'], data['movieFile']['relativePath'])
        logger.info("Client %r scan request for movie: '%s', event: '%s'", request.remote_addr, path,
                    "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])
        final_path = utils.map_pushed_path(conf.configs, path)
        start_scan(final_path, 'Radarr',
                   "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])

    elif 'series' in data and 'episodeFile' in data and 'eventType' in data:
        # sonarr download/upgrade webhook
        path = os.path.join(data['series']['path'], data['episodeFile']['relativePath'])
        logger.info("Client %r scan request for series: '%s', event: '%s'", request.remote_addr, path,
                    "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])
        final_path = utils.map_pushed_path(conf.configs, path)
        start_scan(final_path, 'Sonarr',
                   "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])

    elif 'artist' in data and 'trackFile' in data and 'eventType' in data:
        # lidarr download/upgrade webhook
        path = os.path.join(data['artist']['path'], data['trackFile']['relativePath'])
        logger.info("Client %r scan request for album track: '%s', event: '%s'", request.remote_addr, path,
                    "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])
        final_path = utils.map_pushed_path(conf.configs, path)
        start_scan(final_path, 'Lidarr',
                   "Upgrade" if ('isUpgrade' in data and data['isUpgrade']) else data['eventType'])

    else:
        logger.error("Unknown scan request from: %r", request.remote_addr)
        abort(400)

    return "OK"


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    logger.info("""
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
# Part of the Cloudbox project: https://cloudbox.rocks                  #
#########################################################################
# GNU General Public License v3.0                                       #
#########################################################################
""")
    if conf.args['cmd'] == 'sections':
        plex.show_sections(conf.configs)

    elif conf.args['cmd'] == 'server':
        if conf.configs['SERVER_USE_SQLITE']:
            start_queue_reloader()

        logger.info("Starting server: http://%s:%d/%s",
                    conf.configs['SERVER_IP'],
                    conf.configs['SERVER_PORT'],
                    conf.configs['SERVER_PASS']
                    )
        app.run(host=conf.configs['SERVER_IP'], port=conf.configs['SERVER_PORT'], debug=False, use_reloader=False)
        logger.info("Server stopped")
    else:
        logger.error("Unknown command...")
