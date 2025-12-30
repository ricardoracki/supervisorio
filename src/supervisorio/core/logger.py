import logging
from datetime import time
from logging.handlers import TimedRotatingFileHandler

from supervisorio.config.settings import LOG_PATH


def get_logger(name: str = "app", log_filename="app.log") -> logging.Logger:
    """
    Logger global e reutilizável.
    Seguro para Streamlit, CLI e serviços long-running.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    # ================== FORMATTERS ==================
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_formatter = logging.Formatter(
        f"[%(asctime)s][%(levelname)s] - %(message)s"
    )

    # ================== FILE HANDLER ==================
    file_handler = TimedRotatingFileHandler(
        filename=LOG_PATH
        / log_filename,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        utc=False,
        atTime=time(0, 0)
    )

    # Arquivos: app.log.2025-12-22
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(file_formatter)

    # ================== CONSOLE HANDLER ==================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    # ================== ADD HANDLERS ==================
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


if __name__ == '__main__':
    get_logger().error('Teste de error')
