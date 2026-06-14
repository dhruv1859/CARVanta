/*
 * TFT Display Manager
 */

#pragma once

#include <TFT_eSPI.h>
#include "config.h"

class Display {
public:
    void begin();
    void showSplash();
    void showDashboard(const SensorReading& r);
    void showError(const char* msg);
    void showWiFiStatus(bool connected, const char* ip = nullptr);
    void showBatteryBar(float soc);
    void showMeasuring(const char* phase);
    void setBrightness(uint8_t level);  // 0–255

private:
    TFT_eSPI _tft;

    void drawHeader(const char* title, float batterySoc);
    void drawDivider(int y);
};
