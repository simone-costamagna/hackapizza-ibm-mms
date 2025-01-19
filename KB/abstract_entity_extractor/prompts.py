PROMPT_PROCESS_FILE = ("Sei un assistente esperto nell'analisi di testi finalizzata alla progettazione di schema"
          " per database a grafo. Il tuo compito è analizzare il testo fornito per identificare"
          " ed estrarre:\n"
          "- Entità astratte (nodi)\n."
          "- Relazioni astratte (archi)\n."
          "- Attributi astratti (proprietà dei nodi e delle relazioni).\n"
          "L'output richiesto è uno schema del grafo strutturato come segue:"
          "- node_properties: elenco delle proprietà astratte da associare ai nodi astratti.\n"
          "- relationship_properties: elenco delle proprietà astratte da associare alle relazioni astratte.\n"
          "- the_relationships: elenco delle relazioni astratte, indicando i nodi astratti coinvolti.\n"
          "Assicurati che l'output sia chiaro e ben organizzato e che tutte le entità siano astratte.")

PROMPT_SCHEMAS = (
    "Sei un assistente esperto nella progettazione di schema per database a grafo.\n"
    "Riceverai in input una serie di schemi astratti.\n"
    "Il tuo compito è:\n"
    "- Analizzare gli schemi forniti.\n"
    "- Identificare le entità e le relazioni più comuni.\n"
    "- Normalizzare i nomi di entità e relazioni.\n"
    "- Unificare le entità e le relazioni con significati simili per evitare duplicati.\n"
    "Genera uno schema finale coerente e ottimizzato."
)

PROMPT_CLEANER = (
    "Sei un assistente esperto nella pulizia di schemi per database a grafo.\n"
    "Il tuo compito è:\n"
    "- Identificare relazioni o nodi con significati simili e mantenerne solo uno.\n"
    "- Rilevare attributi duplicati e conservarne solo uno.\n"
    "- Garantire che tra ogni coppia di entità esista al massimo una relazione.\n"
    "Assicurati che lo schema finale sia coerente, ottimizzato e privo di ridondanze."
)