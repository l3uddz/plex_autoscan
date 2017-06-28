#!/usr/bin/env python2.7
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Lock

from flask import Flask
from flask import abort
from flask import request

import config

############################################################
# INIT
############################################################

# Logging
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

# Multiprocessing
scan_lock = Lock()

# Config
config = config.load()


############################################################
# FUNCS
############################################################

def start_scan(path, scan_for):
    section = get_plex_section(path)
    if section <= 0:
        return

    scan_process = Process(target=plex_scan, args=(scan_lock, path, scan_for, section, config['SERVER_SCAN_DELAY']))
    scan_process.start()
    return


def plex_scan(lock, path, scan_for, section, delay):
    scan_path = ""
    logger.info("Scanning '%s' in %d seconds", path, delay)
    if delay:
        time.sleep(delay)

    # check file exists
    if scan_for == 'radarr':
        checks = 0
        while True:
            checks += 1
            if os.path.exists(path):
                logger.debug("File '%s' exists on check %d of %d, proceeding with scan", path, checks,
                             config['SERVER_MAX_FILE_CHECKS'])
                scan_path = os.path.dirname(path)
                break
            elif checks >= config['SERVER_MAX_FILE_CHECKS']:
                logger.debug("File '%s' exhausted all available checks, aborting scan", path)
                return
            else:
                logger.debug("File '%s' did not exist on check %d of %d, checking again in 60 seconds", path, checks,
                             config['SERVER_MAX_FILE_CHECKS'])
                time.sleep(60)

    else:
        # sonarr doesnt pass the sonarr_episodefile_path in webhook, so we cannot check until this is corrected.
        scan_path = path

    # build plex scanner command
    if os.name == 'nt':
        final_cmd = '""%s" --scan --refresh --section %s --directory "%s""' \
                    % (config['PLEX_SCANNER'], str(section), scan_path)
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] \
              + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
              + config['PLEX_SUPPORT_DIR'] + ';' + config['PLEX_SCANNER'] + ' --scan --refresh --section ' \
              + str(section) + ' --directory \\"' + scan_path + '\\"'
        final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)

    with lock:
        logger.debug("Using:\n%s", final_cmd)
        os.system(final_cmd)
        logger.debug("Finished")
    return


def show_plex_sections():
    if os.name == 'nt':
        final_cmd = '""%s" --list"' % config['PLEX_SCANNER']
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] \
              + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
              + config['PLEX_SUPPORT_DIR'] + ';' + config['PLEX_SCANNER'] + ' --list'
        final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
    os.system(final_cmd)


def get_plex_section(path):
    for section, mappings in config['PLEX_SECTION_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping.lower() in path.lower():
                return section
    logger.debug("Unable to map '%s' to a section id....", path)
    return -1


def map_pushed_path(path):
    for mapped_path, mappings in config['SERVER_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping in path:
                logger.debug("Mapping '%s' to '%s'", mapping, mapped_path)
                return path.replace(mapping, mapped_path)
    return path


# plex config guess functions


############################################################
# SERVER
############################################################

app = Flask(__name__)


@app.route("/%s" % config['SERVER_PASS'], methods=['POST'])
def client_pushed():
    data = request.get_json(silent=True)
    if not data:
        logger.debug("Invalid scan request from: %r", request.remote_addr)
        abort(400)

    if 'Movie' in data:
        logger.debug("Client %r scan request for movie: '%s'", request.remote_addr, data['Movie']['FilePath'])
        final_path = map_pushed_path(data['Movie']['FilePath'])
        start_scan(final_path, 'radarr')
    elif 'Series' in data:
        logger.debug("Client %r scan request for series: '%s'", request.remote_addr, data['Series']['Path'])
        final_path = map_pushed_path(data['Series']['Path'])
        start_scan(final_path, 'sonarr')
    else:
        logger.debug("Unknown scan request from: %r", request.remote_addr)
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
            show_plex_sections()
        elif sys.argv[1].lower() == 'server':
            logger.debug("Starting server: http://%s:%d/%s", config['SERVER_IP'], config['SERVER_PORT'],
                         config['SERVER_PASS'])
            app.run(host=config['SERVER_IP'], port=config['SERVER_PORT'], debug=False, use_reloader=False)
            logger.debug("Server stopped")
        else:
            logger.error("You must pass an argument of either sections or server...")
