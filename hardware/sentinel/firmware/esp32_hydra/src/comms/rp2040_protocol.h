/*
 * RP2040 Communication Protocol (ESP32 side)
 * JSON over UART with CRC8 integrity check
 */

#pragma once

#include <ArduinoJson.h>
#include <HardwareSerial.h>
#include "config.h"

class RP2040Link {
public:
    RP2040Link(HardwareSerial& serial) : _serial(&serial) {}

    void begin(unsigned long baud, int rxPin, int txPin);

    // High-level commands
    bool requestEchem(float channels[8]);
    bool requestEIS(float impedance[8], float phase[8]);
    bool requestSpectral(float channels[11]);
    bool requestThermal(float* temp, float* heaterTemp);
    bool setHeater(bool on, float targetTemp = 65.0f);
    bool setLED(const char* color, bool on);

    // Generic send/receive
    bool sendCommand(const char* cmd, JsonDocument* params = nullptr);
    bool receiveResponse(JsonDocument& doc, unsigned long timeoutMs = RP2040_CMD_TIMEOUT_MS);

    // Status
    bool isConnected();
    uint32_t getLastResponseTime() { return _lastResponseMs; }

private:
    HardwareSerial* _serial;
    uint32_t _lastResponseMs = 0;

    uint8_t crc8(const uint8_t* data, size_t len);
    void    appendCRC(String& msg);
    bool    verifyCRC(String& msg);
};
