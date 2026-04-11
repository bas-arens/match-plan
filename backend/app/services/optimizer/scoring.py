# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/scoring.py
# Author:  Bas Arens
# Purpose: Canonical penalty scoring shared by all solvers and the frontend.
#          Defines one source of truth for penalty values so Greedy, SA,
#          CP-SAT, and the Vue Gantt chart all report identical numbers for
#          the same schedule.
#
# Penalty components (each multiplied by its priority weight):
#   - window          : 1 per minute outside the preferred time window
#   - early           : 0.5 per minute after the window start (within window)
#   - field_pref      : 30 per match on a non-preferred field
#   - team_overlap    : 500 per pair of matches sharing a team that overlap
#   - locker_share    : 50 per pair of matches with overlapping locker windows
#                       times the number of lockers they both use
#   - locker_pref     : 30 per match whose home locker is not preferred
# ─────────────────────────────────────────────────────────────────────────────

import re

LOCKER_BUFFER_AFTER = 30

W_WINDOW       = 1      # per minute outside window
W_EARLY        = 0.5    # per minute after window start (within window)
W_FIELD_PREF   = 30     # per match on non-preferred field
W_TEAM_OVERLAP = 500    # per pair of matches with team overlap
W_LOCKER_SHARE = 50     # per pair × shared locker slot
W_LOCKER_PREF  = 30     # per match whose home locker is non-preferred


def _infer_age(team):
    m = re.search(r"JO(\d+)|MO(\d+)", team.upper())
    return int(m.group(1) or m.group(2)) if m else 100


def _locker_buffer_before(age):
    if age >= 100: return 60
    if age >= 17:  return 45
    if age >= 13:  return 40
    return 30


def _to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def score_schedule(schedule, preferences=None, priorities=None):
    """
    Canonical scoring. Mutates each schedule entry by setting its `penalty`
    field to the per-match penalty sum. Returns a dict with the total and
    per-type breakdown.

    schedule:     list of placed match dicts (see solver outputs)
    preferences:  list of team preference dicts
    priorities:   dict with keys 'lockers', 'time_windows', 'field_preference'
    """
    preferences = preferences or []
    priorities  = priorities or {}
    p_time   = priorities.get("time_windows", 1)
    p_field  = priorities.get("field_preference", 1)
    p_locker = priorities.get("lockers", 1)

    pref_by_team = {p["team"]: p for p in preferences}

    # Attach derived fields without mutating input shape beyond `penalty`
    sched = []
    for m in schedule:
        start = _to_min(m["time"])
        end   = start + m["duration"]
        age   = _infer_age(m["home"])
        lk_before = _locker_buffer_before(age)
        lk_start = m.get("locker_start")
        lk_dur   = m.get("locker_duration")
        if lk_start is None or lk_dur is None:
            lk_start = start - lk_before
            lk_dur   = end + LOCKER_BUFFER_AFTER - lk_start
        sched.append({
            "entry": m,
            "mid": m.get("match_id"),
            "home": m["home"],
            "away": m["away"],
            "start": start,
            "end": end,
            "field_id": m.get("field_id"),
            "home_locker": m.get("home_locker"),
            "away_locker": m.get("away_locker"),
            "lk_start": lk_start,
            "lk_end": lk_start + lk_dur,
        })

    # Reset per-match penalty
    for s in sched:
        s["entry"]["penalty"] = 0

    total = 0.0
    items = []

    def add(s, points, type_, label):
        nonlocal total
        total += points
        s["entry"]["penalty"] = s["entry"].get("penalty", 0) + points
        items.append({
            "type": type_,
            "match_id": s["mid"],
            "points": points,
            "label": label,
        })

    # ── Per-match: window, early, field pref, locker pref ──
    for s in sched:
        pref = pref_by_team.get(s["home"])
        if not pref:
            continue
        ws = _to_min(pref["start"])
        we = _to_min(pref["end"])

        if s["start"] < ws:
            mins = ws - s["start"]
            add(s, mins * W_WINDOW * p_time, "window",
                f'{s["home"]}: {mins} min buiten tijdvenster')
        elif s["end"] > we:
            mins = s["end"] - we
            add(s, mins * W_WINDOW * p_time, "window",
                f'{s["home"]}: {mins} min buiten tijdvenster')
        else:
            early = s["start"] - ws
            if early > 0:
                add(s, early * W_EARLY * p_time, "early",
                    f'{s["home"]}: {early} min na vroegst mogelijke start')

        pref_fids = pref.get("preferred_field_ids", []) or []
        if pref_fids and s["field_id"] not in pref_fids:
            add(s, W_FIELD_PREF * p_field, "field",
                f'{s["home"]}: niet op voorkeursveld')

        pref_lids = pref.get("preferred_locker_ids", []) or []
        if pref_lids and s["home_locker"] not in pref_lids:
            add(s, W_LOCKER_PREF * p_locker, "locker_pref",
                f'{s["home"]}: niet op voorkeurskleedkamer')

    # ── Pair-based: team overlap ──
    for i in range(len(sched)):
        for j in range(i + 1, len(sched)):
            a, b = sched[i], sched[j]
            if a["start"] < b["end"] and b["start"] < a["end"]:
                if (a["home"] in (b["home"], b["away"]) or
                        a["away"] in (b["home"], b["away"])):
                    add(a, W_TEAM_OVERLAP, "overlap",
                        f'{a["home"]} & {b["home"]}: team speelt tegelijk')

    # ── Pair-based: locker sharing ──
    for i in range(len(sched)):
        for j in range(i + 1, len(sched)):
            a, b = sched[i], sched[j]
            if not (a["lk_start"] < b["lk_end"] and b["lk_start"] < a["lk_end"]):
                continue
            a_locks = {a["home_locker"], a["away_locker"]}
            b_locks = {b["home_locker"], b["away_locker"]}
            shared = (a_locks & b_locks)
            shared.discard(None)
            if shared:
                pts = W_LOCKER_SHARE * p_locker * len(shared)
                add(a, pts, "locker",
                    f'{a["home"]} & {b["home"]}: kleedkamer gedeeld')

    return {"total": total, "items": items}
