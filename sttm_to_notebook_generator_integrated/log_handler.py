import logging
import logging.handlers

import colorlog
from queue import Queue
from logging.handlers import QueueHandler, QueueListener
import getpass
from .log_session_id import SESSION_LOG_ID

username = getpass.getuser()

_listeners = {}  # Keep track of listeners per logger

    
def get_logger(name, log_file=None, level=logging.DEBUG, max_bytes=5_000_000, backup_count=5):
    """
    Creates a robust logger with console output (color), file logging with rotation, and async logging.

    Args:
        name (str): Logger name.
        log_file (str): File path for logging to file (optional).
        level (int): Logging level (default: DEBUG).
        max_bytes (int): Max size for log file before rotation.
        backup_count (int): Number of backup files to keep.

    Returns:
        logging.Logger: Configured logger instance.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs if root logger is configured elsewhere

    if logger.handlers:
        return logger

    # Formatter for file output
    file_formatter = logging.Formatter(f'%(asctime)s - <user : {username}> - <session ID : {SESSION_LOG_ID}> - %(levelname)s - %(name)s - %(message)s')

    # Colored formatter for console
    color_formatter = colorlog.ColoredFormatter(
        f'%(log_color)s%(asctime)s - <user : {username}> - <session ID : {SESSION_LOG_ID}> - %(levelname)s - %(name)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Queue for async logging
    log_queue = Queue()

    # Console Handler with color
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    # console_handler.setFormatter(color_formatter) # can be enabled for colorful output in console.
    console_handler.setFormatter(file_formatter)

    handlers = [console_handler]

    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Setup queue handler and listener for async logging
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    # Only start one listener per logger name
    if name not in _listeners:
        listener = QueueListener(log_queue, *handlers)
        listener.start()
        _listeners[name] = listener

    return logger
