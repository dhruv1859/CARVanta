# CARVanta Sentinel v2.0 — Bill of Materials
# 6-Layer, 4-Channel Medical-Grade PCB

## U — Integrated Circuits

| Ref | Component | Part Number | Package | Qty | Price | Notes |
|-----|-----------|-------------|---------|-----|-------|-------|
| U1 | MCU + WiFi/BLE | ESP32-S3-WROOM-1-N8R8 | Module | 1 | $3.50 | 8MB Flash + 8MB PSRAM |
| U2 | USB-C PD Controller | CH224K | ESSOP-10 | 1 | $0.35 | Negotiates 5V/9V |
| U3 | LiPo Charger IC | BQ24075RGTR | QFN-16 | 1 | $1.80 | 1.5A, power path management |
| U4 | 3.3V Digital LDO | TPS7A2033 | SOT-23-5 | 1 | $0.60 | Ultra-low noise, 300mA |
| U5 | 3.3V Analog LDO | TPS7A4533 | SOT-23-5 | 1 | $0.85 | Ultra-low noise, analog supply |
| U6 | 1.8V Core LDO | AP2112K-1.8 | SOT-23-5 | 1 | $0.15 | ESP32 core (optional) |
| U7 | Battery Fuel Gauge | MAX17048 | DFN-8 | 1 | $1.20 | I2C, battery SOC reporting |
| U8 | Battery Protection | BQ29700 | SOT-23-6 | 1 | $0.30 | OVP/UVP/OCP |
| U9-U12 | Potentiostat (×4) | LMP91000 | VSSOP-14 | 4 | $4.50 | One per antigen channel |
| U13 | 24-bit ADC (8-ch) | ADS1256IDBR | SSOP-28 | 1 | $8.50 | 30kSPS, PGA, SPI interface |
| U14 | I2C Mux (for LMP91000) | TCA9548A | TSSOP-24 | 1 | $1.10 | 8-ch I2C multiplexer |
| U15 | SpO2/Heart Rate Sensor | MAX30102 | OLGA-14 | 1 | $3.50 | Integrated LED + photodetector |
| U16 | IR Temperature Sensor | MLX90614ESF | TO-39 | 1 | $4.80 | Contactless, medical grade |
| U17 | Real-Time Clock | DS3231MZ+ | SOIC-8 | 1 | $2.50 | ±2ppm, I2C, battery backup |
| U18 | microSD Card Slot | TF-PUSH | SMD | 1 | $0.30 | SPI mode for data logging |
| U19 | IMU (Fall Detection) | LSM6DSO | LGA-14 | 1 | $2.00 | Accel + gyro, I2C |
| U20-U23 | ESD Protection (×4) | USBLC6-2SC6 | SOT-23-6 | 4 | $0.15 | TVS on USB, sensor, I2C |
| U24 | Analog Switch | TS5A3159 | SOT-23-5 | 1 | $0.25 | Channel select for calibration |
| U25 | Level Shifter | TXB0104 | TSSOP-14 | 1 | $0.45 | 3.3V ↔ 1.8V if needed |

## J — Connectors

| Ref | Component | Part Number | Package | Qty | Price |
|-----|-----------|-------------|---------|-----|-------|
| J1 | USB Type-C Receptacle | TYPE-C-31-M-12 | SMD 16-pin | 1 | $0.25 |
| J2 | Sensor Port 1 (WE/RE/CE) | Molex 53047-0310 | 1.25mm 3P | 1 | $0.12 |
| J3 | Sensor Port 2 | Molex 53047-0310 | 1.25mm 3P | 1 | $0.12 |
| J4 | Sensor Port 3 | Molex 53047-0310 | 1.25mm 3P | 1 | $0.12 |
| J5 | Sensor Port 4 | Molex 53047-0310 | 1.25mm 3P | 1 | $0.12 |
| J6 | TFT Display FPC | FPC 0.5mm 14P | SMD | 1 | $0.20 |
| J7 | Battery JST | JST-PH 2.0mm 2P | Through-hole | 1 | $0.05 |
| J8 | JTAG/Debug Header | 1×6 1.27mm | SMD | 1 | $0.15 |
| J9 | SpO2 Sensor Cable | FPC 0.5mm 6P | SMD | 1 | $0.15 |

## Display & UI

| Ref | Component | Part Number | Package | Qty | Price |
|-----|-----------|-------------|---------|-----|-------|
| LCD1 | 2.4" IPS TFT (320×240) | ST7789V, SPI | FPC | 1 | $3.50 |
| LED1-4 | RGB Status LEDs | WS2812B-2020 | 2020 | 4 | $0.08 |
| BZ1 | Piezo Buzzer (SMD) | MLT-5030 | 5×5mm | 1 | $0.20 |
| SW1 | Reset Button | TS-1187A | 3×6mm SMD | 1 | $0.03 |
| SW2 | Boot/User Button | TS-1187A | 3×6mm SMD | 1 | $0.03 |
| SW3 | Power Switch | MSK-12C02 | Slide SMD | 1 | $0.08 |

## Passive Components

| Ref | Value | Package | Qty | Notes |
|-----|-------|---------|-----|-------|
| **Analog Domain** |
| C_A1-C_A8 | 100nF X7R | 0402 | 8 | LMP91000 bypass (2 per IC) |
| C_A9-C_A12 | 10µF 10V | 0805 | 4 | Sensor reference caps |
| C_A13 | 1µF NP0 | 0603 | 1 | ADS1256 VREF filter |
| C_A14-C_A15 | 10nF NP0 | 0402 | 2 | ADS1256 input filter |
| R_A1-R_A16 | 10kΩ 0.1% | 0402 | 16 | Precision TIA feedback (4 per ch) |
| R_A17-R_A20 | 100kΩ 0.1% | 0402 | 4 | Calibration resistors |
| **Digital Domain** |
| C_D1-C_D10 | 100nF X7R | 0402 | 10 | IC bypass caps |
| C_D11-C_D14 | 10µF 10V | 0805 | 4 | Bulk decoupling |
| C_D15 | 22µF 10V | 0805 | 1 | ESP32 bulk cap |
| R_D1-R_D2 | 5.1kΩ | 0402 | 2 | USB-C CC resistors |
| R_D3 | 10kΩ | 0402 | 1 | I2C pull-up |
| R_D4 | 10kΩ | 0402 | 1 | I2C pull-up |
| R_D5-R_D8 | 0Ω | 0402 | 4 | Domain jumpers |
| **Power Domain** |
| C_P1-C_P3 | 22µF 10V | 0805 | 3 | LDO output caps |
| C_P4-C_P6 | 100nF | 0402 | 3 | LDO input caps |
| C_P7 | 4.7µF 16V | 0805 | 1 | USB input cap |
| L1 | Ferrite Bead 600Ω@100MHz | 0402 | 1 | AGND-DGND bridge |
| L2 | Ferrite Bead 600Ω@100MHz | 0402 | 1 | AVDD filter |
| L3 | 10µH inductor | 1210 | 1 | Battery path filter |
| Y1 | 32.768kHz crystal | 2012 | 1 | RTC crystal |

## PCB Manufacturing (JLCPCB)

| Parameter | Spec |
|-----------|------|
| Layers | 6 |
| Dimensions | 95mm × 65mm |
| Thickness | 1.6mm |
| Copper weight | 1oz outer, 0.5oz inner |
| Surface finish | ENIG (Immersion Gold) |
| Solder mask | Matte Black |
| Silkscreen | White (both sides) |
| Via type | Tented vias, via-in-pad (filled) |
| Impedance control | YES (90Ω USB, 50Ω RF) |
| Min trace/space | 4mil/4mil |
| Qty 5 boards | ~$25-35 |
| SMT assembly | ~$15-20 per board |

## Total Cost per Unit

| Category | Cost |
|----------|------|
| PCB (6-layer, ENIG) | $6.00 |
| Components (LCSC) | $42.00 |
| SMT Assembly | $18.00 |
| **Total per board** | **~$66** |
| Battery + Display | $8.00 |
| Sensor electrodes | $5.00 |
| **Total complete unit** | **~$79** |

## Pin Assignment (ESP32-S3, v2.0)

| GPIO | Function | Layer | Domain |
|------|----------|-------|--------|
| GPIO0 | BOOT button | L1 | Digital |
| GPIO1 | ADS1256_DRDY (Data Ready) | L1→L3 via | Analog |
| GPIO2 | ADS1256_CS | L1 | Digital |
| GPIO3 | WS2812B LED Data | L1 | Digital |
| GPIO4 | Buzzer PWM | L1 | Digital |
| GPIO5 | I2C SDA (via TCA9548A mux) | L1 | Digital |
| GPIO6 | I2C SCL | L1 | Digital |
| GPIO7 | TFT DC | L1 | Digital |
| GPIO8 | TFT CS | L1 | Digital |
| GPIO9 | TFT RST | L1 | Digital |
| GPIO10 | TFT Backlight (PWM) | L1 | Digital |
| GPIO11 | SPI MOSI (shared: TFT + ADS1256 + SD) | L1/L5 | Digital |
| GPIO12 | SPI SCK | L1/L5 | Digital |
| GPIO13 | SPI MISO | L1/L5 | Digital |
| GPIO14 | SD Card CS | L5 | Digital |
| GPIO15 | Battery Sense (ADC) | L3 | Analog |
| GPIO16 | MAX30102 INT | L1 | Digital |
| GPIO17 | LSM6DSO INT1 | L1 | Digital |
| GPIO18 | Channel Select A | L1 | Digital |
| GPIO19 | Channel Select B | L1 | Digital |
| GPIO20 | USB D- | L5 | High-speed |
| GPIO21 | USB D+ | L5 | High-speed |
| GPIO35 | LMP91000 MENB[0] | L3 via | Analog |
| GPIO36 | LMP91000 MENB[1] | L3 via | Analog |
| GPIO37 | LMP91000 MENB[2] | L3 via | Analog |
| GPIO38 | LMP91000 MENB[3] | L3 via | Analog |
| GPIO43 | UART TX (Debug) | L1 | Digital |
| GPIO44 | UART RX (Debug) | L1 | Digital |
