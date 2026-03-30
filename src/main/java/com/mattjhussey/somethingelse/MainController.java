package com.mattjhussey.somethingelse;

import javafx.application.Platform;
import javafx.concurrent.Worker;
import javafx.fxml.FXML;
import javafx.fxml.Initializable;
import javafx.scene.control.Label;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;

import java.net.URL;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.ResourceBundle;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

public class MainController implements Initializable {

    private static final Logger LOGGER = Logger.getLogger(MainController.class.getName());

    /** UK bounding box used for the OpenSky query. */
    static final double UK_LAT_MIN = 49.0;
    static final double UK_LON_MIN = -8.0;
    static final double UK_LAT_MAX = 61.5;
    static final double UK_LON_MAX = 2.0;

    private static final int REFRESH_INTERVAL_SECONDS = 15;

    @FXML private WebView mapWebView;
    @FXML private Label statusLabel;

    private WebEngine webEngine;
    private AdsbService adsbService;
    private ScheduledExecutorService scheduler;

    @Override
    public void initialize(URL location, ResourceBundle resources) {
        webEngine = mapWebView.getEngine();
        adsbService = new AdsbService();

        URL mapUrl = getClass().getResource("map.html");
        if (mapUrl != null) {
            webEngine.load(mapUrl.toExternalForm());
        }

        // Start the ADSB feed once the map page has fully loaded
        webEngine.getLoadWorker().stateProperty().addListener((obs, oldState, newState) -> {
            if (newState == Worker.State.SUCCEEDED) {
                startAdsbFeed();
            }
        });
    }

    private void startAdsbFeed() {
        scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "adsb-refresh");
            t.setDaemon(true);
            return t;
        });
        scheduler.scheduleAtFixedRate(this::refreshAircraft, 0, REFRESH_INTERVAL_SECONDS, TimeUnit.SECONDS);
    }

    private void refreshAircraft() {
        try {
            List<Aircraft> aircraft = adsbService.fetchAircraftInBounds(
                    UK_LAT_MIN, UK_LON_MIN, UK_LAT_MAX, UK_LON_MAX);
            Platform.runLater(() -> updateMap(aircraft));
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Failed to fetch ADSB data from OpenSky Network", e);
        }
    }

    private void updateMap(List<Aircraft> aircraft) {
        webEngine.executeScript("clearAircraft()");
        for (Aircraft a : aircraft) {
            webEngine.executeScript(buildUpdateScript(a));
        }
        String time = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
        statusLabel.setText("Updated: " + time + " | " + aircraft.size() + " aircraft");
    }

    /** Builds a JavaScript call to place one aircraft marker on the Leaflet map. */
    String buildUpdateScript(Aircraft a) {
        String callsign = a.getCallsign()
                .replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace("\n", "")
                .replace("\r", "");
        return String.format(
                "updateAircraft('%s',%f,%f,'%s',%d,%d,%b)",
                a.getIcao24(),
                a.getLatitude(),
                a.getLongitude(),
                callsign,
                (int) a.getAltitudeFeet(),
                (int) a.getHeadingDegrees(),
                a.isOnGround());
    }

    /** Called by {@link MapApplication#stop()} to release the scheduler thread. */
    public void shutdown() {
        if (scheduler != null) {
            scheduler.shutdownNow();
        }
    }
}
