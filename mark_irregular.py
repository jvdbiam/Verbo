"""
Helper script to manually mark specific verbs as irregular for specific tenses.

Usage:
    python mark_irregular.py andare presente futuro passato_remoto
    python mark_irregular.py essere --all-tenses
    python mark_irregular.py fare --remove presente
"""

import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERB_DB_FILE = os.path.join(BASE_DIR, "verbs.json")

AVAILABLE_TENSES = [
    "presente",
    "imperfetto",
    "futuro",
    "passato_remoto",
    "passato_prossimo",
    "trapassato_prossimo",
    "trapassato_remoto",
    "futuro_anteriore"
]

def load_database():
    """Load the verb database."""
    with open(VERB_DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_database(data):
    """Save the verb database."""
    with open(VERB_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def mark_tenses_irregular(verb: str, tenses: list, remove: bool = False):
    """Mark specific tenses as irregular (or regular if remove=True) for a verb."""
    
    # Load database
    data = load_database()
    
    if "verbs" not in data:
        print("Error: Database is in old format. Please run migration first.")
        return False
    
    # Find the verb
    verb_entry = None
    for v in data["verbs"]:
        if v["infinitive"] == verb:
            verb_entry = v
            break
    
    if not verb_entry:
        print(f"Error: Verb '{verb}' not found in database.")
        return False
    
    # Get current irregular tenses
    irregular_tenses = set(verb_entry.get("irregular_tenses", []))
    
    # Update irregular tenses
    if remove:
        # Remove tenses from irregular list
        for tense in tenses:
            if tense in irregular_tenses:
                irregular_tenses.remove(tense)
                print(f"✓ Marked '{verb}' as REGULAR for tense: {tense}")
            else:
                print(f"✗ '{verb}' was already regular for tense: {tense}")
    else:
        # Add tenses to irregular list
        for tense in tenses:
            if tense not in irregular_tenses:
                irregular_tenses.add(tense)
                print(f"✓ Marked '{verb}' as IRREGULAR for tense: {tense}")
            else:
                print(f"✗ '{verb}' was already irregular for tense: {tense}")
    
    # Update verb entry
    verb_entry["irregular_tenses"] = sorted(list(irregular_tenses))
    
    # Save database
    save_database(data)
    print(f"\nDatabase updated successfully!")
    print(f"Verb '{verb}' now has {len(irregular_tenses)} irregular tense(s): {', '.join(sorted(irregular_tenses)) or 'none'}")
    
    return True

def show_verb_info(verb: str):
    """Show information about a verb."""
    data = load_database()
    
    if "verbs" not in data:
        print("Error: Database is in old format.")
        return
    
    for v in data["verbs"]:
        if v["infinitive"] == verb:
            print(f"\nVerb: {v['infinitive']}")
            print(f"Group: {v['group']}")
            print(f"Irregular tenses: {', '.join(v.get('irregular_tenses', [])) or 'none'}")
            return
    
    print(f"Verb '{verb}' not found.")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Mark tenses as irregular:")
        print("    python mark_irregular.py <verb> <tense1> [tense2 ...]")
        print("  Mark all tenses as irregular:")
        print("    python mark_irregular.py <verb> --all-tenses")
        print("  Mark tenses as regular (remove from irregular list):")
        print("    python mark_irregular.py <verb> --remove <tense1> [tense2 ...]")
        print("  Show verb info:")
        print("    python mark_irregular.py <verb> --info")
        print()
        print(f"Available tenses: {', '.join(AVAILABLE_TENSES)}")
        sys.exit(1)
    
    verb = sys.argv[1]
    
    # Check for flags
    if len(sys.argv) > 2:
        if sys.argv[2] == "--info":
            show_verb_info(verb)
            return
        elif sys.argv[2] == "--all-tenses":
            mark_tenses_irregular(verb, AVAILABLE_TENSES, remove=False)
            return
        elif sys.argv[2] == "--remove":
            if len(sys.argv) < 4:
                print("Error: Please specify tenses to remove.")
                sys.exit(1)
            tenses = sys.argv[3:]
            # Validate tenses
            invalid = [t for t in tenses if t not in AVAILABLE_TENSES]
            if invalid:
                print(f"Error: Invalid tense(s): {', '.join(invalid)}")
                print(f"Available tenses: {', '.join(AVAILABLE_TENSES)}")
                sys.exit(1)
            mark_tenses_irregular(verb, tenses, remove=True)
            return
    
    # Mark tenses as irregular
    tenses = sys.argv[2:]
    
    # Validate tenses
    invalid = [t for t in tenses if t not in AVAILABLE_TENSES]
    if invalid:
        print(f"Error: Invalid tense(s): {', '.join(invalid)}")
        print(f"Available tenses: {', '.join(AVAILABLE_TENSES)}")
        sys.exit(1)
    
    if not tenses:
        print("Error: Please specify at least one tense.")
        sys.exit(1)
    
    mark_tenses_irregular(verb, tenses, remove=False)

if __name__ == "__main__":
    main()
