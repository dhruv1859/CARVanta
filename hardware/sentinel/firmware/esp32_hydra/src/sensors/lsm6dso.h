/*
 * LSM6DSO 6-Axis IMU Driver (Accelerometer + Gyroscope)
 */

#pragma once

#include <Wire.h>
#include <cstdint>

class LSM6DSO {
public:
    LSM6DSO(uint8_t addr = 0x6A) : _addr(addr) {}

    bool begin(TwoWire& wire = Wire);

    // Read processed values
    void readAccel(float& x, float& y, float& z);   // in g
    void readGyro(float& x, float& y, float& z);    // in dps
    float readTemperature();

    // Configuration
    void setAccelODR(uint16_t hz);     // 12.5, 26, 52, 104, 208, 416, 833
    void setGyroODR(uint16_t hz);
    void setAccelRange(uint8_t g);     // 2, 4, 8, 16
    void setGyroRange(uint16_t dps);   // 125, 250, 500, 1000, 2000

private:
    uint8_t   _addr;
    TwoWire*  _wire;
    float     _accelScale;  // mg/LSB
    float     _gyroScale;   // mdps/LSB

    void    writeReg(uint8_t reg, uint8_t val);
    uint8_t readReg(uint8_t reg);
    void    readMulti(uint8_t reg, uint8_t* buf, uint8_t len);

    static constexpr uint8_t REG_WHO_AM_I     = 0x0F;
    static constexpr uint8_t REG_CTRL1_XL     = 0x10;  // Accel config
    static constexpr uint8_t REG_CTRL2_G      = 0x11;  // Gyro config
    static constexpr uint8_t REG_CTRL3_C      = 0x12;  // Control
    static constexpr uint8_t REG_STATUS       = 0x1E;
    static constexpr uint8_t REG_TEMP_L       = 0x20;
    static constexpr uint8_t REG_OUTX_L_G     = 0x22;  // Gyro data start
    static constexpr uint8_t REG_OUTX_L_A     = 0x28;  // Accel data start
};
