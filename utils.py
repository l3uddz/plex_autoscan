import logging
import os
import subprocess
import sys
import time

import psutil

logger = logging.getLogger("UTILS")
logger.setLevel(logging.DEBUG)


def get_plex_section(config, path):
    for section, mappings in config['PLEX_SECTION_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping.lower() in path.lower():
                return int(section)
    logger.error("Unable to map '%s' to a section id....", path)
    return -1


def map_pushed_path(config, path):
    for mapped_path, mappings in config['SERVER_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping in path:
                logger.debug("Mapping '%s' to '%s'", mapping, mapped_path)
                return path.replace(mapping, mapped_path)
    return path


def is_process_running(process_name):
    try:
        for process in psutil.process_iter():
            if process.name().lower() == process_name.lower():
                return True, process

        return False, None
    except:
        logger.exception("Exception checking for process: '%s': ", process_name)
        return False, None


def wait_running_process(process_name):
    try:
        running, process = is_process_running(process_name)
        while running and process:
            logger.debug("'%s' is running, pid: %d, cmdline: %r. Checking again in 60 seconds...", process.name(),
                         process.pid, process.cmdline())
            time.sleep(60)
            running, process = is_process_running(process_name)
        return True
    except:
        logger.exception("Exception waiting for process: '%s'", process_name())
        return False


def get_logfile_path():
    pos = 0
    log_path = os.path.join(os.path.dirname(sys.argv[0]), 'plex_autoscan.log')

    try:
        for item in sys.argv:
            if item == '--logfile':
                log_path = sys.argv[pos + 1]
                break
            pos += 1
    except:
        logger.exception("Exception retrieving supplied logfile: ")

    return log_path


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        output = str(process.stdout.readline()).lstrip('b').replace('\\n', '')
        if process.poll() is not None:
            break
        if output and len(output) >= 6:
            logger.info(output)

    rc = process.poll()
    return rc
