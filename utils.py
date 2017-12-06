import logging
import subprocess
import time

import psutil

logger = logging.getLogger("UTILS")


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


def map_pushed_path_file_exists(config, path):
    for mapped_path, mappings in config['SERVER_FILE_EXIST_PATH_MAPPINGS'].items():
        for mapping in mappings:
            if mapping in path:
                logger.debug("Mapping file check path '%s' to '%s'", mapping, mapped_path)
                return path.replace(mapping, mapped_path)
    return path


def is_process_running(process_name):
    try:
        for process in psutil.process_iter():
            if process.name().lower() == process_name.lower():
                return True, process

        return False, None

    except Exception:
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

    except Exception:
        logger.exception("Exception waiting for process: '%s'", process_name())

        return False


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        output = str(process.stdout.readline()).lstrip('b').replace('\\n', '').strip()
        if process.poll() is not None:
            break
        if output and len(output) >= 8:
            logger.info(output)

    rc = process.poll()
    return rc


def should_ignore(file_path, config):
    for item in config['SERVER_IGNORE_LIST']:
        if item.lower() in file_path.lower():
            return True, item

    return False, None


def remove_item_from_list(item, from_list):
    while item in from_list:
        from_list.pop(from_list.index(item))
    return


def get_priority(config, scan_path):
    try:
        for priority, paths in config['SEVER_SCAN_PRIORITIES'].items():
            for path in paths:
                if path.lower() in scan_path.lower():
                    logger.debug("Using priority %d for path '%s'", priority, scan_path)
                    return priority
        logger.debug("Using default priority 0 for path '%s'", scan_path)
    except Exception:
        logger.exception("Exception determining priority to use for '%s': ", scan_path)
    return 0
