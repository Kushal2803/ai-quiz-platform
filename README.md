# 🧠 AI Daily Quiz Platform — Setup Guide

## What's New in This Version
- ✅ **Gemini AI** generates 10 real-world news questions every day
- ✅ **Auto-scheduler** — quiz generates automatically at 7 AM daily
- ✅ **PostgreSQL** — all data saved permanently (users + scores + questions)
- ✅ **Mobile-friendly** frontend — works on phone, tablet, desktop
- ✅ **Railway deployment** — live 24/7 for free

---

## Step 1 — Copy These Files Into Your Project

Replace/add these files in your project:

```
your-project/
├── main.py                          ← REPLACE
├── requirements.txt                 ← REPLACE
├── railway.toml                     ← NEW
├── Procfile                         ← NEW
├── frontend/
│   └── index.html                   ← NEW (mobile app)
└── app/
    ├── models/
    │   └── __init__.py              ← REPLACE
    ├── api/
    │   └── quiz.py                  ← REPLACE (was app/api/quiz.py)
    └── services/
        └── quiz_generator.py        ← REPLACE
```

---

## Step 2 — Get Your Free API Keys

### Gemini API Key (FREE)
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### News API Key (FREE - optional but recommended)
1. Go to: https://newsapi.org/register
2. Register free account
3. Copy the API key

---

## Step 3 — Update Your .env File

```
GEMINI_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_newsapi_key_here
DATABASE_URL=sqlite:///./quiz.db
```

---

## Step 4 — Install New Packages

```bash
pip install -r requirements.txt
```

---

## Step 5 — Run Locally to Test

```bash
uvicorn main:app --reload
```

Then open: http://localhost:8000

- Go to http://localhost:8000/docs
- POST /api/quiz/generate → generates 10 AI questions from real news
- Open http://localhost:8000 → mobile app

---

## Step 6 — Deploy to Railway (Free, Always Live)

1. Go to https://railway.app and sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub repo
4. Add Environment Variables in Railway dashboard:
   - GEMINI_API_KEY = your key
   - NEWS_API_KEY = your key
5. Add a PostgreSQL database:
   - In Railway: click "+ New" → "Database" → "PostgreSQL"
   - Railway auto-sets DATABASE_URL for you ✅
6. Deploy! Railway gives you a live URL like:
   https://your-project.up.railway.app

---

## Features Summary

| Feature | Status |
|---------|--------|
| 10 AI questions per day | ✅ Gemini 1.5 Flash |
| Real world news | ✅ NewsAPI + fallback |
| Auto daily generation | ✅ 7 AM scheduler |
| All data saved permanently | ✅ PostgreSQL on Railway |
| User accounts + login | ✅ |
| Leaderboard | ✅ |
| Mobile phone support | ✅ Responsive design |
| Always live 24/7 | ✅ Railway free tier |

---

## Troubleshooting

**"AI generation failed"** → Check GEMINI_API_KEY in .env

**"Cannot connect"** → Make sure uvicorn is running

**Questions not saving** → Check DATABASE_URL in .env

**Mobile not loading** → Access via the Railway URL, not localhost
