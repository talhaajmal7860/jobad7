import ast
import concurrent.futures
from datetime import datetime, timedelta, timezone

import requests

TARGETS_FILE = "workable_targets.txt"
OUTPUT_FILE = "seen_jobs.txt"
HOURS_WINDOW = 5      # Workable only exposes day-level published_on (no time), so use a day window
MAX_WORKERS = 20          # parallel requests, lower this if you start getting 429s
TIMEOUT = 15              # seconds per request
RETRIES = 2


def load_targets(path):
    """Parse tuples like ("Name", "slug", "workable") from the targets file."""
    slugs = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip().rstrip(",")
            if not line.startswith("("):
                continue
            try:
                tup = ast.literal_eval(line)
            except (ValueError, SyntaxError):
                continue
            if len(tup) == 3 and str(tup[2]).lower() == "workable":
                slugs.append(tup[1])
    return slugs


def load_existing_urls(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def parse_date(value):
    """published_on / created_at come back as 'YYYY-MM-DD' (date only, no time)."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_remote(job):
    """Check telecommuting flag first (accurate on Workable), title as backup."""
    if job.get("telecommuting") is True:
        return True
    title = (job.get("title") or "").lower()
    if "remote" in title:
        return True
    city = (job.get("city") or "").lower()
    state = (job.get("state") or "").lower()
    if "remote" in city or "remote" in state:
        return True
    return False


def fetch_recent_jobs(slug, cutoff):
    """Return list of job URLs for remote jobs published/created on/after cutoff date.

    Uses the public widget endpoint:
      https://apply.workable.com/api/v1/widget/accounts/{slug}
    which lists all jobs for that account without needing auth.
    """
    url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
    last_err = None
    for attempt in range(RETRIES + 1):
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            if resp.status_code == 404:
                return []  # account doesn't exist / no public jobs
            if resp.status_code == 429:
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
        published = parse_date(job.get("published_on")) or parse_date(job.get("created_at"))
        if published and published >= cutoff:
            shortcode = job.get("shortcode")
            if not shortcode:
                continue
            # NOTE: job.get("shortlink") does NOT include the account slug (just
            # apply.workable.com/j/{code}). We build our own URL with the slug baked in
            # so downstream (jobad7.py) can identify the company straight from the URL,
            # same as the greenhouse/ashby/lever URLs do.
            job_url = f"https://apply.workable.com/{slug}/j/{shortcode}"
            found.append(job_url)
    return found


def main():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    slugs = load_targets(TARGETS_FILE)
    print(f"Loaded {len(slugs)} workable accounts from {TARGETS_FILE}")
    print(f"Cutoff (last {HOURS_WINDOW}h, day-level): {cutoff.isoformat()}")

    existing = load_existing_urls(OUTPUT_FILE)
    print(f"{len(existing)} URLs already in {OUTPUT_FILE} (will be skipped)")

    new_urls = []
    checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_recent_jobs, slug, cutoff): slug for slug in slugs}
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
                print(f"  checked {checked}/{len(slugs)} accounts, {len(new_urls)} new so far...")

    if new_urls:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for u in new_urls:
                f.write(u + "\n")
        print(f"\nDone. Added {len(new_urls)} new job URLs to {OUTPUT_FILE}")
    else:
        print(f"\nDone. No new jobs found in the last {HOURS_WINDOW} hours.")


if __name__ == "__main__":
    main()