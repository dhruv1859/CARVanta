/*
 * Non-blocking Buzzer Controller
 */

#pragma once

#include <Arduino.h>
#include "pins.h"

struct ToneStep {
    uint16_t freq;
    uint16_t durationMs;
    uint16_t pauseMs;
};

class Buzzer {
public:
    void begin();
    void update();  // call in loop

    void bootChime();
    void successBeep();
    void errorBeep();
    void lowBatteryWarning();
    void singleTone(uint16_t freq, uint16_t durationMs);

    bool isPlaying() const { return _playing; }

private:
    static constexpr uint8_t MAX_STEPS = 8;
    ToneStep      _sequence[MAX_STEPS];
    uint8_t       _seqLen = 0;
    uint8_t       _seqIdx = 0;
    unsigned long _stepStart = 0;
    bool          _playing = false;
    bool          _inPause = false;

    void startSequence(const ToneStep* steps, uint8_t len);
};
