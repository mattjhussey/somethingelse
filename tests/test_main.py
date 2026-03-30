"""Tests for the somethingelse package."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import somethingelse.main as app_module


def _resources_dir() -> Path:
    """Return the resolved resources directory path."""
    package_path = importlib.resources.files("somethingelse") / "resources"
    with importlib.resources.as_file(package_path) as p:
        return p


class TestResources:
    """Verify that required resource files are bundled with the package."""

    def test_map_html_exists(self) -> None:
        resources = _resources_dir()
        assert (resources / "map.html").exists(), "map.html must be present in resources"

    def test_leaflet_js_exists(self) -> None:
        resources = _resources_dir()
        assert (resources / "leaflet.js").exists(), "leaflet.js must be present in resources"

    def test_leaflet_css_exists(self) -> None:
        resources = _resources_dir()
        assert (resources / "leaflet.css").exists(), "leaflet.css must be present in resources"

    def test_marker_images_exist(self) -> None:
        resources = _resources_dir()
        for name in ("marker-icon.png", "marker-shadow.png"):
            assert (resources / "images" / name).exists(), (
                f"{name} must be present in resources/images"
            )


class TestAircraftTrackerApi:
    """Unit tests for AircraftTrackerApi (no WebView required)."""

    def test_api_instantiates(self) -> None:
        api = app_module.AircraftTrackerApi([])
        assert api is not None

    def test_update_aircraft_no_window_does_not_raise(self) -> None:
        """Calling update_aircraft with no window should be a silent no-op."""
        api = app_module.AircraftTrackerApi([])
        api.update_aircraft("ABC123", 51.5, -0.1, "SPEED1", 35000, 90, False)

    def test_update_aircraft_on_ground_no_window_does_not_raise(self) -> None:
        """Calling update_aircraft for a grounded aircraft should be a silent no-op."""
        api = app_module.AircraftTrackerApi([])
        api.update_aircraft("GND001", 51.5, -0.1, "RYR1", 0, 0, True)

    def test_clear_aircraft_no_window_does_not_raise(self) -> None:
        """Calling clear_aircraft with no window should be a silent no-op."""
        api = app_module.AircraftTrackerApi([])
        api.clear_aircraft()


class TestResourcesDir:
    """Tests for the internal _resources_dir helper."""

    def test_returns_path(self) -> None:
        p = app_module._resources_dir()
        assert isinstance(p, Path)

    def test_path_is_directory(self) -> None:
        p = app_module._resources_dir()
        assert p.is_dir(), f"Expected a directory at {p}"
