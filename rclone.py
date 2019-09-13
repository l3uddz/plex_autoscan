import subprocess
import os
import logging

logger = logging.getLogger("RCLONE")

class RcloneDecoder:
    def __init__(self, binary, crypt_mappings, config):
        self._binary = binary
        if self._binary == "" or not os.path.isfile(binary):
             self._binary = os.path.normpath(subprocess.check_output(["which", "rclone"]).decode().rstrip('\n'))
             logger.info("Rclone binary path located as '{}'".format(binary))

        self._config = config
        self._crypt_mappings = crypt_mappings

    def decode_path(self, path):
        for crypt_dir, mapped_remotes in self._crypt_mappings.items():
            # Isolate root/file path and attempt to locate entry in mappings
            file_path = path.replace(crypt_dir,'')
            logger.info("Encoded file Path identified as '{}'".format(file_path))
            if path.lower().startswith(crypt_dir.lower()):
                for mapped_remote in mapped_remotes:
                    logger.info("Crypt base directory identified as '{}'".format(crypt_dir))
                    logger.info("Crypt base directory '{}' has mapping defined in config as remote '{}'. Attempting to decode".format(crypt_dir, mapped_remote))
                    logger.debug("Raw query is '{}'".format(" ".join([self._binary, "--config", self._config, "cryptdecode", mapped_remote, file_path])))
                    try:
                        decoded = subprocess.check_output([self._binary, "--config", self._config, "cryptdecode", mapped_remote, file_path], stderr=subprocess.STDOUT).decode('utf-8').rstrip('\n')
                    except subprocess.CalledProcessError as e:
                        logger.error("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
                        return None

                    decoded = decoded.split(' ',1)[1].lstrip()

                    if "failed" in decoded.lower():
                        logger.error("Failed to decode path '{}'".format(file_path))
                    else:
                        logger.info("Decoded path of '{}' is '{}'".format(file_path, decoded))
                        return [os.path.join(crypt_dir, decoded)]
            else:
                logger.debug("Ignoring crypt decode for path '%s' because '%s' was not matched from CRYPT_MAPPINGS", path, crypt_dir)
        return None
