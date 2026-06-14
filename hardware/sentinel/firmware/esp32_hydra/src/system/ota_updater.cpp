/*
 * OTA Update Manager — Implementation
 */

#include "ota_updater.h"

#if ENABLE_OTA
#include <ArduinoOTA.h>
#endif

void OTAUpdater::begin(const char* hostname) {
#if ENABLE_OTA
    ArduinoOTA.setHostname(hostname);

    ArduinoOTA.onStart([this]() {
        _updating = true;
        Serial.println("[OTA] Update starting...");
    });

    ArduinoOTA.onEnd([this]() {
        _updating = false;
        Serial.println("[OTA] Update complete. Rebooting...");
    });

    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        Serial.printf("[OTA] Progress: %u%%\r", (progress / (total / 100)));
    });

    ArduinoOTA.onError([this](ota_error_t error) {
        _updating = false;
        Serial.printf("[OTA] Error[%u]: ", error);
        switch (error) {
            case OTA_AUTH_ERROR:    Serial.println("Auth Failed"); break;
            case OTA_BEGIN_ERROR:   Serial.println("Begin Failed"); break;
            case OTA_CONNECT_ERROR: Serial.println("Connect Failed"); break;
            case OTA_RECEIVE_ERROR: Serial.println("Receive Failed"); break;
            case OTA_END_ERROR:     Serial.println("End Failed"); break;
        }
    });

    ArduinoOTA.begin();
    Serial.printf("[OTA] Ready. Hostname: %s\n", hostname);
#endif
}

void OTAUpdater::handle() {
#if ENABLE_OTA
    ArduinoOTA.handle();
#endif
}
