"""
Analyze conjugation JSON files (like abandonare.json) to identify irregular patterns.

This script compares conjugations with expected regular patterns to help identify
which tenses should be marked as irregular.

Usage:
    python analyze_conjugations.py abandonare.json
    python analyze_conjugations.py data/raw_verbs/*.json
"""

import json
import sys
import os

# Regular conjugation patterns for -are, -ere, -ire verbs
# Based on standard Italian conjugation rules

def get_verb_root(infinitive: str) -> tuple:
    """
    Get verb root and conjugation group.
    Returns (root, group) where group is 'ARE', 'ERE', or 'IRE'
    """
    if infinitive.endswith("are"):
        return infinitive[:-3], "ARE"
    elif infinitive.endswith("ere"):
        return infinitive[:-3], "ERE"
    elif infinitive.endswith("ire"):
        return infinitive[:-3], "IRE"
    return infinitive, "OTHER"

def get_regular_presente(root: str, group: str) -> list:
    """Get regular presente conjugations."""
    if group == "ARE":
        return [f"{root}o", f"{root}i", f"{root}a", f"{root}iamo", f"{root}ate", f"{root}ano"]
    elif group == "ERE":
        return [f"{root}o", f"{root}i", f"{root}e", f"{root}iamo", f"{root}ete", f"{root}ono"]
    elif group == "IRE":
        return [f"{root}o", f"{root}i", f"{root}e", f"{root}iamo", f"{root}ite", f"{root}ono"]
    return []

def get_regular_imperfetto(root: str, group: str) -> list:
    """Get regular imperfetto conjugations."""
    if group == "ARE":
        return [f"{root}avo", f"{root}avi", f"{root}ava", f"{root}avamo", f"{root}avate", f"{root}avano"]
    elif group == "ERE":
        return [f"{root}evo", f"{root}evi", f"{root}eva", f"{root}evamo", f"{root}evate", f"{root}evano"]
    elif group == "IRE":
        return [f"{root}ivo", f"{root}ivi", f"{root}iva", f"{root}ivamo", f"{root}ivate", f"{root}ivano"]
    return []

def get_regular_futuro(infinitive: str) -> list:
    """Get regular futuro conjugations."""
    # For -are verbs, 'a' changes to 'e'
    if infinitive.endswith("are"):
        stem = infinitive[:-3] + "er"
    else:
        stem = infinitive[:-1]
    
    return [
        f"{stem}ò", f"{stem}ai", f"{stem}à",
        f"{stem}emo", f"{stem}ete", f"{stem}anno"
    ]

def get_regular_passato_remoto(root: str, group: str) -> list:
    """Get regular passato remoto conjugations."""
    if group == "ARE":
        return [f"{root}ai", f"{root}asti", f"{root}ò", f"{root}ammo", f"{root}aste", f"{root}arono"]
    elif group == "ERE":
        # ERE has two common patterns, we use the -etti pattern
        return [f"{root}ei", f"{root}esti", f"{root}é", f"{root}emmo", f"{root}este", f"{root}erono"]
    elif group == "IRE":
        return [f"{root}ii", f"{root}isti", f"{root}ì", f"{root}immo", f"{root}iste", f"{root}irono"]
    return []

def normalize_conjugation(conj: str) -> str:
    """Normalize conjugation for comparison (remove accents, etc)."""
    # Basic normalization - you may want to extend this
    replacements = {
        'à': 'a', 'è': 'e', 'é': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u'
    }
    result = conj.lower().strip()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result

def extract_conjugations_from_json(data: dict) -> dict:
    """Extract conjugations from JSON structure."""
    conjugations = {}
    
    for entry in data.get("conjugations", []):
        group = entry.get("group", "")
        value = entry.get("value", "")
        
        if group == "indicative/present":
            if "presente" not in conjugations:
                conjugations["presente"] = []
            conjugations["presente"].append(value)
        elif group == "indicative/imperfect":
            if "imperfetto" not in conjugations:
                conjugations["imperfetto"] = []
            conjugations["imperfetto"].append(value)
        elif group == "indicative/future":
            if "futuro" not in conjugations:
                conjugations["futuro"] = []
            conjugations["futuro"].append(value)
        elif group == "indicative/pasthistoric":
            if "passato_remoto" not in conjugations:
                conjugations["passato_remoto"] = []
            conjugations["passato_remoto"].append(value)
    
    return conjugations

def compare_with_regular(infinitive: str, actual_conjugations: dict) -> dict:
    """Compare actual conjugations with regular patterns."""
    root, group = get_verb_root(infinitive)
    
    irregularities = {}
    
    # Check presente
    if "presente" in actual_conjugations:
        regular = get_regular_presente(root, group)
        actual = actual_conjugations["presente"]
        if len(actual) >= 6 and len(regular) == 6:
            mismatches = sum(1 for i in range(6) if normalize_conjugation(actual[i]) != normalize_conjugation(regular[i]))
            if mismatches > 0:
                irregularities["presente"] = {
                    "mismatches": mismatches,
                    "actual": actual,
                    "expected": regular
                }
    
    # Check imperfetto
    if "imperfetto" in actual_conjugations:
        regular = get_regular_imperfetto(root, group)
        actual = actual_conjugations["imperfetto"]
        if len(actual) >= 6 and len(regular) == 6:
            mismatches = sum(1 for i in range(6) if normalize_conjugation(actual[i]) != normalize_conjugation(regular[i]))
            if mismatches > 0:
                irregularities["imperfetto"] = {
                    "mismatches": mismatches,
                    "actual": actual,
                    "expected": regular
                }
    
    # Check futuro
    if "futuro" in actual_conjugations:
        regular = get_regular_futuro(infinitive)
        actual = actual_conjugations["futuro"]
        if len(actual) >= 6 and len(regular) == 6:
            mismatches = sum(1 for i in range(6) if normalize_conjugation(actual[i]) != normalize_conjugation(regular[i]))
            if mismatches > 0:
                irregularities["futuro"] = {
                    "mismatches": mismatches,
                    "actual": actual,
                    "expected": regular
                }
    
    # Check passato_remoto
    if "passato_remoto" in actual_conjugations:
        regular = get_regular_passato_remoto(root, group)
        actual = actual_conjugations["passato_remoto"]
        if len(actual) >= 6 and len(regular) == 6:
            mismatches = sum(1 for i in range(6) if normalize_conjugation(actual[i]) != normalize_conjugation(regular[i]))
            if mismatches > 0:
                irregularities["passato_remoto"] = {
                    "mismatches": mismatches,
                    "actual": actual,
                    "expected": regular
                }
    
    return irregularities

def analyze_file(filepath: str):
    """Analyze a single conjugation JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        infinitive = data.get("word", data.get("description", "unknown"))
        
        # Extract conjugations
        conjugations = extract_conjugations_from_json(data)
        
        if not conjugations:
            print(f"⚠️  {infinitive}: No conjugations found")
            return None
        
        # Compare with regular patterns
        irregularities = compare_with_regular(infinitive, conjugations)
        
        if irregularities:
            print(f"\n🔍 {infinitive}")
            print(f"   Root: {get_verb_root(infinitive)[0]}, Group: {get_verb_root(infinitive)[1]}")
            
            irregular_tenses = []
            for tense, info in irregularities.items():
                irregular_tenses.append(tense)
                print(f"   ❌ {tense}: {info['mismatches']} mismatches")
                print(f"      Expected: {' '.join(info['expected'][:3])}...")
                print(f"      Actual:   {' '.join(info['actual'][:3])}...")
            
            # Print command to mark as irregular
            print(f"   💡 Command: python mark_irregular.py {infinitive} {' '.join(irregular_tenses)}")
            
            return infinitive, irregular_tenses
        else:
            print(f"✅ {infinitive}: Regular conjugation")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing {filepath}: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_conjugations.py <file1.json> [file2.json ...]")
        print("\nExample:")
        print("  python analyze_conjugations.py abandonare.json")
        print("  python analyze_conjugations.py data/raw_verbs/a*.json")
        sys.exit(1)
    
    files = sys.argv[1:]
    
    print("=" * 70)
    print("Conjugation Analysis - Finding Irregular Patterns")
    print("=" * 70)
    
    irregular_verbs = []
    
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        result = analyze_file(filepath)
        if result:
            irregular_verbs.append(result)
    
    # Summary
    if irregular_verbs:
        print("\n" + "=" * 70)
        print(f"Summary: Found {len(irregular_verbs)} irregular verb(s)")
        print("=" * 70)
        
        print("\n# Batch command to mark all irregular tenses:")
        for verb, tenses in irregular_verbs:
            print(f"python mark_irregular.py {verb} {' '.join(tenses)}")
    else:
        print("\n✅ All analyzed verbs have regular conjugations!")

if __name__ == "__main__":
    main()
