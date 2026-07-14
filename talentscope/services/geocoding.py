"""
Geocoding service — converts address strings to lat/lng and calculates
distance between two coordinates using the Haversine formula.
Uses Nominatim (free, no API key required).
"""
import math
import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "TalentScope/1.0 (job search app)"}


async def geocode(address: str) -> tuple[float, float] | None:
    """Return (lat, lng) for an address string, or None on failure."""
    params = {"q": address, "format": "json", "limit": 1}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(NOMINATIM_URL, params=params, headers=HEADERS)
            r.raise_for_status()
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
