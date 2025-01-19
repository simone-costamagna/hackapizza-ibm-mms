import csv
import json
import logging
import os
import pandas
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_neo4j import Neo4jGraph
from pydantic import BaseModel, Field
from difflib import SequenceMatcher
from typing import List

from tqdm import tqdm

from app.QUERY_EXECUTOR.prompts import PROMPT_QUERY_CYPHER
from utils.wrapper import LLMWrapper

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_KEY = os.getenv('NEO4J_KEY')

neo4j_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_KEY)

prompt_cypher = ChatPromptTemplate([
        ("system", PROMPT_QUERY_CYPHER),
        ("human", "Generami tutte le possibili query cypher per rispondere alla domanda basandoti sullo schema del grafo.\n\nSchema del grafo: {schema}\n\nDomanda: {domanda}"),
])

class QueryCypher(BaseModel):
    queries_cypher: List[str] = Field(description="List of cypher queries to answer the question")


def extract_query(state):
    return state['response'].queries_cypher


wrapper = LLMWrapper(model_id="gpt-4o")
wrapper.set_structured_output(QueryCypher)

runnable_cypher = (
    RunnablePassthrough.assign(response=prompt_cypher | wrapper.llm)
    | RunnablePassthrough.assign(query_cypher=extract_query)
)


def get_query_cypher(state):
    question = state['domanda']

    response = runnable_cypher.invoke({"domanda": question, 'schema': neo4j_graph.schema})

    return response['query_cypher']


def execute_query(state):
    query_cypher = state['query_cypher']
    results = []
    for q in query_cypher:
        # print(neo4j_graph.schema)
        try:
            response = neo4j_graph.query(q)
        except Exception as e:
            return None
        results += response

    return results


def extract_id_plates(state):
    path = 'data/Misc/dish_mapping.json'

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    ids = []
    if state['context'] is None:
        return [50]

    for plate in state['context']:
        try:
            name = plate['p']['nome']

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
        except KeyError:
            logging.warning("No found plate")

    if len(ids) == 0:
        return [50]

    return list(set(ids))


executor_chain = (
    RunnablePassthrough.assign(query_cypher=get_query_cypher)
    | RunnablePassthrough.assign(context=execute_query)
    | RunnablePassthrough.assign(id_plates=extract_id_plates)
)

# executor_chain.invoke({"domanda": "Quali sono i piatti che includono le Chocobo Wings come ingrediente?"})



def load_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        csv_content = []
        for row in reader:
            csv_content.append(", ".join(row))
        # text = "\n".join(csv_content).strip()
        return csv_content

domande = load_csv("data/domande.csv")

ids = []



for domanda in tqdm(domande[1:], desc="processing question"):
    response = executor_chain.invoke({"domanda": domanda})
    ids.append(response['id_plates'])


pandas.DataFrame()
results = []
for index, id in enumerate(ids):
   results.append({'row_id': index+1, 'result': ','.join([str(el) for el in id])})

file = pandas.DataFrame(results)

file.to_csv("responses.csv", index=False)

