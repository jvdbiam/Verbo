"""
Migration script to convert verb database from verb-level irregularity to tense-level irregularity.

Old structure:
{
  "ARE": [...],
  "ERE": [...],
  "IRE": [...],
  "ONREGELMATIG": [...]
}

New structure:
{
  "verbs": [
    {
      "infinitive": "abandonare",
      "group": "ARE",
      "tenses": {
        "presente": {"irregular": false},
        "imperfetto": {"irregular": false},
        "futuro": {"irregular": false},
        "passato_remoto": {"irregular": false},
        "passato_prossimo": {"irregular": false},
        "trapassato_prossimo": {"irregular": false},
        "trapassato_remoto": {"irregular": false},
        "futuro_anteriore": {"irregular": false}
      }
    },
    ...
  ]
}
"""

import json
import os

# Available tenses
TENSES = [
    "presente",
    "imperfetto",
    "futuro",
    "passato_remoto",
    "passato_prossimo",
    "trapassato_prossimo",
    "trapassato_remoto",
    "futuro_anteriore"
]

def determine_verb_group(verb: str) -> str:
    """Determine verb group based on infinitive ending."""
    if verb.endswith("are"):
        return "ARE"
    elif verb.endswith("ere"):
        return "ERE"
    elif verb.endswith("ire"):
        return "IRE"
    else:
        return "OTHER"

def migrate_verb_database(old_db_path: str, new_db_path: str):
    """Migrate old verb database structure to new tense-level irregularity structure."""
    
    # Load old database
    with open(old_db_path, 'r', encoding='utf-8') as f:
        old_db = json.load(f)
    
    # Create new structure
    new_db = {"verbs": []}
    
    # Track which verbs are irregular
    irregular_verbs = set(old_db.get("ONREGELMATIG", []))
    
    # Process each group
    for group in ["ARE", "ERE", "IRE"]:
        if group not in old_db:
            continue
            
        for verb in old_db[group]:
            # Create verb entry with tense-level irregularity
            verb_entry = {
                "infinitive": verb,
                "group": group,
                "tenses": {}
            }
            
            # Initialize all tenses
            # If the verb is in ONREGELMATIG list, mark all tenses as irregular by default
            # (you can manually adjust specific tenses later)
            is_generally_irregular = verb in irregular_verbs
            
            for tense in TENSES:
                verb_entry["tenses"][tense] = {
                    "irregular": is_generally_irregular
                }
            
            new_db["verbs"].append(verb_entry)
    
    # Process ONREGELMATIG verbs that don't fit into ARE/ERE/IRE
    if "ONREGELMATIG" in old_db:
        processed_verbs = {v["infinitive"] for v in new_db["verbs"]}
        
        for verb in old_db["ONREGELMATIG"]:
            if verb not in processed_verbs:
                # Determine group or mark as OTHER
                group = determine_verb_group(verb)
                
                verb_entry = {
                    "infinitive": verb,
                    "group": group,
                    "tenses": {}
                }
                
                # Mark all tenses as irregular
                for tense in TENSES:
                    verb_entry["tenses"][tense] = {
                        "irregular": True
                    }
                
                new_db["verbs"].append(verb_entry)
    
    # Sort verbs alphabetically
    new_db["verbs"].sort(key=lambda x: x["infinitive"])
    
    # Save new database
    with open(new_db_path, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, ensure_ascii=False, indent=2)
    
    print(f"Migration complete!")
    print(f"Total verbs: {len(new_db['verbs'])}")
    print(f"New database saved to: {new_db_path}")

def create_simplified_structure(old_db_path: str, simplified_db_path: str):
    """
    Create a simplified structure where each verb has a list of irregular tenses.
    This is more compact than the full structure.
    
    Structure:
    {
      "verbs": [
        {
          "infinitive": "andare",
          "group": "ARE",
          "irregular_tenses": ["presente", "futuro", "passato_remoto"]
        }
      ]
    }
    """
    # Load old database
    with open(old_db_path, 'r', encoding='utf-8') as f:
        old_db = json.load(f)
    
    # Create new structure
    new_db = {"verbs": []}
    
    # Track which verbs are irregular
    irregular_verbs = set(old_db.get("ONREGELMATIG", []))
    
    # Process each group
    for group in ["ARE", "ERE", "IRE"]:
        if group not in old_db:
            continue
            
        for verb in old_db[group]:
            verb_entry = {
                "infinitive": verb,
                "group": group,
                "irregular_tenses": TENSES.copy() if verb in irregular_verbs else []
            }
            new_db["verbs"].append(verb_entry)
    
    # Process ONREGELMATIG verbs that don't fit into ARE/ERE/IRE
    if "ONREGELMATIG" in old_db:
        processed_verbs = {v["infinitive"] for v in new_db["verbs"]}
        
        for verb in old_db["ONREGELMATIG"]:
            if verb not in processed_verbs:
                group = determine_verb_group(verb)
                
                verb_entry = {
                    "infinitive": verb,
                    "group": group,
                    "irregular_tenses": TENSES.copy()
                }
                new_db["verbs"].append(verb_entry)
    
    # Sort verbs alphabetically
    new_db["verbs"].sort(key=lambda x: x["infinitive"])
    
    # Save new database
    with open(simplified_db_path, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, ensure_ascii=False, indent=2)
    
    print(f"Simplified structure created!")
    print(f"Total verbs: {len(new_db['verbs'])}")
    print(f"New database saved to: {simplified_db_path}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OLD_DB_PATH = os.path.join(BASE_DIR, "verbs.json")
    NEW_DB_PATH = os.path.join(BASE_DIR, "verbs_new.json")
    SIMPLIFIED_DB_PATH = os.path.join(BASE_DIR, "verbs_simplified.json")
    
    print("=" * 60)
    print("Verb Database Migration")
    print("=" * 60)
    print()
    
    print("Option 1: Full structure (each tense has irregular flag)")
    print("Option 2: Simplified structure (list of irregular tenses per verb)")
    print()
    
    choice = input("Choose migration type (1 or 2, default=2): ").strip() or "2"
    
    if choice == "1":
        migrate_verb_database(OLD_DB_PATH, NEW_DB_PATH)
        print(f"\nBackup your old database and rename {NEW_DB_PATH} to verbs.json")
    elif choice == "2":
        create_simplified_structure(OLD_DB_PATH, SIMPLIFIED_DB_PATH)
        print(f"\nBackup your old database and rename {SIMPLIFIED_DB_PATH} to verbs.json")
    else:
        print("Invalid choice!")
