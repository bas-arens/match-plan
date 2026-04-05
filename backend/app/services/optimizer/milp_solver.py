# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/milp_solver.py
# Author:  Bas Arens
# Purpose: Mixed-Integer Linear Programming scheduler using PuLP + CBC.
#          Formulates match placement as an MILP problem with binary variables
#          for slot assignment (x), locker assignment (y), and non-overlap
#          ordering (z_team, z_lock). Minimizes deviation from team time windows.
#
# Classes:
#   MILPScheduler — __init__, build(), solve(), _extract_solution()
#
# Standalone helpers:
#   to_minutes(t)          — "HH:MM" to integer minutes
#   infer_field_size(name) — field fraction from team name
#   infer_duration(name)   — match duration from team name
# ─────────────────────────────────────────────────────────────────────────────

from pulp import (
    LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, PULP_CBC_CMD
)
from datetime import datetime, timedelta


def to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def infer_field_size(team_name):
    t = team_name.upper()
    if any(x in t for x in ("JO7","JO8","JO9","MO7","MO8","MO9")):
        return 0.25
    if any(x in t for x in ("JO10","JO11","MO10","MO11")):
        return 0.5
    if any(x in t for x in ("JO12","JO13","MO12","MO13")):
        return 0.75
    return 1.0


def infer_duration(team_name):
    t = team_name.upper()
    if any(x in t for x in ("JO7","MO7")):
        return 55
    if any(x in t for x in ("JO8","MO8","JO9","MO9")):
        return 65
    if any(x in t for x in ("JO10","MO10","JO11","MO11")):
        return 75
    if any(x in t for x in ("JO12","MO12","JO13","MO13")):
        return 75
    if any(x in t for x in ("JO14","MO14","JO15","MO15")):
        return 85
    if any(x in t for x in ("JO16","MO16","JO17","MO17")):
        return 95
    return 105



class MILPScheduler:

    def __init__(self, matches, fields, lockers, windows=None, date=None):
        self.raw_matches = matches
        self.fields = fields
        self.lockers = lockers
        self.windows = windows or []

        self.buffer_pre = 45
        self.buffer_post = 45

        self.date = datetime.strptime(date, "%Y-%m-%d")

        self.matches = self._normalize_matches()
        self.time_slots = self._generate_time_slots()

        self.problem = LpProblem("MatchPlanInterval_MILP", LpMinimize)

        self.x = {}      # match m starts at time t on field f
        self.y = {}      # locker assignment
        self.z_team = {} # team non-overlap binaries
        self.z_lock = {} # locker non-overlap binaries


    # ------------------------------------------------------
    def _normalize_matches(self):
        out = []
        for i, m in enumerate(self.raw_matches):
            out.append({
                "id": str(m.get("wedstrijdcode") or f"AUTO_{i}"),
                "home": m["thuisteam"],
                "away": m["uitteam"],
                "duration": infer_duration(m["thuisteam"]),
                "field_size": infer_field_size(m["thuisteam"]),
            })
        return out


    # ------------------------------------------------------
    def _generate_time_slots(self):
        start = self.date.replace(hour=7, minute=0)
        end = self.date.replace(hour=18, minute=0)

        slots = []
        cur = start
        while cur <= end:
            slots.append(cur.strftime("%H:%M"))
            cur += timedelta(minutes=15)

        return slots


    # ------------------------------------------------------
    def build(self):
        print("Building interval MILP...")

        # -----------------------------
        # Decision variables
        # -----------------------------
        for m in self.matches:
            mid = m["id"]
            for f in self.fields:
                fid = str(f["id"])
                for t in self.time_slots:
                    name = f"x_{mid}_{fid}_{t.replace(':','_')}"
                    self.x[(mid, fid, t)] = LpVariable(name, cat=LpBinary)

        for m in self.matches:
            mid = m["id"]
            for role in ["home", "away"]:
                for l in self.lockers:
                    lid = str(l["id"])
                    self.y[(mid, role, lid)] = LpVariable(
                        f"y_{mid}_{role}_{lid}", cat=LpBinary
                    )

        # non-overlap binaries
        for i in range(len(self.matches)):
            for j in range(i+1, len(self.matches)):
                m1 = self.matches[i]["id"]
                m2 = self.matches[j]["id"]

                # team conflict binary
                self.z_team[(m1, m2)] = LpVariable(
                    f"z_team_{m1}_{m2}", cat=LpBinary
                )

                # locker conflict binaries
                for l in self.lockers:
                    lid = str(l["id"])
                    self.z_lock[(m1, m2, lid)] = LpVariable(
                        f"z_lock_{m1}_{m2}_{lid}", cat=LpBinary
                    )

        # -----------------------------
        # C1: each match exactly once
        # -----------------------------
        for m in self.matches:
            mid = m["id"]
            self.problem += lpSum(
                self.x[(mid, str(f["id"]), t)]
                for f in self.fields
                for t in self.time_slots
            ) == 1


        # -----------------------------
        # C2: field capacity
        # -----------------------------
        for f in self.fields:
            fid = str(f["id"])
            for s in self.time_slots:
                s_min = to_minutes(s)

                used = []
                for m in self.matches:
                    mid = m["id"]
                    dur = m["duration"]
                    req = m["field_size"]

                    for t in self.time_slots:
                        t_min = to_minutes(t)
                        if t_min <= s_min < t_min + dur:
                            used.append(req * self.x[(mid, fid, t)])

                self.problem += lpSum(used) <= 1


        # -----------------------------
        # C3: one home locker + one away locker
        # -----------------------------
        for m in self.matches:
            mid = m["id"]

            self.problem += lpSum(self.y[(mid, "home", str(l["id"]))] for l in self.lockers) == 1
            self.problem += lpSum(self.y[(mid, "away", str(l["id"]))] for l in self.lockers) == 1


        # -----------------------------
        # Interval helper functions
        # -----------------------------
        def start_time(mid):
            return lpSum(
                to_minutes(t) * self.x[(mid, str(f["id"]), t)]
                for f in self.fields for t in self.time_slots
            )

        def assigned_field(mid, fid, t):
            return self.x[(mid, fid, t)]


        # -----------------------------
        # TEAM NON-OVERLAP
        # -----------------------------
        for i in range(len(self.matches)):
            for j in range(i+1, len(self.matches)):

                m1 = self.matches[i]
                m2 = self.matches[j]

                # skip if no shared team
                if not (m1["home"] in [m2["home"], m2["away"]] or
                        m1["away"] in [m2["home"], m2["away"]]):
                    continue

                mid1 = m1["id"]
                mid2 = m2["id"]

                t1 = start_time(mid1)
                t2 = start_time(mid2)

                d1 = m1["duration"] + self.buffer_pre + self.buffer_post
                d2 = m2["duration"] + self.buffer_pre + self.buffer_post

                z = self.z_team[(mid1, mid2)]

                M = 2000

                # m1 before m2
                self.problem += t1 + d1 <= t2 + M * (1 - z)

                # m2 before m1
                self.problem += t2 + d2 <= t1 + M * z


        # -----------------------------
        # LOCKER NON-OVERLAP
        # -----------------------------
        for i in range(len(self.matches)):
            for j in range(i+1, len(self.matches)):

                m1 = self.matches[i]
                m2 = self.matches[j]

                mid1 = m1["id"]
                mid2 = m2["id"]

                t1 = start_time(mid1)
                t2 = start_time(mid2)

                d1 = m1["duration"] + self.buffer_pre + self.buffer_post
                d2 = m2["duration"] + self.buffer_pre + self.buffer_post

                for l in self.lockers:
                    lid = str(l["id"])
                    z = self.z_lock[(mid1, mid2, lid)]

                    M = 2000

                    # both assigned to same locker?
                    assigned_both = (
                        self.y[(mid1, "home", lid)]
                        + self.y[(mid1, "away", lid)]
                        + self.y[(mid2, "home", lid)]
                        + self.y[(mid2, "away", lid)]
                    )

                    # enforce non-overlap only if both use locker l
                    self.problem += t1 + d1 <= t2 + M * (1 - z) + M * (2 - assigned_both)
                    self.problem += t2 + d2 <= t1 + M * z + M * (2 - assigned_both)


        # -----------------------------
        # OBJECTIVE (prefer windows)
        # -----------------------------
        terms = []
        P = 10

        for m in self.matches:
            mid = m["id"]
            team = m["home"]
            dur = m["duration"]

            pref = next((w for w in self.windows if w["team"] == team), None)
            if not pref:
                continue

            ws = to_minutes(pref["start"])
            we = to_minutes(pref["end"])

            for f in self.fields:
                fid = str(f["id"])
                for t in self.time_slots:
                    t_min = to_minutes(t)

                    if t_min < ws:
                        terms.append((ws - t_min) * P * self.x[(mid, fid, t)])
                    elif t_min > we:
                        terms.append((t_min - we) * P * self.x[(mid, fid, t)])

        self.problem += lpSum(terms)

        print("MILP build complete.\n")


    # ------------------------------------------------------


    def solve(self):
        print("Solving...")

        # CBC solver with optimality cutoff:
        solver = PULP_CBC_CMD(
            msg=True,
            options=[
                "-bestObjStop", "1e-6"
            ]
        )



        self.problem.solve(solver)

        print("Done.")
        return self._extract_solution()



    # ------------------------------------------------------
    def _extract_solution(self):
        schedule = []
        for (mid, fid, t), var in self.x.items():
            if var.value() == 1:
                schedule.append({
                    "match_id": mid,
                    "field_id": fid,
                    "time": t,
                })
        return schedule
