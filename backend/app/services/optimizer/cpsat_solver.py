# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/cpsat_solver.py
# Author:  Bas Arens
# Purpose: Constraint Programming scheduler using Google OR-Tools CP-SAT.
#          Optimizes field, time, and locker assignment in a single model.
#          No Big-M tricks or auxiliary variables needed — CP-SAT handles
#          NoOverlap and AllDifferent constraints natively.
#
# Classes:
#   CPSATScheduler — __init__, solve()
# ─────────────────────────────────────────────────────────────────────────────

import re
from ortools.sat.python import cp_model

from app.services.sportlink import infer_field_size, infer_duration


def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


class CPSATScheduler:

    LOCKER_BUFFER   = 20
    WARMUP_DURATION = 15
    SLOT_SIZE       = 15
    TIME_LIMIT      = 30   # seconds

    DAY_START = 8 * 60 + 30   # 08:30
    DAY_END   = 20 * 60       # 20:00

    def __init__(self, matches, fields, lockers, preferences=None,
                 fixed_slots=None, priorities=None):
        self.raw_matches  = matches
        self.fields       = fields
        self.lockers      = lockers
        self.preferences  = preferences or []
        self.fixed_slots  = fixed_slots or []
        self.priorities   = priorities or {"lockers": 1, "time_windows": 1, "field_preference": 1}

        self.pref_by_team  = {p["team"]: p for p in self.preferences}
        self.fixed_by_team = {fs["team"]: fs for fs in self.fixed_slots}
        self.field_by_id   = {f["id"]: f for f in self.fields}

        self.matches = self._normalize_matches()

        # Map field/locker IDs to consecutive indices for CP-SAT
        self.field_ids  = [f["id"] for f in self.fields]
        self.locker_ids = [lk["id"] for lk in self.lockers]
        self.field_idx  = {fid: i for i, fid in enumerate(self.field_ids)}
        self.locker_idx = {lid: i for i, lid in enumerate(self.locker_ids)}

    # ------------------------------------------------------------------
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
                "window_start": to_min(pref["start"]) if pref else self.DAY_START,
                "window_end":   to_min(pref["end"])   if pref else self.DAY_END,
            })
        return out

    def _warmup_size(self, match):
        team = match["home"].upper()
        return 0.125 if ("JO" in team or "MO" in team) else 0.25

    # ------------------------------------------------------------------
    def solve(self):
        model = cp_model.CpModel()
        n_fields  = len(self.fields)
        n_lockers = len(self.lockers)
        p = self.priorities

        print(f"\n{'='*55}")
        print(f"  CP-SAT SOLVER — {len(self.matches)} matches, "
              f"{n_fields} fields, {n_lockers} lockers")
        print(f"{'='*55}")

        # ── Decision variables ──────────────────────────────
        start_vars  = {}  # mid → IntVar (start time in minutes)
        field_vars  = {}  # mid → IntVar (field index)
        hlk_vars    = {}  # mid → IntVar (home locker index)
        alk_vars    = {}  # mid → IntVar (away locker index)

        # Penalty collector variables
        window_penalty_vars = {}
        early_penalty_vars  = {}
        field_penalty_vars  = {}

        for m in self.matches:
            mid = m["id"]
            dur = m["duration"]
            ws  = m["window_start"]
            we  = m["window_end"]

            # Start time: must be on 15-min grid within day bounds
            # Allow 60 min slack outside window for trade-offs
            earliest = max(self.DAY_START, ws - 60)
            latest   = min(self.DAY_END,   we + 60)

            start_vars[mid] = model.new_int_var(
                earliest // self.SLOT_SIZE,
                latest   // self.SLOT_SIZE,
                f"start_{mid}"
            )

            field_vars[mid] = model.new_int_var(0, n_fields - 1, f"field_{mid}")

            if n_lockers >= 2:
                hlk_vars[mid] = model.new_int_var(0, n_lockers - 1, f"hlk_{mid}")
                alk_vars[mid] = model.new_int_var(0, n_lockers - 1, f"alk_{mid}")
                # Home and away locker must differ
                model.add(hlk_vars[mid] != alk_vars[mid])

            # ── Penalty variables for objective ──
            # Window penalty: max(0, ws - start) + max(0, start + dur - we)
            # We work in slot units (multiply by SLOT_SIZE at the end)
            start_min_expr = start_vars[mid] * self.SLOT_SIZE
            ws_slot = ws // self.SLOT_SIZE
            we_slot = we // self.SLOT_SIZE
            dur_slots = dur // self.SLOT_SIZE

            # Early penalty: minutes from window start (when inside window)
            early_penalty_vars[mid] = model.new_int_var(0, (self.DAY_END - self.DAY_START) // self.SLOT_SIZE, f"early_{mid}")

            # Window penalty: minutes outside window
            before_var = model.new_int_var(0, (self.DAY_END - self.DAY_START) // self.SLOT_SIZE, f"before_{mid}")
            after_var  = model.new_int_var(0, (self.DAY_END - self.DAY_START) // self.SLOT_SIZE, f"after_{mid}")

            # before = max(0, ws_slot - start)
            model.add(before_var >= ws_slot - start_vars[mid])
            model.add(before_var >= 0)
            # after = max(0, start + dur_slots - we_slot)
            model.add(after_var >= start_vars[mid] + dur_slots - we_slot)
            model.add(after_var >= 0)

            window_penalty_vars[mid] = model.new_int_var(0, 2 * (self.DAY_END - self.DAY_START) // self.SLOT_SIZE, f"winpen_{mid}")
            model.add(window_penalty_vars[mid] == before_var + after_var)

            # Earliness = start - ws_slot when inside window (0 when outside)
            # early = max(0, start - ws_slot) but only when window_penalty == 0
            # Simplification: always add start - ws_slot clamped to 0; the window
            # penalty already dominates when outside window
            model.add(early_penalty_vars[mid] >= start_vars[mid] - ws_slot)
            model.add(early_penalty_vars[mid] >= 0)

            # Field preference penalty (boolean)
            pref = self.pref_by_team.get(m["home"])
            preferred_fids = pref.get("preferred_field_ids", []) if pref else []
            preferred_idxs = [self.field_idx[fid] for fid in preferred_fids if fid in self.field_idx]

            field_penalty_vars[mid] = model.new_bool_var(f"fpen_{mid}")
            if preferred_idxs and len(preferred_idxs) < n_fields:
                # field_penalty = 1 when field NOT in preferred list
                # field IN preferred → penalty = 0
                # We express: if field in preferred_idxs then penalty = 0
                for idx in preferred_idxs:
                    model.add(field_penalty_vars[mid] == 0).only_enforce_if(
                        field_vars[mid] == idx  # type: ignore
                    )
                # If field not in preferred_idxs, penalty = 1
                # We need: penalty >= 1 - sum(field == idx for idx in preferred)
                # Simpler: for each non-preferred index, if field == idx, penalty = 1
                non_preferred = [i for i in range(n_fields) if i not in preferred_idxs]
                for idx in non_preferred:
                    model.add(field_penalty_vars[mid] == 1).only_enforce_if(
                        field_vars[mid] == idx  # type: ignore
                    )
            else:
                # No preference or all fields preferred → no penalty
                model.add(field_penalty_vars[mid] == 0)

        # ── Fixed slots ─────────────────────────────────────
        for m in self.matches:
            fix = self.fixed_by_team.get(m["home"])
            if not fix:
                continue
            mid = m["id"]
            if fix.get("time") and fix.get("field_id"):
                fixed_slot = to_min(fix["time"]) // self.SLOT_SIZE
                model.add(start_vars[mid] == fixed_slot)
                if fix["field_id"] in self.field_idx:
                    model.add(field_vars[mid] == self.field_idx[fix["field_id"]])
            if fix.get("locker_id") is not None and mid in hlk_vars:
                if fix["locker_id"] in self.locker_idx:
                    model.add(hlk_vars[mid] == self.locker_idx[fix["locker_id"]])

        # ── Team non-overlap ────────────────────────────────
        for i in range(len(self.matches)):
            for j in range(i + 1, len(self.matches)):
                m1 = self.matches[i]
                m2 = self.matches[j]
                if not (m1["home"] in (m2["home"], m2["away"]) or
                        m1["away"] in (m2["home"], m2["away"])):
                    continue
                mid1, mid2 = m1["id"], m2["id"]
                dur1_slots = m1["duration"] // self.SLOT_SIZE
                dur2_slots = m2["duration"] // self.SLOT_SIZE

                # m1 before m2 OR m2 before m1
                b = model.new_bool_var(f"order_{mid1}_{mid2}")
                model.add(start_vars[mid1] + dur1_slots <= start_vars[mid2]).only_enforce_if(b)
                model.add(start_vars[mid2] + dur2_slots <= start_vars[mid1]).only_enforce_if(~b)

        # ── Field capacity ──────────────────────────────────
        # For each field and timeslot, total field_size of active matches <= 1.0
        # We use interval variables + NoOverlap per field for full-size matches.
        # For partial-field matches (halves/quarters), use cumulative constraint.
        SCALE = 8  # multiply field_size by 8 to get integers (1/8 → 1, 1/4 → 2, 1/2 → 4, 1 → 8)
        n_slots = (self.DAY_END - self.DAY_START) // self.SLOT_SIZE

        for fi, fid in enumerate(self.field_ids):
            intervals = []
            demands   = []
            for m in self.matches:
                mid = m["id"]
                dur_slots = m["duration"] // self.SLOT_SIZE
                demand = int(m["field_size"] * SCALE)

                # Boolean: is this match on this field?
                on_field = model.new_bool_var(f"onf_{mid}_{fi}")
                model.add(field_vars[mid] == fi).only_enforce_if(on_field)
                model.add(field_vars[mid] != fi).only_enforce_if(~on_field)

                # Optional interval: active only if match is on this field
                interval = model.new_optional_fixed_size_interval_var(
                    start_vars[mid], dur_slots, on_field, f"iv_{mid}_{fi}"
                )
                intervals.append(interval)
                demands.append(demand)

            if intervals:
                model.add_cumulative(intervals, demands, SCALE)

        # ── Locker non-overlap ──────────────────────────────
        # For each locker, no two matches can use it at the same time.
        # Locker window = [start - buffer, start + duration + buffer] in slot units.
        if n_lockers >= 2:
            buf_slots = self.LOCKER_BUFFER // self.SLOT_SIZE
            # Round up buffer to at least 1 slot
            if buf_slots == 0 and self.LOCKER_BUFFER > 0:
                buf_slots = 1

            for li, lid in enumerate(self.locker_ids):
                intervals = []
                for m in self.matches:
                    mid = m["id"]
                    dur_slots = m["duration"] // self.SLOT_SIZE
                    lk_dur = dur_slots + 2 * buf_slots  # total locker window in slots

                    # Locker start = match start - buffer (in slot units)
                    lk_start = model.new_int_var(
                        (self.DAY_START - self.LOCKER_BUFFER) // self.SLOT_SIZE,
                        self.DAY_END // self.SLOT_SIZE,
                        f"lks_{mid}_{li}"
                    )
                    model.add(lk_start == start_vars[mid] - buf_slots)

                    # Home team uses this locker?
                    h_uses = model.new_bool_var(f"huses_{mid}_{li}")
                    model.add(hlk_vars[mid] == li).only_enforce_if(h_uses)
                    model.add(hlk_vars[mid] != li).only_enforce_if(~h_uses)

                    # Away team uses this locker?
                    a_uses = model.new_bool_var(f"auses_{mid}_{li}")
                    model.add(alk_vars[mid] == li).only_enforce_if(a_uses)
                    model.add(alk_vars[mid] != li).only_enforce_if(~a_uses)

                    # Either team uses this locker
                    either = model.new_bool_var(f"either_{mid}_{li}")
                    model.add_max_equality(either, [h_uses, a_uses])

                    interval = model.new_optional_fixed_size_interval_var(
                        lk_start, lk_dur, either, f"lkiv_{mid}_{li}"
                    )
                    intervals.append(interval)

                if intervals:
                    model.add_no_overlap(intervals)

        # ── Objective ───────────────────────────────────────
        # Scale penalties by SLOT_SIZE to convert from slots to minutes
        obj_terms = []
        W_WEIGHT = int(10 * p["time_windows"])       # 1/min * SLOT_SIZE * 10 for precision
        E_WEIGHT = int(5  * p["time_windows"])        # 0.5/min * SLOT_SIZE * 10
        F_WEIGHT = int(300 * p["field_preference"])   # 30 * 10

        for m in self.matches:
            mid = m["id"]
            obj_terms.append(W_WEIGHT * self.SLOT_SIZE * window_penalty_vars[mid])
            obj_terms.append(E_WEIGHT * self.SLOT_SIZE * early_penalty_vars[mid])
            obj_terms.append(F_WEIGHT * field_penalty_vars[mid])

        model.minimize(sum(obj_terms))

        # ── Solve ───────────────────────────────────────────
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.TIME_LIMIT

        print(f"Solving (time limit {self.TIME_LIMIT}s)...")
        status = solver.solve(model)

        status_name = {
            cp_model.OPTIMAL: "Optimal",
            cp_model.FEASIBLE: "Feasible (time limit)",
            cp_model.INFEASIBLE: "Infeasible",
            cp_model.MODEL_INVALID: "Invalid model",
            cp_model.UNKNOWN: "Unknown",
        }
        print(f"Status: {status_name.get(status, 'Unknown')}")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("  No solution found!")
            return []

        obj_val = solver.objective_value / 10  # undo 10x precision scaling
        print(f"  Objective: {obj_val:.1f}")
        print(f"  Time: {solver.wall_time:.2f}s")
        print(f"{'='*55}\n")

        # ── Extract solution ────────────────────────────────
        placed = []
        for m in self.matches:
            mid = m["id"]
            start_slot = solver.value(start_vars[mid])
            start_minutes = start_slot * self.SLOT_SIZE
            field_idx = solver.value(field_vars[mid])
            fid = self.field_ids[field_idx]
            field = self.field_by_id[fid]

            h, mn = divmod(start_minutes, 60)
            time_str = f"{h:02d}:{mn:02d}"

            lk_start = start_minutes - self.LOCKER_BUFFER
            lk_end   = start_minutes + m["duration"] + self.LOCKER_BUFFER

            home_lk = self.locker_ids[solver.value(hlk_vars[mid])] if mid in hlk_vars else self.locker_ids[0]
            away_lk = self.locker_ids[solver.value(alk_vars[mid])] if mid in alk_vars else self.locker_ids[1]

            entry = {
                "match_id":        mid,
                "home":            m["home"],
                "away":            m["away"],
                "field_id":        fid,
                "field_name":      field["name"],
                "time":            time_str,
                "duration":        m["duration"],
                "field_size":      m["field_size"],
                "warmup_size":     self._warmup_size(m),
                "warmup_duration": self.WARMUP_DURATION,
                "home_locker":     home_lk,
                "away_locker":     away_lk,
                "locker_start":    lk_start,
                "locker_duration": lk_end - lk_start,
                "penalty":         0,
            }
            placed.append(entry)

        placed.sort(key=lambda e: to_min(e["time"]))
        return placed
