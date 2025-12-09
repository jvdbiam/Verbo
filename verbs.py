import random
from verbecc import CompleteConjugator,LangCodeISO639_1 as Lang,Tenses

# 1. SETUP: Initialiseer de verbecc engine voor Italiaans
cg = CompleteConjugator(Lang.it)

# 2. DATA: Je lijsten met werkwoorden (dit zou later uit een database kunnen komen)
# Je moet zelf definiëren welke werkwoorden 'regelmatig' of 'onregelmatig' zijn in je lijsten.
verb_database = {
    "ARE": ["parlare", "mangiare", "amare", "cantare"],
    "ERE": ["credere", "vedere", "temere"],
    "IRE": ["dormire", "partire", "sentire"],
    "ONREGELMATIG": ["essere", "avere", "andare", "fare", "venire"]
}

# 3. CONFIGURATIE: De instellingen van de gebruiker (dit komt later uit je app interface)
# Opties: "ARE", "ERE", "IRE", "ONREGELMATIG" (of allemaal)
gekozen_groepen = ["ARE", "ONREGELMATIG"] 

# Opties: "presente", "imperfetto", "futuro_semplice", "passato_remoto", etc.

gekozen_tijd = Tenses.it.Presente 

# Mapping van index (0-6) naar persoon
personen = ["io", "tu", "lui", "lei", "noi", "voi", "loro"]

def generate_quiz_question():
    # A. Kies een willekeurige groep uit de voorkeuren van de gebruiker
    groep = random.choice(gekozen_groepen)
    
    # B. Kies een willekeurig werkwoord uit die groep
    werkwoord = random.choice(verb_database[groep])
    
    # C. Haal de vervoeging op via de API/Library
    vervoeging = cg.conjugate(werkwoord).get_data()
    
    # D. Navigeer door de data naar de juiste tijd (Indicativo is de standaard 'Wijs')
    # Let op: verbecc data structuur is: ['moods']['indicativo'][tijd]
    try:
        tijden_lijst = vervoeging['moods']['indicativo'][gekozen_tijd]
    except KeyError:
        print(f"Fout: De tijd '{gekozen_tijd}' bestaat niet of is geen indicativo.")
        return

    # E. Kies een willekeurige persoon (index 0 t/m 6)
    persoon_index = random.randint(0, 6)
    persoon_label = personen[persoon_index]
    # Haal de tekst op uit het object (bijv. "io parlo")
    juiste_antwoord = tijden_lijst[persoon_index]['c'][0]

    # --- DE QUIZ INTERFACE (Simulatie) ---
    print("\n" + "="*40)
    print(f"OEFENING: {gekozen_tijd.replace('_', ' ').upper()}")
    print(f"Werkwoord: {werkwoord.upper()} ({groep})")
    print(f"Persoon:   {persoon_label}")
    print("="*40)

    # F. De gebruiker vult het antwoord in
    user_antwoord = input("Jouw antwoord: ").strip().lower()

    # G. Check het antwoord
    if user_antwoord == juiste_antwoord:
        print(f"✅ Correct! ({juiste_antwoord})")
    else:
        print(f"❌ Helaas. Het juiste antwoord was: '{juiste_antwoord}'")

# Draai de functie om te testen
if __name__ == "__main__":
    while True:
        generate_quiz_question()
        verder = input("\nNog eentje? (j/n): ")
        if verder.lower() != 'j':
            break