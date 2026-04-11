"""
Benchmark script: runs every solver 3 times and prints average runtime and
canonical total penalty. CP-SAT is capped by its time_limit parameter.
"""
import asyncio
import time
import statistics
import sys

# Force UTF-8 on stdout/stderr so emojis in solver logs don't crash the
# benchmark when output is redirected to a file on Windows (cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.core.config import settings as app_settings
from app.services.optimizer.load_settings import load_all_settings
from app.services.sportlink import (
    get_matches_for_date, get_home_match_dates, get_all_matches, get_club_info,
)
from app.services.optimizer.greedy_solver import GreedyScheduler
from app.services.optimizer.sa_solver import SAScheduler
from app.services.optimizer.cpsat_solver import CPSATScheduler
from app.services.optimizer.scoring import score_schedule


TIME_LIMIT_S = 180
REPEATS      = 3


async def pick_date():
    """Pick the date with the most matches in the feed (home-match filter
    returns empty in this environment, so fall back to raw match dates)."""
    dates = await get_home_match_dates()
    candidates = dates
    if not candidates:
        raw = await get_all_matches()
        seen = set()
        for m in raw or []:
            dt = m.get("wedstrijddatum", "")
            if dt:
                seen.add(dt.split("T")[0])
        candidates = sorted(seen)
    if not candidates:
        raise RuntimeError("No match dates found in feed")
    best, best_n = None, 0
    for d in candidates:
        matches = await get_matches_for_date(d)
        if len(matches) > best_n:
            best_n = len(matches)
            best = d
    return best, best_n


def run_greedy(matches, settings_dict, date):
    solver = GreedyScheduler(
        matches,
        settings_dict["fields"],
        settings_dict["lockers"],
        settings_dict["preferences"],
        fixed_slots=settings_dict.get("fixed_slots", []),
        priorities=settings_dict.get("priorities"),
    )
    return solver.solve()


def run_sa(matches, settings_dict, date):
    solver = SAScheduler(
        matches,
        settings_dict["fields"],
        settings_dict["lockers"],
        settings_dict["preferences"],
        fixed_slots=settings_dict.get("fixed_slots", []),
        priorities=settings_dict.get("priorities"),
    )
    return solver.solve()


def run_cpsat(matches, settings_dict, date):
    solver = CPSATScheduler(
        matches,
        settings_dict["fields"],
        settings_dict["lockers"],
        settings_dict["preferences"],
        fixed_slots=settings_dict.get("fixed_slots", []),
        priorities=settings_dict.get("priorities"),
        time_limit=TIME_LIMIT_S,
    )
    return solver.solve()


SOLVERS = [
    ("greedy", run_greedy),
    ("sa",     run_sa),
    ("cpsat",  run_cpsat),
]


async def main():
    # FastAPI lifespan populates CLUB_CODE at startup; do it manually here.
    if not app_settings.CLUB_CODE:
        info = await get_club_info()
        app_settings.CLUB_NAME = info["club_name"]
        app_settings.CLUB_CODE = info["club_code"]
        print(f"Club: {app_settings.CLUB_NAME} ({app_settings.CLUB_CODE})")

    settings_dict = load_all_settings()
    date, n_matches = await pick_date()
    print(f"\nBenchmark date: {date}  ({n_matches} matches)")
    print(f"Time limit per run: {TIME_LIMIT_S}s")
    print(f"Repeats per solver: {REPEATS}\n")

    matches = await get_matches_for_date(date)
    preferences = settings_dict["preferences"]
    priorities  = settings_dict.get("priorities")

    results = {}
    for name, runner in SOLVERS:
        times = []
        penalties = []
        for r in range(REPEATS):
            print(f"-- {name} run {r+1}/{REPEATS} --")
            t0 = time.perf_counter()
            try:
                sched = runner(matches, settings_dict, date)
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {e}")
                sched = []
            dt = time.perf_counter() - t0
            score = score_schedule(sched, preferences=preferences, priorities=priorities)
            times.append(dt)
            penalties.append(score["total"])
            # Per-type breakdown
            by_type = {}
            for item in score["items"]:
                by_type[item["type"]] = by_type.get(item["type"], 0) + item["points"]
            bd = "  ".join(f"{t}={pts:.0f}" for t, pts in sorted(by_type.items()))
            print(f"  time: {dt:.2f}s  |  penalty: {score['total']:.1f}  |  matches: {len(sched)}")
            print(f"  breakdown: {bd}")
        results[name] = {
            "avg_time": statistics.mean(times),
            "avg_penalty": statistics.mean(penalties),
            "times": times,
            "penalties": penalties,
        }

    print("\n" + "=" * 60)
    print(f"{'SOLVER':<10}{'avg time (s)':>14}{'avg penalty':>15}{'best penalty':>15}")
    print("-" * 60)
    for name, r in results.items():
        print(f"{name:<10}{r['avg_time']:>14.2f}{r['avg_penalty']:>15.1f}{min(r['penalties']):>15.1f}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
