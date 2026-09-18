# import requests, json, os, time
# from bs4 import BeautifulSoup
# from datetime import datetime
# from telegram import send_telegram

# KEYWORDS = ["full-stack", "full stack", "ai engineer", "software engineer", "software developer", "backend engineer", "genai", "rag", "langchain", "langraph", "node.js", "fastapi", "Django"]
# LOCATIONS = ["mumbai", "remote", "bangalore", "india", "noida", "gurugram", "hyderabad"]

# def contains_keyword(text):
#     text = text.lower()
#     return any(k in text for k in KEYWORDS)

# def load_seen():
#     try:
#         with open("jobs.json", "r") as f:
#             return set(json.load(f))
#     except:
#         return set()

# def save_seen(seen):
#     with open("jobs.json", "w") as f:
#         json.dump(list(seen), f)

# def scrape_wellfound():
#     jobs = []
#     try:
#         url = "https://wellfound.com/role/l/full-stack-engineer"
#         headers = {"User-Agent": "Mozilla/5.0"}
#         r = requests.get(url, headers=headers, timeout=15)
#         soup = BeautifulSoup(r.text, "html.parser")
#         # Wellfound loads via JS, so we fallback to parsing links
#         for a in soup.find_all("a", href=True)[:30]:
#             if "/jobs/" in a["href"]:
#                 title = a.get_text(strip=True)
#                 if contains_keyword(title):
#                     jobs.append({"title": title, "company": "Wellfound Startup", "link": "https://wellfound.com"+a["href"] if a["href"].startswith("/") else a["href"], "source": "Wellfound"})
#         time.sleep(5)
#     except Exception as e:
#         print("Wellfound error", e)
#     return jobs

# def scrape_cutshort():
#     jobs = []
#     try:
#         url = "https://cutshort.io/jobs?search=full-stack"
#         headers = {"User-Agent": "Mozilla/5.0"}
#         r = requests.get(url, headers=headers, timeout=15)
#         soup = BeautifulSoup(r.text, "html.parser")
#         for div in soup.find_all("a", href=True)[:30]:
#             text = div.get_text(strip=True)
#             if contains_keyword(text) and len(text) > 10:
#                 jobs.append({"title": text[:100], "company": "Cutshort", "link": div["href"] if "http" in div["href"] else "https://cutshort.io"+div["href"], "source": "Cutshort"})
#         time.sleep(5)
#     except Exception as e:
#         print("Cutshort error", e)
#     return jobs

# def scrape_hirist():
#     jobs = []
#     try:
#         url = "https://www.hirist.tech/jobs/?search=full+stack"
#         headers = {"User-Agent": "Mozilla/5.0"}
#         r = requests.get(url, headers=headers, timeout=15)
#         soup = BeautifulSoup(r.text, "html.parser")
#         for a in soup.find_all("a", href=True)[:30]:
#             title = a.get_text(strip=True)
#             if contains_keyword(title) and len(title) > 10:
#                 jobs.append({"title": title[:100], "company": "Hirist Company", "link": a["href"] if "http" in a["href"] else "https://www.hirist.tech"+a["href"], "source": "Hirist"})
#         time.sleep(5)
#     except Exception as e:
#         print("Hirist error", e)
#     return jobs

# if __name__ == "__main__":
#     seen = load_seen()
#     all_jobs = scrape_wellfound() + scrape_cutshort() + scrape_hirist()
    
#     new_jobs = []
#     for job in all_jobs:
#         job_id = job["link"]
#         if job_id not in seen:
#             new_jobs.append(job)
#             seen.add(job_id)

#     save_seen(seen)
    
#     if new_jobs:
#         for job in new_jobs[:10]:  # Send only 10 to avoid spam
#             msg = f"🔥 *{job['title']}*\n🏢 {job['company']}\n📍 {job['source']}\n🔗 {job['link']}"
#             send_telegram(msg)
#             time.sleep(2)
#         print(f"Sent {len(new_jobs)} jobs")
#     else:
#         print("No new jobs")


import requests, json, os, time
from telegram import send_telegram

def load_seen():
    try:
        with open("jobs.json","r") as f: return set(json.load(f))
    except: return set()

def save_seen(s):
    with open("jobs.json","w") as f: json.dump(list(s),f)

def scrape_hirist():
    jobs=[]
    try:
        url = "https://gladiator.hirist.tech/job/search"
        # Real payload Hirist uses
        payload = {
            "query": "full stack ai",
            "locations": [],
            "experience": [],
            "jobType": [],
            "page": 1,
            "limit": 20
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Origin": "https://www.hirist.tech",
            "Referer": "https://www.hirist.tech/"
        }
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        print("Hirist status:", r.status_code)
        data = r.json()
        print("Hirist raw keys:", data.keys())
        for j in data.get("jobs", data.get("data", []))[:20]:
            title = j.get("title","")
            comp = j.get("companyName", j.get("company",""))
            jid = j.get("id") or j.get("_id")
            link = f"https://www.hirist.tech/j/{jid}" if jid else "https://www.hirist.tech"
            jobs.append({"title":title, "company":comp, "link":link, "source":"Hirist"})
    except Exception as e:
        print("Hirist error:", e)
    return jobs

def scrape_cutshort():
    jobs=[]
    try:
        # Cutshort public search API
        url = "https://cutshort.io/api/jobs/search"
        params = {"keyword": "full stack ai", "page": 1}
        r = requests.get(url, params=params, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        print("Cutshort status:", r.status_code)
        data = r.json()
        for j in data.get("jobs", [])[:20]:
            jobs.append({"title":j.get("title",""), "company":j.get("company_name",""), "link":f"https://cutshort.io/job/{j.get('id','')}", "source":"Cutshort"})
    except Exception as e:
        print("Cutshort error:", e)
        # Fallback mock to test notification flow
        jobs.append({"title":"Full-Stack AI Engineer - TEST", "company":"TestCo", "link":"https://cutshort.io/job/test-123", "source":"Cutshort"})
    return jobs

if __name__ == "__main__":
    seen=load_seen()
    all_jobs = scrape_hirist() + scrape_cutshort()
    print(f"Found {len(all_jobs)} jobs")

    new_jobs = [j for j in all_jobs if j["link"] not in seen]

    if new_jobs:
        for job in new_jobs[:10]:
            msg = f"🔥 *{job['title']}*\n🏢 {job['company']}\n🔗 {job['link']}\n📍 {job['source']}"
            send_telegram(msg)
            seen.add(job["link"])
            time.sleep(1)
    else:
        if all_jobs:
            send_telegram(f"Found {len(all_jobs)} jobs but all seen already. Bot working fine!")
        else:
            send_telegram("✅ Bot connected but API returned 0 — need to update API payload. Check Actions logs.")

    save_seen(seen)
