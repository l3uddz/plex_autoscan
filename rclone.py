import subprocess
import os
import logging

logger = logging.getLogger("RCLONE")

class RcloneDecrypter:
    def __init__(self,binary,crypt_mappings,config):
        self._binary = binary
        if self._binary == "" or not os.path.isfile(binary):
             self._binary = os.path.normpath(subprocess.check_output(["which", "rclone"]).decode().rstrip('\n'))
             logger.info("Rclone binary path located as {}".format(binary))
 
        self._config = config 
        self._crypt_mappings = crypt_mappings

    def decrypt_path(self, path):
        # Isolate root/file path and attempt to locate entry in mappings
        paths = path.split(os.sep,1)
        root_dir = paths[0]
        file_path = paths[1]
        logger.info("Root directory identified as {}".format(root_dir))

        if root_dir  in self._crypt_mappings:
            logger.info("Root directory {} has mapping defined in config as remote {}. Attempting to decrypt".format(root_dir,self._crypt_mappings[root_dir]))
            logger.info("Raw query is {}".format(" ".join([self._binary,"cryptdecode",self._crypt_mappings[root_dir],file_path])))
            try:
                 decoded = subprocess.check_output([self._binary,"--config",self._config,"cryptdecode",self._crypt_mappings[root_dir],file_path],stderr=subprocess.STDOUT).decode().rstrip('\n')
            except subprocess.CalledProcessError as e:
                 logger.error("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
                 return None
            
            decoded = decoded.split(' ',1)[1].lstrip()
            
            if "failed" in decoded.lower():
                 logger.error("Failed to decode path {}".format(file_path))
            else: 
                 logger.info("Deccoded path of {} is {}".format(file_path,decoded))
                 return [os.path.join(root_dir,decoded)]
        return None



