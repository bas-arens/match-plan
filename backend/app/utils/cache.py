# app/utils/cache.py

import time
import requests
from typing import List, Dict

CACHE_TTL = 60 * 10  # 10 minuten cache
_cache_data = None
_cache_timestamp = None


def get_cached_matches(client_id: str) -> List[Dict]:
    """
    Haal alle programmawedstrijden binnen voor het hele seizoen.
    Dit gebruikt het officiële Sportlink-artikel PROGRAMMA
    en filtert daarna lokaal op de club.
    """

    global _cache_data, _cache_timestamp

    now = time.time()

    # geldige cache?
    if _cache_data and _cache_timestamp and (now - _cache_timestamp < CACHE_TTL):
        return _cache_data

    # ---- API CALL ----
    url = (
        "https://data.sportlink.com/programma"
        f"?client_id={client_id}&aantalregels=500&gebruiklokaleteamgegevens=J"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json().get("programma", [])

    _cache_data = data
    _cache_timestamp = now

    return data
