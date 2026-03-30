package com.mattjhussey.somethingelse;

import org.junit.jupiter.api.Test;

import java.net.URL;

import static org.junit.jupiter.api.Assertions.assertNotNull;

class MapApplicationTest {

    @Test
    void mapHtmlResourceExists() {
        URL resource = MapApplicationTest.class.getResource("/com/mattjhussey/somethingelse/map.html");
        assertNotNull(resource, "map.html resource should be present on the classpath");
    }

    @Test
    void fxmlResourceExists() {
        URL resource = MapApplicationTest.class.getResource("/com/mattjhussey/somethingelse/main-view.fxml");
        assertNotNull(resource, "main-view.fxml resource should be present on the classpath");
    }
}
