"""Aircraft Tracker – UK Live Map application."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import webview


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
    callers written against the original Java interface continue to work
    unchanged.
    """

    def __init__(self, window_ref: list[webview.Window]) -> None:
        self._window_ref = window_ref

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
    ) -> None:
        """Add or refresh an aircraft marker on the map."""
        window = self._window_ref[0] if self._window_ref else None
        if window is None:
            return
        js = (
            f"updateAircraft({icao!r}, {lat}, {lon}, {callsign!r}, {altitude});"
        )
        window.evaluate_js(js)

    def clear_aircraft(self) -> None:
        """Remove all aircraft markers from the map."""
        window = self._window_ref[0] if self._window_ref else None
        if window is None:
            return
        window.evaluate_js("clearAircraft();")


def main() -> None:
    """Entry point – create the WebView window and start the event loop."""
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

    webview.start()


if __name__ == "__main__":
    main()
