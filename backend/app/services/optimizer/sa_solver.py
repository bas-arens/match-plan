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
    FIELD_PREF_PENALTY      = 30
    SURFACE_AVOID_PENALTY   = 40
    LOCKER_BUFFER           = 20
    LOCKER_PENALTY          = 50
    LOCKER_PREF_PENALTY     = 30
    WARMUP_DURATION         = 15   # minutes of warm-up before match on the same field

    # Hard constraint penalties (large, but finite so SA can escape)
    TEAM_OVERLAP_PENALTY    = 500
    FIELD_CAPACITY_PENALTY  = 500

    # Annealing schedule
    T_INIT       = 300.0
    T_MIN        = 0.5
    COOLING      = 0.995
    ITER_PER_T   = 40

    DEFAULT_WINDOW = {"start": "08:00", "end": "20:00"}

    def __init__(self, matches, fields, lockers, preferences=None, slot_size=15):
        self.raw_matches  = matches
        self.fields       = fields
        self.lockers      = lockers
        self.preferences  = preferences or []
        self.slot_size    = slot_size

        self.matches    = self._normalize_matches()
        self.time_slots = self._generate_time_slots()

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
                "preferred":  self._get_window(home),
            })
        return out

    def _generate_time_slots(self):
        slots = []
        start = datetime(2025, 1, 1, 8, 0)
        for i in range(int(12 * 60 / self.slot_size)):
            t = start + timedelta(minutes=i * self.slot_size)
            slots.append(t.strftime("%H:%M"))
        return slots

    # ------------------------------------------------------------------
    # COST FUNCTION
    # assignment: {match_id -> (field_id, time_str)}
    # ------------------------------------------------------------------

    def _cost(self, assignment):
        cost = 0
        items = [(mid, fid, to_min(t), next(m for m in self.matches if m["id"] == mid))
                 for mid, (fid, t) in assignment.items()]

        for mid, fid, start, match in items:
            end = start + match["duration"]

            # Time window penalty
            ws = to_min(match["preferred"]["start"])
            we = to_min(match["preferred"]["end"])
            if start < ws:
                cost += (ws - start) * self.WINDOW_PENALTY_PER_MIN
            elif start > we:
                cost += (start - we) * self.WINDOW_PENALTY_PER_MIN

            # Field preference penalty
            pref = self._get_preference(match["home"])
            if pref:
                field = next((f for f in self.fields if f["id"] == fid), None)
                preferred_ids = pref.get("preferred_field_ids", [])
                avoid_surfaces = pref.get("avoid_surfaces", [])
                if preferred_ids and fid not in preferred_ids:
                    cost += self.FIELD_PREF_PENALTY
                if field and field.get("surface") in avoid_surfaces:
                    cost += self.SURFACE_AVOID_PENALTY

        # Pairwise constraints
        for i in range(len(items)):
            mid1, fid1, s1, m1 = items[i]
            e1 = s1 + m1["duration"]

            for j in range(i + 1, len(items)):
                mid2, fid2, s2, m2 = items[j]
                e2 = s2 + m2["duration"]

                overlapping = s1 < e2 and s2 < e1

                if not overlapping:
                    continue

                # Team conflict
                if (m1["home"] in (m2["home"], m2["away"]) or
                        m1["away"] in (m2["home"], m2["away"])):
                    cost += self.TEAM_OVERLAP_PENALTY

                # Field capacity conflict (match vs match)
                if fid1 == fid2:
                    excess = m1["field_size"] + m2["field_size"] - 1.0
                    if excess > 1e-6:
                        cost += self.FIELD_CAPACITY_PENALTY * excess

        # Warm-up capacity conflicts (warm-up vs match and warm-up vs warm-up)
        for i in range(len(items)):
            mid1, fid1, s1, m1 = items[i]
            wu1_start = s1 - self.WARMUP_DURATION
            wu1_size  = self._warmup_size(m1)

            for j in range(i + 1, len(items)):
                mid2, fid2, s2, m2 = items[j]
                if fid1 != fid2:
                    continue
                e2        = s2 + m2["duration"]
                wu2_start = s2 - self.WARMUP_DURATION
                wu2_size  = self._warmup_size(m2)

                def ov(a1, a2, b1, b2): return a1 < b2 and b1 < a2

                # warmup1 vs match2
                if ov(wu1_start, s1, s2, e2):
                    excess = wu1_size + m2["field_size"] - 1.0
                    if excess > 1e-6:
                        cost += self.FIELD_CAPACITY_PENALTY * excess

                # match1 vs warmup2
                if ov(s1, s1 + m1["duration"], wu2_start, s2):
                    excess = m1["field_size"] + wu2_size - 1.0
                    if excess > 1e-6:
                        cost += self.FIELD_CAPACITY_PENALTY * excess

                # warmup1 vs warmup2
                if ov(wu1_start, s1, wu2_start, s2):
                    excess = wu1_size + wu2_size - 1.0
                    if excess > 1e-6:
                        cost += self.FIELD_CAPACITY_PENALTY * excess

        # Locker sharing penalty
        cost += self._locker_cost(assignment)

        return cost

    def _locker_cost(self, assignment):
        """Simulate locker assignment and return total sharing penalty."""
        placed = []
        total  = 0

        for mid, (fid, t) in sorted(assignment.items(), key=lambda x: to_min(x[1][1])):
            match     = next(m for m in self.matches if m["id"] == mid)
            start_min = to_min(t)
            end_min   = start_min + match["duration"]
            lk_start  = start_min - self.LOCKER_BUFFER
            lk_end    = end_min   + self.LOCKER_BUFFER
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
            pref = next((p for p in self.preferences if p["team"] == match["home"]), None)
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

            # Soft penalty if preferred locker was unavailable
            if preferred_locker_ids and home_lk["id"] not in preferred_locker_ids:
                penalty += self.LOCKER_PREF_PENALTY

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
            self.preferences, self.slot_size
        )
        result = greedy.solve()

        assignment = {s["match_id"]: (s["field_id"], s["time"]) for s in result}

        # Fall back for any unplaced matches
        for m in self.matches:
            if m["id"] not in assignment:
                assignment[m["id"]] = (self.fields[0]["id"], self.time_slots[0])

        return assignment

    # ------------------------------------------------------------------
    # NEIGHBOUR MOVES
    # ------------------------------------------------------------------

    def _neighbor(self, assignment):
        new = dict(assignment)
        move = random.choice(["time", "field", "swap", "both"])
        ids  = list(new.keys())

        if move == "time":
            mid = random.choice(ids)
            fid, _ = new[mid]
            new[mid] = (fid, random.choice(self.time_slots))

        elif move == "field":
            mid = random.choice(ids)
            _, t = new[mid]
            new[mid] = (random.choice(self.fields)["id"], t)

        elif move == "both":
            mid = random.choice(ids)
            new[mid] = (random.choice(self.fields)["id"], random.choice(self.time_slots))

        elif move == "swap" and len(ids) >= 2:
            m1, m2 = random.sample(ids, 2)
            new[m1], new[m2] = new[m2], new[m1]

        return new

    # ------------------------------------------------------------------
    # LOCKER ASSIGNMENT  (same logic as greedy)
    # ------------------------------------------------------------------

    def _assign_lockers(self, start_min, duration, placed):
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
        for mid, (fid, t) in sorted(assignment.items(), key=lambda x: to_min(x[1][1])):
            match = next(m for m in self.matches if m["id"] == mid)
            field = next((f for f in self.fields if f["id"] == fid), None)
            start_min = to_min(t)
            lockers   = self._assign_lockers(start_min, match["duration"], placed)

            entry = {
                "match_id":        mid,
                "home":            match["home"],
                "away":            match["away"],
                "field_id":        fid,
                "field_name":      field["name"] if field else str(fid),
                "time":            t,
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
        current_cost = self._cost(current)
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

        while T > self.T_MIN:
            for _ in range(self.ITER_PER_T):
                neighbor      = self._neighbor(current)
                neighbor_cost = self._cost(neighbor)
                delta         = neighbor_cost - current_cost

                if delta < 0 or random.random() < math.exp(-delta / T):
                    current      = neighbor
                    current_cost = neighbor_cost

                    if current_cost < best_cost:
                        best      = dict(current)
                        best_cost = current_cost

            T *= self.COOLING

        improvement = initial_cost - best_cost
        print(f"  Cost: {initial_cost:.1f} → {best_cost:.1f}  "
              f"(improved by {improvement:.1f})")
        print(f"{'='*55}\n")

        return self._build_schedule(best)
