/*
 * Power Manager — Implementation
 */

#include "power_manager.h"
#include <esp_sleep.h>

void PowerManager::begin() {
    pinMode(PIN_CHG_INT, INPUT_PULLUP);
    pinMode(PIN_BATT_ALT, INPUT_PULLUP);
    pinMode(PIN_PG_3V3, INPUT_PULLUP);
}

bool PowerManager::isCharging() {
    return digitalRead(PIN_CHG_INT) == LOW;  // Active low
}

bool PowerManager::isPowerGood() {
    return digitalRead(PIN_PG_3V3) == LOW;   // Active low
}

bool PowerManager::isBatteryAlert() {
    return digitalRead(PIN_BATT_ALT) == LOW;  // Active low
}

void PowerManager::configureWakeSource() {
    // Wake on timer or button press (SW1 on GPIO, routed via external pull)
    // Use EXT0 wakeup on CHG_INT (charge state change)
    esp_sleep_enable_ext0_wakeup((gpio_num_t)PIN_CHG_INT, 0);
}

void PowerManager::enterDeepSleep(uint32_t sleepSeconds) {
    Serial.printf("[PWR] Entering deep sleep for %lu seconds\n", sleepSeconds);
    Serial.flush();

    esp_sleep_enable_timer_wakeup(sleepSeconds * 1000000ULL);
    configureWakeSource();

    esp_deep_sleep_start();
    // Never returns
}

void PowerManager::checkCriticalBattery(float soc) {
    if (soc < BATTERY_CRITICAL && !isCharging()) {
        Serial.println("[PWR] CRITICAL BATTERY — entering deep sleep");
        enterDeepSleep(3600);  // Sleep for 1 hour
    }
}
