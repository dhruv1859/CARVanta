/*
 * SD Card CSV Data Logger — Implementation
 */

#include "sd_logger.h"
#include "pins.h"

bool SDLogger::begin(uint8_t csPin) {
    if (!SD.begin(csPin)) {
        _ready = false;
        return false;
    }

    // Create log directory
    if (!SD.exists(SD_LOG_DIR)) {
        SD.mkdir(SD_LOG_DIR);
    }

    _ready = true;
    snprintf(_currentFile, sizeof(_currentFile), "%s/log.csv", SD_LOG_DIR);
    return true;
}

void SDLogger::generateFilename(const SensorReading& r) {
    snprintf(_currentFile, sizeof(_currentFile), "%s/%04d%02d%02d.csv",
             SD_LOG_DIR, r.year + 2000, r.month, r.day);
}

void SDLogger::writeHeader(File& f) {
    f.println("timestamp,year,month,day,hour,min,sec,"
              "ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,"
              "z1,z2,z3,z4,z5,z6,z7,z8,"
              "p1,p2,p3,p4,p5,p6,p7,p8,"
              "s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,"
              "spo2,hr,ir_obj,ir_amb,precision_temp,heater_temp,"
              "ax,ay,az,gx,gy,gz,batt_soc,batt_v");
}

bool SDLogger::logReading(const SensorReading& r) {
    if (!_ready) return false;

    generateFilename(r);

    bool newFile = !SD.exists(_currentFile);
    File file = SD.open(_currentFile, FILE_APPEND);
    if (!file) return false;

    if (newFile) writeHeader(file);

    // File rotation: check size
    if (file.size() > SD_MAX_FILE_SIZE) {
        file.close();
        // Append counter to filename
        char newName[40];
        snprintf(newName, sizeof(newName), "%s/%04d%02d%02d_%lu.csv",
                 SD_LOG_DIR, r.year + 2000, r.month, r.day, millis() / 1000);
        snprintf(_currentFile, sizeof(_currentFile), "%s", newName);
        file = SD.open(_currentFile, FILE_WRITE);
        if (!file) return false;
        writeHeader(file);
    }

    // Write CSV row
    file.printf("%lu,%d,%d,%d,%d,%d,%d,",
                r.timestamp, r.year + 2000, r.month, r.day,
                r.hour, r.minute, r.second);

    // Echem channels
    for (int i = 0; i < 8; i++) file.printf("%.4f,", r.echem_channels[i]);
    // EIS impedance
    for (int i = 0; i < 8; i++) file.printf("%.2f,", r.eis_impedance[i]);
    // EIS phase
    for (int i = 0; i < 8; i++) file.printf("%.2f,", r.eis_phase[i]);
    // Spectral
    for (int i = 0; i < 11; i++) file.printf("%.0f,", r.spectral[i]);
    // Vitals + thermal + motion + battery
    file.printf("%.1f,%.0f,%.1f,%.1f,%.2f,%.1f,",
                r.spo2, r.heart_rate, r.ir_object_temp, r.ir_ambient_temp,
                r.precision_temp, r.heater_temp);
    file.printf("%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%.1f,%.2f\n",
                r.accel[0], r.accel[1], r.accel[2],
                r.gyro[0], r.gyro[1], r.gyro[2],
                r.battery_soc, r.battery_voltage);

    file.close();
    return true;
}
