/*
 * Non-blocking Buzzer Controller — Implementation
 */

#include "buzzer.h"

void Buzzer::begin() {
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);
}

void Buzzer::startSequence(const ToneStep* steps, uint8_t len) {
    if (len > MAX_STEPS) len = MAX_STEPS;
    memcpy(_sequence, steps, len * sizeof(ToneStep));
    _seqLen   = len;
    _seqIdx   = 0;
    _playing  = true;
    _inPause  = false;
    _stepStart = millis();
    tone(PIN_BUZZER, _sequence[0].freq, _sequence[0].durationMs);
}

void Buzzer::update() {
    if (!_playing) return;

    unsigned long elapsed = millis() - _stepStart;

    if (!_inPause) {
        // Playing tone
        if (elapsed >= _sequence[_seqIdx].durationMs) {
            noTone(PIN_BUZZER);
            _inPause = true;
            _stepStart = millis();
        }
    } else {
        // In pause between notes
        if (elapsed >= _sequence[_seqIdx].pauseMs) {
            _seqIdx++;
            if (_seqIdx >= _seqLen) {
                _playing = false;
                return;
            }
            _inPause = false;
            _stepStart = millis();
            tone(PIN_BUZZER, _sequence[_seqIdx].freq, _sequence[_seqIdx].durationMs);
        }
    }
}

void Buzzer::bootChime() {
    static const ToneStep seq[] = {
        {1000, 100, 50},
        {1500, 100, 50},
        {2000, 150, 0}
    };
    startSequence(seq, 3);
}

void Buzzer::successBeep() {
    static const ToneStep seq[] = {
        {2000, 80, 30},
        {2500, 120, 0}
    };
    startSequence(seq, 2);
}

void Buzzer::errorBeep() {
    static const ToneStep seq[] = {
        {400, 200, 100},
        {300, 300, 0}
    };
    startSequence(seq, 2);
}

void Buzzer::lowBatteryWarning() {
    static const ToneStep seq[] = {
        {800, 100, 200},
        {800, 100, 200},
        {800, 100, 0}
    };
    startSequence(seq, 3);
}

void Buzzer::singleTone(uint16_t freq, uint16_t durationMs) {
    ToneStep seq = {freq, durationMs, 0};
    startSequence(&seq, 1);
}
