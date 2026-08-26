import ast
import concurrent.futures
import time
from datetime import datetime, timedelta, timezone
 
import requests
 
TARGETS_FILE = "lever_targets.txt"
OUTPUT_FILE = "seen_jobs.txt"
HOURS_WINDOW = 5
MAX_WORKERS = 20          # parallel requests, lower this if you start getting 429s
TIMEOUT = 15              # seconds per request
RETRIES = 2
 
 
def load_targets(path):
    """Parse tuples like ("Name", "token", "lever") from the targets file."""
    tokens = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip().rstrip(",")
            if not line.startswith("("):
                continue
            try:
                tup = ast.literal_eval(line)
            except (ValueError, SyntaxError):
                continue
            if len(tup) == 3 and str(tup[2]).lower() == "lever":
                tokens.append(tup[1])
    return tokens
 
 
def load_existing_urls(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()
 
 
def parse_created_at(value):
    """Lever's createdAt is epoch milliseconds (int or numeric string)."""
    if value is None:
        return None
    try:
        ms = float(value)
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    except (TypeError, ValueError):
        return None
 
 
def is_remote(posting):
    """
    Strict remote check, same philosophy as the Ashby scraper: trust the
    explicit workplaceType field first ("remote" only counts), and only
    fall back to location-text sniffing if the field is missing entirely.
    """
    workplace_type = posting.get("workplaceType")
    if workplace_type is not None:
        return str(workplace_type).strip().lower() == "remote"
 
    categories = posting.get("categories") or {}
    location = (categories.get("location") or "").lower()
    if "remote" in location:
        return True
    title = (posting.get("text") or "").lower()
    if "remote" in title:
        return True
    return False
 
 
def fetch_recent_jobs(board_token, cutoff):
    """Return list of hostedUrl for remote postings created >= cutoff."""
    url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
    data = None
    for attempt in range(RETRIES + 1):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            if resp.status_code == 404:
                return []  # no public board for this token
            if resp.status_code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception:
            continue
    if data is None or not isinstance(data, list):
        return []
 
    found = []
    for posting in data:
        if not is_remote(posting):
            continue
        created = parse_created_at(posting.get("createdAt"))
        if created and created >= cutoff:
            job_url = posting.get("hostedUrl") or posting.get("applyUrl")
            if job_url:
                found.append(job_url)
    return found
 
 
def main():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    tokens = load_targets(TARGETS_FILE)
    print(f"Loaded {len(tokens)} lever boards from {TARGETS_FILE}")
    print(f"Strict cutoff (last {HOURS_WINDOW}h): {cutoff.isoformat()}")
 
    existing = load_existing_urls(OUTPUT_FILE)
    print(f"{len(existing)} URLs already in {OUTPUT_FILE} (will be skipped)")
 
    new_urls = []
    checked = 0
 
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_recent_jobs, token, cutoff): token for token in tokens}
        for fut in concurrent.futures.as_completed(futures):
            checked += 1
            try:
                urls = fut.result()
            except Exception:
                urls = []
            for u in urls:
                if u not in existing:
                    new_urls.append(u)
                    existing.add(u)
            if checked % 250 == 0:
                print(f"  checked {checked}/{len(tokens)} boards, {len(new_urls)} new so far...")
 
    if new_urls:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for u in new_urls:
                f.write(u + "\n")
        print(f"\nDone. Added {len(new_urls)} new remote job URLs to {OUTPUT_FILE}")
    else:
        print("\nDone. No new remote jobs found in the last 24 hours.")
 
 
if __name__ == "__main__":
    main()