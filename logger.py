import logging.config

logging.config.fileConfig("logging_config_file.ini")
logger = logging.getLogger("root")
