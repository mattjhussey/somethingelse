package com.mattjhussey.somethingelse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Fetches live aircraft state vectors from the OpenSky Network REST API.
 * <p>
 * OpenSky Network: <a href="https://opensky-network.org">https://opensky-network.org</a>
 * API docs: <a href="https://openskynetwork.github.io/opensky-api/rest.html">REST API</a>
 * <p>
 * No authentication is required for anonymous access (rate-limited to ~1 request / 10 s).
 */
public class AdsbService {

    private static final String OPENSKY_API_URL = "https://opensky-network.org/api/states/all";
    private static final double METRES_TO_FEET = 3.28084;

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public AdsbService() {
        this.httpClient = HttpClient.newHttpClient();
        this.objectMapper = new ObjectMapper();
    }

    /** Package-private constructor used by tests to inject mocks. */
    AdsbService(HttpClient httpClient, ObjectMapper objectMapper) {
        this.httpClient = httpClient;
        this.objectMapper = objectMapper;
    }

    /**
     * Fetches aircraft currently within the given geographic bounding box.
     *
     * @param latMin southern latitude boundary
     * @param lonMin western longitude boundary
     * @param latMax northern latitude boundary
     * @param lonMax eastern longitude boundary
     * @return list of aircraft (may be empty if no data or on error)
     */
    public List<Aircraft> fetchAircraftInBounds(double latMin, double lonMin,
                                                double latMax, double lonMax)
            throws IOException, InterruptedException {

        String url = OPENSKY_API_URL
                + "?lamin=" + latMin
                + "&lomin=" + lonMin
                + "&lamax=" + latMax
                + "&lomax=" + lonMax;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Accept", "application/json")
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            return Collections.emptyList();
        }

        return parseAircraftStates(response.body());
    }

    /**
     * Parses the JSON response body from the OpenSky /states/all endpoint.
     * Each state vector is an array with the following indices:
     * <pre>
     *  0  icao24          (String)
     *  1  callsign        (String, may be null)
     *  2  origin_country  (String)
     *  3  time_position   (long, may be null)
     *  4  last_contact    (long)
     *  5  longitude       (double, may be null)
     *  6  latitude        (double, may be null)
     *  7  baro_altitude   (double, metres, may be null)
     *  8  on_ground       (boolean)
     *  9  velocity        (double, m/s, may be null)
     * 10  true_track      (double, degrees, may be null)
     * 11  vertical_rate   (double, may be null)
     * 12  sensors         (array, may be null)
     * 13  geo_altitude    (double, may be null)
     * 14  squawk          (String, may be null)
     * 15  spi             (boolean)
     * 16  position_source (int)
     * </pre>
     */
    List<Aircraft> parseAircraftStates(String json) throws IOException {
        JsonNode root = objectMapper.readTree(json);
        JsonNode states = root.get("states");
        if (states == null || states.isNull() || !states.isArray()) {
            return Collections.emptyList();
        }

        List<Aircraft> aircraft = new ArrayList<>();
        for (JsonNode state : states) {
            if (!state.isArray() || state.size() < 17) {
                continue;
            }

            String icao24 = state.get(0).asText("");
            JsonNode callsignNode = state.get(1);
            String callsign = (callsignNode.isNull() ? icao24 : callsignNode.asText(icao24)).trim();
            if (callsign.isEmpty()) {
                callsign = icao24;
            }

            JsonNode lonNode = state.get(5);
            JsonNode latNode = state.get(6);

            // Skip aircraft without a known position
            if (lonNode.isNull() || latNode.isNull()) {
                continue;
            }

            double longitude = lonNode.asDouble();
            double latitude = latNode.asDouble();

            JsonNode altNode = state.get(7);
            double altitudeFeet = altNode.isNull() ? 0.0 : altNode.asDouble() * METRES_TO_FEET;

            boolean onGround = !state.get(8).isNull() && state.get(8).asBoolean();

            JsonNode velNode = state.get(9);
            double velocityMps = velNode.isNull() ? 0.0 : velNode.asDouble();

            JsonNode trackNode = state.get(10);
            double headingDegrees = trackNode.isNull() ? 0.0 : trackNode.asDouble();

            aircraft.add(new Aircraft(icao24, callsign, latitude, longitude,
                    altitudeFeet, onGround, velocityMps, headingDegrees));
        }
        return aircraft;
    }
}
