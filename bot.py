import json, os, re
from playwright.sync_api import sync_playwright

# Title keywords (relaxed - what appears in TITLE)
TITLE_KEYWORDS = ["backend", "full", "software", "sde", "developer", "engineer",
                   "node", "python", "ai", "genai", "fastapi", "django"]

# For logging only
KEYWORDS = ["full-stack", "ai engineer", "software engineer", "backend engineer",
            "genai", "rag", "langchain", "node.js", "fastapi", "django"]

MIN_EXP = 0
MAX_EXP = 3  # <-- changed from 2 to 3

# Hard-block titles/seniority regardless of numeric experience mentioned
BLOCK_TITLES = re.compile(
    r'senior|sr\.?\s|lead|principal|manager|architect|staff engineer|director|head of',
    re.I
)

# Matches "0-2 years", "2-4 yrs", "3+ years", "3 to 5 years", "3 years",
# "0.5 years", "min 3 years" etc. Decimal part is captured so "0.5" isn't
# misread as "5".
EXP_RANGE_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:\+|-|–|to)?\s*(\d+(?:\.\d+)?)?\s*\+?\s*(?:yrs?|years?)',
    re.I
)


def send_telegram(message):
    import requests
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram creds missing, skipping send.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, data=data, timeout=15)
        if r.status_code != 200:
            print(f"Telegram send failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print("Telegram send error:", e)


def load_seen():
    try:
        with open("jobs.json", "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(s):
    with open("jobs.json", "w") as f:
        json.dump(list(s), f)


def contains_keyword(text):
    t = text.lower()
    return any(k in t for k in TITLE_KEYWORDS)


def valid_experience(text):
    """
    Reject on seniority keywords, and reject any numeric experience
    range/floor that starts above MAX_EXP.
    Accepts jobs with no experience mentioned (benefit of the doubt).
    """
    t = text.lower()

    if BLOCK_TITLES.search(t):
        return False

    min_required = None
    for m in EXP_RANGE_RE.finditer(t):
        lo = float(m.group(1))
        hi = float(m.group(2)) if m.group(2) else lo
        # take the smallest lower-bound found across all matches in the text
        if min_required is None or lo < min_required:
            min_required = lo
        # if the match itself is something like "3+ years", hi==lo, that's fine
        _ = hi  # currently unused beyond sanity, kept for future range checks

    if min_required is not None and min_required > MAX_EXP:
        return False

    return True


def dedupe_add(jobs, seen_links, title, link, source):
    """Append a job dict if link not already present, using O(1) set lookup."""
    if link in seen_links:
        return False
    jobs.append({"title": title[:150], "link": link, "source": source})
    seen_links.add(link)
    return True


def scrape():
    jobs = []
    seen_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        # 1. CUTSHORT - experience range now matches MIN_EXP-MAX_EXP
        try:
            print(f"Scraping Cutshort {MIN_EXP}-{MAX_EXP} years...")
            page.goto(
                f"https://cutshort.io/jobs?search=backend%20developer&experience={MIN_EXP}-{MAX_EXP}",
                timeout=30000,
            )
            page.wait_for_timeout(7000)
            cards = page.query_selector_all("a[href*='/job/']")
            print(f"Cutshort raw cards: {len(cards)}")
            count = 0
            for c in cards[:40]:
                try:
                    title = c.inner_text().strip().replace("\n", " | ")[:200]
                    link = c.get_attribute("href")
                    if not link or "/job/" not in link:
                        continue
                    if len(title) < 5:
                        continue
                    if not valid_experience(title):
                        continue
                    full_link = link if "http" in link else "https://cutshort.io" + link
                    if dedupe_add(jobs, seen_links, title, full_link, "Cutshort"):
                        count += 1
                except Exception:
                    continue
            print(f"Cutshort KEPT: {count}")
        except Exception as e:
            print("Cutshort err", e)

        # 2. HIRIST
        try:
            print("Scraping Hirist...")
            page.goto("https://www.hirist.tech/jobs/?search=backend%20developer", timeout=30000)
            page.wait_for_timeout(8000)
            cards = page.query_selector_all("a[href*='/j/']")
            print(f"Hirist raw cards: {len(cards)}")
            h_count = 0
            for c in cards:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if not link or len(title) < 15 or len(title) > 200:
                        continue
                    if not valid_experience(title):
                        continue
                    if not contains_keyword(title):
                        continue
                    full_link = link if "http" in link else "https://www.hirist.tech" + link
                    if dedupe_add(jobs, seen_links, title, full_link, "Hirist"):
                        h_count += 1
                except Exception:
                    continue
            print(f"Hirist KEPT: {h_count} | Total now: {len(jobs)}")
        except Exception as e:
            print("Hirist err", e)

        # 3. WELLFOUND
        try:
            print("Scraping Wellfound...")
            page.goto("https://wellfound.com/role/l/software-engineer", timeout=40000)
            page.wait_for_timeout(10000)
            cards = page.query_selector_all("a[href*='/jobs/']")
            print(f"Wellfound raw: {len(cards)}")
            w_count = 0
            for c in cards[:40]:
                try:
                    title = c.inner_text().strip()
                    link = c.get_attribute("href") or ""
                    if "/jobs/" not in link or not 10 < len(title) < 200:
                        continue
                    if not valid_experience(title):
                        continue
                    full_link = link if "http" in link else "https://wellfound.com" + link
                    if dedupe_add(jobs, seen_links, title, full_link, "Wellfound"):
                        w_count += 1
                except Exception:
                    continue
            print(f"Wellfound KEPT: {w_count} | Total now: {len(jobs)}")
        except Exception as e:
            print("Wellfound err", e)

        browser.close()

    return jobs


if __name__ == "__main__":
    seen = load_seen()
    all_jobs = scrape()

    # dedupe already mostly handled during scrape via seen_links, this is a final safety net
    unique = {j["link"]: j for j in all_jobs}.values()
    all_jobs = list(unique)

    print(f"After filter: {len(all_jobs)} jobs | Seen: {len(seen)}")
    new_jobs = [j for j in all_jobs if j["link"] not in seen]
    print(f"New: {len(new_jobs)}")

    if new_jobs:
        msg = f"🔥 *{len(new_jobs)} New Jobs ({MIN_EXP}-{MAX_EXP} Yrs)*\n\n"
        for i, job in enumerate(new_jobs[:15], 1):
            clean = job['title'].replace("\n", " ").replace("|", "-").replace("*", "")[:80]
            msg += f"{i}. {clean}\n   📍 {job['source']} | [Apply]({job['link']})\n\n"
            seen.add(job["link"])
        msg += "_Auto-checked 3 platforms_"
        send_telegram(msg)
    else:
        send_telegram(f"✅ Checked 3 platforms. Found {len(all_jobs)} jobs, 0 new. Next in 6h.")

    save_seen(seen)
