/*
 * Cloud Client — Implementation
 */

#include "cloud_client.h"

void CloudClient::begin(const char* ssid, const char* password) {
    _ssid     = ssid;
    _password = password;
    WiFi.mode(WIFI_STA);
}

bool CloudClient::connectWiFi(unsigned long timeoutMs) {
    if (WiFi.status() == WL_CONNECTED) return true;

    WiFi.begin(_ssid, _password);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < timeoutMs) {
        delay(250);
    }
    return WiFi.status() == WL_CONNECTED;
}

bool CloudClient::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

String CloudClient::getDeviceID() {
    uint64_t mac = ESP.getEfuseMac();
    char id[24];
    snprintf(id, sizeof(id), "%s_%04X%08X",
             DEVICE_ID_PREFIX,
             (uint16_t)(mac >> 32),
             (uint32_t)mac);
    return String(id);
}

unsigned long CloudClient::backoffDelay() {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, capped at 30s
    unsigned long delay_ms = CLOUD_BACKOFF_BASE_MS * (1UL << _retryCount);
    if (delay_ms > 30000) delay_ms = 30000;
    return delay_ms;
}

bool CloudClient::uploadReading(const SensorReading& r) {
    if (!isConnected()) {
        if (!connectWiFi()) return false;
    }

    HTTPClient http;
    http.begin(API_ENDPOINT);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(10000);

    // Build JSON payload
    StaticJsonDocument<2048> doc;
    doc["device_id"]   = getDeviceID();
    doc["firmware"]    = FW_VERSION;
    doc["battery_soc"] = r.battery_soc;
    doc["battery_v"]   = r.battery_voltage;
    doc["timestamp"]   = r.timestamp;

    // Electrochemical
    if (r.echem_valid) {
        JsonArray echem = doc.createNestedArray("electrochemical");
        for (int i = 0; i < 8; i++) echem.add(r.echem_channels[i]);
    }

    // EIS
    if (r.eis_valid) {
        JsonObject eis = doc.createNestedObject("eis");
        JsonArray imp = eis.createNestedArray("impedance");
        JsonArray pha = eis.createNestedArray("phase");
        for (int i = 0; i < 8; i++) {
            imp.add(r.eis_impedance[i]);
            pha.add(r.eis_phase[i]);
        }
    }

    // Spectral
    if (r.spectral_valid) {
        JsonArray spec = doc.createNestedArray("spectral");
        for (int i = 0; i < 11; i++) spec.add(r.spectral[i]);
    }

    // Vitals
    if (r.vitals_valid) {
        JsonObject vitals = doc.createNestedObject("vitals");
        vitals["spo2"]        = r.spo2;
        vitals["heart_rate"]  = r.heart_rate;
        vitals["ir_obj_temp"] = r.ir_object_temp;
        vitals["ir_amb_temp"] = r.ir_ambient_temp;
    }

    // Thermal
    if (r.thermal_valid) {
        JsonObject thermal = doc.createNestedObject("thermal");
        thermal["precision_temp"] = r.precision_temp;
        thermal["heater_temp"]    = r.heater_temp;
    }

    // Motion
    if (r.motion_valid) {
        JsonObject motion = doc.createNestedObject("motion");
        JsonArray accel = motion.createNestedArray("accel");
        JsonArray gyro  = motion.createNestedArray("gyro");
        for (int i = 0; i < 3; i++) {
            accel.add(r.accel[i]);
            gyro.add(r.gyro[i]);
        }
    }

    String payload;
    serializeJson(doc, payload);

    int responseCode = http.POST(payload);
    http.end();

    if (responseCode == 200 || responseCode == 201) {
        _retryCount = 0;
        return true;
    }

    _retryCount = (_retryCount < CLOUD_RETRY_MAX) ? _retryCount + 1 : CLOUD_RETRY_MAX;
    delay(backoffDelay());
    return false;
}
