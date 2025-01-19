import csv
import json
from difflib import SequenceMatcher
import pandas
from langchain_core.runnables import RunnableParallel
from tqdm import tqdm

from app.query_embedding.query_embedding import query_embedding
from app.query_executor.executor import executor_chain


def extract_id_plates(state):
    data = state['json_mapping']
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
            pass

    if len(ids) == 0:
        return [50]

    return list(set(ids))



map_chain = RunnableParallel(executor_chain=executor_chain)

def load_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        csv_content = []
        for row in reader:
            csv_content.append(", ".join(row))
        # text = "\n".join(csv_content).strip()
        return csv_content

domande = load_csv("data/domande.csv")
path = 'data/Misc/dish_mapping.json'

with open(path, "r", encoding="utf-8") as file:
    data = json.load(file)

ids = []
for domanda in tqdm(domande[1:], desc="processing question"):
    response = map_chain.invoke({"domanda": domanda, "json_mapping": data})
    id = extract_id_plates(response['executor_chain'])
    # id_ = response['query_embedding']['ids']
    # id.extend(id_)
    list(set(id))
    if len(id) == 0:
        ids.append([50])
    else:
        ids.append(id)

pandas.DataFrame()
results = []
for index, id in enumerate(ids):
   results.append({'row_id': index+1, 'result': ','.join([str(el) for el in id])})

file = pandas.DataFrame(results)
file['result'] = file['result'].astype(str)
file.to_csv("responses.csv", index=False)
