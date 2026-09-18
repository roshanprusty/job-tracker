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


import json, os, time
from playwright.sync_api import sync_playwright

def send_telegram(message):
    import requests
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
        print(f"Sent: {message[:50]}")
    except Exception as e:
        print("Telegram error", e)

def load_seen():
    try:
        with open("jobs.json","r") as f: 
            return set(json.load(f))
    except: 
        return set()

def save_seen(s):
    with open("jobs.json","w") as f: 
        json.dump(list(s), f)

def scrape_with_browser():
    jobs=[]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        # Hirist
        try:
            print("Scraping Hirist...")
            page.goto("https://www.hirist.tech/jobs/?search=full+stack+ai", timeout=30000)
            page.wait_for_timeout(8000)
            cards = page.query_selector_all("a")
            print(f"Hirist found {len(cards)} total a-tags")
            for c in cards[:40]:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/j/" in link and len(title) > 10:
                        full_link = link if "http" in link else "https://www.hirist.tech"+link
                        jobs.append({"title": title[:120], "company": "Hirist", "link": full_link, "source": "Hirist"})
                except:
                    continue
        except Exception as e:
            print("Hirist error", e)

        # Cutshort
        try:
            print("Scraping Cutshort...")
            page.goto("https://cutshort.io/jobs?search=full-stack-ai", timeout=30000)
            page.wait_for_timeout(6000)
            cards = page.query_selector_all("a[href*='/job/']")
            print(f"Cutshort found {len(cards)} links")
            for c in cards[:25]:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if len(title) > 10 and len(title) < 150:
                        full_link = link if "http" in link else "https://cutshort.io"+link
                        jobs.append({"title": title[:120], "company": "Cutshort", "link": full_link, "source": "Cutshort"})
                except:
                    continue
        except Exception as e:
            print("Cutshort error", e)

        browser.close()
    return jobs

if __name__ == "__main__":
    seen=load_seen()
    all_jobs = scrape_with_browser()
    print(f"Total scraped: {len(all_jobs)}")
    new_jobs = [j for j in all_jobs if j["link"] not in seen]
    print(f"New jobs: {len(new_jobs)}")

    if new_jobs:
        for job in new_jobs[:10]:
            msg = f"🔥 {job['title']}\n🔗 {job['link']}\n📍 {job['source']}"
            send_telegram(msg)
            seen.add(job["link"])
            time.sleep(1)
    else:
        send_telegram(f"Bot ran. Found {len(all_jobs)} total, 0 new.")

    save_seen(seen)
