# somethingelse
Python Aircraft tracking UI using ADSB and Weather data

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
uv sync
```

## Run

```bash
uv run somethingelse
```

## Test

```bash
uv run pytest
```

## Architecture

The application uses [pywebview](https://pywebview.flowrl.com/) to render an
interactive [Leaflet](https://leafletjs.com/) map (Leaflet 1.9.4 bundled
locally) centred on the United Kingdom.  Two JavaScript functions exposed by
the map page allow the Python backend to push live aircraft positions into the
browser canvas:

- `updateAircraft(icao, lat, lon, callsign, altitude)` – add/refresh a marker
- `clearAircraft()` – remove all markers

These can be driven programmatically via `AircraftTrackerApi.update_aircraft()`
and `AircraftTrackerApi.clear_aircraft()`.

