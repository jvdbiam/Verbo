# Tense-Level Irregularity System - Quick Start Guide

## ✅ What I've Created for You

I've created a complete system to track verb irregularity at the **tense level** instead of the **verb level**. Here's what you have:

### 1. **migrate_verb_structure.py** 
   - Converts your current `verbs.json` from old format to new format
   - Two options: Full structure or Simplified structure (recommended)
   - **Preserves your original data** during migration

### 2. **main_updated.py**
   - Updated backend API that supports **both old and new formats**
   - Automatically detects which format you're using
   - New features:
     - Filter verbs by tense-specific irregularity
     - Get verb information with `/verb/<verb>` endpoint
     - Smarter quiz generation

### 3. **mark_irregular.py**
   - Easy command-line tool to mark specific tenses as irregular
   - Examples:
     ```bash
     python mark_irregular.py andare presente futuro passato_remoto
     python mark_irregular.py essere --all-tenses
     python mark_irregular.py andare --remove imperfetto
     python mark_irregular.py andare --info
     ```

### 4. **analyze_conjugations.py**
   - Analyzes conjugation JSON files (like your `abandonare.json` example)
   - Automatically detects irregular patterns
   - Generates commands to mark verbs as irregular

### 5. **MIGRATION_GUIDE.md**
   - Complete documentation with examples
   - Common Italian irregular verbs reference
   - Batch update scripts

---

## 🚀 How to Get Started

### Option 1: Quick Migration (Recommended)

```bash
# 1. Backup your current database
cp verbs.json verbs_backup.json

# 2. Run the migration (choose option 2 when prompted)
python migrate_verb_structure.py

# 3. Replace your old database
mv verbs.json verbs_old.json
mv verbs_simplified.json verbs.json

# 4. Test it (optional but recommended)
python main_updated.py
# Visit http://localhost:8000/quiz
```

### Option 2: Use Both Formats (Safe)

Your `main_updated.py` is **backward compatible**, so you can:

1. Keep your current `verbs.json` (old format)
2. Start using `main_updated.py` right away
3. Migrate later when you're ready

---

## 📊 New Database Structure

### Before (Old Format):
```json
{
  "ARE": ["parlare", "andare", ...],
  "ONREGELMATIG": ["andare", "essere", ...]
}
```

**Problem**: `andare` is marked as fully irregular, even though it's only irregular in some tenses.

### After (New Format):
```json
{
  "verbs": [
    {
      "infinitive": "andare",
      "group": "ARE",
      "irregular_tenses": ["presente", "futuro", "passato_remoto"]
    }
  ]
}
```

**Benefit**: You can now see that `andare` is regular in imperfetto!

---

## 🎯 Common Use Cases

### Mark a verb as irregular in specific tenses

```bash
# Andare is irregular in presente, futuro, and passato_remoto
python mark_irregular.py andare presente futuro passato_remoto
```

### Mark all tenses as irregular (highly irregular verbs)

```bash
# Essere and Avere are irregular in all tenses
python mark_irregular.py essere --all-tenses
python mark_irregular.py avere --all-tenses
```

### Check if a verb is correct

```bash
python mark_irregular.py andare --info
```

Output:
```
Verb: andare
Group: ARE
Irregular tenses: presente, futuro, passato_remoto
```

### Remove irregularity from a tense

```bash
# If you marked something wrong
python mark_irregular.py andare --remove imperfetto
```

### Generate quiz with tense-specific filtering

```bash
# Only verbs irregular in presente
curl "http://localhost:8000/quiz?groups=IRREGULAR&tenses=presente"

# Only verbs regular in presente
curl "http://localhost:8000/quiz?groups=REGULAR&tenses=presente"
```

---

## 💡 Smart Features

### 1. Auto-Detection of Database Format

The `main_updated.py` automatically detects whether you're using:
- Old format (groups: ARE, ERE, IRE, ONREGELMATIG)
- New format (verbs with irregular_tenses list)

### 2. Backward Compatibility

You don't need to migrate immediately. The new code works with both formats!

### 3. Tense-Specific Filtering

When you request a quiz with `groups=IRREGULAR&tenses=presente`, it returns:
- **New format**: Only verbs where "presente" is in the irregular_tenses list
- **Old format**: All verbs in ONREGELMATIG (same as before)

---

## 📋 Available Tenses

Your system supports 8 tenses:

1. `presente` - Presente indicativo
2. `imperfetto` - Imperfetto indicativo  
3. `futuro` - Futuro semplice
4. `passato_remoto` - Passato remoto
5. `passato_prossimo` - Passato prossimo
6. `trapassato_prossimo` - Trapassato prossimo
7. `trapassato_remoto` - Trapassato remoto
8. `futuro_anteriore` - Futuro anteriore

---

## 🔧 Recommended Migration Steps

### Step 1: Understand the Current State
```bash
# See how many verbs you have in each group
python main.py  # Start your server
curl http://localhost:8000/groups
```

### Step 2: Run Migration
```bash
python migrate_verb_structure.py
# Choose option 2 (Simplified structure)
```

### Step 3: Review Output
```bash
# Check the generated file
cat verbs_simplified.json | head -50
```

### Step 4: Backup and Replace
```bash
mv verbs.json verbs_old.json
mv verbs_simplified.json verbs.json
```

### Step 5: Start Marking Irregular Tenses
```bash
# Start with the most common irregular verbs
python mark_irregular.py essere --all-tenses
python mark_irregular.py avere --all-tenses
python mark_irregular.py andare presente futuro passato_remoto
python mark_irregular.py fare presente futuro passato_remoto
```

### Step 6: Update Your Backend (Optional)
```bash
cp main.py main_old.py
cp main_updated.py main.py
```

### Step 7: Test
```bash
python main.py
# Visit http://localhost:8000/quiz?groups=IRREGULAR&tenses=presente
```

---

## 📚 Example: Batch Update Common Irregular Verbs

Create a file `update_irregular.sh`:

```bash
#!/bin/bash

echo "Marking common irregular verbs..."

# Highly irregular
python mark_irregular.py essere --all-tenses
python mark_irregular.py avere --all-tenses

# Irregular in presente, futuro, passato_remoto
python mark_irregular.py andare presente futuro passato_remoto
python mark_irregular.py fare presente futuro passato_remoto
python mark_irregular.py dare presente futuro passato_remoto
python mark_irregular.py stare presente futuro passato_remoto

# Irregular in presente and passato_remoto
python mark_irregular.py venire presente passato_remoto
python mark_irregular.py dire presente passato_remoto
python mark_irregular.py bere presente passato_remoto
python mark_irregular.py sapere presente passato_remoto

# Irregular in futuro (contracted)
python mark_irregular.py vedere futuro
python mark_irregular.py vivere futuro
python mark_irregular.py dovere futuro
python mark_irregular.py potere futuro
python mark_irregular.py volere futuro

echo "Done! Run 'python main.py' to test."
```

Then run:
```bash
chmod +x update_irregular.sh
./update_irregular.sh
```

---

## ❓ FAQ

### Q: Do I need to migrate right away?
**A:** No! The new `main_updated.py` works with both old and new formats. You can migrate when you're ready.

### Q: What happens to my old data?
**A:** Nothing! The migration creates new files (`verbs_simplified.json`). Your original `verbs.json` stays intact until you manually replace it.

### Q: Can I test before switching?
**A:** Yes! Keep your old `verbs.json` and `main.py`. Test with `verbs_simplified.json` and `main_updated.py` in a different terminal.

### Q: How do I know which verbs should be marked irregular?
**A:** 
1. Use the `analyze_conjugations.py` script on your JSON conjugation files
2. Reference Italian grammar books or websites
3. Test the conjugations in your app and mark wrong ones as irregular

### Q: Can I rollback?
**A:** Yes! Just restore your backup:
```bash
mv verbs_old.json verbs.json
mv main_old.py main.py
```

---

## 🎉 Summary

You now have a **flexible system** that tracks verb irregularity at the **tense level**:

✅ **Migration script** to convert your database  
✅ **Backward-compatible API** that works with both formats  
✅ **Command-line tools** to manage irregularities easily  
✅ **Analysis tools** to detect irregular patterns automatically  
✅ **Complete documentation** with examples  

Start by running the migration, then gradually mark verbs as irregular for specific tenses using the `mark_irregular.py` tool!

---

## 📞 Need Help?

Check the `MIGRATION_GUIDE.md` for detailed documentation and more examples.

Happy conjugating! 🇮🇹
