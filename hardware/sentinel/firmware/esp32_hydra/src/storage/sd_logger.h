/*
 * SD Card CSV Data Logger
 */

#pragma once

#include <SD.h>
#include <SPI.h>
#include "config.h"

class SDLogger {
public:
    bool begin(uint8_t csPin);
    bool logReading(const SensorReading& r);
    bool isReady() const { return _ready; }
    const char* currentFile() const { return _currentFile; }

private:
    bool  _ready = false;
    char  _currentFile[32];

    void generateFilename(const SensorReading& r);
    void writeHeader(File& f);
};
