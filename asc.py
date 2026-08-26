import ast
import concurrent.futures
import time
from datetime import datetime, timedelta, timezone
 
import requests
 
TARGETS_FILE = "ashby_targets.txt"
OUTPUT_FILE = "seen_jobs.txt"
HOURS_WINDOW = 5
MAX_WORKERS = 20          # parallel requests, lower this if you start getting 429s
TIMEOUT = 15              # seconds per request
RETRIES = 2
 
 
def load_targets(path):
    """Parse tuples like ("Name", "token", "ashby") from the targets file."""
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
            if len(tup) == 3 and str(tup[2]).lower() == "ashby":
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
        # Ashby uses ISO 8601 with "Z" suffix, fromisoformat needs +00:00
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None
 
 
def is_remote(job):
    """
    Strict remote check. Ashby's `isRemote` flag can be True even for
    Hybrid roles, so we trust `workplaceType` first (values seen:
    "Remote", "Hybrid", "InOffice") and only fall back to isRemote/location
    text when workplaceType isn't present at all.
    """
    workplace_type = job.get("workplaceType")
    if workplace_type is not None:
        return str(workplace_type).strip().lower() == "remote"
 
    # fallback only if workplaceType field is missing entirely
    if job.get("isRemote") is True:
        return True
    location = (job.get("location") or "").lower()
    if "remote" in location:
        return True
    title = (job.get("title") or "").lower()
    if "remote" in title:
        return True
    return False
 
 
def fetch_recent_jobs(board_token, cutoff):
    """Return list of jobUrl for remote jobs published >= cutoff."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}?includeCompensation=false"
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
    if data is None:
        return []
 
    found = []
    for job in data.get("jobs", []):
        if not is_remote(job):
            continue
        published = parse_dt(job.get("publishedAt")) or parse_dt(job.get("updatedAt"))
        if published and published >= cutoff:
            job_url = job.get("jobUrl") or job.get("applyUrl")
            if job_url:
                found.append(job_url)
    return found
 
 
def main():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    tokens = load_targets(TARGETS_FILE)
    print(f"Loaded {len(tokens)} ashby boards from {TARGETS_FILE}")
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