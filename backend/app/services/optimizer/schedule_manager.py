# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/schedule_manager.py
# Author:  Bas Arens
# Purpose: ScheduleManager bridges the saved JSON settings (fields, lockers,
#          team windows, optimizer options) to the solver classes. A singleton
#          instance is exposed at module level for convenience.
#
# Classes:
#   ScheduleManager — load_all(), summary()
# ─────────────────────────────────────────────────────────────────────────────

from app.services.optimizer.load_settings import load_fields, load_lockers, load_windows, load_optimizer_settings

class ScheduleManager:
    """
    Bridge between the saved settings (fields, lockers, team windows, optimizer options)
    and the actual solver (MILP, greedy, metaheuristic).
    """

    def __init__(self):
        self.fields = []
        self.lockers = []
        self.windows = []
        self.optimizer_settings = {}

    async def load_all(self):
        """Load everything from JSON configuration files."""
        self.fields = load_fields()
        self.lockers = load_lockers()
        self.windows = load_windows()
        self.optimizer_settings = load_optimizer_settings()

    def summary(self):
        """Return a basic summary for debugging."""
        return {
            "fields": self.fields,
            "lockers": self.lockers,
            "windows": self.windows,
            "optimizer_settings": self.optimizer_settings
        }

schedule_manager = ScheduleManager()
