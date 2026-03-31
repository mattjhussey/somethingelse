"""Aircraft Tracker – UK Live Map application."""

from __future__ import annotations

import importlib.resources
import logging
import threading
import time
from pathlib import Path

import webview

from somethingelse import adsb

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 15


def _resources_dir() -> Path:
    """Return the absolute path to the bundled resources directory."""
    package_path = importlib.resources.files("somethingelse") / "resources"
    # importlib.resources may return a traversable; resolve to a real path.
    with importlib.resources.as_file(package_path) as p:
        return p


class AircraftTrackerApi:
    """Python API exposed to JavaScript running inside the WebView.

    Methods on this class can be called from JavaScript via
    ``window.pywebview.api.<method_name>(...)``.  The public JavaScript helpers
    ``updateAircraft`` / ``clearAircraft`` delegate to these methods so that
    the map page can be driven from both Python and JavaScript.
    """

    def __init__(self, window_ref: list[webview.Window]) -> None:
        self._window_ref = window_ref
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API (callable from Python *and* JavaScript)
    # ------------------------------------------------------------------

    def update_aircraft(
        self,
        icao: str,
        lat: float,
        lon: float,
        callsign: str,
        altitude: int,
        heading: int = 0,
        on_ground: bool = False,
        speed_knots: float = 0.0,
    ) -> None:
        """Add or refresh an aircraft marker on the map."""
        window = self._window_ref[0] if self._window_ref else None
        if window is None:
            return
        callsign_safe = (
            callsign.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "")
            .replace("\r", "")
        )
        js = (
            f"updateAircraft('{icao}', {lat}, {lon}, '{callsign_safe}',"
            f" {altitude}, {heading}, {'true' if on_ground else 'false'},"
            f" {speed_knots});"
        )
        window.evaluate_js(js)

    def clear_aircraft(self) -> None:
        """Remove all aircraft markers from the map."""
        window = self._window_ref[0] if self._window_ref else None
        if window is None:
            return
        window.evaluate_js("clearAircraft();")

    # ------------------------------------------------------------------
    # ADSB polling (runs in a background daemon thread)
    # ------------------------------------------------------------------

    def start_adsb_feed(self) -> None:
        """Start the background thread that polls OpenSky every 15 seconds."""
        t = threading.Thread(target=self._adsb_loop, name="adsb-refresh", daemon=True)
        t.start()

    def stop_adsb_feed(self) -> None:
        """Signal the background thread to stop."""
        self._stop_event.set()

    def _adsb_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                aircraft_list = adsb.fetch_all_aircraft()
                self.clear_aircraft()
                for a in aircraft_list:
                    self.update_aircraft(
                        a.icao24,
                        a.latitude,
                        a.longitude,
                        a.callsign,
                        int(a.altitude_feet),
                        int(a.heading_degrees),
                        a.on_ground,
                        round(a.speed_knots, 1),
                    )
                logger.info("ADSB refresh: %d aircraft", len(aircraft_list))
            except Exception:
                logger.exception("Failed to fetch ADSB data from OpenSky Network")
            self._stop_event.wait(REFRESH_INTERVAL_SECONDS)


def main() -> None:
    """Entry point – create the WebView window and start the event loop."""
    logging.basicConfig(level=logging.INFO)
    resources = _resources_dir()
    map_html = resources / "map.html"

    # Mutable list so that AircraftTrackerApi can reference the window once
    # it has been created by the webview framework.
    window_ref: list[webview.Window] = []
    api = AircraftTrackerApi(window_ref)

    window = webview.create_window(
        title="Aircraft Tracker – UK Live Map",
        url=map_html.as_uri(),
        width=1200,
        height=800,
        js_api=api,
    )
    window_ref.append(window)

    def on_loaded() -> None:
        api.start_adsb_feed()

    window.events.loaded += on_loaded

    webview.start()
    api.stop_adsb_feed()


if __name__ == "__main__":
    main()

