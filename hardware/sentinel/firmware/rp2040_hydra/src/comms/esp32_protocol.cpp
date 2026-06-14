/*
 * ESP32 Communication Protocol — Implementation (RP2040 side)
 */

#include "esp32_protocol.h"

void ESP32Protocol::begin(unsigned long baud, int txPin, int rxPin) {
    _serial->setTX(txPin);
    _serial->setRX(rxPin);
    _serial->begin(baud);
}

uint8_t ESP32Protocol::crc8(const uint8_t* data, size_t len) {
    uint8_t crc = 0;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            crc = (crc & 0x80) ? (crc << 1) ^ 0x07 : (crc << 1);
        }
    }
    return crc;
}

void ESP32Protocol::appendCRC(String& msg) {
    uint8_t c = crc8((const uint8_t*)msg.c_str(), msg.length());
    char hex[4];
    snprintf(hex, sizeof(hex), "*%02X", c);
    msg += hex;
}

bool ESP32Protocol::verifyCRC(String& msg) {
    int starIdx = msg.lastIndexOf('*');
    if (starIdx < 0 || starIdx + 3 > (int)msg.length()) {
        // No CRC present — accept anyway for backward compatibility
        return true;
    }

    String payload = msg.substring(0, starIdx);
    String crcStr  = msg.substring(starIdx + 1, starIdx + 3);
    uint8_t received = (uint8_t)strtol(crcStr.c_str(), nullptr, 16);
    uint8_t computed = crc8((const uint8_t*)payload.c_str(), payload.length());

    if (received == computed) {
        msg = payload;
        return true;
    }
    return false;
}

bool ESP32Protocol::hasCommand() {
    return _serial->available() > 0;
}

bool ESP32Protocol::receiveCommand(JsonDocument& doc) {
    if (!_serial->available()) return false;

    String line = _serial->readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return false;

    if (!verifyCRC(line)) {
        Serial.println("[COMMS] CRC mismatch, ignoring");
        return false;
    }

    DeserializationError err = deserializeJson(doc, line);
    return !err;
}

void ESP32Protocol::sendResponse(const char* type, JsonDocument& data) {
    // Copy data into response with type field
    StaticJsonDocument<1024> resp;
    resp["type"] = type;

    // Merge data fields into response
    for (JsonPair kv : data.as<JsonObject>()) {
        resp[kv.key()] = kv.value();
    }

    String msg;
    serializeJson(resp, msg);
    appendCRC(msg);
    _serial->println(msg);
}

void ESP32Protocol::sendAck(const char* cmd) {
    StaticJsonDocument<128> resp;
    resp["type"] = "ack";
    resp["cmd"]  = cmd;

    String msg;
    serializeJson(resp, msg);
    appendCRC(msg);
    _serial->println(msg);
}

void ESP32Protocol::sendError(const char* cmd, const char* errorMsg) {
    StaticJsonDocument<256> resp;
    resp["type"]  = "error";
    resp["cmd"]   = cmd;
    resp["error"] = errorMsg;

    String msg;
    serializeJson(resp, msg);
    appendCRC(msg);
    _serial->println(msg);
}
