"""
Orchestrator: chalata hai chaaron scrapers (background threads, apne-apne
interval pe) + jobad7 ka realtime watcher (poster.py) - sab ek process me,
taake sab ek hi 'seen_jobs.txt' file share karein (Railway ke ephemeral
filesystem ke saath ye zaroori hai - alag services alag filesystem rakhte hain).
"""
import threading
import time
import traceback

import gsc
import asc
import lsc
import wsc
import poster

# Sab scrapers ab har 1 ghante (3600s) pe chalte hain.
# NOTE: gsc.HOURS_WINDOW bhi 1h hai (exactly interval ke barabar) - agar scrape
# ya deploy me thora delay ho jaye to edge-case pe koi job miss ho sakti hai.
# Agar ye risk avoid karna ho to gsc ka interval thoda kam (e.g. 50 min) rakhna behtar hai.
SCHEDULES = [
    ("greenhouse", gsc.main, 60 * 60),      # har 1h
    ("ashby", asc.main, 60 * 60),           # har 1h
    ("lever", lsc.main, 60 * 60),           # har 1h
    ("workable", wsc.main, 60 * 60),        # har 1h
]


def run_periodic(name, func, interval_seconds):
    while True:
        try:
            print(f"\n=== [{name}] scrape shuru ===", flush=True)
            func()
        except Exception:
            print(f"[{name}] scrape me error aaya:", flush=True)
            traceback.print_exc()
        time.sleep(interval_seconds)


def main():
    threads = []
    for name, func, interval in SCHEDULES:
        t = threading.Thread(target=run_periodic, args=(name, func, interval), daemon=True)
        t.start()
        threads.append(t)
        # thoda stagger kar dete hain taake sab ek saath hi na chalein
        time.sleep(5)

    print("\n✅ Chaaron scrapers background me schedule ho gaye. Ab realtime poster shuru...\n", flush=True)

    # Ye function apna khud ka infinite loop hai (Ctrl+C tak chalta rahega)
    poster.run_realtime_watcher()


if __name__ == "__main__":
    main()
