import os

from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain_neo4j import Neo4jVector
from langchain_openai import OpenAIEmbeddings

load_dotenv()

NEO4J_KEY=os.getenv('NEO4J_KEY')
NEO4J_URI=os.getenv('NEO4J_URI')
NEO4J_USERNAME=os.getenv('NEO4J_USERNAME')

def execute_embedding(status):
    existing_graph = Neo4jVector.from_existing_index(
        embedding=OpenAIEmbeddings(),
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_KEY,
        index_name="index",
        node_label="Element",
        text_node_property="nome"
    )


create_embeddings = (
    execute_embedding
)