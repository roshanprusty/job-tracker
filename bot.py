import json, os, re
from playwright.sync_api import sync_playwright

KEYWORDS = ["full-stack", "full stack", "ai engineer", "software engineer", "software developer", "backend engineer", "genai", "rag", "langchain", "langraph", "node.js", "fastapi", "django"]
LOCATIONS = ["mumbai", "remote", "bangalore", "india", "noida", "gurugram", "hyderabad", "pune", "delhi"]
MAX_EXP = 3

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
    return any(k.lower() in text.lower() for k in KEYWORDS)

def valid_location(text):
    # if no location mentioned, allow it
    t = text.lower()
    if not any(x in t for x in ["mumbai","bangalore","delhi","remote","noida","pune","hyderabad","gurugram"]):
        return True
    return any(loc in t for loc in LOCATIONS)

def valid_experience(text):
    t = text.lower()
    # REJECT senior 4+ years
    if re.search(r'4\+?\s*year|5\+?\s*year|6\+?\s*year|3\s*-\s*5|4\s*-\s*6|senior|lead|manager', t):
        return False
    if "fresher" in t or "0 year" in t or "0-1" in t or "0-2" in t or "0 - 2" in t or "0-3" in t:
        return True
    matches = re.findall(r'(\d+)\s*-\s*(\d+)\s*year', t)
    for _, max_y in matches:
        if int(max_y) <= MAX_EXP + 1: # allow 0-3, 1-3 etc
            return True
    single = re.findall(r'(\d+)\+?\s*year', t)
    for y in single:
        if int(y) <= MAX_EXP:
            return True
    # If no year mentioned, ALLOW (most startup cards don't show exp)
    if "year" not in t and "yoe" not in t and "yrs" not in t:
        return True
    return False

def scrape():
    jobs=[]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        # 1. CUTSHORT - URL already has 0-2 filter
        try:
            print("Scraping Cutshort 0-2 years...")
            page.goto("https://cutshort.io/jobs?search=backend%20developer&experience=0-2", timeout=30000)
            page.wait_for_timeout(7000)
            cards = page.query_selector_all("a[href*='/job/']")
            print(f"Cutshort raw cards: {len(cards)}")
            count=0
            for c in cards[:40]:
                try:
                    title = c.inner_text().strip().replace("\n"," | ")[:200]
                    link = c.get_attribute("href")
                    if not link or "/job/" not in link: continue
                    # Filter: keyword + exp
                    if not valid_experience(title): continue
                    # Cutshort titles are short, so check keyword loosely
                    if not contains_keyword(title) and "developer" not in title.lower() and "engineer" not in title.lower():
                        continue
                    full_link = link if "http" in link else "https://cutshort.io"+link
                    if len(title) < 5: continue
                    jobs.append({"title": title[:150], "link": full_link, "source": "Cutshort"})
                    count+=1
                except: continue
            print(f"Cutshort KEPT: {count}")
        except Exception as e: print("Cutshort err", e)

        # 2. HIRIST
        try:
            print("Scraping Hirist...")
            page.goto("https://www.hirist.tech/j/Software-Engineer-Jobs-0-2-years-experience.html", timeout=30000)
            page.wait_for_timeout(8000)
            cards = page.query_selector_all("a")
            h_count=0
            for c in cards:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/j/" not in link or not 15 < len(title) < 200: continue
                    if not valid_experience(title): continue
                    if not contains_keyword(title): continue
                    if not valid_location(title): continue
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
            for c in cards[:50]:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/jobs/" not in link or not 10 < len(title) < 200: continue
                    if not valid_experience(title): continue
                    if not contains_keyword(title) and "engineer" not in title.lower(): continue
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
    unique = {j["link"]: j for j in all_jobs}.values()
    all_jobs = list(unique)

    print(f"After filter: {len(all_jobs)} jobs | Seen: {len(seen)}")
    new_jobs = [j for j in all_jobs if j["link"] not in seen]
    print(f"New: {len(new_jobs)}")

    if new_jobs:
        # ONE MESSAGE ONLY
        msg = f"🔥 *{len(new_jobs)} New Jobs (0-{MAX_EXP} Yrs)*\n\n"
        for i, job in enumerate(new_jobs[:15], 1):
            clean = job['title'].replace("\n"," ").replace("|","-").replace("*","")[:80]
            msg += f"{i}. {clean}\n   📍 {job['source']} | [Apply]({job['link']})\n\n"
            seen.add(job["link"])
        msg += f"_Filters: {', '.join(KEYWORDS[:4])}... | {len(all_jobs)} total_"
        send_telegram(msg)
    else:
        send_telegram(f"✅ Checked 3 platforms. Found {len(all_jobs)} jobs (0-{MAX_EXP} Yrs), no NEW. Next in 6 hrs.")

    save_seen(seen)
