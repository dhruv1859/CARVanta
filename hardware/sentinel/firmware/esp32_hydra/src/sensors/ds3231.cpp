/*
 * DS3231 Real-Time Clock — Implementation
 */

#include "ds3231.h"

uint8_t DS3231::bcdToDec(uint8_t bcd) {
    return ((bcd >> 4) * 10) + (bcd & 0x0F);
}

uint8_t DS3231::decToBcd(uint8_t dec) {
    return ((dec / 10) << 4) | (dec % 10);
}

void DS3231::writeReg(uint8_t reg, uint8_t val) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->write(val);
    _wire->endTransmission();
}

uint8_t DS3231::readReg(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)1);
    return _wire->available() ? _wire->read() : 0;
}

bool DS3231::begin(TwoWire& wire) {
    _wire = &wire;
    // Test by reading status register
    _wire->beginTransmission(_addr);
    _wire->write(0x0F);  // Status register
    if (_wire->endTransmission() != 0) return false;

    // Disable 32kHz output, clear oscillator stop flag
    uint8_t status = readReg(0x0F);
    writeReg(0x0F, status & ~0x88);

    // Enable oscillator (clear EOSC bit in control register)
    uint8_t control = readReg(0x0E);
    writeReg(0x0E, control & ~0x80);

    return true;
}

DateTime DS3231::getDateTime() {
    DateTime dt;
    _wire->beginTransmission(_addr);
    _wire->write(0x00);  // Start at seconds register
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)7);

    if (_wire->available() >= 7) {
        dt.second    = bcdToDec(_wire->read() & 0x7F);
        dt.minute    = bcdToDec(_wire->read() & 0x7F);
        dt.hour      = bcdToDec(_wire->read() & 0x3F);
        dt.dayOfWeek = bcdToDec(_wire->read() & 0x07);
        dt.day       = bcdToDec(_wire->read() & 0x3F);
        dt.month     = bcdToDec(_wire->read() & 0x1F);
        dt.year      = 2000 + bcdToDec(_wire->read());
    }
    return dt;
}

void DS3231::setDateTime(const DateTime& dt) {
    _wire->beginTransmission(_addr);
    _wire->write(0x00);
    _wire->write(decToBcd(dt.second));
    _wire->write(decToBcd(dt.minute));
    _wire->write(decToBcd(dt.hour));
    _wire->write(decToBcd(dt.dayOfWeek));
    _wire->write(decToBcd(dt.day));
    _wire->write(decToBcd(dt.month));
    _wire->write(decToBcd(dt.year - 2000));
    _wire->endTransmission();
}

float DS3231::getTemperature() {
    _wire->beginTransmission(_addr);
    _wire->write(0x11);  // Temp MSB
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)2);

    if (_wire->available() >= 2) {
        int8_t  msb = _wire->read();
        uint8_t lsb = _wire->read();
        return (float)msb + (lsb >> 6) * 0.25f;
    }
    return -999.0f;
}

uint32_t DS3231::getEpoch() {
    DateTime dt = getDateTime();
    // Simplified: seconds since 2000-01-01 00:00:00
    // Not accounting for leap years precisely
    uint32_t days = 0;
    for (uint16_t y = 2000; y < dt.year; y++) {
        days += (y % 4 == 0) ? 366 : 365;
    }
    static const uint8_t daysInMonth[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    for (uint8_t m = 1; m < dt.month; m++) {
        days += daysInMonth[m - 1];
        if (m == 2 && (dt.year % 4 == 0)) days++;
    }
    days += dt.day - 1;

    return days * 86400UL + dt.hour * 3600UL + dt.minute * 60UL + dt.second;
}
