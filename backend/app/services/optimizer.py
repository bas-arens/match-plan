# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer.py
# Author:  Bas Arens
# Purpose: Stub optimizer service kept for backward compatibility. Actual
#          optimization is handled by the solver modules in
#          app/services/optimizer/ (greedy, SA, CP-SAT).
#
# Functions:
#   run_optimizer(data) — placeholder that echoes input with a status message
# ─────────────────────────────────────────────────────────────────────────────

def run_optimizer(data):
    # TODO: koppelen met jouw echte optimizer.py
    return {
        "message": "Optimizer executed",
        "input": data
    }
