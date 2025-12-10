import random
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from verbecc import CompleteConjugator, LangCodeISO639_1 as Lang, Tenses
from deep_translator import GoogleTranslator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. SETUP: Initialiseer de verbecc engine voor Frans
cg = CompleteConjugator(Lang.fr)
translator = GoogleTranslator(source='fr', target='nl')

# 2. DATA: Load verbs
VERB_DB_FILE = "verbs_fr.json"

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
        "ER": ["parler", "manger", "aimer", "chanter", "travailler", "étudier", "jouer", "marcher"],
        "IR": ["finir", "choisir", "dormir", "partir", "sentir", "réussir"],
        "RE": ["vendre", "attendre", "entendre", "répondre", "perdre"],
        "ONREGELMATIG": ["être", "avoir", "aller", "faire", "venir", "dire", "pouvoir", "vouloir", "devoir", "savoir", "prendre", "voir"]
    }

verb_database = load_verb_database()

# 3. CONFIGURATIE
# Mapping van tense strings naar Tenses enum (Frans)
tense_map = {
    "presente": Tenses.fr.Présent,
    "imperfetto": Tenses.fr.Imparfait,
    "futuro": Tenses.fr.FuturSimple,
    "passato_remoto": Tenses.fr.PasséSimple,
    "trapassato_remoto": Tenses.fr.PasséAntérieur,
    "passato_prossimo": Tenses.fr.PasséComposé,
    "trapassato_prossimo": Tenses.fr.PlusQueParfait,
    "futuro_anteriore": Tenses.fr.FuturAntérieur,
} 

# Mapping van index naar persoon
# 0: je, 1: tu, 2: il, 3: elle, 5: nous, 6: vous, 7: ils, 8: elles
# We gebruiken een subset voor de quiz
personen = ["je", "tu", "il", "elle", "nous", "vous", "ils", "elles"]

# Mapping voor check_answer
person_map = {
    "je": 0, "tu": 1, "il": 2, "elle": 3, 
    "nous": 5, "vous": 6, "ils": 7, "elles": 8,
    "on": 4
}

class QuizRequest(BaseModel):
    verb: str
    person: str
    tense: str
    answer: str

@app.get("/")
def read_root():
    return "French Backend Running"

@app.get("/quiz")
def get_quiz(groups: str = "ER,ONREGELMATIG", tenses: str = "presente"):
    groups_list = groups.split(',')
    tenses_list = tenses.split(',')
    
    # Filter groups that exist in our database
    valid_groups = [g for g in groups_list if g in verb_database]
    if not valid_groups:
        valid_groups = list(verb_database.keys())
        
    groep = random.choice(valid_groups)
    werkwoord = random.choice(verb_database[groep])
    
    tense_str = random.choice(tenses_list)
    chosen_tense = tense_map.get(tense_str)
    if not chosen_tense:
        # Fallback to present if tense not found
        chosen_tense = Tenses.fr.Présent
        tense_str = "presente"
    
    # Kies een willekeurige persoon uit onze lijst
    persoon_label = random.choice(personen)
    
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
    
    vervoeging = cg.conjugate(request.verb).get_data()
    try:
        tijden_lijst = vervoeging['moods']['indicatif'][chosen_tense]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Tense '{request.tense}' not found")
    
    persoon_index = person_map.get(request.person)
    if persoon_index is None:
        raise HTTPException(status_code=400, detail=f"Person '{request.person}' not valid")
    
    # verbecc returns e.g. "je parle"
    # Sometimes it might return multiple forms? No, usually list of dicts.
    # Let's check if index exists
    if persoon_index >= len(tijden_lijst):
         raise HTTPException(status_code=500, detail=f"Index {persoon_index} out of bounds for verb {request.verb}")

    raw_answer = tijden_lijst[persoon_index]['c'][0] # "je parle"
    
    # Handle "j'" case (e.g. "j'aime")
    # Split logic
    parts = raw_answer.split(' ')
    if len(parts) > 1:
        verb_only = parts[-1]
        full_phrase = raw_answer
    elif "'" in raw_answer: # j'aime
        verb_only = raw_answer.split("'")[-1]
        full_phrase = raw_answer
    else:
        verb_only = raw_answer
        full_phrase = raw_answer

    user_ans = request.answer.strip().lower()
    
    correct = (user_ans == verb_only.lower()) or (user_ans == full_phrase.lower())
    
    return {
        "correct": correct,
        "correct_answer": verb_only,
        "your_answer": request.answer
    }

@app.get("/api/reference/{verb}")
def get_full_conjugation(verb: str):
    target_verb = verb.lower().strip()
    try:
        conjugation = cg.conjugate(target_verb).get_data()
        if isinstance(conjugation.get('verb'), dict):
            conjugation['verb'] = conjugation['verb'].get('infinitive', target_verb)
            
        try:
            translation = translator.translate(target_verb)
            conjugation['translation'] = translation
        except Exception:
            conjugation['translation'] = "Vertaling niet beschikbaar"
            
        return conjugation
    except Exception:
        raise HTTPException(status_code=404, detail="Verb not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
