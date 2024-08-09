import logging.config

logging.config.fileConfig("logging_config.ini")
logger = logging.getLogger("my_module")