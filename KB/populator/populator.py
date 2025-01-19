import json
import logging
import os

from dotenv import load_dotenv
from tqdm import tqdm
from KB.config import CACHE_FOLDER_PATH
from KB.populator.prompts import PROMPT
from utils.wrapper import initialize_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
import re
from langchain_core.runnables import Runnable, RunnablePassthrough

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_KEY = os.getenv("NEO4J_KEY")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")


class SchemaElements(BaseModel):
    queries: list[str] = Field(description="Elenco delle query Cypher da eseguire per popolare il DB. Esempio: CREATE (r:Ristorante {nome: 'Da Pippo'})")



# Funzione per eseguire le query Cypher
def execute_cypher_queries(cypher_queries):
    # Crea una connessione al database Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_KEY))

    # Separiamo la stringa in una lista di query (assumiamo che le query siano separate da ";")
    queries = cypher_queries.strip()

    with driver.session() as session:
        try:
            # Esegui la query
            session.run(queries)
        except Exception as e:
            logging.warning(f"Errore durante l'esecuzione della query: {queries}")
            logging.warning(f"Dettaglio errore: {e}")

        # Chiudi la connessione al driver
        driver.close()


def output_parser(result):
    content = result['response'].content
    content = re.sub(r'```$','',re.sub(r'^```\w*\n?', '',content))
    return content


def populate_db(state):
    logging.info("Populate db started")

    schema = state['schema']
    documents = state['files']

    # model = initialize_llm(model_id="meta-llama/llama-3-3-70b-instruct")
    model = initialize_llm(model_id="gpt-4o")
    model.with_structured_output(SchemaElements)
    prompt = ChatPromptTemplate([
        ("system", PROMPT),
        ("human", "Schema attuale: {schema}\n\Contenuto documento: {document}"),
    ])
    chain = (
        RunnablePassthrough.assign(response=prompt | model) | output_parser
    )

    queries = []
    for document in tqdm(documents, desc="Creating queries..."):
        queries.append(chain.invoke({"schema": schema, "document": document}))

    # save queries
    json_data = {item: "" for item in queries}
    file_name = os.path.join(CACHE_FOLDER_PATH, "queries.json")
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)

    for q in tqdm(queries, desc="Executing queries..."):
        execute_cypher_queries(q)

    query_element = "MATCH (n) SET n:Element"
    execute_cypher_queries(query_element)

    logging.info("Populate db completed")


populator_chain = (
    RunnablePassthrough(populate_db)
)