/*
 * TFT Display Manager — Implementation
 */

#include "display.h"
#include "pins.h"

void Display::begin() {
    _tft.init();
    _tft.setRotation(1);  // Landscape
    _tft.fillScreen(TFT_BLACK);

    pinMode(PIN_TFT_BL, OUTPUT);
    setBrightness(TFT_BACKLIGHT_PWM);
}

void Display::setBrightness(uint8_t level) {
    analogWrite(PIN_TFT_BL, level);
}

void Display::drawHeader(const char* title, float batterySoc) {
    _tft.setTextColor(TFT_CYAN, TFT_BLACK);
    _tft.setTextSize(1);
    _tft.drawString(title, 10, 5);

    // Battery indicator
    uint16_t battColor = (batterySoc > 20) ? TFT_GREEN : TFT_RED;
    _tft.setTextColor(battColor, TFT_BLACK);
    char batt[16];
    snprintf(batt, sizeof(batt), "BAT:%.0f%%", batterySoc);
    _tft.drawString(batt, 260, 5);

    drawDivider(15);
}

void Display::drawDivider(int y) {
    _tft.drawLine(0, y, 320, y, TFT_DARKGREY);
}

void Display::showSplash() {
    _tft.fillScreen(TFT_BLACK);
    _tft.setTextColor(TFT_CYAN, TFT_BLACK);
    _tft.setTextSize(2);
    _tft.drawString("CARVanta HYDRA", 40, 40);
    _tft.setTextSize(1);
    _tft.setTextColor(TFT_WHITE, TFT_BLACK);
    _tft.drawString("Multimodal Diagnostic Engine", 30, 75);
    _tft.drawString("v" FW_VERSION, 130, 95);
    _tft.drawString("Initializing...", 100, 130);
}

void Display::showDashboard(const SensorReading& r) {
    _tft.fillScreen(TFT_BLACK);
    drawHeader("SENTINEL HYDRA v2.0", r.battery_soc);

    int y = 20;

    // Electrochemical
    if (r.echem_valid) {
        _tft.setTextColor(TFT_GREEN, TFT_BLACK);
        _tft.drawString("ECHEM (uA):", 10, y);
        y += 12;
        for (int i = 0; i < 8; i++) {
            char buf[16];
            snprintf(buf, sizeof(buf), "Ch%d:%.2f", i + 1, r.echem_channels[i]);
            _tft.drawString(buf, 10 + (i % 4) * 78, y + (i / 4) * 12);
        }
        y += 30;
    }

    // Spectral
    if (r.spectral_valid) {
        _tft.setTextColor(TFT_MAGENTA, TFT_BLACK);
        _tft.drawString("SPECTRAL:", 10, y);
        y += 12;
        for (int i = 0; i < 8; i++) {
            char buf[16];
            snprintf(buf, sizeof(buf), "F%d:%.0f", i + 1, r.spectral[i]);
            _tft.drawString(buf, 10 + (i % 4) * 78, y + (i / 4) * 12);
        }
        y += 30;
    }

    // Vitals
    if (r.vitals_valid) {
        drawDivider(y);
        y += 4;
        _tft.setTextColor(TFT_YELLOW, TFT_BLACK);
        char vitals[64];
        snprintf(vitals, sizeof(vitals), "SpO2:%.0f%%  HR:%.0f  Temp:%.1fC",
                 r.spo2, r.heart_rate, r.ir_object_temp);
        _tft.drawString(vitals, 10, y);
        y += 16;
    }

    // Thermal
    if (r.thermal_valid) {
        _tft.setTextColor(TFT_ORANGE, TFT_BLACK);
        char thermal[48];
        snprintf(thermal, sizeof(thermal), "Precision:%.2fC  Heater:%.1fC",
                 r.precision_temp, r.heater_temp);
        _tft.drawString(thermal, 10, y);
        y += 16;
    }

    // Motion
    if (r.motion_valid) {
        _tft.setTextColor(TFT_WHITE, TFT_BLACK);
        char motion[48];
        snprintf(motion, sizeof(motion), "Acc:%.2f,%.2f,%.2f g",
                 r.accel[0], r.accel[1], r.accel[2]);
        _tft.drawString(motion, 10, y);
    }

    // Timestamp
    char ts[24];
    snprintf(ts, sizeof(ts), "%04d-%02d-%02d %02d:%02d:%02d",
             r.year + 2000, r.month, r.day, r.hour, r.minute, r.second);
    _tft.setTextColor(TFT_DARKGREY, TFT_BLACK);
    _tft.drawString(ts, 10, 228);
}

void Display::showError(const char* msg) {
    _tft.fillRect(0, 200, 320, 40, TFT_BLACK);
    _tft.setTextColor(TFT_RED, TFT_BLACK);
    _tft.setTextSize(1);
    _tft.drawString(msg, 10, 210);
}

void Display::showWiFiStatus(bool connected, const char* ip) {
    _tft.fillRect(0, 115, 320, 15, TFT_BLACK);
    _tft.setTextSize(1);
    if (connected && ip) {
        _tft.setTextColor(TFT_GREEN, TFT_BLACK);
        char buf[32];
        snprintf(buf, sizeof(buf), "WiFi: %s", ip);
        _tft.drawString(buf, 10, 115);
    } else {
        _tft.setTextColor(TFT_RED, TFT_BLACK);
        _tft.drawString("WiFi: Disconnected", 10, 115);
    }
}

void Display::showBatteryBar(float soc) {
    int barW = (int)(soc * 0.5f);  // max 50px
    uint16_t color = (soc > 20) ? TFT_GREEN : TFT_RED;
    _tft.fillRect(300, 2, 18, 10, TFT_BLACK);
    _tft.drawRect(300, 2, 18, 10, TFT_WHITE);
    _tft.fillRect(301, 3, (int)(soc * 0.16f), 8, color);
}

void Display::showMeasuring(const char* phase) {
    _tft.fillRect(0, 200, 320, 40, TFT_BLACK);
    _tft.setTextColor(TFT_YELLOW, TFT_BLACK);
    _tft.setTextSize(1);
    char buf[48];
    snprintf(buf, sizeof(buf), "Measuring: %s...", phase);
    _tft.drawString(buf, 80, 210);
}
