import logging
import os
import sqlite3
import time

import db

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote

import requests
import utils

logger = logging.getLogger("PLEX")


def scan(config, lock, path, scan_for, section, scan_type, resleep_paths):
    scan_path = ""

    # sleep for delay
    while True:
        if config['SERVER_SCAN_DELAY']:
            logger.info("Scan request for '%s', sleeping for %d seconds...", path, config['SERVER_SCAN_DELAY'])
            time.sleep(config['SERVER_SCAN_DELAY'])
        else:
            logger.info("Scan request for '%s'", path)

        # check if root scan folder for
        if path in resleep_paths:
            logger.info("Another scan request occurred for folder of '%s', sleeping again!",
                        path)
            utils.remove_item_from_list(path, resleep_paths)
        else:
            break

    # check file exists
    if scan_for == 'radarr' or scan_for == 'sonarr_dev' or scan_for == 'manual':
        checks = 0
        check_path = utils.map_pushed_path_file_exists(config, path)
        while True:
            checks += 1
            if os.path.exists(check_path):
                logger.info("File '%s' exists on check %d of %d.", check_path, checks, config['SERVER_MAX_FILE_CHECKS'])
                scan_path = os.path.dirname(path).strip()
                break
            elif checks >= config['SERVER_MAX_FILE_CHECKS']:
                logger.warning("File '%s' exhausted all available checks, aborting scan request.", check_path)
                # remove item from database if sqlite is enabled
                if config['SERVER_USE_SQLITE']:
                    if db.remove_item(path):
                        logger.info("Removed '%s' from database", path)
                        time.sleep(1)
                    else:
                        logger.error("Failed removing '%s' from database", path)
                return
            else:
                logger.info("File '%s' did not exist on check %d of %d, checking again in 60 seconds.", check_path,
                            checks,
                            config['SERVER_MAX_FILE_CHECKS'])
                time.sleep(60)

    else:
        # old sonarr doesnt pass the sonarr_episodefile_path in webhook, so we cannot check until this is corrected.
        scan_path = path.strip()

    # build plex scanner command
    if os.name == 'nt':
        final_cmd = '""%s" --scan --refresh --section %s --directory "%s""' \
                    % (config['PLEX_SCANNER'], str(section), scan_path)
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] + ';'
        if not config['USE_DOCKER']:
            cmd += 'export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' + config['PLEX_SUPPORT_DIR'] + ';'
        cmd += config['PLEX_SCANNER'] + ' --scan --refresh --section ' + str(section) + ' --directory ' + cmd_quote(
            scan_path)

        if config['USE_DOCKER']:
            final_cmd = 'docker exec -u %s -i %s bash -c %s' % \
                        (cmd_quote(config['PLEX_USER']), cmd_quote(config['DOCKER_NAME']), cmd_quote(cmd))
        elif config['USE_SUDO']:
            final_cmd = 'sudo -u %s bash -c %s' % (config['PLEX_USER'], cmd_quote(cmd))
        else:
            final_cmd = cmd

    # invoke plex scanner
    priority = utils.get_priority(config, scan_path)
    logger.debug("Waiting for turn in the scan request backlog with priority: %d", priority)

    lock.acquire(priority)
    try:
        logger.info("Scan request is now being processed")
        # wait for existing scanners being ran by plex
        if config['PLEX_WAIT_FOR_EXTERNAL_SCANNERS']:
            scanner_name = os.path.basename(config['PLEX_SCANNER']).replace('\\', '')
            if not utils.wait_running_process(scanner_name):
                logger.warning(
                    "There was a problem waiting for existing '%s' process(s) to finish, aborting scan.", scanner_name)
                # remove item from database if sqlite is enabled
                if config['SERVER_USE_SQLITE']:
                    if db.remove_item(path):
                        logger.info("Removed '%s' from database", path)
                        time.sleep(1)
                    else:
                        logger.error("Failed removing '%s' from database", path)
                return
            else:
                logger.info("No '%s' processes were found.", scanner_name)

        # run external command if supplied
        if len(config['RUN_COMMAND_BEFORE_SCAN']) > 2:
            logger.info("Running external command: %r", config['RUN_COMMAND_BEFORE_SCAN'])
            utils.run_command(config['RUN_COMMAND_BEFORE_SCAN'])
            logger.info("Finished running external command")

        # begin scan
        logger.info("Starting Plex Scanner")
        logger.debug(final_cmd)
        utils.run_command(final_cmd.encode("utf-8"))
        logger.info("Finished scan!")

        # remove item from database if sqlite is enabled
        if config['SERVER_USE_SQLITE']:
            if db.remove_item(path):
                logger.info("Removed '%s' from database", path)
                time.sleep(1)
                logger.info("There is %d queued items remaining...", db.queued_count())
            else:
                logger.error("Failed removing '%s' from database", path)

        # empty trash if configured
        if config['PLEX_EMPTY_TRASH'] and config['PLEX_TOKEN'] and config['PLEX_EMPTY_TRASH_MAX_FILES']:
            logger.info("Checking deleted item count in 10 seconds...")
            time.sleep(10)

            # check deleted item count, don't proceed if more than this value
            deleted_items = get_deleted_count(config)
            if deleted_items > config['PLEX_EMPTY_TRASH_MAX_FILES']:
                logger.warning("There were %d deleted files, skipping emptying trash for section %s", deleted_items,
                               section)
            elif deleted_items == -1:
                logger.error("Could not determine deleted item count, aborting emptying trash")
            elif not config['PLEX_EMPTY_TRASH_ZERO_DELETED'] and not deleted_items and scan_type != 'Upgrade':
                logger.info("Skipping emptying trash as there were no deleted items")
            else:
                logger.info("Emptying trash to clear %d deleted items", deleted_items)
                empty_trash(config, str(section))

        # analyze movie/season
        if config['PLEX_ANALYZE_FILE'] and config['PLEX_TOKEN'] and config['PLEX_LOCAL_URL']:
            logger.debug("Sleeping 10 seconds before sending analyze request")
            time.sleep(10)
            analyze_item(config, path)
    except Exception:
        logger.exception("Unexpected exception occurred while processing: '%s'", scan_path)
    finally:
        lock.release()
    return


def show_sections(config):
    if os.name == 'nt':
        final_cmd = '""%s" --list"' % config['PLEX_SCANNER']
    else:
        cmd = 'export LD_LIBRARY_PATH=' + config['PLEX_LD_LIBRARY_PATH'] + ';'
        if not config['USE_DOCKER']:
            cmd += 'export PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=' + config['PLEX_SUPPORT_DIR'] + ';'
        cmd += config['PLEX_SCANNER'] + ' --list'

        if config['USE_DOCKER']:
            final_cmd = 'docker exec -u %s -it %s bash -c %s' % (
                cmd_quote(config['PLEX_USER']), cmd_quote(config['DOCKER_NAME']), cmd_quote(cmd))
        elif config['USE_SUDO']:
            final_cmd = 'sudo -u %s bash -c "%s"' % (config['PLEX_USER'], cmd)
        else:
            final_cmd = cmd
    logger.info("Using Plex Scanner")
    logger.debug(final_cmd)
    os.system(final_cmd)


def analyze_item(config, scan_path):
    if not os.path.exists(config['PLEX_DATABASE_PATH']):
        logger.info("Could not analyze '%s' because plex database could not be found?", scan_path)
        return
    # get files metadata_item_id
    metadata_item_id = get_file_metadata_id(config, scan_path)
    if not metadata_item_id:
        logger.info("Aborting analyze of '%s' because could not find a metadata_item_id for it", scan_path)
        return
    else:
        logger.info("Sending analyze request for library item: %d", metadata_item_id)

    # send analyze request to server
    for x in range(5):
        try:
            resp = requests.put("%s/library/metadata/%d/analyze?X-Plex-Token=%s" % (
                config['PLEX_LOCAL_URL'], metadata_item_id, config['PLEX_TOKEN']), timeout=600)
            if resp.status_code == 200:
                logger.info("Analyze request was completed successfully after %d/5 tries!", x + 1)
                break
            else:
                logger.error("Unexpected response status_code for analyze request: %d, %d/5 attempts...",
                             resp.status_code, x + 1)
                time.sleep(10)
        except Exception:
            logger.exception("Exception sending analyze request for library item %d, %d/5 attempts: ",
                             metadata_item_id, x + 1)
            time.sleep(10)
    return


def get_file_metadata_id(config, file_path):
    # query db to locate media_item_id
    result = None
    media_item_row = None

    try:
        conn = sqlite3.connect(config['PLEX_DATABASE_PATH'])
        c = conn.cursor()
        for x in range(5):
            media_item_row = c.execute("SELECT * FROM media_parts WHERE file=?", (file_path,)).fetchone()
            if media_item_row:
                logger.info("Found row in media_parts where file = '%s' after %d/5 tries!", file_path, x + 1)
                break
            else:
                logger.error("Could not locate record in media_parts where file = '%s', %d/5 attempts...",
                             file_path, x + 1)
                time.sleep(10)

        if not media_item_row:
            logger.error("Could not locate record in media_parts where file = '%s' after 5 tries...", file_path)
            conn.close()
            return None

        media_item_id = media_item_row[1]
        # query db to find metadata_item_id
        if int(media_item_id):
            metadata_item_id = c.execute("SELECT * FROM media_items WHERE id=?", (int(media_item_id),)).fetchone()[3]
            if int(metadata_item_id):
                # check for parent_id in metadata_items
                parent_id = c.execute("SELECT * FROM metadata_items WHERE id=?", (int(metadata_item_id),)).fetchone()[2]
                if parent_id:
                    result = int(parent_id)
                    logger.debug("Found parent_id for '%s': %d", file_path, result)
                else:
                    result = int(metadata_item_id)
                    logger.debug("Found metadata_item_id for '%s': %d", file_path, result)

        conn.close()
    except Exception as ex:
        logger.exception("Exception finding metadata_item_id for '%s': ", file_path)
    return result


def empty_trash(config, section):
    for control in config['PLEX_EMPTY_TRASH_CONTROL_FILES']:
        if not os.path.exists(control):
            logger.info("Skipping emptying trash as control file does not exist: '%s'", control)
            return

    if len(config['PLEX_EMPTY_TRASH_CONTROL_FILES']):
        logger.info("Control file(s) exist!")

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
    try:
        conn = sqlite3.connect(config['PLEX_DATABASE_PATH'])
        c = conn.cursor()
        deleted_metadata = c.execute('SELECT count(*) FROM metadata_items WHERE deleted_at IS NOT NULL').fetchone()[0]
        deleted_media_parts = c.execute('SELECT count(*) FROM media_parts WHERE deleted_at IS NOT NULL').fetchone()[0]
        conn.close()
        return int(deleted_metadata) + int(deleted_media_parts)
    except Exception as ex:
        logger.exception("Exception retrieving deleted item count from database: ")
        return -1
