import logging
import os
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
        final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)

    # invoke plex scanner
    with lock:
        logger.debug("Using:\n%s", final_cmd)
        os.system(final_cmd)
        logger.info("Finished")
        if config['PLEX_EMPTY_TRASH_UPGRADE'] and config['PLEX_TOKEN'] and scan_type == 'Upgrade':
            logger.info("Emptying trash in 10 seconds...")
            time.sleep(10)
            empty_trash(config, str(section))

    return


def show_sections(config):
    if os.name == 'nt':
        final_cmd = '""%s" --list"' % config['PLEX_SCANNER']
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] \
              + ';export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' \
              + config['PLEX_SUPPORT_DIR'] + ';' + config['PLEX_SCANNER'] + ' --list'
        final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
    os.system(final_cmd)


def empty_trash(config, section):
    for control in config['PLEX_EMPTY_TRASH_CONTROL_FILES']:
        if not os.path.exists(control):
            logger.info("Skipping emptying trash as control file does not exist: '%s'", control)
            return

    logger.info("Control file(s) exist, performing empty trash on section %s", section)
    try:
        resp = requests.put('%s/library/sections/%s/emptyTrash?X-Plex-Token=%s' % (
            config['PLEX_LOCAL_URL'], section, config['PLEX_TOKEN']), data=None)
        if resp.status_code == 200:
            logger.info("Trash cleared for section %s", section)
        else:
            logger.error("Unexpected response status_code for empty trash request: %d", resp.status_code)

    except Exception as ex:
        logger.exception("Exception while sending empty trash request")
    return
