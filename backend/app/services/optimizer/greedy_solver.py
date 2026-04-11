# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/greedy_solver.py
# Author:  Bas Arens
# Purpose: Greedy match scheduler that places the hardest matches first
#          (narrowest time window, largest field, most team conflicts) and
#          scores each candidate slot by field preference, window deviation,
#          and locker availability.
#
# Classes:
#   GreedyScheduler — __init__, solve()
#
# Key constants:
#   LOCKER_BUFFER, LOCKER_PENALTY, FIELD_PREF_PENALTY,
#   EARLY_PREF_PER_MIN, WARMUP_DURATION
# ─────────────────────────────────────────────────────────────────────────────

import re
from datetime import datetime, timedelta

from app.services.sportlink import infer_field_size, infer_duration


def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


class GreedyScheduler:

    LOCKER_BUFFER_AFTER  = 30   # minutes after match for locker use
    LOCKER_PENALTY       = 50   # penalty per forced locker share
    FIELD_PREF_PENALTY   = 30   # penalty per match on non-preferred field
    EARLY_PREF_PER_MIN   = 0.5  # penalty per minute late within time window
    WARMUP_DURATION      = 15   # minutes of warm-up before match on the same field

    DEFAULT_WINDOW = {"start": "08:00", "end": "20:00"}

    def __init__(self, matches, fields, lockers, preferences=None, slot_size=15, fixed_slots=None, priorities=None):
        self.raw_matches  = matches
        self.fields       = fields
        self.lockers      = lockers
        self.preferences  = preferences or []
        self.slot_size    = slot_size
        self.fixed_slots  = fixed_slots or []
        self.priorities   = priorities or {"lockers": 1, "time_windows": 1, "field_preference": 1}

        # Apply priority multipliers to penalty weights
        self.LOCKER_PENALTY      = 50  * self.priorities["lockers"]
        self.FIELD_PREF_PENALTY  = 30  * self.priorities["field_preference"]
        self.EARLY_PREF_PER_MIN  = 0.5 * self.priorities["time_windows"]

        # Build lookup: team → fixed slot config
        self.fixed_by_team = {fs["team"]: fs for fs in self.fixed_slots}

        self.matches    = self._normalize_matches()
        self.time_slots = self._generate_time_slots()
        self.schedule   = []

    # ------------------------------------------------------------------
    # NORMALISATION
    # ------------------------------------------------------------------

    def _infer_age(self, team):
        m = re.search(r"JO(\d+)|MO(\d+)", team.upper())
        return int(m.group(1) or m.group(2)) if m else 100

    def _locker_buffer_before(self, match):
        """Minutes before the match that lockers are occupied, based on age."""
        age = match["age"]
        if age >= 100:    return 60   # seniors
        if age >= 17:     return 45   # JO17–JO19
        if age >= 13:     return 40   # JO13–JO15
        return 30                     # JO8–JO12

    def _warmup_size(self, match):
        """1/4 field for seniors, 1/8 for juniors."""
        team = match["home"].upper()
        return 0.125 if ("JO" in team or "MO" in team) else 0.25

    def _get_preference(self, team):
        return next((p for p in self.preferences if p["team"] == team), None)

    def _get_window(self, team):
        p = self._get_preference(team)
        if p:
            return {"start": p["start"], "end": p["end"]}
        return self.DEFAULT_WINDOW

    def _normalize_matches(self):
        out = []
        for i, m in enumerate(self.raw_matches):
            home = m["thuisteam"]
            out.append({
                "id":         str(m.get("wedstrijdcode") or f"AUTO_{i}"),
                "home":       home,
                "away":       m["uitteam"],
                "duration":   infer_duration(home),
                "field_size": infer_field_size(home),
                "age":        self._infer_age(home),
                "preferred":  self._get_window(home),
            })
        return out

    def _generate_time_slots(self):
        slots = []
        start = datetime(2025, 1, 1, 8, 30)
        n_slots = (20 * 60 - (8 * 60 + 30)) // self.slot_size  # 8:30 → 20:00
        for i in range(n_slots):
            t = start + timedelta(minutes=i * self.slot_size)
            slots.append(t.strftime("%H:%M"))
        return slots

    # ------------------------------------------------------------------
    # DIFFICULTY SORT
    # Hardest matches are placed first so they get the widest choice.
    #
    # Sort key (all descending → negate for Python's ascending sort):
    #   1. Narrow preferred window  → fewer valid slots
    #   2. Large field size         → blocks more field capacity
    #   3. Many shared teams        → more conflict potential
    # ------------------------------------------------------------------

    def _difficulty(self, match):
        ws = to_min(match["preferred"]["start"])
        we = to_min(match["preferred"]["end"])
        window_width = we - ws  # smaller = harder

        shared = sum(
            1 for o in self.matches
            if o["id"] != match["id"] and (
                match["home"] in (o["home"], o["away"]) or
                match["away"] in (o["home"], o["away"])
            )
        )

        return (-window_width, -match["field_size"], -shared)

    # ------------------------------------------------------------------
    # HARD CONSTRAINT CHECKS
    # ------------------------------------------------------------------

    def _field_capacity_ok(self, match, field_id, start_min):
        end_min  = start_min + match["duration"]
        wu_start = start_min - self.WARMUP_DURATION
        wu_size  = self._warmup_size(match)

        def used_in(a, b):
            total = 0
            for s in self.schedule:
                if s["field_id"] != field_id:
                    continue
                s_start = to_min(s["time"])
                s_end   = s_start + s["duration"]
                s_wu    = s_start - self.WARMUP_DURATION
                if self._overlap(s_start, s_end, a, b):
                    total += s["field_size"]
                if self._overlap(s_wu, s_start, a, b):
                    total += s.get("warmup_size", 0)
            return total

        # Match period must not exceed capacity
        if used_in(start_min, end_min) + match["field_size"] > 1.0 + 1e-6:
            return False
        # Warm-up period must not exceed capacity
        if used_in(wu_start, start_min) + wu_size > 1.0 + 1e-6:
            return False
        return True

    def _team_overlap_ok(self, match, start_min):
        end_min = start_min + match["duration"]
        for s in self.schedule:
            if (match["home"] in (s["home"], s["away"]) or
                    match["away"] in (s["home"], s["away"])):
                if self._overlap(to_min(s["time"]), to_min(s["time"]) + s["duration"],
                                 start_min, end_min):
                    return False
        return True

    def _free_lockers(self, start_min, end_min, match=None):
        """Returns list of lockers with no booking overlapping the locker window."""
        before   = self._locker_buffer_before(match) if match else 45
        lk_start = start_min - before
        lk_end   = end_min   + self.LOCKER_BUFFER_AFTER
        free = []
        for lk in self.lockers:
            busy = any(
                lk["id"] in (s.get("home_locker"), s.get("away_locker"))
                and self._overlap(s["locker_start"],
                                  s["locker_start"] + s["locker_duration"],
                                  lk_start, lk_end)
                for s in self.schedule
            )
            if not busy:
                free.append(lk)
        return free

    def can_place(self, match, field_id, start_min):
        """True when all hard constraints pass (locker sharing is allowed)."""
        if not self._field_capacity_ok(match, field_id, start_min):
            return False
        if not self._team_overlap_ok(match, start_min):
            return False
        # Need at least 2 distinct lockers in the system for home/away
        if len(self.lockers) < 2:
            return False
        return True

    # ------------------------------------------------------------------
    # SLOT SCORING  (lower = better)
    #
    # Primary:   field preference penalty (wrong field)
    # Secondary: field already in use?   (fill fields before opening new ones)
    # Tertiary:  window penalty          (minutes outside preferred window)
    # Quaternary: earliness              (minutes from window start, prefer early)
    #
    # Using a 4-tuple makes each criterion dominant over the next.
    # ------------------------------------------------------------------

    def _slot_score(self, match, field_id, start_min):
        ws = to_min(match["preferred"]["start"])
        we = to_min(match["preferred"]["end"])

        end_min = start_min + match["duration"]
        if start_min < ws:
            window_penalty = ws - start_min
            earliness = 0
        elif end_min > we:
            window_penalty = end_min - we
            earliness = 0
        else:
            window_penalty = 0
            earliness = start_min - ws  # prefer earliest slot within window

        field_is_new = 0 if any(s["field_id"] == field_id for s in self.schedule) else 1

        # Field preference penalties
        field_penalty = 0
        pref = self._get_preference(match["home"])
        if pref:
            field = next((f for f in self.fields if f["id"] == field_id), None)
            preferred_ids = pref.get("preferred_field_ids", [])
            if preferred_ids and field_id not in preferred_ids:
                field_penalty += self.FIELD_PREF_PENALTY

        return (field_penalty, field_is_new, window_penalty, earliness)

    # ------------------------------------------------------------------
    # LOCKER ASSIGNMENT
    # ------------------------------------------------------------------

    def _assign_lockers(self, start_min, duration, match=None, force_home_locker=None):
        end_min         = start_min + duration
        before          = self._locker_buffer_before(match) if match else 45
        locker_start    = start_min - before
        locker_end      = end_min   + self.LOCKER_BUFFER_AFTER
        locker_duration = locker_end - locker_start

        free    = self._free_lockers(start_min, end_min, match)
        penalty = 0

        # Fixed locker assignment overrides preference logic
        if force_home_locker is not None:
            home_lk = next((lk for lk in self.lockers if lk["id"] == force_home_locker), None)
            if not home_lk:
                home_lk = self.lockers[0]
            remaining = [lk for lk in free if lk["id"] != home_lk["id"]]
            away_lk = remaining[0] if remaining else next(lk for lk in self.lockers if lk["id"] != home_lk["id"])
            return {
                "home_locker":     home_lk["id"],
                "away_locker":     away_lk["id"],
                "locker_start":    locker_start,
                "locker_duration": locker_duration,
                "locker_penalty":  0,
            }

        # Sort free lockers so preferred ones come first
        if match:
            pref = self._get_preference(match["home"])
            preferred_ids = pref.get("preferred_locker_ids", []) if pref else []
            if preferred_ids:
                free.sort(key=lambda lk: 0 if lk["id"] in preferred_ids else 1)

        if len(free) >= 2:
            home_lk, away_lk = free[0], free[1]

        elif len(free) == 1:
            home_lk = free[0]
            away_lk = next(lk for lk in self.lockers if lk["id"] != home_lk["id"])
            penalty += self.LOCKER_PENALTY

        else:
            home_lk = self.lockers[0]
            away_lk = self.lockers[1]
            penalty += self.LOCKER_PENALTY * 2

        return {
            "home_locker":     home_lk["id"],
            "away_locker":     away_lk["id"],
            "locker_start":    locker_start,
            "locker_duration": locker_duration,
            "locker_penalty":  penalty,
        }

    # ------------------------------------------------------------------
    # MAIN SOLVER
    # ------------------------------------------------------------------

    def solve(self):
        sorted_matches = sorted(self.matches, key=self._difficulty)

        print(f"\n{'='*55}")
        print(f"  GREEDY SOLVER — {len(sorted_matches)} matches, "
              f"{len(self.fields)} fields, {len(self.lockers)} lockers")
        print(f"{'='*55}")
        print(f"  {'#':<4} {'Match':<10} {'Home':<20} {'Window':<14} {'Size'}")
        print(f"  {'-'*60}")
        for i, m in enumerate(sorted_matches, 1):
            w = m["preferred"]
            print(f"  {i:<4} {m['id']:<10} {m['home'][:19]:<20} "
                  f"{w['start']}–{w['end']:<8} {m['field_size']}")
        print()

        total_penalty = 0

        # --- Phase 1: pre-place fixed-slot matches ---
        fixed_ids = set()
        for match in sorted_matches:
            fix = self.fixed_by_team.get(match["home"])
            if not fix:
                continue

            fixed_time     = fix.get("time")
            fixed_field_id = fix.get("field_id")
            fixed_locker   = fix.get("locker_id")

            if not fixed_time or not fixed_field_id:
                continue  # need at least time + field to pre-place

            start_min = to_min(fixed_time)
            field     = next((f for f in self.fields if f["id"] == fixed_field_id), None)
            if not field:
                continue

            lockers = self._assign_lockers(start_min, match["duration"], match,
                                           force_home_locker=fixed_locker)

            h, m = divmod(start_min, 60)
            time_slot = f"{h:02d}:{m:02d}"

            print(f"  📌 {match['id']:<10} {match['home'][:19]:<20} "
                  f"→ {field['name']:<12} {time_slot}  (FIXED)")

            self.schedule.append({
                "match_id":        match["id"],
                "home":            match["home"],
                "away":            match["away"],
                "field_id":        fixed_field_id,
                "field_name":      field["name"],
                "time":            time_slot,
                "duration":        match["duration"],
                "field_size":      match["field_size"],
                "warmup_size":     self._warmup_size(match),
                "warmup_duration": self.WARMUP_DURATION,
                "home_locker":     lockers["home_locker"],
                "away_locker":     lockers["away_locker"],
                "locker_start":    lockers["locker_start"],
                "locker_duration": lockers["locker_duration"],
                "penalty":         lockers["locker_penalty"],
            })
            fixed_ids.add(match["id"])

        # --- Phase 2: schedule remaining matches ---
        for match in sorted_matches:
            if match["id"] in fixed_ids:
                continue

            best = None  # (score_tuple, field_id, time_str)

            for t in self.time_slots:
                t_min = to_min(t)
                for f in self.fields:
                    if not self.can_place(match, f["id"], t_min):
                        continue
                    score = self._slot_score(match, f["id"], t_min)
                    if best is None or score < best[0]:
                        best = (score, f["id"], t)

            if best is None:
                print(f"  ❌ UNPLACED  {match['id']}  {match['home']} vs {match['away']}")
                continue

            score_tuple, field_id, time_slot = best
            start_min = to_min(time_slot)
            field     = next(f for f in self.fields if f["id"] == field_id)
            lockers   = self._assign_lockers(start_min, match["duration"], match)

            field_penalty, _, window_penalty, earliness = score_tuple
            total_penalty += (lockers["locker_penalty"]
                              + window_penalty * self.priorities["time_windows"]
                              + earliness * self.EARLY_PREF_PER_MIN
                              + field_penalty)

            locker_note = ""
            if lockers["locker_penalty"] > 0:
                locker_note = f"  ⚠ locker share (+{lockers['locker_penalty']})"
            window_note = ""
            if window_penalty > 0:
                window_note = f"  ⚠ {window_penalty} min outside window"

            home_lk_name = next((l["name"] for l in self.lockers if l["id"] == lockers["home_locker"]), lockers["home_locker"])
            away_lk_name = next((l["name"] for l in self.lockers if l["id"] == lockers["away_locker"]), lockers["away_locker"])

            print(f"  ✅ {match['id']:<10} {match['home'][:19]:<20} "
                  f"→ {field['name']:<12} {time_slot}  "
                  f"lockers: {home_lk_name}/{away_lk_name}"
                  f"{locker_note}{window_note}")

            self.schedule.append({
                "match_id":        match["id"],
                "home":            match["home"],
                "away":            match["away"],
                "field_id":        field_id,
                "field_name":      field["name"],
                "time":            time_slot,
                "duration":        match["duration"],
                "field_size":      match["field_size"],
                "warmup_size":     self._warmup_size(match),
                "warmup_duration": self.WARMUP_DURATION,
                "home_locker":     lockers["home_locker"],
                "away_locker":     lockers["away_locker"],
                "locker_start":    lockers["locker_start"],
                "locker_duration": lockers["locker_duration"],
                "penalty":         lockers["locker_penalty"],
            })

        placed = len(self.schedule)
        print(f"\n  {placed}/{len(sorted_matches)} placed  |  ★ GREEDY TOTAL PENALTY: {total_penalty}")
        print(f"{'='*55}\n")

        return self.schedule

    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    def _overlap(self, a1, a2, b1, b2):
        return a1 < b2 and b1 < a2
