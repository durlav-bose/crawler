import logging
import sys

def setup_logger(level=logging.INFO):
    """
    Sets up the logger with the specified logging level.
    Logs will be output to stdout.
    """
    logger = logging.getLogger('crawler_logger')
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger