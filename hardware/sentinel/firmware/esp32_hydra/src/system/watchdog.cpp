/*
 * Hardware Watchdog Timer — Implementation
 */

#include "watchdog.h"
#include <esp_task_wdt.h>

void Watchdog::begin(uint32_t timeoutSeconds) {
#if ENABLE_WATCHDOG
    esp_task_wdt_config_t wdtConfig = {
        .timeout_ms = timeoutSeconds * 1000,
        .idle_core_mask = (1 << 0) | (1 << 1),  // Watch both cores
        .trigger_panic = true
    };
    esp_task_wdt_init(&wdtConfig);
    esp_task_wdt_add(NULL);  // Add current task
    Serial.printf("[WDT] Watchdog started, timeout=%lus\n", timeoutSeconds);
#endif
}

void Watchdog::feed() {
#if ENABLE_WATCHDOG
    esp_task_wdt_reset();
#endif
}

void Watchdog::disable() {
#if ENABLE_WATCHDOG
    esp_task_wdt_delete(NULL);
#endif
}
