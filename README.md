# 🤖 Job Bot - 0-2 Years | Full-Stack / AI Engineer

Telegram bot that scrapes 3 job platforms every 6 hours and sends you only NEW jobs matching your stack.

### 📌 Platforms Covered
| Platform | Why |
|---|---|
| **Cutshort.io** | Best for 0-2 years, startup jobs |
| **Hirist.tech** | Tech-only (Backend, Full-Stack, AI) - updates hourly |
| **Wellfound** (AngelList) | Remote + Startup jobs |

### 🎯 My Filters
- **Experience:** 0-2 Years / Fresher
- **Keywords:** `full-stack`, `full stack`, `ai engineer`, `software engineer`, `software developer`, `backend engineer`, `genai`, `rag`, `langchain`, `langraph`, `node.js`, `fastapi`, `django`
- **Locations:** `mumbai`, `remote`, `bangalore`, `india`, `noida`, `gurugram`, `hyderabad`, `pune`, `delhi`

### ⚙️ How it works
1. GitHub Actions runs `bot.py` every 6 hours
2. Scrapes 3 sites with Playwright
3. Filters by KEYWORDS + 0-2 years experience
4. Checks `jobs.json` to avoid duplicate links
5. Sends NEW jobs to Telegram
6. Saves seen jobs back to `jobs.json`

### 🔧 Setup
1. Fork this repo
2. Add GitHub Secrets:
   - `TELEGRAM_TOKEN` - from @BotFather
   - `TELEGRAM_CHAT_ID` - from @userinfobot
3. Enable Actions -> Run workflow

### 📂 Files
- `bot.py` - Main scraper (3 platforms)
- `jobs.json` - Stores seen job links (auto-updated)
- `.github/workflows/job-bot.yml` - Cron every 6 hrs

### 📊 Workflow
- Bot jobs -> Auto Telegram
- LinkedIn / Naukri -> You apply manually
- No duplicate alerts (uses `jobs.json`)

### 🚀 Manual Run
Go to Actions tab -> Job Bot -> Run workflow

---
Built for 0-2 years Full-Stack / AI roles in Mumbai/Remote.
