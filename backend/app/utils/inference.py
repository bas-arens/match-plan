def infer_field_size(team_name: str) -> float:
    t = team_name.upper()

    if any(x in t for x in ("JO7","JO8","JO9","MO7","MO8","MO9")):
        return 0.25
    if any(x in t for x in ("JO10","JO11","MO10","MO11")):
        return 0.5
    if any(x in t for x in ("JO12","JO13","MO12","MO13")):
        return 0.75
    return 1.0


def infer_duration(team_name: str) -> int:
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
