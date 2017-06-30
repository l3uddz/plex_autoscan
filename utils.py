import logging
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
            logger.debug("'%s' is running, pid: %d. Checking again in 60 seconds...", process.name(), process.pid)
            time.sleep(60)
            running, process = is_process_running(process_name)
        return True
    except:
        logger.exception("Exception waiting for process: '%s'", process_name())
        return False
