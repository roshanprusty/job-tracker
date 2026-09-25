import json, os, time, re
from playwright.sync_api import sync_playwright

KEYWORDS = ["full-stack", "full stack", "ai engineer", "software engineer", "software developer", "backend engineer", "genai", "rag", "langchain", "langraph", "node.js", "fastapi", "django"]
LOCATIONS = ["mumbai", "remote", "bangalore", "india", "noida", "gurugram", "hyderabad", "pune", "delhi"]
MAX_EXP = 2

def send_telegram(message):
    import requests
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, data=data, timeout=10)

def load_seen():
    try:
        with open("jobs.json","r") as f: return set(json.load(f))
    except: return set()

def save_seen(s):
    with open("jobs.json","w") as f: json.dump(list(s), f)

def contains_keyword(text):
    text = text.lower()
    return any(k.lower() in text for k in KEYWORDS)

def valid_location(text):
    text = text.lower()
    return any(loc in text for loc in LOCATIONS)

def valid_experience(text):
    text = text.lower()
    if "fresher" in text or "0 year" in text or "0-1" in text or "0-2" in text or "0 - 2" in text:
        return True
    matches = re.findall(r'(\d+)\s*-\s*(\d+)\s*year', text)
    for _, max_y in matches:
        if int(max_y) <= MAX_EXP + 1:
            return True
    single = re.findall(r'(\d+)\+?\s*year', text)
    for y in single:
        if int(y) <= MAX_EXP:
            return True
    if "year" not in text:
        return True
    return False

def scrape():
    jobs=[]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        # 1. CUTSHORT - DON'T filter strictly here
        try:
            print("Scraping Cutshort 0-2 years...")
            page.goto(f"https://cutshort.io/jobs?search=backend%20developer&experience=0-2", timeout=30000)
            page.wait_for_timeout(7000)
            cards = page.query_selector_all("a[href*='/job/']")
            print(f"Cutshort raw cards: {len(cards)}")
            count=0
            for c in cards[:30]:
                try:
                    title = c.inner_text().strip().replace("\n"," | ")[:150]
                    link = c.get_attribute("href")
                    if not link or "/job/" not in link: continue
                    full_link = link if "http" in link else "https://cutshort.io"+link
                    # ONLY check if title is not empty - NO keyword filter for Cutshort
                    if len(title) < 5: continue
                    # Keep all 0-2 jobs from Cutshort
                    jobs.append({"title": title, "link": full_link, "source": "Cutshort"})
                    count+=1
                except: continue
            print(f"Cutshort KEPT: {count}")
        except Exception as e: print("Cutshort err", e)

        # 2. HIRIST
        try:
            print("Scraping Hirist...")
            page.goto("https://www.hirist.tech/jobs/?search=backend&experience=0-2", timeout=30000)
            page.wait_for_timeout(8000)
            # Hirist loads via API - get all links
            cards = page.query_selector_all("a")
            h_count=0
            for c in cards:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/j/" in link and len(title) > 15 and len(title) < 200:
                        # Light filter only
                        if any(k in title.lower() for k in ["backend","full","software","developer","engineer","node","python","ai"]):
                            full_link = link if "http" in link else "https://www.hirist.tech"+link
                            if full_link not in [j["link"] for j in jobs]:
                                jobs.append({"title": title[:150], "link": full_link, "source": "Hirist"})
                                h_count+=1
                except: continue
            print(f"Hirist KEPT: {h_count} | Total now: {len(jobs)}")
        except Exception as e: print("Hirist err", e)

        # 3. WELLFOUND
        try:
            print("Scraping Wellfound...")
            page.goto("https://wellfound.com/role/l/software-engineer", timeout=40000)
            page.wait_for_timeout(10000)
            cards = page.query_selector_all("a[href*='/jobs/']")
            w_count=0
            for c in cards[:40]:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/jobs/" not in link or len(title) < 10 or len(title) > 200: continue
                    full_link = link if "http" in link else "https://wellfound.com"+link
                    if full_link not in [j["link"] for j in jobs]:
                        jobs.append({"title": title[:150], "link": full_link, "source": "Wellfound"})
                        w_count+=1
                except: continue
            print(f"Wellfound KEPT: {w_count} | Total now: {len(jobs)}")
        except Exception as e: print("Wellfound err", e)

        browser.close()
    return jobs

if __name__ == "__main__":
    seen=load_seen()
    all_jobs = scrape()
    # de-dupe by link
    unique = {j["link"]: j for j in all_jobs}.values()
    all_jobs = list(unique)

    print(f"After filter: {len(all_jobs)} jobs")
    new_jobs = [j for j in all_jobs if j["link"] not in seen]

    print(f"New: {len(new_jobs)}")
    for job in new_jobs[:15]:
        msg = f"🔥 *{job['title']}*\n📍 {job['source']} | 0-2 Yrs | Mumbai/Remote\n🔗 {job['link']}"
        send_telegram(msg)
        seen.add(job["link"])
        time.sleep(1)

    if not new_jobs:
        send_telegram(f"✅ Checked 3 platforms (Cutshort, Hirist, Wellfound). Found {len(all_jobs)} matching your keywords (0-2 yrs). No new ones.")

    save_seen(seen)
