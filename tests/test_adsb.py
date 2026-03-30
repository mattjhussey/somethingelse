"""Tests for the somethingelse.adsb module."""

from __future__ import annotations

import json

import pytest

from somethingelse import adsb


SAMPLE_RESPONSE = {
    "time": 1700000000,
    "states": [
        # Full valid state vector
        [
            "abc123", "BA001   ", "United Kingdom",
            1700000000, 1700000000,
            -0.461941, 51.477890,
            10972.8, False,
            245.4, 92.0,
            None, None, None, None, False, 0,
        ],
        # Aircraft on the ground (altitude 0)
        [
            "def456", "EZY123  ", "United Kingdom",
            1700000000, 1700000000,
            -1.747082, 53.865471,
            0.0, True,
            0.0, 0.0,
            None, None, None, None, False, 0,
        ],
        # Missing position – should be skipped
        [
            "ghi789", None, "United Kingdom",
            None, 1700000000,
            None, None,
            None, False,
            None, None,
            None, None, None, None, False, 0,
        ],
        # Short array – should be skipped
        ["jkl000"],
    ],
}


class TestParseAircraftStates:
    def test_returns_expected_count(self) -> None:
        result = adsb._parse_aircraft_states(json.dumps(SAMPLE_RESPONSE))
        # Missing-position and short-array rows are skipped
        assert len(result) == 2

    def test_first_aircraft_fields(self) -> None:
        result = adsb._parse_aircraft_states(json.dumps(SAMPLE_RESPONSE))
        a = result[0]
        assert a.icao24 == "abc123"
        assert a.callsign == "BA001"
        assert pytest.approx(a.latitude, abs=1e-4) == 51.477890
        assert pytest.approx(a.longitude, abs=1e-4) == -0.461941
        assert a.altitude_feet > 0
        assert not a.on_ground
        assert pytest.approx(a.velocity_mps, abs=0.1) == 245.4
        assert pytest.approx(a.heading_degrees, abs=0.1) == 92.0

    def test_altitude_converted_from_metres(self) -> None:
        result = adsb._parse_aircraft_states(json.dumps(SAMPLE_RESPONSE))
        a = result[0]
        expected_feet = 10972.8 * adsb.METRES_TO_FEET
        assert pytest.approx(a.altitude_feet, rel=1e-4) == expected_feet

    def test_on_ground_aircraft(self) -> None:
        result = adsb._parse_aircraft_states(json.dumps(SAMPLE_RESPONSE))
        a = result[1]
        assert a.icao24 == "def456"
        assert a.on_ground
        assert a.altitude_feet == 0.0

    def test_null_callsign_falls_back_to_icao(self) -> None:
        data = {
            "states": [
                [
                    "xyz000", None, "UK",
                    None, 1700000000,
                    -1.0, 52.0,
                    5000.0, False,
                    100.0, 180.0,
                    None, None, None, None, False, 0,
                ]
            ]
        }
        result = adsb._parse_aircraft_states(json.dumps(data))
        assert len(result) == 1
        assert result[0].callsign == "xyz000"

    def test_empty_states(self) -> None:
        data = {"time": 1700000000, "states": []}
        assert adsb._parse_aircraft_states(json.dumps(data)) == []

    def test_null_states_field(self) -> None:
        data = {"time": 1700000000, "states": None}
        assert adsb._parse_aircraft_states(json.dumps(data)) == []

    def test_missing_states_key(self) -> None:
        data = {"time": 1700000000}
        assert adsb._parse_aircraft_states(json.dumps(data)) == []


class TestAircraftDataclass:
    def test_aircraft_fields(self) -> None:
        a = adsb.Aircraft(
            icao24="aaa111",
            callsign="TEST",
            latitude=51.5,
            longitude=-0.1,
            altitude_feet=35000.0,
            on_ground=False,
            velocity_mps=250.0,
            heading_degrees=90.0,
        )
        assert a.icao24 == "aaa111"
        assert a.on_ground is False
