# Verb Database Migration Guide

## Overview

This guide explains how to migrate your verb database from a **verb-level irregularity system** to a **tense-level irregularity system**.

### Why Migrate?

Some Italian verbs are irregular in certain tenses but regular in others. For example:
- **andare** (to go): irregular in presente and futuro, but regular in imperfetto
- **bere** (to drink): irregular in many tenses but follows patterns in some

The new system allows you to specify which tenses are irregular for each verb, giving you more granular control.

---

## Old Structure vs New Structure

### Old Structure
```json
{
  "ARE": ["parlare", "mangiare", "andare", ...],
  "ERE": ["credere", "vedere", ...],
  "IRE": ["dormire", "partire", ...],
  "ONREGELMATIG": ["andare", "essere", "avere", ...]
}
```

**Limitation**: A verb is either fully regular or fully irregular across all tenses.

### New Structure (Simplified)
```json
{
  "verbs": [
    {
      "infinitive": "parlare",
      "group": "ARE",
      "irregular_tenses": []
    },
    {
      "infinitive": "andare",
      "group": "ARE",
      "irregular_tenses": ["presente", "futuro", "passato_remoto"]
    },
    {
      "infinitive": "essere",
      "group": "ERE",
      "irregular_tenses": [
        "presente", "imperfetto", "futuro", "passato_remoto",
        "passato_prossimo", "trapassato_prossimo", 
        "trapassato_remoto", "futuro_anteriore"
      ]
    }
  ]
}
```

**Benefits**: 
- Each verb can be irregular in specific tenses only
- More accurate representation of Italian verb conjugation patterns
- Better filtering for quiz generation

---

## Migration Steps

### Step 1: Backup Your Current Database

```bash
cp verbs.json verbs_backup.json
```

### Step 2: Run the Migration Script

```bash
python migrate_verb_structure.py
```

You'll be prompted to choose between two formats:
1. **Full structure**: Each tense has an explicit irregular flag
2. **Simplified structure** (recommended): Each verb has a list of irregular tenses

**Recommendation**: Choose option 2 (simplified) as it's more compact and easier to maintain.

### Step 3: Review the Output

The script will create:
- `verbs_simplified.json` - Your new database structure

### Step 4: Replace Your Old Database

```bash
# After reviewing the new file
mv verbs.json verbs_old.json
mv verbs_simplified.json verbs.json
```

### Step 5: Update Your Application Code

If you're using the old `main.py`, replace it with `main_updated.py`:

```bash
cp main.py main_old.py
cp main_updated.py main.py
```

The updated `main.py` is **backward compatible** - it detects and works with both old and new database formats!

---

## Managing Irregular Tenses

### Using the Helper Script

The `mark_irregular.py` script helps you manage irregular tenses for specific verbs.

#### Mark a verb as irregular for specific tenses:
```bash
python mark_irregular.py andare presente futuro passato_remoto
```

#### Mark all tenses as irregular:
```bash
python mark_irregular.py essere --all-tenses
```

#### Mark a tense as regular (remove from irregular list):
```bash
python mark_irregular.py andare --remove imperfetto
```

#### View verb information:
```bash
python mark_irregular.py andare --info
```

---

## Available Tenses

The system supports 8 main tenses:

1. **presente** - Presente indicativo
2. **imperfetto** - Imperfetto indicativo
3. **futuro** - Futuro semplice
4. **passato_remoto** - Passato remoto
5. **passato_prossimo** - Passato prossimo
6. **trapassato_prossimo** - Trapassato prossimo
7. **trapassato_remoto** - Trapassato remoto
8. **futuro_anteriore** - Futuro anteriore

---

## API Changes

### New Query Parameter: Tense-Specific Filtering

The `/quiz` endpoint now supports filtering irregular verbs by tense:

```bash
# Get quiz with verbs irregular in presente
GET /quiz?groups=IRREGULAR&tenses=presente

# Get quiz with verbs regular in presente
GET /quiz?groups=REGULAR&tenses=presente
```

### New Endpoint: Verb Information

Get detailed information about a verb:

```bash
GET /verb/andare
```

Response:
```json
{
  "infinitive": "andare",
  "group": "ARE",
  "irregular_tenses": ["presente", "futuro", "passato_remoto"],
  "format": "new"
}
```

---

## Common Italian Irregular Verbs by Tense

Here are some examples to help you get started with marking irregular tenses:

### Highly Irregular (All Tenses)
- essere, avere

```bash
python mark_irregular.py essere --all-tenses
python mark_irregular.py avere --all-tenses
```

### Irregular in Presente, Futuro, Passato Remoto
- andare, fare, dare, stare

```bash
python mark_irregular.py andare presente futuro passato_remoto
python mark_irregular.py fare presente futuro passato_remoto
python mark_irregular.py dare presente futuro passato_remoto
python mark_irregular.py stare presente futuro passato_remoto
```

### Irregular in Presente and Passato Remoto
- venire, dire, bere, sapere

```bash
python mark_irregular.py venire presente passato_remoto
python mark_irregular.py dire presente passato_remoto
python mark_irregular.py bere presente passato_remoto
python mark_irregular.py sapere presente passato_remoto
```

### Irregular in Futuro Only
- Some verbs with contracted futures

```bash
python mark_irregular.py vedere futuro
python mark_irregular.py vivere futuro
```

---

## Verifying the Migration

### Test the New Structure

```bash
# Test that the API still works
python main.py
```

Then visit `http://localhost:8000/quiz` to ensure everything works correctly.

### Check Verb Counts

```bash
# View group statistics
curl http://localhost:8000/groups
```

---

## Rollback

If you need to rollback to the old structure:

```bash
mv verbs_old.json verbs.json
cp main_old.py main.py
```

The migration is **non-destructive** - your original files are preserved!

---

## Tips for Maintaining Your Database

1. **Start with common verbs**: Focus on the most frequently used irregular verbs first
2. **Reference conjugation tables**: Use reliable sources like:
   - Wiktionary
   - Reverso Conjugation
   - Your existing `abandonare.json` format files
3. **Test as you go**: Use `mark_irregular.py --info` to verify changes
4. **Batch updates**: Write a script to process multiple verbs at once

---

## Example: Bulk Marking Script

Create a file `mark_common_irregular.sh`:

```bash
#!/bin/bash

# Highly irregular
python mark_irregular.py essere --all-tenses
python mark_irregular.py avere --all-tenses

# Present and future irregular
python mark_irregular.py andare presente futuro passato_remoto
python mark_irregular.py fare presente futuro passato_remoto
python mark_irregular.py dare presente futuro passato_remoto
python mark_irregular.py stare presente futuro passato_remoto

# Present irregular
python mark_irregular.py volere presente
python mark_irregular.py potere presente
python mark_irregular.py dovere presente

echo "Done!"
```

Run it:
```bash
chmod +x mark_common_irregular.sh
./mark_common_irregular.sh
```

---

## Need Help?

- Check verb information: `python mark_irregular.py <verb> --info`
- View available tenses: Run `python mark_irregular.py` without arguments
- Test the API: Use the `/verb/<verb>` endpoint to see verb details

---

## Summary

✅ **Backup** your database  
✅ Run **migrate_verb_structure.py** (choose option 2)  
✅ Review the output file  
✅ Replace **verbs.json**  
✅ Update **main.py** (optional, backward compatible)  
✅ Use **mark_irregular.py** to fine-tune irregularity  
✅ Test your application  

You now have a more flexible and accurate verb conjugation system! 🎉
