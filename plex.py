import logging
import os
import sqlite3
import time

import requests

logger = logging.getLogger("PLEX")
logger.setLevel(logging.DEBUG)


def scan(config, lock, path, scan_for, section, scan_type):
    scan_path = ""

    # sleep for delay
    logger.info("Scanning '%s' in %d seconds", path, config['SERVER_SCAN_DELAY'])
    if config['SERVER_SCAN_DELAY']:
        time.sleep(config['SERVER_SCAN_DELAY'])

    # check file exists
    if scan_for == 'radarr':
        checks = 0
        while True:
            checks += 1
            if os.path.exists(path):
                logger.info("File '%s' exists on check %d of %d, proceeding with scan", path, checks,
                            config['SERVER_MAX_FILE_CHECKS'])
                scan_path = os.path.dirname(path)
                break
            elif checks >= config['SERVER_MAX_FILE_CHECKS']:
                logger.info("File '%s' exhausted all available checks, aborting scan", path)
                return
            else:
                logger.info("File '%s' did not exist on check %d of %d, checking again in 60 seconds", path, checks,
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
        if config['USE_SUDO']:
            final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
        else:
            final_cmd = cmd

    # invoke plex scanner
    with lock:
        logger.debug("Using:\n%s", final_cmd)
        os.system(final_cmd)
        logger.info("Finished scan")
        # empty trash if configured
        if config['PLEX_EMPTY_TRASH'] and config['PLEX_TOKEN'] and config['PLEX_EMPTY_TRASH_MAX_FILES']:
            logging.debug("Checking deleted item count in 5 seconds...")
            time.sleep(5)

            # check deleted item count, don't proceed if more than this value
            deleted_items = get_deleted_count(config)
            if deleted_items > config['PLEX_EMPTY_TRASH_MAX_FILES']:
                logger.warning("There were %d deleted files, skipping emptying trash for section %s", deleted_items,
                               section)
                return
            if not deleted_items:
                logger.info("Skipping emptying trash as there were no deleted items")
                return
            logger.info("Emptying trash to clear %d deleted items", deleted_items)
            empty_trash(config, str(section))

    return


def show_sections(config):
    if os.name == 'nt':
        final_cmd = '""%s" --list"' % config['PLEX_SCANNER']
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] \
              + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
              + config['PLEX_SUPPORT_DIR'] + ';' + config['PLEX_SCANNER'] + ' --list'
        if config['USE_SUDO']:
            final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
        else:
            final_cmd = cmd
    os.system(final_cmd)


def empty_trash(config, section):
    for control in config['PLEX_EMPTY_TRASH_CONTROL_FILES']:
        if not os.path.exists(control):
            logger.info("Skipping emptying trash as control file does not exist: '%s'", control)
            return

    if len(config['PLEX_EMPTY_TRASH_CONTROL_FILES']):
        logger.info("Control file(s) exist, performing empty trash on section %s", section)
    else:
        logger.info("Emptying trash for section %s", section)

    try:
        resp = requests.put('%s/library/sections/%s/emptyTrash?X-Plex-Token=%s' % (
            config['PLEX_LOCAL_URL'], section, config['PLEX_TOKEN']), data=None)
        if resp.status_code == 200:
            logger.info("Trash cleared for section %s", section)
        else:
            logger.error("Unexpected response status_code for empty trash request: %d", resp.status_code)

    except Exception as ex:
        logger.exception("Exception while sending empty trash request: ")
    return


def get_deleted_count(config):
    deleted = 0

    try:
        conn = sqlite3.connect(config['PLEX_DATABASE_PATH'])
        c = conn.cursor()
        deleted = c.execute('SELECT count(*) FROM metadata_items WHERE deleted_at IS NOT NULL').fetchone()[0]
        conn.close()
        return int(deleted)
    except Exception as ex:
        logger.exception("Exception retrieving deleted item count from database: ")
        return 0
