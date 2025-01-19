import csv
import json
import logging
import operator
import os
from difflib import SequenceMatcher
from typing import TypedDict, Annotated

import pandas
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
from tqdm import tqdm

from KB.preprocesser.preprocesser import load_docx
from app.childreen_queries.prompts import PROMPT_SUBTASK, PROMPT_CONVERTER
from utils.wrapper import LLMWrapper

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_KEY = os.getenv('NEO4J_KEY')

neo4j_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_KEY)


class OverallState(TypedDict):
    question: str
    subtasks: Annotated[list[str], operator.add]
    cypher_queries: Annotated[list[str], operator.add]
    responses: Annotated[list[str], operator.add]
    schema: str


# SUBTASK
class Subtasks(BaseModel):
    """Decompose a given question/query into sub-queries"""
    subtasks: list[str] = Field(..., description="List of subtasks derived from the input query")

wrapper = LLMWrapper()
wrapper.set_structured_output(Subtasks)

prompt_subtask = ChatPromptTemplate([
    ("system", PROMPT_SUBTASK),
    ("human", "Schema del database: {schema}\nDomanda da scomporre: {question}"),
])

runnable_subtask = ( prompt_subtask | wrapper.llm)

def decompose_query(state):
    response = runnable_subtask.invoke(state)

    return {"subtasks": response.subtasks}


# CONVERT TO CYPHER
class CypherQuery(BaseModel):
    """Decompose a given question/query into sub-queries"""
    cypher_query: str = Field(..., description="Query cypher per risponder al subtask")

wrapper_cypher = LLMWrapper()
wrapper_cypher.set_structured_output(CypherQuery)

prompt_subtask = ChatPromptTemplate([
        ("system", PROMPT_CONVERTER),
        ("human", "Traduci questa domanda in query cypher: {subtask}\n\nBasati su questo schema {schema}"),
    ])

runnable_cypher = ( prompt_subtask | wrapper_cypher.llm )

def convert_to_cypher(state):
    query_cyphers = []
    for subtask in state["subtasks"]:
        response = runnable_cypher.invoke({"subtask": subtask, 'schema': neo4j_graph.schema})
        query_cyphers.append(response.cypher_query)

    return {'cypher_queries': query_cyphers}


# EXECUTE CYPHER
def execute_cypher(state):
    responses = []

    for cypher_query in state["cypher_queries"]:
        try:
            response = neo4j_graph.query(cypher_query)
        except Exception as e:
            response = None

        responses.append(response)

    return {'responses': list(zip(state['subtasks'], responses))}


graph = StateGraph(OverallState)
graph.add_node("decompose_query", decompose_query)
graph.add_node("convert_to_cypher", convert_to_cypher)
graph.add_node("execute_cypher", execute_cypher)

graph.add_edge(START, "decompose_query")
graph.add_edge("decompose_query", "convert_to_cypher")
graph.add_edge("convert_to_cypher", "execute_cypher")
graph.add_edge("execute_cypher", END)

children_queries_graph = graph.compile()

# def children_queries(state):
#     question = state['question']
#     res = children_queries_graph.invoke({
#             "question": question
#         })

#     return res.responses


def load_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        csv_content = []
        for row in reader:
            csv_content.append(", ".join(row))
        # text = "\n".join(csv_content).strip()
        return csv_content

domande = load_csv("/home/mattiasangermano/Developer/MattiaSangermano/hackpizza/hackapizza-ibm-mms/data/domande.csv")


def extract(response):
    path = '/home/mattiasangermano/Developer/MattiaSangermano/hackpizza/hackapizza-ibm-mms/data/Misc/dish_mapping.json'
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    ids = []
    for r in response:
        piatti = r[1]
        c_ids = []
        if piatti is not None:
            for plate in piatti:
                try:
                    name = plate['p']['nome']

                    try:
                        c_ids.append(data[name])
                    except Exception as e:
                        best_match = None
                        for key, value in data.items():
                            if best_match is None:
                                best_match = [key, value, SequenceMatcher(None, key, name).ratio()]
                            else:
                                d = SequenceMatcher(None, key, name).ratio()
                                if d > best_match[2]:
                                    best_match = [key, value, d]
                        c_ids.append(best_match[1])
                except KeyError:
                    logging.warning("No found plate")
        ids.append(c_ids)
    ids = [el for el in ids if el != []]
    if len(ids) == 0:
        return [50]
    result = set(ids[0])
    for lst in ids[1:]:
        result.intersection_update(lst)
    return list(set(result))



ids = []
for domanda in tqdm(domande[4:8], desc="processing question"):
    response = children_queries_graph.invoke({"question": domanda, "schema": neo4j_graph.schema})
    ids.append(extract(response['responses']))


pandas.DataFrame()
results = []
for index, id in enumerate(ids):
   results.append({'row_id': index+1, 'result': ','.join([str(el) for el in id])})

file = pandas.DataFrame(results)

file.to_csv("responses_II.csv", index=False)

