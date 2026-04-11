# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/sa_solver.py
# Author:  Bas Arens
# Purpose: Simulated annealing scheduler that starts from the greedy solution
#          and iteratively improves it by randomly moving/swapping matches
#          between time slots and fields, accepting worse solutions with a
#          temperature-dependent probability.
#
# Classes:
#   SAScheduler — __init__, solve()
#
# Annealing parameters: T_INIT=300, T_MIN=0.5, COOLING=0.995, ITER_PER_T=40
# ─────────────────────────────────────────────────────────────────────────────

import math
import random
import re
import time
from datetime import datetime, timedelta

from app.services.sportlink import infer_field_size, infer_duration


def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


class SAScheduler:

    # Soft penalty weights
    WINDOW_PENALTY_PER_MIN  = 1
    EARLY_PREF_PER_MIN      = 0.5   # prefer earlier start within the time window
    FIELD_PREF_PENALTY      = 30
    LOCKER_BUFFER_AFTER     = 30    # minutes after match for locker use
    LOCKER_PENALTY          = 50
    WARMUP_DURATION         = 15   # minutes of warm-up before match on the same field

    # Hard constraint penalties (large, but finite so SA can escape)
    TEAM_OVERLAP_PENALTY    = 500
    FIELD_CAPACITY_PENALTY  = 500

    # Annealing schedule
    T_INIT       = 500.0
    T_MIN        = 0.3
    COOLING      = 0.998
    ITER_PER_T   = 60

    # Hard wall-clock cap — cooling schedule finishes well under this on
    # current workloads, but the cap guarantees SA is bounded.
    TIME_LIMIT   = 180  # seconds

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
        self.WINDOW_PENALTY_PER_MIN = 1   * self.priorities["time_windows"]
        self.EARLY_PREF_PER_MIN     = 0.5 * self.priorities["time_windows"]
        self.FIELD_PREF_PENALTY     = 30  * self.priorities["field_preference"]
        self.LOCKER_PENALTY         = 50  * self.priorities["lockers"]

        # --- Pre-computed lookups for speed (must be before _normalize_matches) ---
        self.field_by_id = {f["id"]: f for f in self.fields}
        self.pref_by_team = {p["team"]: p for p in self.preferences}
        self.fixed_by_team = {fs["team"]: fs for fs in self.fixed_slots}

        self.matches    = self._normalize_matches()
        self.time_slots = self._generate_time_slots()

        self.match_by_id = {m["id"]: m for m in self.matches}

        # Pre-compute which match pairs share a team (only these need overlap checks)
        self.conflict_pairs = []
        for i in range(len(self.matches)):
            for j in range(i + 1, len(self.matches)):
                m1 = self.matches[i]
                m2 = self.matches[j]
                if (m1["home"] in (m2["home"], m2["away"]) or
                        m1["away"] in (m2["home"], m2["away"])):
                    self.conflict_pairs.append((m1["id"], m2["id"]))

        # Number of locker slots (each match needs 2: home + away)
        self.num_lockers = len(self.lockers)

        # Calibrated per-pair locker weight: 2 * LOCKER_PENALTY / num_lockers
        self._locker_pair_weight = 2.0 * self.LOCKER_PENALTY / max(self.num_lockers, 1)

        # Pre-compute time slot minutes
        self.time_slot_mins = [to_min(t) for t in self.time_slots]

        # Pre-compute window-aligned slots per match (for biased moves)
        self.window_slots = {}   # mid → list of slot-minutes within/near the window
        for m in self.matches:
            ws = to_min(m["preferred"]["start"])
            we = to_min(m["preferred"]["end"])
            dur = m["duration"]
            # Slots where match starts inside window and ends inside window
            self.window_slots[m["id"]] = [
                t for t in self.time_slot_mins
                if ws <= t and t + dur <= we
            ] or [
                # Fallback: slots where start is within ±30 min of window
                t for t in self.time_slot_mins
                if ws - 30 <= t <= we
            ]

    # ------------------------------------------------------------------
    # NORMALISATION  (same as greedy)
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
        return self.pref_by_team.get(team)

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
    # PER-MATCH COST  (independent penalties for a single match)
    # ------------------------------------------------------------------

    def _match_cost(self, mid, fid, start):
        """Cost contributions that depend only on this match's placement."""
        match = self.match_by_id[mid]
        end = start + match["duration"]
        cost = 0.0

        # Time window penalty + earliness preference
        ws = to_min(match["preferred"]["start"])
        we = to_min(match["preferred"]["end"])
        if start < ws:
            cost += (ws - start) * self.WINDOW_PENALTY_PER_MIN
        elif end > we:
            cost += (end - we) * self.WINDOW_PENALTY_PER_MIN
        else:
            cost += (start - ws) * self.EARLY_PREF_PER_MIN

        # Field preference penalty
        pref = self._get_preference(match["home"])
        if pref:
            preferred_ids = pref.get("preferred_field_ids", [])
            if preferred_ids and fid not in preferred_ids:
                cost += self.FIELD_PREF_PENALTY

        return cost

    # ------------------------------------------------------------------
    # PAIRWISE COST  (penalties between two matches)
    # ------------------------------------------------------------------

    def _pair_cost_team_overlap(self, mid1, mid2, assignment):
        """Team overlap penalty for a pair that shares a team."""
        fid1, start1 = assignment[mid1]
        fid2, start2 = assignment[mid2]
        m1 = self.match_by_id[mid1]
        m2 = self.match_by_id[mid2]
        e1 = start1 + m1["duration"]
        e2 = start2 + m2["duration"]

        if start1 < e2 and start2 < e1:
            return self.TEAM_OVERLAP_PENALTY
        return 0.0

    def _pair_cost_field(self, mid1, mid2, assignment):
        """Field capacity + warmup conflict penalty for two matches on the same field."""
        fid1, start1 = assignment[mid1]
        fid2, start2 = assignment[mid2]
        if fid1 != fid2:
            return 0.0

        m1 = self.match_by_id[mid1]
        m2 = self.match_by_id[mid2]
        e1 = start1 + m1["duration"]
        e2 = start2 + m2["duration"]
        wu1_start = start1 - self.WARMUP_DURATION
        wu2_start = start2 - self.WARMUP_DURATION
        wu1_size = self._warmup_size(m1)
        wu2_size = self._warmup_size(m2)

        cost = 0.0

        # Match vs match capacity
        if start1 < e2 and start2 < e1:
            excess = m1["field_size"] + m2["field_size"] - 1.0
            if excess > 1e-6:
                cost += self.FIELD_CAPACITY_PENALTY * excess

        # Warmup1 vs match2
        if wu1_start < e2 and start2 < start1:
            excess = wu1_size + m2["field_size"] - 1.0
            if excess > 1e-6:
                cost += self.FIELD_CAPACITY_PENALTY * excess

        # Match1 vs warmup2
        if start1 < start2 and wu2_start < e1:
            excess = m1["field_size"] + wu2_size - 1.0
            if excess > 1e-6:
                cost += self.FIELD_CAPACITY_PENALTY * excess

        # Warmup1 vs warmup2
        if wu1_start < start2 and wu2_start < start1:
            excess = wu1_size + wu2_size - 1.0
            if excess > 1e-6:
                cost += self.FIELD_CAPACITY_PENALTY * excess

        return cost

    def _pair_cost_locker(self, mid1, mid2, assignment):
        """
        Fast locker pressure approximation. Each overlapping pair adds
        a penalty calibrated to the actual locker assignment cost.

        With N concurrent matches needing 2 lockers each and L lockers,
        the actual cost is max(0, 2N - L) * LOCKER_PENALTY.
        With C(N,2) overlapping pairs, the per-pair weight should be:
            2 * LOCKER_PENALTY / L
        This tracks the real penalty closely across different concurrency
        levels without needing an expensive full locker simulation.
        """
        _, start1 = assignment[mid1]
        _, start2 = assignment[mid2]
        m1 = self.match_by_id[mid1]
        m2 = self.match_by_id[mid2]

        # Locker windows: (start - before_buffer) .. (end + after_buffer)
        lk1_start = start1 - self._locker_buffer_before(m1)
        lk1_end   = start1 + m1["duration"] + self.LOCKER_BUFFER_AFTER
        lk2_start = start2 - self._locker_buffer_before(m2)
        lk2_end   = start2 + m2["duration"] + self.LOCKER_BUFFER_AFTER

        if lk1_start < lk2_end and lk2_start < lk1_end:
            return self._locker_pair_weight
        return 0.0

    # ------------------------------------------------------------------
    # FULL COST  (used once for initial solution)
    # ------------------------------------------------------------------

    def _full_cost(self, assignment):
        """Compute total cost from scratch. Used for initial solution only."""
        cost = 0.0
        ids = list(assignment.keys())

        # Per-match costs
        for mid in ids:
            fid, start = assignment[mid]
            cost += self._match_cost(mid, fid, start)

        # Team overlap (only pre-computed conflict pairs)
        for mid1, mid2 in self.conflict_pairs:
            if mid1 in assignment and mid2 in assignment:
                cost += self._pair_cost_team_overlap(mid1, mid2, assignment)

        # Field capacity + warmup + locker pressure (all pairs)
        for i in range(len(ids)):
            fid_i, _ = assignment[ids[i]]
            for j in range(i + 1, len(ids)):
                fid_j, _ = assignment[ids[j]]
                if fid_i == fid_j:
                    cost += self._pair_cost_field(ids[i], ids[j], assignment)
                cost += self._pair_cost_locker(ids[i], ids[j], assignment)

        return cost

    # ------------------------------------------------------------------
    # DELTA COST  (fast: only recompute what changed)
    # ------------------------------------------------------------------

    def _delta_cost(self, assignment, old_assignment, changed_ids):
        """
        Compute cost difference when only `changed_ids` moved.
        Returns new_cost - old_cost (negative = improvement).
        """
        delta = 0.0
        all_ids = list(assignment.keys())

        # Per-match cost difference for changed matches
        for mid in changed_ids:
            old_fid, old_start = old_assignment[mid]
            new_fid, new_start = assignment[mid]
            delta -= self._match_cost(mid, old_fid, old_start)
            delta += self._match_cost(mid, new_fid, new_start)

        # Team overlap: only pairs involving changed matches
        for mid1, mid2 in self.conflict_pairs:
            if mid1 not in assignment or mid2 not in assignment:
                continue
            if mid1 not in changed_ids and mid2 not in changed_ids:
                continue
            # Remove old contribution
            delta -= self._pair_cost_team_overlap(mid1, mid2, old_assignment)
            # Add new contribution
            delta += self._pair_cost_team_overlap(mid1, mid2, assignment)

        # Field capacity + locker pressure: pairs involving changed matches
        for mid in changed_ids:
            new_fid, _ = assignment[mid]
            old_fid, _ = old_assignment[mid]

            for other_mid in all_ids:
                if other_mid == mid:
                    continue
                # Skip if both changed — will be counted when we process the other one
                if other_mid in changed_ids and other_mid < mid:
                    continue

                other_fid, _ = assignment[other_mid]
                old_other_fid, _ = old_assignment[other_mid]

                # Remove old field pair cost (if they were on same field)
                if old_fid == old_other_fid:
                    delta -= self._pair_cost_field(mid, other_mid, old_assignment)
                # Add new field pair cost (if they are now on same field)
                if new_fid == other_fid:
                    delta += self._pair_cost_field(mid, other_mid, assignment)

                # Locker pressure (pairwise, always checked)
                delta -= self._pair_cost_locker(mid, other_mid, old_assignment)
                delta += self._pair_cost_locker(mid, other_mid, assignment)

        return delta

    # ------------------------------------------------------------------
    # LOCKER COST
    # ------------------------------------------------------------------

    def _locker_cost(self, assignment):
        """Simulate locker assignment and return total sharing penalty."""
        placed = []
        total  = 0

        for mid, (fid, start) in sorted(assignment.items(), key=lambda x: x[1][1]):
            match     = self.match_by_id[mid]
            end       = start + match["duration"]
            lk_start  = start - self._locker_buffer_before(match)
            lk_end    = end   + self.LOCKER_BUFFER_AFTER
            lk_dur    = lk_end - lk_start

            free = [
                lk for lk in self.lockers
                if not any(
                    lk["id"] in (s["home_locker"], s["away_locker"])
                    and s["lk_start"] < lk_end
                    and s["lk_start"] + s["lk_dur"] > lk_start
                    for s in placed
                )
            ]

            # Sort free lockers so preferred ones come first
            pref = self._get_preference(match["home"])
            preferred_locker_ids = pref.get("preferred_locker_ids", []) if pref else []
            if preferred_locker_ids:
                free.sort(key=lambda lk: 0 if lk["id"] in preferred_locker_ids else 1)

            if len(free) >= 2:
                home_lk, away_lk = free[0], free[1]
                penalty = 0
            elif len(free) == 1:
                home_lk  = free[0]
                away_lk  = next(lk for lk in self.lockers if lk["id"] != home_lk["id"])
                penalty  = self.LOCKER_PENALTY
            else:
                home_lk, away_lk = self.lockers[0], self.lockers[1]
                penalty  = self.LOCKER_PENALTY * 2

            total += penalty
            placed.append({
                "home_locker": home_lk["id"],
                "away_locker": away_lk["id"],
                "lk_start":   lk_start,
                "lk_dur":     lk_dur,
            })

        return total

    # ------------------------------------------------------------------
    # INITIAL SOLUTION  (from greedy)
    # ------------------------------------------------------------------

    def _initial_assignment(self):
        from app.services.optimizer.greedy_solver import GreedyScheduler
        greedy = GreedyScheduler(
            self.raw_matches, self.fields, self.lockers,
            self.preferences, self.slot_size, fixed_slots=self.fixed_slots
        )
        result = greedy.solve()

        # Store as {match_id: (field_id, start_minutes)} for fast math
        assignment = {}
        for s in result:
            assignment[s["match_id"]] = (s["field_id"], to_min(s["time"]))

        # Fall back for any unplaced matches
        first_slot = self.time_slot_mins[0] if self.time_slot_mins else 510
        for m in self.matches:
            if m["id"] not in assignment:
                assignment[m["id"]] = (self.fields[0]["id"], first_slot)

        # Track which match IDs are fixed (never moved by SA)
        self.fixed_match_ids = set()
        for m in self.matches:
            fix = self.fixed_by_team.get(m["home"])
            if fix and fix.get("time") and fix.get("field_id"):
                self.fixed_match_ids.add(m["id"])

        return assignment

    # ------------------------------------------------------------------
    # NEIGHBOUR MOVES
    # ------------------------------------------------------------------

    def _pick_time(self, mid):
        """Pick a time slot biased toward the match's preferred window.
        70% chance: pick within/near window (favoring early slots).
        30% chance: pick any slot (exploration)."""
        if random.random() < 0.7:
            slots = self.window_slots.get(mid)
            if slots:
                # Bias toward earlier slots: pick from the first half 60% of the time
                half = max(1, len(slots) // 2)
                if random.random() < 0.6:
                    return random.choice(slots[:half])
                return random.choice(slots)
        return random.choice(self.time_slot_mins)

    def _neighbor(self, assignment):
        new = dict(assignment)
        # Weighted move selection: time moves are most valuable
        r = random.random()
        if r < 0.40:
            move = "time"
        elif r < 0.55:
            move = "early"
        elif r < 0.70:
            move = "field"
        elif r < 0.85:
            move = "swap"
        else:
            move = "both"

        movable = [mid for mid in new if mid not in self.fixed_match_ids]

        if not movable:
            return new, set()

        if move == "time":
            mid = random.choice(movable)
            fid, _ = new[mid]
            new[mid] = (fid, self._pick_time(mid))
            return new, {mid}

        elif move == "early":
            # Move match to the earliest slot in its window
            mid = random.choice(movable)
            fid, _ = new[mid]
            slots = self.window_slots.get(mid)
            if slots:
                new[mid] = (fid, slots[0])
            else:
                new[mid] = (fid, self._pick_time(mid))
            return new, {mid}

        elif move == "field":
            mid = random.choice(movable)
            _, start = new[mid]
            new[mid] = (random.choice(self.fields)["id"], start)
            return new, {mid}

        elif move == "both":
            mid = random.choice(movable)
            new[mid] = (random.choice(self.fields)["id"], self._pick_time(mid))
            return new, {mid}

        elif move == "swap" and len(movable) >= 2:
            m1, m2 = random.sample(movable, 2)
            new[m1], new[m2] = new[m2], new[m1]
            return new, {m1, m2}

        return new, set()

    # ------------------------------------------------------------------
    # LOCKER ASSIGNMENT  (same logic as greedy)
    # ------------------------------------------------------------------

    def _assign_lockers(self, start_min, duration, placed, match=None):
        end_min        = start_min + duration
        before         = self._locker_buffer_before(match) if match else 45
        lk_start       = start_min - before
        lk_end         = end_min   + self.LOCKER_BUFFER_AFTER
        lk_duration    = lk_end - lk_start

        free = [
            lk for lk in self.lockers
            if not any(
                lk["id"] in (s["home_locker"], s["away_locker"])
                and s["locker_start"] < lk_end
                and s["locker_start"] + s["locker_duration"] > lk_start
                for s in placed
            )
        ]

        # Sort free lockers so preferred ones come first
        if match:
            pref = self._get_preference(match["home"])
            preferred_ids = pref.get("preferred_locker_ids", []) if pref else []
            if preferred_ids:
                free.sort(key=lambda lk: 0 if lk["id"] in preferred_ids else 1)

        penalty = 0
        if len(free) >= 2:
            home_lk, away_lk = free[0], free[1]
        elif len(free) == 1:
            home_lk = free[0]
            away_lk = next(lk for lk in self.lockers if lk["id"] != home_lk["id"])
            penalty = self.LOCKER_PENALTY
        else:
            home_lk, away_lk = self.lockers[0], self.lockers[1]
            penalty = self.LOCKER_PENALTY * 2

        return {
            "home_locker":    home_lk["id"],
            "away_locker":    away_lk["id"],
            "locker_start":   lk_start,
            "locker_duration": lk_duration,
            "locker_penalty": penalty,
        }

    # ------------------------------------------------------------------
    # CONVERT ASSIGNMENT → FULL SCHEDULE
    # ------------------------------------------------------------------

    def _build_schedule(self, assignment):
        placed = []
        for mid, (fid, start) in sorted(assignment.items(), key=lambda x: x[1][1]):
            match = self.match_by_id[mid]
            field = self.field_by_id.get(fid)
            lockers = self._assign_lockers(start, match["duration"], placed, match)

            # Convert minutes back to HH:MM
            h, m = divmod(start, 60)
            time_str = f"{h:02d}:{m:02d}"

            entry = {
                "match_id":        mid,
                "home":            match["home"],
                "away":            match["away"],
                "field_id":        fid,
                "field_name":      field["name"] if field else str(fid),
                "time":            time_str,
                "duration":        match["duration"],
                "field_size":      match["field_size"],
                "warmup_size":     self._warmup_size(match),
                "warmup_duration": self.WARMUP_DURATION,
                "home_locker":     lockers["home_locker"],
                "away_locker":     lockers["away_locker"],
                "locker_start":    lockers["locker_start"],
                "locker_duration": lockers["locker_duration"],
                "penalty":         lockers["locker_penalty"],
            }
            placed.append(entry)

        return placed

    # ------------------------------------------------------------------
    # POST-SA POLISH: try shifting each match earlier
    # ------------------------------------------------------------------

    def _polish(self, assignment, cost):
        """
        Greedy sweep: for each non-fixed match, try every earlier time slot
        (earliest first) on each field. Keep the first move that lowers cost.
        Repeat until no improvement is found.
        """
        improved = True
        passes = 0
        while improved:
            improved = False
            passes += 1
            for m in self.matches:
                mid = m["id"]
                if mid in self.fixed_match_ids:
                    continue

                cur_fid, cur_start = assignment[mid]

                # Candidate slots: all times earlier than current, plus current
                # time on other fields — sorted earliest first
                candidates = []
                for t in self.time_slot_mins:
                    if t >= cur_start:
                        break
                    for f in self.fields:
                        candidates.append((f["id"], t))
                # Also try current time on different fields
                for f in self.fields:
                    if f["id"] != cur_fid:
                        candidates.append((f["id"], cur_start))

                for fid, t in candidates:
                    old = assignment.copy()
                    assignment[mid] = (fid, t)
                    delta = self._delta_cost(assignment, old, {mid})
                    if delta < -0.01:
                        cost += delta
                        improved = True
                        break  # move to next match
                    else:
                        assignment[mid] = (cur_fid, cur_start)

        # Resync cost after all moves
        cost = self._full_cost(assignment)
        print(f"  Polish: {passes} passes")
        return assignment, cost

    # ------------------------------------------------------------------
    # MAIN SOLVE
    # ------------------------------------------------------------------

    def solve(self):
        n_steps = int(math.log(self.T_MIN / self.T_INIT) / math.log(self.COOLING))

        current      = self._initial_assignment()
        current_cost = self._full_cost(current)
        best         = dict(current)
        best_cost    = current_cost
        initial_cost = current_cost

        print(f"\n{'='*55}")
        print(f"  SIMULATED ANNEALING — {len(self.matches)} matches")
        print(f"  T: {self.T_INIT} → {self.T_MIN}  |  "
              f"steps/restart: {n_steps}  |  evals/restart: {n_steps * self.ITER_PER_T:,}")
        print(f"  Time limit: {self.TIME_LIMIT}s")
        print(f"  Starting cost (greedy): {initial_cost:.1f}")
        print(f"{'='*55}")
        print(f"  {'restart':>7s}  {'time':>7s}  {'T_end':>8s}  {'cur':>9s}  {'best':>9s}")
        print(f"  {'-'*7}  {'-'*7}  {'-'*8}  {'-'*9}  {'-'*9}")

        RESYNC_EVERY = 50  # full cost recalc every N temperature steps
        start_time = time.perf_counter()
        deadline = start_time + self.TIME_LIMIT
        restart = 0
        interrupted = False

        # Outer restart loop: reheat from best until the deadline. Each
        # restart reuses the best-so-far as its starting state but resets
        # the temperature, so SA re-explores around the current champion.
        while time.perf_counter() < deadline:
            restart += 1
            current = dict(best)
            current_cost = best_cost
            T = self.T_INIT
            step = 0

            while T > self.T_MIN:
                if time.perf_counter() > deadline:
                    interrupted = True
                    break
                for _ in range(self.ITER_PER_T):
                    neighbor, changed_ids = self._neighbor(current)

                    if not changed_ids:
                        continue

                    delta = self._delta_cost(neighbor, current, changed_ids)

                    if delta < 0 or random.random() < math.exp(-delta / T):
                        current      = neighbor
                        current_cost += delta

                        if current_cost < best_cost:
                            best      = dict(current)
                            best_cost = current_cost

                T *= self.COOLING
                step += 1

                # Periodic full recalc to correct floating-point drift
                if step % RESYNC_EVERY == 0:
                    current_cost = self._full_cost(current)
                    full_best = self._full_cost(best)
                    if full_best < best_cost:
                        best_cost = full_best

            elapsed = time.perf_counter() - start_time
            print(f"  {restart:>7d}  {elapsed:>6.1f}s  {T:>8.2f}  "
                  f"{current_cost:>9.1f}  {best_cost:>9.1f}")

            if interrupted:
                break

        improvement = initial_cost - best_cost
        print(f"  SA cost: {initial_cost:.1f} → {best_cost:.1f}  "
              f"(improved by {improvement:.1f}, {restart} restart{'s' if restart != 1 else ''})")

        # ── Post-SA polish: greedy sweep ──
        best, best_cost = self._polish(best, best_cost)

        total_improvement = initial_cost - best_cost
        print(f"  Final cost: {best_cost:.1f}  "
              f"(total improvement: {total_improvement:.1f})")
        print(f"{'='*55}\n")

        return self._build_schedule(best)
