import requests, json, os, time
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import send_telegram

KEYWORDS = ["full-stack", "full stack", "ai engineer", "software engineer", "software developer", "backend engineer", "genai", "rag", "langchain", "langraph", "node.js", "fastapi", "Django"]
LOCATIONS = ["mumbai", "remote", "bangalore", "india", "noida", "gurugram", "hyderabad"]

def contains_keyword(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)

def load_seen():
    try:
        with open("jobs.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open("jobs.json", "w") as f:
        json.dump(list(seen), f)

def scrape_wellfound():
    jobs = []
    try:
        url = "https://wellfound.com/role/l/full-stack-engineer"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Wellfound loads via JS, so we fallback to parsing links
        for a in soup.find_all("a", href=True)[:30]:
            if "/jobs/" in a["href"]:
                title = a.get_text(strip=True)
                if contains_keyword(title):
                    jobs.append({"title": title, "company": "Wellfound Startup", "link": "https://wellfound.com"+a["href"] if a["href"].startswith("/") else a["href"], "source": "Wellfound"})
        time.sleep(5)
    except Exception as e:
        print("Wellfound error", e)
    return jobs

def scrape_cutshort():
    jobs = []
    try:
        url = "https://cutshort.io/jobs?search=full-stack"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.find_all("a", href=True)[:30]:
            text = div.get_text(strip=True)
            if contains_keyword(text) and len(text) > 10:
                jobs.append({"title": text[:100], "company": "Cutshort", "link": div["href"] if "http" in div["href"] else "https://cutshort.io"+div["href"], "source": "Cutshort"})
        time.sleep(5)
    except Exception as e:
        print("Cutshort error", e)
    return jobs

def scrape_hirist():
    jobs = []
    try:
        url = "https://www.hirist.tech/jobs/?search=full+stack"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True)[:30]:
            title = a.get_text(strip=True)
            if contains_keyword(title) and len(title) > 10:
                jobs.append({"title": title[:100], "company": "Hirist Company", "link": a["href"] if "http" in a["href"] else "https://www.hirist.tech"+a["href"], "source": "Hirist"})
        time.sleep(5)
    except Exception as e:
        print("Hirist error", e)
    return jobs

if __name__ == "__main__":
    seen = load_seen()
    all_jobs = scrape_wellfound() + scrape_cutshort() + scrape_hirist()
    
    new_jobs = []
    for job in all_jobs:
        job_id = job["link"]
        if job_id not in seen:
            new_jobs.append(job)
            seen.add(job_id)

    save_seen(seen)
    
    if new_jobs:
        for job in new_jobs[:10]:  # Send only 10 to avoid spam
            msg = f"🔥 *{job['title']}*\n🏢 {job['company']}\n📍 {job['source']}\n🔗 {job['link']}"
            send_telegram(msg)
            time.sleep(2)
        print(f"Sent {len(new_jobs)} jobs")
    else:
        print("No new jobs")
