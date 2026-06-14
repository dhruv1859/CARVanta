/*
 * OTA Update Manager
 */

#pragma once

#include <Arduino.h>
#include "config.h"

class OTAUpdater {
public:
    void begin(const char* hostname = "hydra-sentinel");
    void handle();  // call in loop
    bool isUpdating() const { return _updating; }

private:
    bool _updating = false;
};
