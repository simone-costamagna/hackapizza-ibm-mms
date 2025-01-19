import logging
from KB.abstract_entity_extractor.abstract_entity_extractor import abstract_entity_extractor
from KB.create_embedding import create_embedding
from KB.populator.populator import populator_chain
from KB.preprocesser.preprocesser import preprocceser_chain
from log_config import log_config

log_config.setup_logging()
logger = logging.getLogger(__name__)

knowledge_base_chain = (
    preprocceser_chain
    # | abstract_entity_extractor
    | populator_chain
    # | create_embedding
)

knowledge_base_chain.invoke({})