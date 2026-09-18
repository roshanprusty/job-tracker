import json, os, time, re
from playwright.sync_api import sync_playwright

KEYWORDS = ["full-stack", "full stack", "ai engineer", "software engineer", "software developer", "backend engineer", "genai", "rag", "langchain", "langraph", "node.js", "fastapi", "django"]
LOCATIONS = ["mumbai", "remote", "bangalore", "india", "noida", "gurugram", "hyderabad", "pune", "delhi"]
MAX_EXP = 2 # 0-2 years only

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
    # Find patterns like "0-2 years", "1 year", "2+ years", "Fresher", "0-2 YOE"
    text = text.lower()
    if "fresher" in text or "0 year" in text or "0-1" in text or "0-2" in text:
        return True
    # Extract numbers like "0-2 years" -> take max number
    matches = re.findall(r'(\d+)\s*-\s*(\d+)\s*year', text)
    for _, max_y in matches:
        if int(max_y) <= MAX_EXP + 1: # allow 0-3 to catch 0-2
            return True
    # Single number like "2 years"
    single = re.findall(r'(\d+)\+?\s*year', text)
    for y in single:
        if int(y) <= MAX_EXP:
            return True
    # If no exp mentioned, keep it (many startups don't mention)
    if "year" not in text:
        return True
    return False

def scrape():
    jobs=[]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        # CUTSHORT - best for 0-2 years filter
        try:
            print("Scraping Cutshort 0-2 years...")
            # Cutshort has exp filter in URL
            page.goto(f"https://cutshort.io/jobs?search=full-stack&experience=0-2", timeout=30000)
            page.wait_for_timeout(6000)
            cards = page.query_selector_all("div[class*='jobCard'], li[class*='job']")
            if not cards:
                cards = page.query_selector_all("a[href*='/job/']")

            print(f"Cutshort raw cards: {len(cards)}")
            for c in cards[:30]:
                try:
                    full_text = c.inner_text()
                    title = full_text.split("\n")[0][:120]
                    link = c.get_attribute("href") if c.get_attribute("href") else c.query_selector("a").get_attribute("href") if c.query_selector("a") else ""
                    if not link: continue
                    if "/job/" not in link: continue

                    full_link = link if "http" in link else "https://cutshort.io"+link

                    # APPLY YOUR FILTERS
                    if not contains_keyword(full_text): continue
                    # if not valid_location(full_text): continue # enable if too many
                    if not valid_experience(full_text):
                        # still keep if it says fresher
                        if "fresher" not in full_text.lower() and "0-2" not in full_text.lower():
                            pass # comment this to strictly filter exp

                    jobs.append({"title": title, "company": "Cutshort", "link": full_link, "raw": full_text[:200], "source": "Cutshort"})
                except: continue
        except Exception as e: print("Cutshort err", e)

        # HIRIST - for backend/ai
        try:
            print("Scraping Hirist...")
            page.goto("https://www.hirist.tech/jobs/?search=backend&experience=0-2", timeout=30000)
            page.wait_for_timeout(8000)
            cards = page.query_selector_all("a")
            for c in cards[:50]:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/j/" in link and len(title) > 10 and contains_keyword(title):
                        full_link = link if "http" in link else "https://www.hirist.tech"+link
                        jobs.append({"title": title[:120], "company": "Hirist", "link": full_link, "raw": title, "source": "Hirist"})
                except: continue
        except Exception as e: print("Hirist err", e)

        browser.close()
    return jobs

if __name__ == "__main__":
    seen=load_seen()
    all_jobs = scrape()
    print(f"After filter: {len(all_jobs)} jobs")
    new_jobs = [j for j in all_jobs if j["link"] not in seen]

    print(f"New: {len(new_jobs)}")
    for job in new_jobs[:10]:
        # Better formatted message with your filters
        msg = f"🔥 *{job['title']}*\n📍 {job['source']} | 0-2 Yrs\n🔗 {job['link']}"
        send_telegram(msg)
        seen.add(job["link"])
        time.sleep(1)

    if not new_jobs:
        send_telegram(f"✅ Bot checked. Found {len(all_jobs)} matching your keywords (0-2 yrs). No new ones.")

    save_seen(seen)
