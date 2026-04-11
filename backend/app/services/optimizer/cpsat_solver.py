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
import time
from ortools.sat.python import cp_model

from app.services.sportlink import infer_field_size, infer_duration


class _ProgressCallback(cp_model.CpSolverSolutionCallback):
    """Logs every improving solution found during the search."""

    def __init__(self, scale):
        super().__init__()
        self._scale = scale
        self._start = time.perf_counter()
        self._count = 0

    def on_solution_callback(self):
        self._count += 1
        elapsed = time.perf_counter() - self._start
        obj = self.objective_value / self._scale
        best = self.best_objective_bound / self._scale
        gap = abs(obj - best) / max(abs(obj), 1e-9) * 100
        print(f"  #{self._count:>3d}  {elapsed:7.1f}s  "
              f"cost={obj:8.1f}  bound={best:8.1f}  gap={gap:5.1f}%")


def _infer_age(team):
    m = re.search(r"JO(\d+)|MO(\d+)", team.upper())
    return int(m.group(1) or m.group(2)) if m else 100


def _locker_buffer_before_age(age):
    """Minutes before the match that lockers are occupied, based on age."""
    if age >= 100:    return 60
    if age >= 17:     return 45
    if age >= 13:     return 40
    return 30


def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


class CPSATScheduler:

    LOCKER_BUFFER_AFTER = 30
    WARMUP_DURATION     = 15
    SLOT_SIZE       = 15
    TIME_LIMIT      = 0    # 0 = unlimited; override via constructor

    DAY_START = 8 * 60 + 30   # 08:30
    DAY_END   = 20 * 60       # 20:00

    def __init__(self, matches, fields, lockers, preferences=None,
                 fixed_slots=None, priorities=None, time_limit=None):
        self.raw_matches  = matches
        self.fields       = fields
        self.lockers      = lockers
        self.preferences  = preferences or []
        self.fixed_slots  = fixed_slots or []
        self.priorities   = priorities or {"lockers": 1, "time_windows": 1, "field_preference": 1}
        if time_limit is not None:
            self.TIME_LIMIT = time_limit

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
            age = _infer_age(home)
            out.append({
                "id":         str(m.get("wedstrijdcode") or f"AUTO_{i}"),
                "home":       home,
                "away":       m["uitteam"],
                "duration":   infer_duration(home),
                "field_size": infer_field_size(home),
                "age":        age,
                "lk_before":  _locker_buffer_before_age(age),
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

        # Penalty collector variables — all in MINUTES so CP-SAT's cost lines
        # up with the canonical scorer in scoring.py.
        before_penalty_vars = {}
        after_penalty_vars  = {}
        early_penalty_vars  = {}
        field_penalty_vars  = {}

        day_range = self.DAY_END - self.DAY_START

        for m in self.matches:
            mid = m["id"]
            dur = m["duration"]
            pref = self.pref_by_team.get(m["home"])
            ws = to_min(pref["start"]) if pref else None
            we = to_min(pref["end"])   if pref else None

            # Start time: must be on 15-min grid within day bounds.
            # Allow 60 min slack outside window for trade-offs.
            earliest = max(self.DAY_START, (ws - 60) if ws is not None else self.DAY_START)
            latest   = min(self.DAY_END,   (we + 60) if we is not None else self.DAY_END)

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

            # ── Window / early penalty (skip teams without a preference) ──
            # Work in exact minutes (not slot units) so rounding at window
            # edges matches scoring.py.
            if pref is not None:
                start_min_expr = start_vars[mid] * self.SLOT_SIZE

                # before = max(0, ws - start_min)
                before_var = model.new_int_var(0, day_range, f"before_{mid}")
                model.add(before_var >= ws - start_min_expr)
                model.add(before_var >= 0)

                # after = max(0, start_min + dur - we)
                after_var = model.new_int_var(0, day_range, f"after_{mid}")
                model.add(after_var >= start_min_expr + dur - we)
                model.add(after_var >= 0)

                # Canonical charges `early` only when the match ends inside
                # the window (if/elif/else). Bind `is_late` to the actual
                # condition `start + dur > we` — otherwise the solver can
                # inflate `after_var` to flip the gate and skip early cost.
                is_late = model.new_bool_var(f"late_{mid}")
                model.add(start_min_expr + dur >= we + 1).only_enforce_if(is_late)
                model.add(start_min_expr + dur <= we).only_enforce_if(~is_late)

                early_var = model.new_int_var(0, day_range, f"early_{mid}")
                model.add(early_var >= start_min_expr - ws).only_enforce_if(~is_late)
                model.add(early_var >= 0)
                model.add(early_var == 0).only_enforce_if(is_late)

                before_penalty_vars[mid] = before_var
                after_penalty_vars[mid]  = after_var
                early_penalty_vars[mid]  = early_var

            # Field preference penalty (boolean)
            preferred_fids = pref.get("preferred_field_ids", []) if pref else []
            preferred_idxs = [self.field_idx[fid] for fid in preferred_fids if fid in self.field_idx]

            field_penalty_vars[mid] = model.new_bool_var(f"fpen_{mid}")
            if preferred_idxs and len(preferred_idxs) < n_fields:
                # field_penalty = 1 when field NOT in preferred list
                # Create bool vars for "field == idx" to use with only_enforce_if
                for idx in preferred_idxs:
                    is_idx = model.new_bool_var(f"fis_{mid}_{idx}")
                    model.add(field_vars[mid] == idx).only_enforce_if(is_idx)
                    model.add(field_vars[mid] != idx).only_enforce_if(~is_idx)
                    model.add(field_penalty_vars[mid] == 0).only_enforce_if(is_idx)
                non_preferred = [i for i in range(n_fields) if i not in preferred_idxs]
                for idx in non_preferred:
                    is_idx = model.new_bool_var(f"fnp_{mid}_{idx}")
                    model.add(field_vars[mid] == idx).only_enforce_if(is_idx)
                    model.add(field_vars[mid] != idx).only_enforce_if(~is_idx)
                    model.add(field_penalty_vars[mid] == 1).only_enforce_if(is_idx)
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

        # ── Locker usage (soft sharing penalty) ─────────────
        # For each (match, locker) create an `either_uses` boolean. Sharing
        # is a soft penalty: per pair of matches whose locker windows overlap,
        # each locker they both use costs 50 × priorities.lockers.
        either_vars = {}  # (mid, li) → bool
        lk_end_expr = {}  # mid → end expression in slot units (exclusive)
        lk_start_expr = {}  # mid → start expression in slot units
        share_terms = []
        if n_lockers >= 2:
            after_buf_min = self.LOCKER_BUFFER_AFTER

            for m in self.matches:
                mid = m["id"]
                dur = m["duration"]
                before_buf_min = m["lk_before"]

                # Express locker window in exact minutes so CP-SAT pair
                # overlaps match scoring.py (rounding 40-min buffers to 2
                # slots = 30 min used to drop ~10 min off age-13 windows).
                lk_start_expr[mid] = start_vars[mid] * self.SLOT_SIZE - before_buf_min
                lk_end_expr[mid]   = start_vars[mid] * self.SLOT_SIZE + dur + after_buf_min

                for li in range(n_lockers):
                    h_uses = model.new_bool_var(f"huses_{mid}_{li}")
                    model.add(hlk_vars[mid] == li).only_enforce_if(h_uses)
                    model.add(hlk_vars[mid] != li).only_enforce_if(~h_uses)

                    a_uses = model.new_bool_var(f"auses_{mid}_{li}")
                    model.add(alk_vars[mid] == li).only_enforce_if(a_uses)
                    model.add(alk_vars[mid] != li).only_enforce_if(~a_uses)

                    either = model.new_bool_var(f"either_{mid}_{li}")
                    model.add_max_equality(either, [h_uses, a_uses])
                    either_vars[(mid, li)] = either

            # ── Pair overlap booleans (locker windows) ──
            pair_overlap = {}  # (mid1, mid2) → bool
            for i in range(len(self.matches)):
                for j in range(i + 1, len(self.matches)):
                    mid1 = self.matches[i]["id"]
                    mid2 = self.matches[j]["id"]

                    overlap = model.new_bool_var(f"lkov_{mid1}_{mid2}")
                    # overlap ⇔ lk_start1 < lk_end2 ∧ lk_start2 < lk_end1
                    model.add(lk_start_expr[mid1] < lk_end_expr[mid2]).only_enforce_if(overlap)
                    model.add(lk_start_expr[mid2] < lk_end_expr[mid1]).only_enforce_if(overlap)
                    # ¬overlap ⇔ lk_start1 ≥ lk_end2 ∨ lk_start2 ≥ lk_end1
                    na = model.new_bool_var(f"lkov_na_{mid1}_{mid2}")
                    nb = model.new_bool_var(f"lkov_nb_{mid1}_{mid2}")
                    model.add(lk_start_expr[mid1] >= lk_end_expr[mid2]).only_enforce_if(na)
                    model.add(lk_start_expr[mid1] < lk_end_expr[mid2]).only_enforce_if(~na)
                    model.add(lk_start_expr[mid2] >= lk_end_expr[mid1]).only_enforce_if(nb)
                    model.add(lk_start_expr[mid2] < lk_end_expr[mid1]).only_enforce_if(~nb)
                    model.add_bool_or([na, nb]).only_enforce_if(~overlap)
                    pair_overlap[(mid1, mid2)] = overlap

                    # ── Per-locker share booleans ──
                    for li in range(n_lockers):
                        share = model.new_bool_var(f"share_{mid1}_{mid2}_{li}")
                        # share ⇔ overlap ∧ either1_l ∧ either2_l
                        model.add_bool_and([
                            overlap,
                            either_vars[(mid1, li)],
                            either_vars[(mid2, li)],
                        ]).only_enforce_if(share)
                        model.add_bool_or([
                            overlap.Not(),
                            either_vars[(mid1, li)].Not(),
                            either_vars[(mid2, li)].Not(),
                        ]).only_enforce_if(share.Not())
                        share_terms.append(share)

        # ── Locker preference penalty variables ─────────────
        locker_penalty_vars = {}
        if n_lockers >= 2:
            for m in self.matches:
                mid = m["id"]
                pref = self.pref_by_team.get(m["home"])
                preferred_lids = pref.get("preferred_locker_ids", []) if pref else []
                preferred_lis = [self.locker_idx[lid] for lid in preferred_lids if lid in self.locker_idx]

                locker_penalty_vars[mid] = model.new_bool_var(f"lpen_{mid}")
                if preferred_lis and len(preferred_lis) < n_lockers:
                    for li in preferred_lis:
                        is_li = model.new_bool_var(f"lis_{mid}_{li}")
                        model.add(hlk_vars[mid] == li).only_enforce_if(is_li)
                        model.add(hlk_vars[mid] != li).only_enforce_if(~is_li)
                        model.add(locker_penalty_vars[mid] == 0).only_enforce_if(is_li)
                    non_preferred = [i for i in range(n_lockers) if i not in preferred_lis]
                    for li in non_preferred:
                        is_li = model.new_bool_var(f"lnp_{mid}_{li}")
                        model.add(hlk_vars[mid] == li).only_enforce_if(is_li)
                        model.add(hlk_vars[mid] != li).only_enforce_if(~is_li)
                        model.add(locker_penalty_vars[mid] == 1).only_enforce_if(is_li)
                else:
                    model.add(locker_penalty_vars[mid] == 0)

        # ── Objective ───────────────────────────────────────
        # Penalty vars are in MINUTES already; weights mirror scoring.py
        # scaled by 10 for integer precision. Divide by 10 at the end.
        obj_terms = []
        W_WEIGHT  = int(10 * p["time_windows"])         # 1/min × 10
        E_WEIGHT  = int(5  * p["time_windows"])         # 0.5/min × 10
        F_WEIGHT  = int(300 * p["field_preference"])    # 30 × 10
        LP_WEIGHT = int(300 * p["lockers"])             # 30 × 10 (locker preference)
        LS_WEIGHT = int(500 * p["lockers"])             # 50 × 10 (locker sharing)

        for m in self.matches:
            mid = m["id"]
            if mid in before_penalty_vars:
                obj_terms.append(W_WEIGHT * before_penalty_vars[mid])
                obj_terms.append(W_WEIGHT * after_penalty_vars[mid])
                obj_terms.append(E_WEIGHT * early_penalty_vars[mid])
            obj_terms.append(F_WEIGHT * field_penalty_vars[mid])
            if mid in locker_penalty_vars:
                obj_terms.append(LP_WEIGHT * locker_penalty_vars[mid])

        for share in share_terms:
            obj_terms.append(LS_WEIGHT * share)

        model.minimize(sum(obj_terms))

        # ── Solve ───────────────────────────────────────────
        solver = cp_model.CpSolver()
        if self.TIME_LIMIT > 0:
            solver.parameters.max_time_in_seconds = self.TIME_LIMIT

        callback = _ProgressCallback(scale=10)

        print(f"  Weights: window={W_WEIGHT}, early={E_WEIGHT}, field={F_WEIGHT}, "
              f"locker_pref={LP_WEIGHT}, locker_share={LS_WEIGHT}")
        print(f"Solving (time limit {self.TIME_LIMIT}s)...")
        print(f"  {'#':>5s}  {'time':>7s}  {'cost':>8s}  {'bound':>8s}  {'gap':>5s}")
        print(f"  {'-'*5}  {'-'*7}  {'-'*8}  {'-'*8}  {'-'*5}")
        status = solver.solve(model, callback)

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

            lk_start = start_minutes - m["lk_before"]
            lk_end   = start_minutes + m["duration"] + self.LOCKER_BUFFER_AFTER

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
