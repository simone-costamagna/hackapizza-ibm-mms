import os

from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

from utils.wrapper import LLMWrapper

load_dotenv()

NEO4J_URL = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_KEY = os.getenv("NEO4J_KEY")

wrapper = LLMWrapper(model_id="gpt-4o")


def query_graph(query: str, exclude_types: list = None):
    graph = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USERNAME, password=NEO4J_KEY)

    graph.refresh_schema()

    print(graph.schema)

    chain = GraphCypherQAChain.from_llm(
        cypher_llm=wrapper.llm,
        qa_llm=wrapper.llm,
        graph=graph,
        verbose=False,
        allow_dangerous_requests=True,
        return_intermediate_steps=True,
        # return_direct=True,
        # exclude_types=["Movie"],
        exclude_types=exclude_types if exclude_types else [],
        validate_cypher=True
    )

    result = chain.invoke({"query": query})
    print(f"Intermediate steps: {result['intermediate_steps']}")
    print(f"Final answer: {result['result']}")

    return result['result']


res = query_graph("Quali sono i piatti che includono le Chocobo Wings come ingrediente?")


print(res)