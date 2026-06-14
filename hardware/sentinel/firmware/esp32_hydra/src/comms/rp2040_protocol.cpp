/*
 * RP2040 Communication Protocol — Implementation
 */

#include "rp2040_protocol.h"

void RP2040Link::begin(unsigned long baud, int rxPin, int txPin) {
    _serial->begin(baud, SERIAL_8N1, rxPin, txPin);
}

uint8_t RP2040Link::crc8(const uint8_t* data, size_t len) {
    uint8_t crc = 0;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            crc = (crc & 0x80) ? (crc << 1) ^ 0x07 : (crc << 1);
        }
    }
    return crc;
}

void RP2040Link::appendCRC(String& msg) {
    uint8_t c = crc8((const uint8_t*)msg.c_str(), msg.length());
    char hex[4];
    snprintf(hex, sizeof(hex), "*%02X", c);
    msg += hex;
}

bool RP2040Link::verifyCRC(String& msg) {
    int starIdx = msg.lastIndexOf('*');
    if (starIdx < 0 || starIdx + 3 > (int)msg.length()) return false;

    String payload = msg.substring(0, starIdx);
    String crcStr  = msg.substring(starIdx + 1, starIdx + 3);
    uint8_t received = (uint8_t)strtol(crcStr.c_str(), nullptr, 16);
    uint8_t computed = crc8((const uint8_t*)payload.c_str(), payload.length());

    if (received == computed) {
        msg = payload;  // strip CRC
        return true;
    }
    return false;
}

bool RP2040Link::sendCommand(const char* cmd, JsonDocument* params) {
    StaticJsonDocument<256> doc;
    doc["cmd"] = cmd;
    doc["ts"]  = millis();
    if (params) {
        JsonObject p = doc.createNestedObject("params");
        for (JsonPair kv : params->as<JsonObject>()) {
            p[kv.key()] = kv.value();
        }
    }

    String msg;
    serializeJson(doc, msg);
    appendCRC(msg);
    _serial->println(msg);
    return true;
}

bool RP2040Link::receiveResponse(JsonDocument& doc, unsigned long timeoutMs) {
    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
        if (_serial->available()) {
            String line = _serial->readStringUntil('\n');
            line.trim();
            if (line.length() == 0) continue;

            if (!verifyCRC(line)) continue;  // CRC mismatch, skip

            DeserializationError err = deserializeJson(doc, line);
            if (!err) {
                _lastResponseMs = millis();
                return true;
            }
        }
        delay(1);
    }
    return false;
}

bool RP2040Link::requestEchem(float channels[8]) {
    for (uint8_t attempt = 0; attempt < RP2040_RETRY_COUNT; attempt++) {
        sendCommand("run_echem");
        StaticJsonDocument<1024> resp;
        if (receiveResponse(resp)) {
            if (strcmp(resp["type"], "echem") != 0) continue;
            JsonArray ch = resp["channels"];
            for (int i = 0; i < 8 && i < (int)ch.size(); i++)
                channels[i] = ch[i];
            return true;
        }
    }
    return false;
}

bool RP2040Link::requestEIS(float impedance[8], float phase[8]) {
    for (uint8_t attempt = 0; attempt < RP2040_RETRY_COUNT; attempt++) {
        sendCommand("run_eis");
        StaticJsonDocument<1024> resp;
        if (receiveResponse(resp, 10000)) {  // EIS takes longer
            if (strcmp(resp["type"], "eis") != 0) continue;
            JsonArray imp = resp["impedance"];
            JsonArray pha = resp["phase"];
            for (int i = 0; i < 8; i++) {
                impedance[i] = imp[i];
                phase[i]     = pha[i];
            }
            return true;
        }
    }
    return false;
}

bool RP2040Link::requestSpectral(float channels[11]) {
    for (uint8_t attempt = 0; attempt < RP2040_RETRY_COUNT; attempt++) {
        sendCommand("read_spectral");
        StaticJsonDocument<512> resp;
        if (receiveResponse(resp)) {
            if (strcmp(resp["type"], "spectral") != 0) continue;
            JsonArray ch = resp["channels"];
            for (int i = 0; i < 11 && i < (int)ch.size(); i++)
                channels[i] = ch[i];
            return true;
        }
    }
    return false;
}

bool RP2040Link::requestThermal(float* temp, float* heaterTemp) {
    for (uint8_t attempt = 0; attempt < RP2040_RETRY_COUNT; attempt++) {
        sendCommand("read_thermal");
        StaticJsonDocument<256> resp;
        if (receiveResponse(resp)) {
            if (strcmp(resp["type"], "thermal") != 0) continue;
            *temp       = resp["temp"];
            *heaterTemp = resp["heater"];
            return true;
        }
    }
    return false;
}

bool RP2040Link::setHeater(bool on, float targetTemp) {
    StaticJsonDocument<64> params;
    if (on) {
        params["temp"] = targetTemp;
        return sendCommand("heater_on", &params);
    }
    return sendCommand("heater_off");
}

bool RP2040Link::setLED(const char* color, bool on) {
    StaticJsonDocument<64> params;
    params["on"] = on;
    char cmd[16];
    snprintf(cmd, sizeof(cmd), "led_%s", color);
    return sendCommand(cmd, &params);
}

bool RP2040Link::isConnected() {
    return (millis() - _lastResponseMs) < 10000;  // 10s timeout
}
