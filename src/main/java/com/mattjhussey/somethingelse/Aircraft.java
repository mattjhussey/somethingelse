package com.mattjhussey.somethingelse;

/**
 * Represents a single aircraft state vector from the OpenSky Network API.
 */
public class Aircraft {

    private final String icao24;
    private final String callsign;
    private final double latitude;
    private final double longitude;
    private final double altitudeFeet;
    private final boolean onGround;
    private final double velocityMps;
    private final double headingDegrees;

    public Aircraft(String icao24, String callsign, double latitude, double longitude,
                    double altitudeFeet, boolean onGround, double velocityMps, double headingDegrees) {
        this.icao24 = icao24;
        this.callsign = callsign;
        this.latitude = latitude;
        this.longitude = longitude;
        this.altitudeFeet = altitudeFeet;
        this.onGround = onGround;
        this.velocityMps = velocityMps;
        this.headingDegrees = headingDegrees;
    }

    public String getIcao24() { return icao24; }
    public String getCallsign() { return callsign; }
    public double getLatitude() { return latitude; }
    public double getLongitude() { return longitude; }
    public double getAltitudeFeet() { return altitudeFeet; }
    public boolean isOnGround() { return onGround; }
    public double getVelocityMps() { return velocityMps; }
    public double getHeadingDegrees() { return headingDegrees; }
}
