from langchain_core.prompts import ChatPromptTemplate
rom app.responder.prompts import PROMPT_RESPONDER

prompt_process_file = ChatPromptTemplate([
        ("system", PROMPT_RESPONDER),
        ("human", "Contesto delle sottoquery: {}\n\nContesto delle query: {}\n\nDomanda: {question}"),
    ])

responder_chain = ()











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
                ids.append([best_match[1]])
        except KeyError:
            logging.warning("No found plate")

    if len(ids) == 0:
        return [50]

    return ids


for domanda in tqdm(domande[1:], desc="processing question"):
    response = executor_chain.invoke({"domanda": domanda})
    ids.append(response['id_plates'])


pandas.DataFrame()
results = []
for index, id in enumerate(ids):
   results.append({'row_id': index+1, 'result': ','.join([str(el) for el in id])})

file = pandas.DataFrame(results)

file.to_csv("responses.csv", index=False)
