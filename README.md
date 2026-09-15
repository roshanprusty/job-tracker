# 🤖 Job Tracker - Full-Stack AI Jobs Bot

Auto-tracks Full-Stack AI / GenAI Engineer jobs every 1 hour and sends instant alerts on Telegram.

**Live for:** Mumbai + Remote roles | **Cost:** ₹0 / Free forever

---

### 🚀 What it does
- Checks Wellfound (AngelList) + Remotive every 60 mins
- Filters for Full-Stack + AI/LLM roles
- Sends Telegram message only for NEW jobs (no spam)
- Runs 24/7 even when laptop is off (via GitHub Actions)

### 🛠️ Stack
- Python (`requests`)
- GitHub Actions (free server)
- Telegram Bot API

### 📂 Files
- `tracker.py` - Main brain, fetches jobs
- `.github/workflows/jobs.yml` - Alarm clock that runs every 1 hr
- `sent.json` - Auto-created, remembers sent jobs
- `README.md` - This file

### 🔧 Setup (Already Done)
1. Created Telegram Bot via @BotFather -> Got `BOT_TOKEN`
2. Got `CHAT_ID` via `getUpdates` API
3. Added both as GitHub Secrets
4. Pushed workflow to GitHub

### ▶️ How to run manually
Go to **Actions** tab -> **Job Tracker** -> **Run workflow**

### 📈 Free Limit Usage
- ~720 runs/month * 30 sec = ~360 mins/month
- GitHub Free limit = 2000 mins/month
- So 100% free forever

### ➕ Want to add more keywords/sources?
Edit `tracker.py` -> Add your search terms in `KEYWORDS` list.

---

Made by Roshan | Mumbai, India