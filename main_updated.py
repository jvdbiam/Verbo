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
    """
    Load verb database. Supports both old and new format.
    
    Old format:
    {
      "ARE": [...],
      "ERE": [...],
      "IRE": [...],
      "ONREGELMATIG": [...]
    }
    
    New format (simplified):
    {
      "verbs": [
        {
          "infinitive": "andare",
          "group": "ARE",
          "irregular_tenses": ["presente", "futuro"]
        }
      ]
    }
    
    Returns a dict with:
    - format: "old" or "new"
    - data: the loaded data
    - verb_index: dict mapping verb -> verb_data (for new format)
    """
    if os.path.exists(VERB_DB_FILE):
        try:
            with open(VERB_DB_FILE, 'r', encoding='utf-8') as f:
                print(f"Loading verbs from {VERB_DB_FILE}...")
                data = json.load(f)
                
                # Detect format
                if "verbs" in data:
                    # New format
                    verb_index = {v["infinitive"]: v for v in data["verbs"]}
                    return {
                        "format": "new",
                        "data": data,
                        "verb_index": verb_index
                    }
                else:
                    # Old format
                    return {
                        "format": "old",
                        "data": data,
                        "verb_index": None
                    }
        except Exception as e:
            print(f"Error loading {VERB_DB_FILE}: {e}")
    
    print("Using default verb list (old format).")
    return {
        "format": "old",
        "data": {
            "ARE": ["parlare", "mangiare", "amare", "cantare", "lavorare", "studiare", "giocare", "camminare"],
            "ERE": ["credere", "vedere", "temere", "leggere", "scrivere", "vivere", "mettere", "prendere"],
            "IRE": ["dormire", "partire", "sentire", "capire", "finire", "preferire", "pulire", "aprire"],
            "ONREGELMATIG": ["essere", "avere", "andare", "fare", "venire", "dire", "potere", "volere", "dovere", "sapere", "stare", "uscire"]
        },
        "verb_index": None
    }

verb_database = load_verb_database()

def get_verbs_by_group_and_tense(group: str, tense: str = None) -> list:
    """
    Get verbs filtered by group and optionally by tense irregularity.
    
    Args:
        group: Verb group (ARE, ERE, IRE, REGULAR, IRREGULAR, or ONREGELMATIG)
        tense: Optional tense to filter irregular verbs for that specific tense
    
    Returns:
        List of verb infinitives
    """
    if verb_database["format"] == "old":
        # Old format: simple group lookup
        if group == "REGULAR":
            # Return all ARE, ERE, IRE verbs
            verbs = []
            for g in ["ARE", "ERE", "IRE"]:
                verbs.extend(verb_database["data"].get(g, []))
            return verbs
        elif group in ["IRREGULAR", "ONREGELMATIG"]:
            return verb_database["data"].get("ONREGELMATIG", [])
        else:
            return verb_database["data"].get(group, [])
    else:
        # New format: filter by group and tense
        verbs = []
        
        for verb_data in verb_database["data"]["verbs"]:
            # Check group match
            if group == "REGULAR":
                # Regular verbs: check if this tense is not irregular
                if tense:
                    if tense not in verb_data.get("irregular_tenses", []):
                        verbs.append(verb_data["infinitive"])
                else:
                    # No tense specified: include all verbs with no irregular tenses
                    if not verb_data.get("irregular_tenses", []):
                        verbs.append(verb_data["infinitive"])
            elif group in ["IRREGULAR", "ONREGELMATIG"]:
                # Irregular verbs: check if this tense is irregular
                if tense:
                    if tense in verb_data.get("irregular_tenses", []):
                        verbs.append(verb_data["infinitive"])
                else:
                    # No tense specified: include all verbs with any irregular tenses
                    if verb_data.get("irregular_tenses", []):
                        verbs.append(verb_data["infinitive"])
            else:
                # Specific group (ARE, ERE, IRE, OTHER)
                if verb_data["group"] == group:
                    verbs.append(verb_data["infinitive"])
        
        return verbs

def is_verb_irregular_for_tense(verb: str, tense: str) -> bool:
    """Check if a verb is irregular for a specific tense."""
    if verb_database["format"] == "old":
        # Old format: check if verb is in ONREGELMATIG list
        return verb in verb_database["data"].get("ONREGELMATIG", [])
    else:
        # New format: check irregular_tenses list
        verb_data = verb_database["verb_index"].get(verb)
        if verb_data:
            return tense in verb_data.get("irregular_tenses", [])
        return False

def get_all_verbs() -> list:
    """Get all verbs from the database."""
    if verb_database["format"] == "old":
        return [v for sublist in verb_database["data"].values() for v in sublist]
    else:
        return [v["infinitive"] for v in verb_database["data"]["verbs"]]

# Flattened list for reverse search
all_verbs = get_all_verbs()


# 3. CONFIGURATIE: De instellingen van de gebruiker (dit komt later uit je app interface)
# Opties: "ARE", "ERE", "IRE", "ONREGELMATIG", "REGULAR", "IRREGULAR" (of allemaal)
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
    """
    Get a random quiz question.
    
    Args:
        groups: Comma-separated list of verb groups (ARE, ERE, IRE, REGULAR, IRREGULAR, ONREGELMATIG)
        tenses: Comma-separated list of tenses
    
    Returns:
        Quiz question with verb, person, tense, and group
    """
    groups_list = groups.split(',')
    tenses_list = tenses.split(',')
    
    # Choose a random tense first (important for filtering by tense-specific irregularity)
    tense_str = random.choice(tenses_list)
    chosen_tense = tense_map.get(tense_str)
    if not chosen_tense:
        raise HTTPException(status_code=400, detail=f"Tense '{tense_str}' not supported")
    
    # A. Choose a random group from user preferences
    groep = random.choice(groups_list)
    
    # B. Get verbs for this group (filtered by tense if applicable)
    available_verbs = get_verbs_by_group_and_tense(groep, tense_str)
    
    if not available_verbs:
        raise HTTPException(status_code=404, detail=f"No verbs found for group '{groep}' and tense '{tense_str}'")
    
    # C. Choose a random verb
    werkwoord = random.choice(available_verbs)
    
    # D. Choose a random person (index 0 to 6)
    persoon_index = random.randint(0, 6)
    persoon_label = personen[persoon_index]
    
    # E. Check if this verb is irregular for this tense (for UI display)
    is_irregular = is_verb_irregular_for_tense(werkwoord, tense_str)
    
    return {
        "verb": werkwoord,
        "person": persoon_label,
        "tense": tense_str,
        "group": groep,
        "is_irregular": is_irregular
    }

@app.post("/check")
def check_answer(request: QuizRequest):
    verb = request.verb
    person = request.person
    tense_str = request.tense
    user_answer = request.answer.strip().lower()
    
    # Map tense string to Tenses enum
    chosen_tense = tense_map.get(tense_str)
    if not chosen_tense:
        raise HTTPException(status_code=400, detail=f"Tense '{tense_str}' not supported")
    
    # Get person index
    persoon_index = personen.index(person) if person in personen else 0
    
    try:
        # Conjugate the verb using Verbecc
        result = cg.conjugate_mood_tense(verb, mood="indicative", tense=chosen_tense)
        
        # Extract the correct form
        correct_answer = result[persoon_index].strip().lower() if persoon_index < len(result) else ""
        
        # Check if the user's answer is correct
        is_correct = user_answer == correct_answer
        
        # Translation
        try:
            if translator:
                translation = translator.translate(verb)
            else:
                translation = "Translation unavailable"
        except:
            translation = "Translation unavailable"
        
        return {
            "correct": is_correct,
            "correct_answer": correct_answer,
            "translation": translation
        }
    except Exception as e:
        logger.error(f"Error conjugating verb '{verb}': {e}")
        raise HTTPException(status_code=500, detail=f"Error conjugating verb: {str(e)}")

@app.get("/verb/{verb}")
def get_verb_info(verb: str):
    """Get information about a specific verb, including which tenses are irregular."""
    if verb not in all_verbs:
        raise HTTPException(status_code=404, detail=f"Verb '{verb}' not found")
    
    if verb_database["format"] == "new":
        verb_data = verb_database["verb_index"].get(verb)
        if verb_data:
            return {
                "infinitive": verb_data["infinitive"],
                "group": verb_data["group"],
                "irregular_tenses": verb_data.get("irregular_tenses", []),
                "format": "new"
            }
    
    # Old format
    is_irregular = verb in verb_database["data"].get("ONREGELMATIG", [])
    
    # Determine group
    group = "ONREGELMATIG" if is_irregular else None
    if not group:
        for g in ["ARE", "ERE", "IRE"]:
            if verb in verb_database["data"].get(g, []):
                group = g
                break
    
    return {
        "infinitive": verb,
        "group": group,
        "irregular": is_irregular,
        "format": "old"
    }

@app.get("/groups")
def get_groups():
    """Get available verb groups and their counts."""
    if verb_database["format"] == "old":
        return {
            group: len(verbs) 
            for group, verbs in verb_database["data"].items()
        }
    else:
        groups = {}
        for verb_data in verb_database["data"]["verbs"]:
            group = verb_data["group"]
            groups[group] = groups.get(group, 0) + 1
        return groups

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
