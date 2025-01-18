import logging
from KB.preprocesser.preprocesser import preprocceser_chain
from log_config import log_config

log_config.setup_logging()
logger = logging.getLogger(__name__)