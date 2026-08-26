import ast
import concurrent.futures
from datetime import datetime, timedelta, timezone
 
import requests
 
TARGETS_FILE = "greenhouse_targets.txt"
OUTPUT_FILE = "seen_jobs.txt"
HOURS_WINDOW = 1
MAX_WORKERS = 20          # parallel requests, lower this if you start getting 429s
TIMEOUT = 15              # seconds per request
RETRIES = 2
 
 
def load_targets(path):
    """Parse tuples like ("Name", "token", "greenhouse") from the targets file."""
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
            if len(tup) == 3 and str(tup[2]).lower() == "greenhouse":
                tokens.append(tup[1])
    return tokens
 
 
def load_existing_urls(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()
 
 
def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
 
 
def is_remote(job):
    """Check job location (and title, as backup) for the word 'remote'."""
    location = job.get("location") or {}
    location_name = (location.get("name") or "").lower()
    if "remote" in location_name:
        return True
    # some boards only mention remote in the title, e.g. "Account Executive (Remote)"
    title = (job.get("title") or "").lower()
    if "remote" in title:
        return True
    return False
 
 
def fetch_recent_jobs(board_token, cutoff):
    """Return list of absolute_url for remote jobs first_published >= cutoff."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=false"
    last_err = None
    for attempt in range(RETRIES + 1):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            if resp.status_code == 404:
                return []  # board doesn't exist / no public board
            if resp.status_code == 429:
                # rate limited, back off a bit and retry
                import time
                time.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            last_err = e
            continue
    else:
        return []
 
    found = []
    for job in data.get("jobs", []):
        if not is_remote(job):
            continue
        published = parse_dt(job.get("first_published")) or parse_dt(job.get("updated_at"))
        if published and published >= cutoff:
            job_url = job.get("absolute_url")
            if job_url:
                found.append(job_url)
    return found
 
 
def main():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    tokens = load_targets(TARGETS_FILE)
    print(f"Loaded {len(tokens)} greenhouse boards from {TARGETS_FILE}")
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
        print(f"\nDone. Added {len(new_urls)} new job URLs to {OUTPUT_FILE}")
    else:
        print("\nDone. No new jobs found in the last 24 hours.")
 
 
if __name__ == "__main__":
    main()
 