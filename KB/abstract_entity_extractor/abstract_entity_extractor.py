import logging
from tqdm import tqdm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from KB.abstract_entity_extractor.prompts import PROMPT_PROCESS_FILE, PROMPT_SCHEMAS, PROMPT_CLEANER
from utils.wrapper import LLMWrapper


class SchemaElements(BaseModel):
    node_properties: list[str] = Field(description="Elenco delle proprietà dei nodi da aggiungere. Esempio: Chef {nome: STRING, date: STRING}")
    relationship_properties: list[str] = Field(description="Elenco delle proprietà delle relazioni da aggiungere. Esempio: POSSIEDE {Livello: INTEGER}")
    the_relationships: list[str] = Field(description="Elenco delle relazioni da aggiungere. Esempio: (:Chef)-[:POSSIEDE]->(:Licenza)")


def update_schema(input):
    response = input['response']
    schema = "Node properties:\n"
    for node_property in response.node_properties:
        schema += f"{node_property}\n"
    schema += "Relationship properties:\n"
    for relation_property in response.relationship_properties:
        schema += f"{relation_property}\n"
    schema += "The relationships:\n"
    for relation in response.the_relationships:
        schema += f"{relation}\n"

    return schema


### PROCESS FILE
wrapper = LLMWrapper()
wrapper.set_structured_output(SchemaElements)

prompt_process_file = ChatPromptTemplate([
        ("system", PROMPT_PROCESS_FILE),
        ("human", "Testo: {testo}"),
    ])

runnable_process_files = (
    RunnablePassthrough.assign(response=prompt_process_file | wrapper.llm)
    | update_schema
)

def process_files(input):
    logging.info("Process files started")

    files = input['files']

    schemas = []
    for file in tqdm(files, desc="File elaboration"):
        status = {'testo': file}
        schema = runnable_process_files.invoke(status)
        schemas.append(schema)

    logging.info(f"Process files completed. Schemas: {len(schemas)}")

    return schemas


### PROCESS SCHEMA
prompt_schema = ChatPromptTemplate([
        ("system", PROMPT_SCHEMAS),
        ("human", "Schemas: {schemas}"),
    ])

runnable_schema = (
    RunnablePassthrough.assign(response=prompt_schema | wrapper.llm)
    | update_schema
)

def process_schema(status):
    logging.info("Process schema started")

    schemas = []

    for i in range(0, len(status['schemas']), 5):
        blocks = status['schemas'][i:i + 5]
        schemas_content = ""
        for block in blocks:
            schemas_content += f"Schema:\n{block}\n\n"

        schema = runnable_schema.invoke({"schemas": schemas_content})
        schemas.append(schema)

    if len(schemas) == 1:
        logging.info(f"Process schema completed. Schema: {schemas[0]}")
        return schemas[0]
    else:
        return process_schema({'schemas': schemas})



## CLEANER
wrapper_cleaner = LLMWrapper(model_id="gpt-4o")
wrapper_cleaner.set_structured_output(SchemaElements)
prompt_cleaner = ChatPromptTemplate([
        ("system", PROMPT_CLEANER),
        ("human", "Clean this schema: {schema}"),
    ])

def log_clean_schema_started(status):
    logging.info("Cleaning schema started")

def log_clean_schema_completed(status):
    logging.info(f"Cleaning schema completed: {status}")

runnable_cleaner = (
    RunnablePassthrough(log_clean_schema_started)
    | RunnablePassthrough.assign(response=prompt_cleaner | wrapper_cleaner.llm)
    | update_schema
    | RunnablePassthrough(log_clean_schema_completed)
)


abstract_entity_extractor = (
    RunnablePassthrough.assign(
        schemas=process_files
    )
    | RunnablePassthrough.assign(
        schema=process_schema
    )
    | RunnablePassthrough.assign(
        schema=runnable_cleaner
    )
)
