"""ADSB live aircraft feed via the OpenSky Network REST API.

OpenSky Network: https://opensky-network.org
API docs: https://openskynetwork.github.io/opensky-api/rest.html

No authentication is required for anonymous access (rate-limited to ~1 request / 10 s).
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any

OPENSKY_API_URL = "https://opensky-network.org/api/states/all"
METRES_TO_FEET = 3.28084

# UK bounding box
UK_LAT_MIN = 49.0
UK_LON_MIN = -8.0
UK_LAT_MAX = 61.5
UK_LON_MAX = 2.0


@dataclass
class Aircraft:
    """A single aircraft state vector from the OpenSky Network API."""

    icao24: str
    callsign: str
    latitude: float
    longitude: float
    altitude_feet: float
    on_ground: bool
    velocity_mps: float
    heading_degrees: float


def fetch_aircraft_in_bounds(
    lat_min: float,
    lon_min: float,
    lat_max: float,
    lon_max: float,
) -> list[Aircraft]:
    """Fetch aircraft currently within the given geographic bounding box.

    Returns an empty list on any network or parse error.
    """
    url = (
        f"{OPENSKY_API_URL}"
        f"?lamin={lat_min}&lomin={lon_min}&lamax={lat_max}&lomax={lon_max}"
    )
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            return []
        body = resp.read().decode()
    return _parse_aircraft_states(body)


def _parse_aircraft_states(json_text: str) -> list[Aircraft]:
    """Parse the JSON response from the OpenSky /states/all endpoint.

    Each state vector is an array; the indices used here are:
      0  icao24           (str)
      1  callsign         (str | null)
      5  longitude        (float | null)
      6  latitude         (float | null)
      7  baro_altitude    (float metres | null)
      8  on_ground        (bool)
      9  velocity         (float m/s | null)
     10  true_track       (float degrees | null)
    """
    data: dict[str, Any] = json.loads(json_text)
    states = data.get("states")
    if not states:
        return []

    aircraft: list[Aircraft] = []
    for state in states:
        if not isinstance(state, list) or len(state) < 17:
            continue

        icao24: str = state[0] or ""
        raw_callsign = state[1]
        callsign = (raw_callsign or icao24).strip() or icao24

        lon = state[5]
        lat = state[6]
        if lon is None or lat is None:
            continue

        alt_m = state[7]
        altitude_feet = (alt_m * METRES_TO_FEET) if alt_m is not None else 0.0
        on_ground: bool = bool(state[8])
        vel = state[9]
        velocity_mps = vel if vel is not None else 0.0
        track = state[10]
        heading_degrees = track if track is not None else 0.0

        aircraft.append(
            Aircraft(
                icao24=icao24,
                callsign=callsign,
                latitude=float(lat),
                longitude=float(lon),
                altitude_feet=altitude_feet,
                on_ground=on_ground,
                velocity_mps=velocity_mps,
                heading_degrees=heading_degrees,
            )
        )
    return aircraft
