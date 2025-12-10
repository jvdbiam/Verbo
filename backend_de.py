import random
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deep_translator import GoogleTranslator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = GoogleTranslator(source='de', target='nl')

# --- Simple German Conjugator ---

class SimpleGermanConjugator:
    def __init__(self):
        self.irregulars = {
            "sein": {
                "present": ["bin", "bist", "ist", "sind", "seid", "sind"],
                "imperfect": ["war", "warst", "war", "waren", "wart", "waren"],
                "perfect_aux": "sein",
                "participle": "gewesen"
            },
            "haben": {
                "present": ["habe", "hast", "hat", "haben", "habt", "haben"],
                "imperfect": ["hatte", "hattest", "hatte", "hatten", "hattet", "hatten"],
                "perfect_aux": "haben",
                "participle": "gehabt"
            },
            "werden": {
                "present": ["werde", "wirst", "wird", "werden", "werdet", "werden"],
                "imperfect": ["wurde", "wurdest", "wurde", "wurden", "wurdet", "wurden"],
                "perfect_aux": "sein",
                "participle": "geworden"
            },
            # Add more irregulars as needed
             "können": {
                "present": ["kann", "kannst", "kann", "können", "könnt", "können"],
                "imperfect": ["konnte", "konntest", "konnte", "konnten", "konntet", "konnten"],
                "perfect_aux": "haben",
                "participle": "gekonnt"
            },
             "müssen": {
                "present": ["muss", "musst", "muss", "müssen", "müsst", "müssen"],
                "imperfect": ["musste", "musstest", "musste", "mussten", "musstet", "mussten"],
                "perfect_aux": "haben",
                "participle": "gemusst"
            },
             "wollen": {
                "present": ["will", "willst", "will", "wollen", "wollt", "wollen"],
                "imperfect": ["wollte", "wolltest", "wollte", "wollten", "wolltet", "wollten"],
                "perfect_aux": "haben",
                "participle": "gewollt"
            },
             "wissen": {
                "present": ["weiß", "weißt", "weiß", "wissen", "wisst", "wissen"],
                "imperfect": ["wusste", "wusstest", "wusste", "wussten", "wusstet", "wussten"],
                "perfect_aux": "haben",
                "participle": "gewusst"
            }
        }

    def get_stem(self, verb):
        if verb.endswith("en"):
            return verb[:-2]
        elif verb.endswith("n"):
            return verb[:-1]
        return verb

    def conjugate(self, verb, tense):
        verb = verb.lower().strip()
        
        # 1. Check Irregular
        if verb in self.irregulars:
            data = self.irregulars[verb]
            if tense == "present":
                return data["present"]
            elif tense == "imperfect":
                return data["imperfect"]
            elif tense == "perfect":
                aux = self.conjugate(data["perfect_aux"], "present")
                participle = data["participle"]
                return [f"{a} {participle}" for a in aux]
            elif tense == "future":
                werden = self.irregulars["werden"]["present"]
                return [f"{w} {verb}" for w in werden]
        
        # 2. Regular Logic
        stem = self.get_stem(verb)
        
        # Handle stem endings for e-insertion (d, t)
        needs_e = stem.endswith(('d', 't')) or (stem.endswith(('m', 'n')) and not stem.endswith(('rm', 'rn', 'lm', 'ln'))) # Simplified
        
        # Handle s-sound endings (s, ss, ß, z, x) for 'du'
        s_sound = stem.endswith(('s', 'ss', 'ß', 'z', 'x'))

        if tense == "present":
            # ich -e, du -st, er -t, wir -en, ihr -t, sie -en
            e1 = "e"
            e2 = "est" if needs_e else ("t" if s_sound else "st")
            e3 = "et" if needs_e else "t"
            e4 = "en"
            e5 = "et" if needs_e else "t"
            e6 = "en"
            
            return [
                stem + e1,
                stem + e2,
                stem + e3,
                stem + e4,
                stem + e5,
                stem + e6
            ]
            
        elif tense == "imperfect":
            # Regular: stem + te + endings
            # ich -te, du -test, er -te, wir -ten, ihr -tet, sie -ten
            # If needs_e: -ete
            suffix = "ete" if needs_e else "te"
            
            return [
                stem + suffix,
                stem + suffix + "st",
                stem + suffix,
                stem + suffix + "n",
                stem + suffix + "t",
                stem + suffix + "n"
            ]
            
        elif tense == "perfect":
            # haben + ge-stem-t
            # Simplified participle: ge + stem + t (if needs_e: et)
            # Note: verbs ending in -ieren don't take ge-
            if verb.endswith("ieren"):
                participle = stem + ("et" if needs_e else "t")
            else:
                participle = "ge" + stem + ("et" if needs_e else "t")
            
            aux = self.conjugate("haben", "present") # Most regular verbs take haben
            return [f"{a} {participle}" for a in aux]
            
        elif tense == "future":
            werden = self.irregulars["werden"]["present"]
            return [f"{w} {verb}" for w in werden]
            
        return []

cg = SimpleGermanConjugator()

# 2. DATA
VERB_DB_FILE = "verbs_de.json"

def load_verb_database():
    if os.path.exists(VERB_DB_FILE):
        try:
            with open(VERB_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {
        "REGELMATIG": ["machen", "sagen", "hören", "kaufen", "lernen", "spielen", "arbeiten", "reden", "wohnen", "fragen"],
        "ONREGELMATIG": ["sein", "haben", "werden", "können", "müssen", "wollen", "wissen"]
    }

verb_database = load_verb_database()

# 3. CONFIGURATIE
tense_map = {
    "presente": "present",
    "imperfetto": "imperfect", # Präteritum
    "passato_prossimo": "perfect", # Perfekt
    "futuro": "future" # Futur I
} 

personen = ["ich", "du", "er/sie/es", "wir", "ihr", "sie/Sie"]
person_map = {
    "ich": 0, "du": 1, "er": 2, "sie": 2, "es": 2, "er/sie/es": 2,
    "wir": 3, "ihr": 4, "sie/Sie": 5, "Sie": 5
}

class QuizRequest(BaseModel):
    verb: str
    person: str
    tense: str
    answer: str

@app.get("/")
def read_root():
    return "German Backend Running"

@app.get("/quiz")
def get_quiz(groups: str = "REGELMATIG,ONREGELMATIG", tenses: str = "presente"):
    groups_list = groups.split(',')
    tenses_list = tenses.split(',')
    
    valid_groups = [g for g in groups_list if g in verb_database]
    if not valid_groups:
        valid_groups = list(verb_database.keys())
        
    groep = random.choice(valid_groups)
    werkwoord = random.choice(verb_database[groep])
    
    tense_str = random.choice(tenses_list)
    chosen_tense = tense_map.get(tense_str)
    if not chosen_tense:
        chosen_tense = "present"
        tense_str = "presente"
    
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
    
    forms = cg.conjugate(request.verb, chosen_tense)
    if not forms:
        raise HTTPException(status_code=400, detail="Conjugation failed")
        
    persoon_index = person_map.get(request.person)
    if persoon_index is None:
        # Try to match partial
        if "er" in request.person:
            persoon_index = 2
        elif "sie" in request.person and "Sie" in request.person:
            persoon_index = 5
        else:
            raise HTTPException(status_code=400, detail=f"Person '{request.person}' not valid")
    
    correct_answer = forms[persoon_index]
    
    # Handle "ich mache" vs "mache"
    parts = correct_answer.split(' ')
    if len(parts) > 1 and chosen_tense not in ["perfect", "future"]:
        # Usually simple tenses don't have spaces unless I added pronoun?
        # My conjugator returns just the verb form for simple tenses (e.g. "mache")
        # But for perfect/future it returns "habe gemacht"
        pass
    
    # My conjugator returns just the verb form for simple tenses.
    # But the user might type "ich mache".
    # So I should check both.
    
    user_ans = request.answer.strip().lower()
    
    # Construct full phrase for comparison
    pronoun = request.person.split('/')[0] # simple guess
    full_phrase = f"{pronoun} {correct_answer}"
    
    is_correct = (user_ans == correct_answer.lower()) or (user_ans == full_phrase.lower())
    
    return {
        "correct": is_correct,
        "correct_answer": correct_answer,
        "your_answer": request.answer
    }

@app.get("/api/reference/{verb}")
def get_full_conjugation(verb: str):
    target_verb = verb.lower().strip()
    
    # Build a structure similar to verbecc
    moods = {
        "indikativ": {
            "present": cg.conjugate(target_verb, "present"),
            "imperfect": cg.conjugate(target_verb, "imperfect"),
            "perfect": cg.conjugate(target_verb, "perfect"),
            "future": cg.conjugate(target_verb, "future")
        }
    }
    
    # Format for frontend: needs 'c' list
    formatted_moods = {}
    for mood_name, tenses in moods.items():
        formatted_moods[mood_name] = {}
        for tense_name, forms in tenses.items():
            formatted_moods[mood_name][tense_name] = [{"c": [f]} for f in forms]

    response = {
        "verb": target_verb,
        "moods": formatted_moods
    }
    
    try:
        translation = translator.translate(target_verb)
        response['translation'] = translation
    except Exception:
        response['translation'] = "Vertaling niet beschikbaar"
        
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
