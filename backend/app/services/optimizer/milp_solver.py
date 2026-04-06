# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/milp_solver.py
# Author:  Bas Arens
# Purpose: Mixed-Integer Linear Programming scheduler using PuLP + CBC.
#          Formulates match placement as an MILP problem with binary variables
#          for slot assignment. Minimizes time-window deviation + field
#          preference penalties. Locker assignment is done greedily after solve.
#
# Classes:
#   MILPScheduler — __init__, build(), solve(), _extract_solution()
# ─────────────────────────────────────────────────────────────────────────────

from pulp import (
    LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, PULP_CBC_CMD
)
from datetime import datetime, timedelta

from app.services.sportlink import infer_field_size, infer_duration


def to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


class MILPScheduler:

    LOCKER_BUFFER   = 20
    LOCKER_PENALTY  = 50
    WARMUP_DURATION = 15
    TIME_LIMIT      = 30   # seconds

    def __init__(self, matches, fields, lockers, preferences=None, date=None, fixed_slots=None):
        self.raw_matches  = matches
        self.fields       = fields
        self.lockers      = lockers
        self.preferences  = preferences or []
        self.fixed_slots  = fixed_slots or []

        self.date = datetime.strptime(date, "%Y-%m-%d")

        self.pref_by_team  = {p["team"]: p for p in self.preferences}
        self.fixed_by_team = {fs["team"]: fs for fs in self.fixed_slots}
        self.field_by_id   = {f["id"]: f for f in self.fields}

        self.matches    = self._normalize_matches()
        self.time_slots = self._generate_time_slots()

        self.problem = LpProblem("MatchPlan_MILP", LpMinimize)
        self.x = {}  # (mid, fid, t) → binary variable

    # ------------------------------------------------------
    def _normalize_matches(self):
        out = []
        for i, m in enumerate(self.raw_matches):
            home = m["thuisteam"]
            pref = self.pref_by_team.get(home)
            out.append({
                "id":         str(m.get("wedstrijdcode") or f"AUTO_{i}"),
                "home":       home,
                "away":       m["uitteam"],
                "duration":   infer_duration(home),
                "field_size": infer_field_size(home),
                "window_start": pref["start"] if pref else "08:00",
                "window_end":   pref["end"]   if pref else "20:00",
            })
        return out

    # ------------------------------------------------------
    def _generate_time_slots(self):
        start = self.date.replace(hour=8, minute=30)
        end   = self.date.replace(hour=20, minute=0)
        slots = []
        cur = start
        while cur <= end:
            slots.append(cur.strftime("%H:%M"))
            cur += timedelta(minutes=15)
        return slots

    # ------------------------------------------------------
    def _valid_slots(self, match):
        """Return only time slots where the match could reasonably start."""
        ws = to_minutes(match["window_start"])
        we = to_minutes(match["window_end"])
        dur = match["duration"]
        # Allow 60 min slack outside window so optimizer can trade off
        earliest = max(to_minutes(self.time_slots[0]),  ws - 60)
        latest   = min(to_minutes(self.time_slots[-1]), we + 60)
        return [t for t in self.time_slots if earliest <= to_minutes(t) <= latest]

    # ------------------------------------------------------
    def build(self):
        print("Building MILP...")

        # Big-M: max span of the scheduling day
        M = to_minutes(self.time_slots[-1]) - to_minutes(self.time_slots[0]) + 200

        # ----- Decision variables (pruned) -----
        for m in self.matches:
            mid = m["id"]
            valid = self._valid_slots(m)
            for f in self.fields:
                fid = str(f["id"])
                for t in valid:
                    self.x[(mid, fid, t)] = LpVariable(
                        f"x_{mid}_{fid}_{t.replace(':','_')}", cat=LpBinary
                    )

        print(f"  Variables: {len(self.x)} (pruned by time windows)")

        # ----- C0: Fixed slot constraints -----
        for m in self.matches:
            fix = self.fixed_by_team.get(m["home"])
            if not fix:
                continue
            mid = m["id"]
            fixed_time  = fix.get("time")
            fixed_field = fix.get("field_id")
            if not fixed_time or not fixed_field:
                continue
            fid = str(fixed_field)
            for key in list(self.x.keys()):
                if key[0] != mid:
                    continue
                if key[1] == fid and key[2] == fixed_time:
                    self.problem += self.x[key] == 1
                else:
                    self.problem += self.x[key] == 0

        # ----- C1: Each match placed exactly once -----
        for m in self.matches:
            mid = m["id"]
            vars_for_match = [v for k, v in self.x.items() if k[0] == mid]
            self.problem += lpSum(vars_for_match) == 1

        # ----- C2: Field capacity per time slot -----
        for f in self.fields:
            fid = str(f["id"])
            for s in self.time_slots:
                s_min = to_minutes(s)
                used = []
                for m in self.matches:
                    mid = m["id"]
                    dur = m["duration"]
                    req = m["field_size"]
                    for t in self._valid_slots(m):
                        t_min = to_minutes(t)
                        if t_min <= s_min < t_min + dur:
                            used.append(req * self.x[(mid, fid, t)])
                if used:
                    self.problem += lpSum(used) <= 1

        # ----- C3: Team non-overlap (only conflicting pairs) -----
        # Helper: linearized start time for a match
        def start_expr(mid):
            return lpSum(
                to_minutes(t) * self.x[k]
                for k in self.x if k[0] == mid
                for t in [k[2]]
            )

        for i in range(len(self.matches)):
            for j in range(i + 1, len(self.matches)):
                m1 = self.matches[i]
                m2 = self.matches[j]

                if not (m1["home"] in (m2["home"], m2["away"]) or
                        m1["away"] in (m2["home"], m2["away"])):
                    continue

                mid1, mid2 = m1["id"], m2["id"]
                z = LpVariable(f"z_{mid1}_{mid2}", cat=LpBinary)

                t1 = start_expr(mid1)
                t2 = start_expr(mid2)

                # m1 finishes before m2 starts (or vice versa)
                self.problem += t1 + m1["duration"] <= t2 + M * (1 - z)
                self.problem += t2 + m2["duration"] <= t1 + M * z

        # ----- C4: Locker capacity per time slot -----
        # Each match needs 2 lockers during [start - buffer, start + duration + buffer].
        # At any moment, total locker demand must not exceed available lockers.
        num_lockers = len(self.lockers)
        LK_BUF = self.LOCKER_BUFFER
        for s in self.time_slots:
            s_min = to_minutes(s)
            demand = []
            for m in self.matches:
                mid = m["id"]
                dur = m["duration"]
                for t in self._valid_slots(m):
                    t_min = to_minutes(t)
                    lk_start = t_min - LK_BUF
                    lk_end   = t_min + dur + LK_BUF
                    if lk_start <= s_min < lk_end:
                        # Each match needs 2 lockers (home + away), sum over all fields
                        for f in self.fields:
                            fid = str(f["id"])
                            key = (mid, fid, t)
                            if key in self.x:
                                demand.append(2 * self.x[key])
            if demand:
                self.problem += lpSum(demand) <= num_lockers

        # ----- Objective: window + earliness + field preference -----
        terms = []
        W_PENALTY = 1     # per minute outside window (matches SA + frontend)
        E_PENALTY = 0.5   # per minute late within window (prefer early start)
        F_PENALTY = 30    # per match on non-preferred field (matches SA + frontend)

        for m in self.matches:
            mid = m["id"]
            ws = to_minutes(m["window_start"])
            we = to_minutes(m["window_end"])

            pref = self.pref_by_team.get(m["home"])
            preferred_ids = [str(fid) for fid in pref.get("preferred_field_ids", [])] if pref else []

            for k, v in self.x.items():
                if k[0] != mid:
                    continue
                _, fid, t = k
                t_min = to_minutes(t)

                # Window penalty
                if t_min < ws:
                    terms.append((ws - t_min) * W_PENALTY * v)
                elif t_min + m["duration"] > we:
                    terms.append((t_min + m["duration"] - we) * W_PENALTY * v)
                else:
                    # Earliness preference: penalize distance from window start
                    terms.append((t_min - ws) * E_PENALTY * v)

                # Field preference penalty
                if preferred_ids and fid not in preferred_ids:
                    terms.append(F_PENALTY * v)

        self.problem += lpSum(terms)

        n_constraints = len(self.problem.constraints)
        print(f"  Constraints: {n_constraints}")
        print("MILP build complete.\n")

    # ------------------------------------------------------
    def solve(self):
        print(f"Solving (time limit {self.TIME_LIMIT}s)...")

        solver = PULP_CBC_CMD(
            msg=True,
            timeLimit=self.TIME_LIMIT,
        )

        self.problem.solve(solver)

        # sol_status: 1 = Optimal, 0 = Feasible (time limit), -1 = Infeasible
        sol = getattr(self.problem, 'sol_status', None)
        if sol == 1:
            print("Status: Optimal")
        elif self.problem.status == 1:
            obj = self.problem.objective.value()
            print(f"Status: Feasible (time limit) — objective {obj:.1f}")
        else:
            status_map = {0: "Not Solved", -1: "Infeasible", -2: "Unbounded", -3: "Undefined"}
            print(f"Status: {status_map.get(self.problem.status, 'Unknown')}")

        return self._extract_solution()

    # ------------------------------------------------------
    def _warmup_size(self, match):
        team = match["home"].upper()
        return 0.125 if ("JO" in team or "MO" in team) else 0.25

    def _assign_lockers(self, start_min, duration, placed, match=None):
        end_min      = start_min + duration
        lk_start     = start_min - self.LOCKER_BUFFER
        lk_end       = end_min   + self.LOCKER_BUFFER
        lk_duration  = lk_end - lk_start

        free = [
            lk for lk in self.lockers
            if not any(
                lk["id"] in (s["home_locker"], s["away_locker"])
                and s["locker_start"] < lk_end
                and s["locker_start"] + s["locker_duration"] > lk_start
                for s in placed
            )
        ]

        # Check for fixed locker
        if match:
            fix = self.fixed_by_team.get(match["home"])
            if fix and fix.get("locker_id") is not None:
                forced = next((lk for lk in self.lockers if lk["id"] == fix["locker_id"]), None)
                if forced:
                    remaining = [lk for lk in free if lk["id"] != forced["id"]]
                    away_lk = remaining[0] if remaining else next(lk for lk in self.lockers if lk["id"] != forced["id"])
                    return {
                        "home_locker": forced["id"], "away_locker": away_lk["id"],
                        "locker_start": lk_start, "locker_duration": lk_duration,
                        "locker_penalty": 0,
                    }

        # Prefer preferred lockers
        if match:
            pref = self.pref_by_team.get(match["home"])
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
            "home_locker": home_lk["id"], "away_locker": away_lk["id"],
            "locker_start": lk_start, "locker_duration": lk_duration,
            "locker_penalty": penalty,
        }

    def _extract_solution(self):
        # Gather assigned (mid, fid, time) triples
        assigned = []
        for (mid, fid, t), var in self.x.items():
            if var.value() and var.value() > 0.5:
                assigned.append((mid, fid, t))

        # Sort by start time, build full schedule with locker assignment
        assigned.sort(key=lambda x: to_minutes(x[2]))
        placed = []

        for mid, fid, t in assigned:
            match = next(m for m in self.matches if m["id"] == mid)
            field = self.field_by_id.get(int(fid)) if fid.isdigit() else self.field_by_id.get(fid)
            start_min = to_minutes(t)
            lockers = self._assign_lockers(start_min, match["duration"], placed, match)

            entry = {
                "match_id":        mid,
                "home":            match["home"],
                "away":            match["away"],
                "field_id":        int(fid) if fid.isdigit() else fid,
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
