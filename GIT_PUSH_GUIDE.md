# Git Push Guide - What to Push vs NOT Push

## ✅ SAFE TO PUSH (Always Push These)
```
✅ All Python code files (.py)
✅ Prompt files (prompts/*.txt)
✅ Documentation (*.md files)
✅ Data schemas (structure files)
✅ Requirements.txt (dependencies list)
✅ .gitignore (git ignore file)
✅ Configuration examples (config.example.py)
```

## ❌ NEVER PUSH (Security Risk!)
```
❌ .env (contains API keys & credentials)
❌ API keys, passwords, tokens
❌ credentials.json
❌ Database credentials
❌ SMTP passwords
❌ AWS/GCP/Azure credentials
```

## 🔄 Optional Push (Based on Project Needs)
```
? patients.json (test data - can push if anonymized)
? doctors.json (test data - safe if no real data)
? forms.json (safe if no user data)
? *.xlsx reports (usually don't push generated files)
```

---

## Steps to Clean Up Git History (If .env Already Pushed)

### Step 1: Check if .env is in git history
```powershell
git log --all --full-history -- .env
```
If it shows commits, .env was pushed.

---

### Step 2: Remove .env from git (without deleting local file)
```powershell
# Remove from git tracking (but keep local copy)
git rm --cached .env

# Verify it's removed
git status
# Should show: "deleted: .env" or "Changes to be committed: delete mode 100644 .env"

# Commit the removal
git add .gitignore
git commit -m "Remove .env from git tracking + add .gitignore"

# Push to remote
git push origin main
```

---

### Step 3: (IMPORTANT) Delete from git history if already committed
If sensitive API keys are in git history, do this:

```powershell
# Remove from entire history (stronger approach)
git filter-branch --tree-filter 'rm -f .env' -- --all

# Force push (ONLY IF working alone or coordinating with team)
git push origin --force --all
```

**⚠️ WARNING**: `--force` rewrites history. Only do this if:
- You're alone on the project
- Or you coordinate with team members

---

## Current Status Check

### Check what's staged
```powershell
git status
```

### See what would be pushed
```powershell
git diff --cached
```

### Check recent commits
```powershell
git log --oneline -5
```

---

## Recommended Git Workflow Going Forward

### Before each push:
```powershell
# 1. Check status
git status

# 2. Stage files you want
git add app/ agents/ services/ utils/ prompts/ *.md requirements.txt .gitignore

# 3. DO NOT stage .env
git add -p  # Interactive - review each file

# 4. Commit with message
git commit -m "Feature: [description of changes]"

# 5. Push
git push origin main
```

### Template Commits:
```
Feature: Add conversation node
Fix: Bug in scheduling availability
Docs: Update codebase analysis
Refactor: Improve patient service logic
```

---

## Example: What Your Push Should Look Like

### ✅ GOOD (Safe files only)
```
agents/
├─ graph.py
├─ state.py
└─ nodes/
   ├─ conversation_node.py
   ├─ booking_node.py
   ├─ reminder_node.py
   └─ form_distribution_node.py

app/
├─ main.py
├─ session_manager.py
└─ ...

services/
├─ llm_service.py
├─ patient_service.py
└─ ...

CODEBASE_ANALYSIS_CURRENT.md
requirements.txt
.gitignore
README.md
```

### ❌ WRONG (Never push these)
```
.env                    ← API keys inside!
venv/                   ← Virtual environment (huge)
__pycache__/           ← Python cache files
*.xlsx                  ← Generated reports
.streamlit/            ← Local Streamlit config
```

---

## Quick Commands

```powershell
# Stage only safe files
git add app/ agents/ services/ utils/ prompts/ *.md requirements.txt .gitignore

# Check what's staged
git status

# Commit
git commit -m "Description of changes"

# Push
git push origin main

# See what was pushed
git log --oneline -3
```

---

## If You Accidentally Pushed .env

### Option 1: Quick Fix (Local only, not history rewrite)
```powershell
# 1. Add .gitignore
git add .gitignore

# 2. Remove .env from tracking
git rm --cached .env

# 3. Commit & push
git commit -m "Remove .env from git"
git push origin main

# ⚠️ Note: File still exists in git history (but won't track changes)
```

### Option 2: Clean History (if sensitive keys exposed)
```powershell
# Contact your team first!
# Then:
git filter-branch --tree-filter 'rm -f .env' -- --all
git push origin --force --all

# Notify team to pull with: git pull --rebase
```

---

## Summary

| **Task** | **Command** |
|---|---|
| **Check status** | `git status` |
| **Stage safe files** | `git add app/ agents/ services/` |
| **Ignore .env** | `.gitignore` created (automatically excludes) |
| **Commit** | `git commit -m "Message"` |
| **Push** | `git push origin main` |
| **Remove .env tracking** | `git rm --cached .env` |
| **See history** | `git log --oneline` |

---

## Your Next Step

1. **Right now**: Run `git status` to see current state
2. **Check**: Is `.env` showing as changed/staged?
3. **If YES**: Run `git rm --cached .env`
4. **Then**: `git add .gitignore && git commit -m "Add gitignore, remove .env from tracking"`
5. **Finally**: `git push origin main`

All your code/documentation will still be safe!

---

**Created**: May 14, 2026  
**Keep .env local, never in git** ✅
