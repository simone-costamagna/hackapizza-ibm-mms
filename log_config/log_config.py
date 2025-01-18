import logging


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            # logging.FileHandler("logs.log"),
            logging.StreamHandler()
        ]
    )

    # Suppress httpx logs
    logging.getLogger("httpx").setLevel(logging.WARNING)