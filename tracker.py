import requests, json, os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENT_FILE = "sent.json"

def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE,'r') as f: return set(json.load(f))
        except: return set()
    return set()

def save_sent(s): 
    with open(SENT_FILE,'w') as f: json.dump(list(s), f)

def send_tg(msg):
    print(f"Sending to {CHAT_ID}...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    print(f"Telegram Response: {r.status_code} - {r.text}") # THIS WILL SHOW ERROR
    return r.ok

def main():
    sent = load_sent()
    print(f"Loaded {len(sent)} sent")
    new_count=0
    try:
        r = requests.get("https://remotive.com/api/remote-jobs?search=full%20stack", timeout=15).json()
        for job in r.get('jobs', [])[:5]:
            jid = str(job['id'])
            if jid in sent: continue
            msg = f"🚀 {job['title']} at {job['company_name']}\n{job['url']}"
            ok = send_tg(msg)
            if ok:
                sent.add(jid)
                new_count+=1
    except Exception as e:
        print(f"Error: {e}")
    save_sent(sent)
    print(f"Done. Checked at {datetime.now()} - Sent {new_count}")

if __name__ == "__main__":
    main()
