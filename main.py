import random
import json
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from verbecc import CompleteConjugator, LangCodeISO639_1 as Lang, Tenses
from deep_translator import GoogleTranslator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Staat alle origins toe
    allow_credentials=True,
    allow_methods=["*"],  # Staat alle methodes toe
    allow_headers=["*"],  # Staat alle headers toe
)

# 1. SETUP: Initialiseer de verbecc engine voor Italiaans
try:
    cg = CompleteConjugator(Lang.it)
except Exception as e:
    raise RuntimeError(f"Verbecc initialisatie mislukt: {e}")

# Initialiseer vertaler (optioneel, API werkt ook zonder)
try:
    vertaler = GoogleTranslator(source='it', target='nl')
except Exception:
    vertaler = None

# 2. DATA: Laad werkwoorden database
BASIS_MAP = os.path.dirname(os.path.abspath(__file__))
WERKWOORDEN_DB_BESTAND = os.path.join(BASIS_MAP, "verbs.json")

STANDAARD_WERKWOORDEN = {
    "ARE": ["parlare", "mangiare", "amare", "cantare", "lavorare", "studiare", "giocare", "camminare"],
    "ERE": ["credere", "vedere", "temere", "leggere", "scrivere", "vivere", "mettere", "prendere"],
    "IRE": ["dormire", "partire", "sentire", "capire", "finire", "preferire", "pulire", "aprire"],
    "ONREGELMATIG": ["essere", "avere", "andare", "fare", "venire", "dire", "potere", "volere", "dovere", "sapere", "stare", "uscire"]
}

def laad_werkwoorden_database():
    if os.path.exists(WERKWOORDEN_DB_BESTAND):
        try:
            with open(WERKWOORDEN_DB_BESTAND, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return STANDAARD_WERKWOORDEN

werkwoorden_database = laad_werkwoorden_database()

# 3. CONFIGURATIE: Koppeling van tijd strings naar Tenses enum
tijden_koppeling = {
    "presente": Tenses.it.Presente,
    "imperfetto": Tenses.it.Imperfetto,
    "futuro": Tenses.it.Futuro,
    "passato_remoto": Tenses.it.PassatoRemoto,
    "trapassato_remoto": Tenses.it.TrapassatoRemoto,
    "passato_prossimo": Tenses.it.PassatoProssimo,
    "trapassato_prossimo": Tenses.it.TrapassatoProssimo,
    "futuro_anteriore": Tenses.it.FuturoAnteriore,
} 

# Koppeling van index (0-6) naar persoon
personen = ["io", "tu", "lui", "lei", "noi", "voi", "loro"]

class QuizVerzoek(BaseModel):
    verb: str
    person: str
    tense: str
    answer: str

@app.get("/")
def lees_root():
    return FileResponse(os.path.join(BASIS_MAP, "index.html"))

@app.get("/quiz")
def haal_quiz_op(groups: str = "ARE,ONREGELMATIG", tenses: str = "presente"):
    groepen_lijst = groups.split(',')
    tijden_lijst = tenses.split(',')
    
    # A. Kies een willekeurige groep uit de voorkeuren van de gebruiker
    groep = random.choice(groepen_lijst)
    
    # B. Kies een willekeurig werkwoord uit die groep
    werkwoord = random.choice(werkwoorden_database[groep])
    
    # Kies een willekeurige tijd
    tijd_str = random.choice(tijden_lijst)
    gekozen_tijd_enum = tijden_koppeling.get(tijd_str)
    if not gekozen_tijd_enum:
        raise HTTPException(status_code=400, detail=f"Tijd '{tijd_str}' wordt niet ondersteund")
    
    # E. Kies een willekeurige persoon (index 0 t/m 6)
    persoon_index = random.randint(0, 6)
    persoon_label = personen[persoon_index]
    
    return {
        "verb": werkwoord,
        "person": persoon_label,
        "tense": tijd_str,
        "group": groep
    }

@app.post("/check")
def controleer_antwoord(request: QuizVerzoek):
    gekozen_tijd_enum = tijden_koppeling.get(request.tense)
    if not gekozen_tijd_enum:
        raise HTTPException(status_code=400, detail=f"Tijd '{request.tense}' wordt niet ondersteund")
    
    # Haal de vervoeging op
    vervoeging = cg.conjugate(request.verb).get_data()
    try:
        vervoegingen_lijst = vervoeging['moods']['indicativo'][gekozen_tijd_enum]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Tijd '{request.tense}' niet gevonden")
    
    # Vind de index van de persoon
    # Koppeling: io=0, tu=1, lui=2, lei=3, noi=4, voi=5, loro=6
    # Verbecc geeft 7 items terug: io, tu, lui, lei, noi, voi, loro
    persoon_koppeling = {
        "io": 0, "tu": 1, "lui": 2, "lei": 3, 
        "noi": 4, "voi": 5, "loro": 6
    }
    
    persoon_index = persoon_koppeling.get(request.person)
    if persoon_index is None:
        raise HTTPException(status_code=400, detail=f"Persoon '{request.person}' is niet geldig")
    
    # Haal de vervoegde vorm op van verbecc
    # verbecc geeft vormen terug zoals "io parlo" (eenvoudig) of "io ho parlato" (samengesteld)
    ruw_antwoord = vervoegingen_lijst[persoon_index]['c'][0]
    
    # Extraheer het werkwoorddeel zonder het voornaamwoord
    # Voor eenvoudige tijden: "io parlo" -> "parlo"
    # Voor samengestelde tijden: "io ho parlato" -> "ho parlato"
    delen = ruw_antwoord.split(' ', 1)  # Splits alleen bij de eerste spatie om voornaamwoord te scheiden
    if len(delen) > 1:
        alleen_werkwoord = delen[1]  # Alles na het voornaamwoord
        volledige_zin = ruw_antwoord
    else:
        alleen_werkwoord = ruw_antwoord
        volledige_zin = ruw_antwoord

    # Controleer antwoord (sta beide toe met en zonder voornaamwoord)
    gebruiker_antwoord = request.answer.strip().lower()
    
    correct = (gebruiker_antwoord == alleen_werkwoord.lower()) or (gebruiker_antwoord == volledige_zin.lower())
    
    return {
        "correct": correct,
        "correct_answer": alleen_werkwoord,  # Geef de vorm zonder voornaamwoord terug
        "your_answer": request.answer
    }

@app.get("/api/reference/{verb}")
def haal_volledige_vervoeging_op(verb: str):
    # Maak de invoer schoon
    doel_werkwoord = verb.lower().strip()

    try:
        # Directe vervoeging van het gevraagde werkwoord
        vervoeging = cg.conjugate(doel_werkwoord).get_data()
        
        # Zorg ervoor dat 'verb' een string is (infinitief)
        if isinstance(vervoeging.get('verb'), dict):
            vervoeging['verb'] = vervoeging['verb'].get('infinitive', doel_werkwoord)
            
        # Vertaal de infinitief naar het Nederlands
        if vertaler:
            try:
                vervoeging['translation'] = vertaler.translate(doel_werkwoord)
            except Exception:
                vervoeging['translation'] = "Vertaling niet beschikbaar"
        else:
            vervoeging['translation'] = "Vertaling niet beschikbaar"
            
        return vervoeging
    except Exception:
        raise HTTPException(status_code=404, detail="Werkwoord niet gevonden of vervoeging mislukt")

if __name__ == "__main__":
    poort = int(os.environ.get("PORT", 1000))
    uvicorn.run(app, host="0.0.0.0", port=poort)
