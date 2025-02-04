# agent/container_logging.py

import logging
import os


def setup_dual_logger(agent_name: str,
                      external_logs_folder: str,
                      external_level=logging.DEBUG,
                      container_level=logging.INFO):
    """
    Sets up a logger to write to:
      1) An external file for full verbosity
      2) Console (which Docker can capture) with a lower verbosity
    """
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.DEBUG)  # capture all messages internally

    # 1) External File
    os.makedirs(external_logs_folder, exist_ok=True)
    ext_log_path = os.path.join(external_logs_folder, f"{agent_name}.log")
    file_handler = logging.FileHandler(ext_log_path)
    file_handler.setLevel(external_level)
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

    # 2) Console Handler (for container logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(container_level)
    console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
