import json
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw_verbs"
OUTPUT_FILE = BASE_DIR / "verbs.json"

def classify_verb(verb):
    """Classifies a verb into ARE, ERE, IRE, or ONREGELMATIG."""
    verb = verb.lower().strip()
    
    # List of known irregular verbs (you can expand this)
    irregular_verbs = [
        "essere", "avere", "andare", "fare", "venire", "dire", "potere", 
        "volere", "dovere", "sapere", "stare", "uscire", "dare", "bere"
    ]
    
    if verb in irregular_verbs:
        return "ONREGELMATIG"
    elif verb.endswith("are"):
        return "ARE"
    elif verb.endswith("ere"):
        return "ERE"
    elif verb.endswith("ire"):
        return "IRE"
    else:
        return "ONREGELMATIG" # Fallback for verbs like 'porre', 'trarre'

def import_verbs():
    all_verbs = set()
    
    # 1. Iterate over all JSON files in the raw_data directory
    if not RAW_DATA_DIR.exists():
        print(f"Directory {RAW_DATA_DIR} does not exist. Please create it and add your JSON files.")
        return

    print(f"Scanning {RAW_DATA_DIR} for JSON files...")
    
    files = list(RAW_DATA_DIR.glob("*.json"))
    if not files:
        print("No JSON files found.")
        return

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # ADAPT THIS PART based on your JSON structure
                # Scenario A: The JSON is a list of strings ["parlare", "amare"]
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            all_verbs.add(item)
                        elif isinstance(item, dict) and 'verb' in item:
                             all_verbs.add(item['verb'])
                
                # Scenario B: The JSON is a dict {"a": ["amare", ...]}
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            for v in value:
                                if isinstance(v, str):
                                    all_verbs.add(v)
            
            print(f"Processed {file_path.name}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # 2. Organize verbs
    database = {
        "ARE": [],
        "ERE": [],
        "IRE": [],
        "ONREGELMATIG": []
    }
    
    print(f"Found {len(all_verbs)} unique verbs. Classifying...")
    
    for verb in all_verbs:
        group = classify_verb(verb)
        database[group].append(verb)
        
    # Sort lists
    for group in database:
        database[group].sort()
        
    # 3. Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully created {OUTPUT_FILE} with {len(all_verbs)} verbs.")
    print(f"ARE: {len(database['ARE'])}")
    print(f"ERE: {len(database['ERE'])}")
    print(f"IRE: {len(database['IRE'])}")
    print(f"Irregular/Other: {len(database['ONREGELMATIG'])}")

if __name__ == "__main__":
    import_verbs()
