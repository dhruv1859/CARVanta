/*
 * ESP32 Communication Protocol (RP2040 side)
 * Mirror of the ESP32's rp2040_protocol — JSON over UART with CRC8
 */

#pragma once

#include <ArduinoJson.h>
#include <cstdint>

class ESP32Protocol {
public:
    ESP32Protocol(HardwareSerial& serial) : _serial(&serial) {}

    void begin(unsigned long baud, int txPin, int rxPin);

    // Receive command from ESP32
    bool hasCommand();
    bool receiveCommand(JsonDocument& doc);

    // Send response to ESP32
    void sendResponse(const char* type, JsonDocument& data);
    void sendAck(const char* cmd);
    void sendError(const char* cmd, const char* errorMsg);

private:
    HardwareSerial* _serial;

    uint8_t crc8(const uint8_t* data, size_t len);
    void    appendCRC(String& msg);
    bool    verifyCRC(String& msg);
};
