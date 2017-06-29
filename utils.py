import logging

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
