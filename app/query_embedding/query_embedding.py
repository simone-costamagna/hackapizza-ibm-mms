import os
from difflib import SequenceMatcher

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_neo4j import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

from KB.abstract_entity_extractor.abstract_entity_extractor import SchemaElements
from app.query_embedding.prompts import PROMPT_ENTITY_RECOGNITION
from utils.wrapper import LLMWrapper

load_dotenv()

NEO4J_KEY=os.getenv('NEO4J_KEY')
NEO4J_URI=os.getenv('NEO4J_URI')
NEO4J_USERNAME=os.getenv('NEO4J_USERNAME')

retrieval_query = """
OPTIONAL MATCH (node)<-[*0..1]-(piatto:Piatto)
WITH node, score, collect(piatto) AS piatti
RETURN COALESCE(node.info, '') AS text, score,
  node {.*, vector: Null, info: Null, piatti: piatti} AS metadata
"""


existing_graph = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_KEY,
    index_name="index",
    node_label="Element",
    text_node_properties=["nome"],
    embedding_node_property="embedding",
    retrieval_query=retrieval_query
)

def execute_query_cypher(status):
    results = existing_graph.similarity_search(query=status['domanda'], k=4)

    nomi = []
    for result in results:
        metadata = result.metadata
        piatti = metadata['piatti']
        for piatto in piatti:
            nomi.append(piatto['nome'])
    return nomi


def extract_ids(status):
    data = status['json_mapping']
    ids = []
    for name in status['piatti']:
        try:
            ids.append(data[name])
        except Exception as e:
            best_match = None
            for key, value in data.items():
                if best_match is None:
                    best_match = [key, value, SequenceMatcher(None, key, name).ratio()]
                else:
                    d = SequenceMatcher(None, key, name).ratio()
                    if d > best_match[2]:
                        best_match = [key, value, d]
            ids.append(best_match[1])

    return ids


query_embedding = (
    RunnablePassthrough.assign(piatti=execute_query_cypher)
    | RunnablePassthrough.assign(ids=extract_ids)
)
