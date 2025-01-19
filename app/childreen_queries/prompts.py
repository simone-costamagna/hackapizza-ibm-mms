PROMPT_SUBTASK=("Sei un assistente esperto nell'analisi di domande. Il tuo compito è prendere in input una domanda e scomporla in una lista di"
                " subtask semplici che facilitino la risoluzione del problema.")

PROMPT_CONVERTER = (
    "Genera query Cypher per interrogare un database a grafi di Neo4j seguendo la definizione dello schema fornito.\n"
    "Linee guida:\n"
    "- Usa esclusivamente i tipi di relazioni e le proprietà specificate nello schema.\n"
    "- Evita di includere tipi di relazioni o proprietà non definiti."
    "Voglio che ritorni l'entità intera chiamata 'p'."
)