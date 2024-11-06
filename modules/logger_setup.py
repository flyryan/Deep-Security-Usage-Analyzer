import logging
import sys

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and symbols"""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(symbol)s %(message)s"

    FORMATS = {
        logging.DEBUG: (grey, "🔍"),
        logging.INFO: (grey, "ℹ️"),
        logging.WARNING: (yellow, "⚠️"),
        logging.ERROR: (red, "❌"),
        logging.CRITICAL: (bold_red, "🚨")
    }

    def format(self, record):
        color, symbol = self.FORMATS.get(record.levelno, (self.reset, "•"))
        record.symbol = f"{symbol}"
        record.msg = f"{color}{record.msg}{self.reset}"
        return logging.Formatter(self.format_str).format(record)

def setup_logging():
    """Configure logging for the application."""
    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    console_handler.setLevel(logging.INFO)  # Only show INFO and above in console

    # Create file handler with detailed formatting
    file_handler = logging.FileHandler('security_analysis.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)  # Log everything to file

    # Set up logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
