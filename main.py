import random
import json
import os
import uvicorn
import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from verbecc import CompleteConjugator, LangCodeISO639_1 as Lang, Tenses
from deep_translator import GoogleTranslator
from uvicorn.config import LOGGING_CONFIG

# Configure logging to show up in Render logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configure Uvicorn logging
LOGGING_CONFIG["formatters"]["default"] = {
    "()": "uvicorn.logging.DefaultFormatter",
    "fmt": "%(asctime)s [%(levelname)s] %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
}

# Set up a custom logging function for Uvicorn
def configure_uvicorn_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.INFO)
    return logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 1. SETUP: Initialiseer de verbecc engine voor Italiaans
try:
    logger.info("Initializing Verbecc...")
    cg = CompleteConjugator(Lang.it)
    logger.info("Verbecc initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Verbecc: {e}")
    raise e

try:
    logger.info("Initializing GoogleTranslator...")
    translator = GoogleTranslator(source='it', target='nl')
    logger.info("GoogleTranslator initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize GoogleTranslator: {e}")
    # Don't raise here, maybe we can survive without translation
    translator = None

# 2. DATA: Load verbs from external JSON file if it exists, otherwise use default
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERB_DB_FILE = os.path.join(BASE_DIR, "verbs.json")

def load_verb_database():
    if os.path.exists(VERB_DB_FILE):
        try:
            with open(VERB_DB_FILE, 'r', encoding='utf-8') as f:
                print(f"Loading verbs from {VERB_DB_FILE}...")
                return json.load(f)
        except Exception as e:
            print(f"Error loading {VERB_DB_FILE}: {e}")
    
    print("Using default verb list.")
    return {
        "ARE": ["parlare", "mangiare", "amare", "cantare", "lavorare", "studiare", "giocare", "camminare"],
        "ERE": ["credere", "vedere", "temere", "leggere", "scrivere", "vivere", "mettere", "prendere"],
        "IRE": ["dormire", "partire", "sentire", "capire", "finire", "preferire", "pulire", "aprire"],
        "ONREGELMATIG": ["essere", "avere", "andare", "fare", "venire", "dire", "potere", "volere", "dovere", "sapere", "stare", "uscire"]
    }

verb_database = load_verb_database()

# Flattened list for reverse search
all_verbs = [v for sublist in verb_database.values() for v in sublist]


# 3. CONFIGURATIE: De instellingen van de gebruiker (dit komt later uit je app interface)
# Opties: "ARE", "ERE", "IRE", "ONREGELMATIG" (of allemaal)
gekozen_groepen = ["ARE", "ONREGELMATIG"] 

# Opties: "presente", "imperfetto", "futuro_semplice", "passato_remoto", etc.
gekozen_tijd = Tenses.it.Presente 

# Mapping van tense strings naar Tenses enum
tense_map = {
    "presente": Tenses.it.Presente,
    "imperfetto": Tenses.it.Imperfetto,
    "futuro": Tenses.it.Futuro,
    "passato_remoto": Tenses.it.PassatoRemoto,
    "trapassato_remoto": Tenses.it.TrapassatoRemoto,
    "passato_prossimo": Tenses.it.PassatoProssimo,
    "trapassato_prossimo": Tenses.it.TrapassatoProssimo,
    "futuro_anteriore": Tenses.it.FuturoAnteriore,
} 

# Mapping van index (0-6) naar persoon
personen = ["io", "tu", "lui", "lei", "noi", "voi", "loro"]

class QuizRequest(BaseModel):
    verb: str
    person: str
    tense: str
    answer: str

@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/quiz")
def get_quiz(groups: str = "ARE,ONREGELMATIG", tenses: str = "presente"):
    groups_list = groups.split(',')
    tenses_list = tenses.split(',')
    
    # A. Kies een willekeurige groep uit de voorkeuren van de gebruiker
    groep = random.choice(groups_list)
    
    # B. Kies een willekeurig werkwoord uit die groep
    werkwoord = random.choice(verb_database[groep])
    
    # Kies een willekeurige tense
    tense_str = random.choice(tenses_list)
    chosen_tense = tense_map.get(tense_str)
    if not chosen_tense:
        raise HTTPException(status_code=400, detail=f"Tense '{tense_str}' not supported")
    
    # E. Kies een willekeurige persoon (index 0 t/m 6)
    persoon_index = random.randint(0, 6)
    persoon_label = personen[persoon_index]
    
    return {
        "verb": werkwoord,
        "person": persoon_label,
        "tense": tense_str,
        "group": groep
    }

@app.post("/check")
def check_answer(request: QuizRequest):
    chosen_tense = tense_map.get(request.tense)
    if not chosen_tense:
        raise HTTPException(status_code=400, detail=f"Tense '{request.tense}' not supported")
    
    # Haal de vervoeging op
    vervoeging = cg.conjugate(request.verb).get_data()
    try:
        tijden_lijst = vervoeging['moods']['indicativo'][chosen_tense]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Tense '{request.tense}' not found")
    
    # Vind de index van de persoon
    # Mapping: io=0, tu=1, lui=2, lei=3, noi=4, voi=5, loro=6
    # Verbecc returns 7 items: io, tu, lui, lei, noi, voi, loro
    person_map = {
        "io": 0, "tu": 1, "lui": 2, "lei": 3, 
        "noi": 4, "voi": 5, "loro": 6
    }
    
    persoon_index = person_map.get(request.person)
    if persoon_index is None:
        raise HTTPException(status_code=400, detail=f"Person '{request.person}' not valid")
    
    # Get the conjugated form from verbecc
    # verbecc returns forms like "io parlo" (simple) or "io ho parlato" (compound)
    raw_answer = tijden_lijst[persoon_index]['c'][0]
    
    # Extract the verb part without the pronoun
    # For simple tenses: "io parlo" -> "parlo"
    # For compound tenses: "io ho parlato" -> "ho parlato"
    parts = raw_answer.split(' ', 1)  # Split only on the first space to separate pronoun
    if len(parts) > 1:
        verb_only = parts[1]  # Everything after the pronoun
        full_phrase = raw_answer
    else:
        verb_only = raw_answer
        full_phrase = raw_answer

    # Check answer (allow both with and without pronoun)
    user_ans = request.answer.strip().lower()
    
    correct = (user_ans == verb_only.lower()) or (user_ans == full_phrase.lower())
    
    return {
        "correct": correct,
        "correct_answer": verb_only,  # Return the form without pronoun
        "your_answer": request.answer
    }

@app.get("/api/reference/{verb}")
def get_full_conjugation(verb: str):
    # Clean the input
    target_verb = verb.lower().strip()

    try:
        # Direct conjugation of the requested verb
        conjugation = cg.conjugate(target_verb).get_data()
        
        # Ensure 'verb' is a string (infinitive)
        if isinstance(conjugation.get('verb'), dict):
            conjugation['verb'] = conjugation['verb'].get('infinitive', target_verb)
            
        # Translation Logic
        try:
            # Translate the infinitive to Dutch
            translation = translator.translate(target_verb)
            conjugation['translation'] = translation
        except Exception as e:
            print(f"Translation error: {e}")
            conjugation['translation'] = "Vertaling niet beschikbaar"
            
        return conjugation
    except Exception:
        raise HTTPException(status_code=404, detail="Verb not found or conjugation failed")

if __name__ == "__main__":
    uvicorn_logger = configure_uvicorn_logging()
    uvicorn_logger.info("Starting Uvicorn server...")

    port = int(os.environ.get("PORT", 1000))
    logger.info(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
