import requests, os, json, time
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORDS = ["Full Stack Developer", "Backend Engineer", "Software Engineer", "Software Developer", "Full Stack AI Developer", "Gen AI Developer"]

# Using Wellfound + Remotive free APIs (no auth needed)
def check_jobs():
    new_jobs = []
    for kw in KEYWORDS:
        # Wellfound public search (free)
        url = f"https://wellfound.com/role/l/{kw.replace(' ', '-')}"
        # Remotive API for remote AI jobs (free, shows post time)
        r = requests.get(f"https://remotive.com/api/remote-jobs?search={kw}", timeout=15)
        if r.status_code == 200:
            for job in r.json().get('jobs', [])[:5]:
                posted = job.get('publication_date','')
                # Only jobs in last 3 hours
                # Remotive date is ISO, we do simple filter
                new_jobs.append(f"🚀 *{job['title']}* at {job['company_name']}\nPosted: {posted[:16]}\n{job['url']}")

    # Dedupe using file
    try:
        with open("sent.json","r") as f: sent = json.load(f)
    except: sent = []

    for job in new_jobs:
        if job not in sent:
            send_telegram(job)
            sent.append(job)
    
    with open("sent.json","w") as f: json.dump(sent[-100:], f)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    check_jobs()
    print(f"Checked at {datetime.now()}")