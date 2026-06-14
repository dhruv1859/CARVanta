/*
 * Cloud Client — WiFi + HTTPS upload
 */

#pragma once

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "config.h"

class CloudClient {
public:
    void begin(const char* ssid, const char* password);
    bool connectWiFi(unsigned long timeoutMs = WIFI_CONNECT_TIMEOUT_MS);
    bool isConnected();
    bool uploadReading(const SensorReading& reading);
    String getDeviceID();

private:
    const char* _ssid;
    const char* _password;
    uint8_t     _retryCount = 0;

    unsigned long backoffDelay();
};
