import operator
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_neo4j import Neo4jGraph
from langgraph.graph import END, StateGraph, START
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv('NEO4J_URI')
AUTH = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_KEY'))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")

neo4j_graph = Neo4jGraph(url=URI, username=os.getenv('NEO4J_USERNAME'), password=os.getenv('NEO4J_KEY'))


model = ChatOpenAI(model="gpt-4o")

step1_prompt = """Fase 1: Ho un task relativo a {input}. Scomponilo in sub-task."""

step2_prompt = """Fase 2: You are an expert at converting user questions into Neo4j Cypher queries.
For the given subtasks, convert them into Neo4j Cypher queries that can be executed on the database.
Based on the schema of the graph to answer.

Schema: {schema}

subtasks:
{subtasks}
"""


# Define data structures for AI outputs
class Subtasks(BaseModel):
    """Decompose a given question/query into sub-queries"""
    subtasks: list[str] = Field(..., description="List of subtasks derived from the input query")


class CypherQueries(BaseModel):
    """Convert subtasks into Neo4j Cypher queries"""
    queries: list[str] = Field(..., description="List of Neo4j Cypher queries derived from the subtasks")


# Define the overall state of the process
class OverallState(TypedDict):
    input: str
    subtasks: Annotated[list[str], operator.add]
    cypher_queries: Annotated[list[str], operator.add]


# Graph component functions

def decompose_query(state: OverallState):
    # Decompose the query into subtasks
    prompt = step1_prompt.format(input=state["input"])
    response = model.with_structured_output(Subtasks).invoke(prompt)

    return {"subtasks": response.subtasks}


def convert_to_cypher(state: OverallState):
    # Convert subtasks into Neo4j Cypher queries
    neo4j_graph.refresh_schema()
    print(graph.schema)

    prompt = step2_prompt.format(subtasks=state["subtasks"], schema=graph.schema)
    print(prompt)
    response = model.with_structured_output(CypherQueries).invoke(prompt)


    return {"cypher_queries": response.queries}


def execute_query(state: OverallState):
    responses = {}
    for query in state["cypher_queries"]:
        response = neo4j_graph.query(query)

        responses['query'] = response

    return responses



# Construct the graph
graph = StateGraph(OverallState)

# Add nodes to the graph
graph.add_node("decompose_query", decompose_query)
graph.add_node("convert_to_cypher", convert_to_cypher)
graph.add_node("execute_query", execute_query)

# Add edges to connect the nodes
graph.add_edge(START, "decompose_query")
graph.add_edge("decompose_query", "convert_to_cypher")
graph.add_edge("convert_to_cypher", "execute_query")
graph.add_edge("execute_query", END)
# Compile the graph
app = graph.compile(debug=False).with_types(input_type=OverallState)

res = app.invoke({'input': "Quali sono i piatti che includono le Chocobo Wings come ingrediente?"})

print(res)



# # Execute the graph
# for s in app.stream(
#     {
#         "input": "Quali piatti, nella nostra tradizione culinaria magica, richiedono l'uso delle Lacrime di Unicorno e sono preparati sia con la tecnica del Taglio Sinaptico Biomimetico che con l'Idro-Cristallizzazione Sonora Quantistica?",
#     }
# ):
#     print(s)