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
    LOCKER_BUFFER           = 20
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

        # Pre-compute time slot minutes
        self.time_slot_mins = [to_min(t) for t in self.time_slots]

    # ------------------------------------------------------------------
    # NORMALISATION  (same as greedy)
    # ------------------------------------------------------------------

    def _infer_age(self, team):
        m = re.search(r"JO(\d+)|MO(\d+)", team.upper())
        return int(m.group(1) or m.group(2)) if m else 100

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
        a small penalty. With N concurrent matches needing 2 lockers each,
        there are C(N,2) pairs — so the penalty grows quadratically,
        naturally escalating when concurrency exceeds locker capacity.
        Scaled so that exceeding capacity (~5+ concurrent with 8 lockers)
        becomes expensive.
        """
        _, start1 = assignment[mid1]
        _, start2 = assignment[mid2]
        m1 = self.match_by_id[mid1]
        m2 = self.match_by_id[mid2]

        # Locker windows: start - buffer .. end + buffer
        lk1_start = start1 - self.LOCKER_BUFFER
        lk1_end   = start1 + m1["duration"] + self.LOCKER_BUFFER
        lk2_start = start2 - self.LOCKER_BUFFER
        lk2_end   = start2 + m2["duration"] + self.LOCKER_BUFFER

        if lk1_start < lk2_end and lk2_start < lk1_end:
            return 8.0
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
            lk_start  = start - self.LOCKER_BUFFER
            lk_end    = end   + self.LOCKER_BUFFER
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

    def _neighbor(self, assignment):
        new = dict(assignment)
        move = random.choice(["time", "field", "swap", "both"])
        movable = [mid for mid in new if mid not in self.fixed_match_ids]

        if not movable:
            return new, set()

        if move == "time":
            mid = random.choice(movable)
            fid, _ = new[mid]
            new[mid] = (fid, random.choice(self.time_slot_mins))
            return new, {mid}

        elif move == "field":
            mid = random.choice(movable)
            _, start = new[mid]
            new[mid] = (random.choice(self.fields)["id"], start)
            return new, {mid}

        elif move == "both":
            mid = random.choice(movable)
            new[mid] = (random.choice(self.fields)["id"], random.choice(self.time_slot_mins))
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
        lk_start       = start_min - self.LOCKER_BUFFER
        lk_end         = end_min   + self.LOCKER_BUFFER
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
              f"steps: {n_steps}  |  evals: {n_steps * self.ITER_PER_T:,}")
        print(f"  Starting cost (greedy): {initial_cost:.1f}")
        print(f"{'='*55}")

        T = self.T_INIT
        step = 0
        RESYNC_EVERY = 50  # full cost recalc every N temperature steps

        while T > self.T_MIN:
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

        improvement = initial_cost - best_cost
        print(f"  Cost: {initial_cost:.1f} → {best_cost:.1f}  "
              f"(improved by {improvement:.1f})")
        print(f"{'='*55}\n")

        return self._build_schedule(best)
