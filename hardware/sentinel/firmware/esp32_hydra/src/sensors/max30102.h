/*
 * MAX30102 Pulse Oximeter & Heart Rate Sensor Driver
 */

#pragma once

#include <Wire.h>
#include <cstdint>

class MAX30102 {
public:
    MAX30102(uint8_t addr = 0x57) : _addr(addr) {}

    bool begin(TwoWire& wire = Wire);
    void shutdown();
    void wakeup();

    // Configuration
    void setLEDCurrent(uint8_t redMA, uint8_t irMA);
    void setSampleRate(uint16_t rate);   // 50,100,200,400,800,1000,1600,3200
    void setPulseWidth(uint16_t us);     // 69,118,215,411

    // Read FIFO data
    uint16_t readFIFO(uint32_t* redBuf, uint32_t* irBuf, uint16_t maxSamples);

    // Processed values
    bool    readSpO2(float* spo2, float* heartRate, uint16_t sampleDurationMs = 4000);

private:
    uint8_t   _addr;
    TwoWire*  _wire;

    void     writeReg(uint8_t reg, uint8_t val);
    uint8_t  readReg(uint8_t reg);
    void     readMulti(uint8_t reg, uint8_t* buf, uint8_t len);

    // SpO2 algorithm helpers
    float    calculateRatio(uint32_t* red, uint32_t* ir, uint16_t len);
    float    ratioToSpO2(float ratio);
    float    detectHeartRate(uint32_t* ir, uint16_t len, uint16_t sampleRate);

    // Register map
    static constexpr uint8_t REG_INT_STATUS1  = 0x00;
    static constexpr uint8_t REG_INT_ENABLE1  = 0x02;
    static constexpr uint8_t REG_FIFO_WR_PTR  = 0x04;
    static constexpr uint8_t REG_OVF_COUNTER  = 0x05;
    static constexpr uint8_t REG_FIFO_RD_PTR  = 0x06;
    static constexpr uint8_t REG_FIFO_DATA    = 0x07;
    static constexpr uint8_t REG_FIFO_CONFIG  = 0x08;
    static constexpr uint8_t REG_MODE_CONFIG  = 0x09;
    static constexpr uint8_t REG_SPO2_CONFIG  = 0x0A;
    static constexpr uint8_t REG_LED1_PA      = 0x0C;  // Red
    static constexpr uint8_t REG_LED2_PA      = 0x0D;  // IR
    static constexpr uint8_t REG_MULTI_LED1   = 0x11;
    static constexpr uint8_t REG_TEMP_INT     = 0x1F;
    static constexpr uint8_t REG_TEMP_FRAC    = 0x20;
    static constexpr uint8_t REG_TEMP_CONFIG  = 0x21;
    static constexpr uint8_t REG_PART_ID      = 0xFF;
};
