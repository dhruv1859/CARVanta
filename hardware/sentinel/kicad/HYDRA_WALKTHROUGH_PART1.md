# Sentinel Mark II "HYDRA" — KiCad 10 Walkthrough (Part 1: Schematic)

## Phase 1: Create Project
1. File → New Project → Name: `Sentinel_HYDRA` → Location: same kicad folder
2. Open .kicad_sch → File → Page Settings → Size: A3, Title: Sentinel HYDRA v1.0

## Phase 2: Create 7 Hierarchical Sheets
Right-click canvas → Add Hierarchical Sheet. Create:
- `Power.kicad_sch`
- `ESP32.kicad_sch`
- `RP2040.kicad_sch`
- `Electrochemical.kicad_sch`
- `Optical.kicad_sch`
- `Thermal.kicad_sch`
- `Sensors_Display.kicad_sch`

For each sheet: double-click to enter → add hierarchical pins for cross-sheet signals using Ctrl+H.

---

## Sheet 1: POWER

### Components to Place (press A to add)

| Ref | Symbol | Value |
|-----|--------|-------|
| J1 | Connector:USB_C_Receptacle_USB2.0 | USB-C |
| U13 | (Generic IC 24-pin) | BQ25895 |
| U14 | (Generic IC 14-pin) | TPS63020 |
| U15 | Regulator_Linear:TPS7A20 | 3V3_ANALOG |
| U16 | Regulator_Linear:AMS1117-3.3 | 3V3_DIGITAL |
| U17 | (Generic IC 8-pin) | MAX17048 |
| J12 | Connector:Conn_01x02_Pin | Battery |
| L1 | Device:Inductor | 4.7µH |
| L2 | Device:Ferrite_Bead | 600Ω |
| FB1 | Device:Ferrite_Bead | 600Ω |

### USB-C (J1) Wiring
| J1 Pin | Connect To |
|--------|-----------|
| VBUS | BQ25895 VBUS (pin 1) |
| CC1 | 5.1kΩ → GND |
| CC2 | 5.1kΩ → GND |
| D+ | ESP32 GPIO20 (global label: USB_DP) |
| D- | ESP32 GPIO19 (global label: USB_DM) |
| GND | GND |
| SHIELD | GND |

### BQ25895 (U13) Wiring
| BQ25895 Pin | Connect To |
|-------------|-----------|
| VBUS | J1 VBUS via 10µF cap |
| PMID | 1µF to GND |
| SYS | TPS63020 VIN |
| BAT | J12 pin 1 (Battery+), 10µF to GND |
| REGN | 1µF to GND |
| BTST | 100nF to SW |
| SW | 2.2µH inductor → SYS |
| PGND | GND |
| SDA | Global label: I2C_SDA |
| SCL | Global label: I2C_SCL |
| CE | 10kΩ pulldown to GND |
| INT | Global label: CHG_INT |
| OTG | 10kΩ pulldown to GND |
| QON | 10kΩ pullup to SYS |

### TPS63020 (U14) Buck-Boost
| Pin | Connect To |
|-----|-----------|
| VIN | BQ25895 SYS |
| VOUT | Power symbol: **+3V3** (this IS the VSYS_3V3 / main 3.3V rail) |
| EN | VIN (always on) |
| PS/SYNC | GND (PWM mode) |
| PG | Global label: PG_3V3 |
| L1, L2 | 4.7µH inductor between them |
| GND | GND |
| VOUT caps | 22µF + 100nF to GND |
| VIN caps | 10µF + 100nF to GND |

### Analog LDO — TPS7A20 (U15)
| Pin | Connect To |
|-----|-----------|
| IN | **+3V3** power symbol via ferrite bead FB1 |
| OUT | Net label (Ctrl+L): `3V3_A` |
| EN | **+3V3** power symbol |
| GND | GND |
| Caps | 1µF in, 1µF out |

### Digital LDO — AMS1117-3.3 (U16)
| Pin | Connect To |
|-----|-----------|
| VI (IN) | **+3V3** power symbol + 10µF cap to GND |
| VO (OUT) | Net label (Ctrl+L): `3V3_D` + 22µF cap to GND |
| GND | GND power symbol |

> **Note**: `3V3_A` and `3V3_D` are **net labels** (Ctrl+L), NOT power symbols. They are used on downstream sheets to route the filtered rails.

### Fuel Gauge — MAX17048 (U17)
| Pin | Connect To |
|-----|-----------|
| VDD | **+3V3** power symbol, 100nF to GND |
| CELL | Global label (Ctrl+H): `VBAT` (battery voltage from J12 pin 1) |
| SDA | Global label: `I2C_SDA` |
| SCL | Global label: `I2C_SCL` |
| ALT | Global label: `BATT_ALT` |
| QSTRT | 10kΩ pullup to **+3V3** |
| GND | GND |

### Power Symbols & Flags (press P to open Power library)

| Symbol to Place | Search in Power lib | Purpose |
|---|---|---|
| `+3V3` | `+3V3` | Main 3.3V rail (TPS63020 VOUT) — place on every `+3V3` node |
| `GND` | `GND` | Ground — place on every GND pin |
| `VBAT` | `+VBAT` or type `VBAT` | Battery positive rail — J12 Pin 1 + BQ25895 BAT |
| `PWR_FLAG` | `PWR_FLAG` | **Required on: VBUS net, +3V3 net, VBAT net** to fix ERC errors |

> **VSYS_3V3 does NOT exist in KiCad's library.** Use the `+3V3` power symbol everywhere the walkthrough previously said VSYS_3V3.

> **PWR_FLAG placement**: Place one `PWR_FLAG` on: (1) the VBUS wire near J1, (2) the +3V3 wire near TPS63020 VOUT, (3) the VBAT wire near J12 pin 1. This tells KiCad these nets have a power source and clears ERC "power pin not driven" errors.

#### Battery Connector J12
| J12 Pin | Connect To |
|---------|----------|
| Pin 1 (BAT+) | Global label `VBAT` + 10µF cap to GND + PWR_FLAG |
| Pin 2 (BAT−) | GND power symbol |

#### L2 — DELETE
L2 (600Ω ferrite bead) is a duplicate of FB1. Select it → press Delete.

---

## Sheet 2: ESP32

### Components
| Ref | Symbol | Value |
|-----|--------|-------|
| U1 | RF_Module:ESP32-S3-WROOM-1 | ESP32-S3 |
| SW1 | Switch:SW_Push | RESET |
| SW2 | Switch:SW_Push | BOOT |
| C1-C4 | Device:C | 100nF, 100nF, 100nF, 22µF |
| R1-R4 | Device:R | 10kΩ each |

### ESP32 Pin Map

> **`3V3_D` is NOT a power symbol.** Use **Global label (Ctrl+H): `3V3_D`** on the ESP32 3V3 pin. This connects cross-sheet to AMS1117 (U16) VO on the Power sheet.

| ESP32 Pin | Net Label (Ctrl+L) or Global (Ctrl+H) | Purpose |
|-----------|---------------------------------------|---------|
| 3V3 | Global label (Ctrl+H): `3V3_D` | Power from AMS1117 |
| GND | GND power symbol | Ground |
| EN | 10kΩ pullup to **global label `3V3_D`** + SW1 to GND + 100nF to GND | Reset |
| GPIO0 | 10kΩ pullup to **global label `3V3_D`** + SW2 to GND | Boot |
| GPIO1 | Global: UART_TX_ESP | → RP2040 RX |
| GPIO2 | Global: UART_RX_ESP | ← RP2040 TX |
| GPIO3 | Global: LED_DATA | WS2812B chain |
| GPIO4 | Global: BUZZER | Buzzer MOSFET |
| GPIO5 | Global: I2C_SDA | Main I2C bus |
| GPIO6 | Global: I2C_SCL | Main I2C bus |
| GPIO7 | Global: TFT_DC | Display |
| GPIO8 | Global: TFT_CS | Display |
| GPIO9 | Global: TFT_RST | Display |
| GPIO10 | Global: TFT_BL | Backlight |
| GPIO11 | Global: SPI0_MOSI | TFT + SD |
| GPIO12 | Global: SPI0_SCK | TFT + SD |
| GPIO13 | Global: SPI0_MISO | TFT + SD |
| GPIO14 | Global: SD_CS | SD card |
| GPIO15 | Global: CHG_INT | From BQ25895 |
| GPIO16 | Global: BATT_ALT | From MAX17048 |
| GPIO17 | Global: PG_3V3 | Power good |
| GPIO19 | Global: USB_DM | USB D− (hardware fixed, cannot remap) |
| GPIO20 | Global: USB_DP | USB D+ (hardware fixed, cannot remap) |

### Bypass Caps
Place 3× 100nF + 1× 22µF between 3V3 and GND, right next to ESP32.

---

## Sheet 3: RP2040

### Components
| Ref | Symbol | Value |
|-----|--------|-------|
| U2 | MCU_RaspberryPi:RP2040 | RP2040 |
| U3 | Memory_Flash:W25Q16JV | 2MB Flash |
| Y1 | Device:Crystal | 12MHz |
| C5-C12 | Device:C | various |
| R5-R8 | Device:R | various |

### RP2040 Pin Map

> **`3V3_D` = Global label (Ctrl+H)** everywhere below — NOT a power symbol.
> **IOVDD** in the KiCad symbol is ONE pin representing all 4 physical IOVDD pads — connect it once.

| RP2040 Pin | Connect To | How |
|------------|------------|-----|
| IOVDD | Global label `3V3_D` + 100nF to GND | Ctrl+H |
| VREG_VIN | Global label `3V3_D` + 100nF to GND | Ctrl+H |
| VREG_VOUT | Wire directly to DVDD pin + 1µF to GND | Wire |
| DVDD | Connected to VREG_VOUT + 1µF to GND | Wire |
| USB_VDD | Global label `3V3_D` + 100nF to GND | Ctrl+H |
| ADC_AVDD | Global label `3V3_D` + 100nF to GND | Ctrl+H |
| GND | GND power symbol | P |
| XIN | 12MHz crystal pin 1, 15pF to GND | Wire |
| XOUT | 12MHz crystal pin 2, 15pF to GND | Wire |
| RUN | 10kΩ pullup to global label `3V3_D` | Ctrl+H |
| GPIO0 | Global: `UART_RX_RP` | Ctrl+H |
| GPIO1 | Global: `UART_TX_RP` | Ctrl+H |
| GPIO2 | Global: `AD5941_1_CS` | Ctrl+H |
| GPIO3 | Global: `AD5941_1_RST` | Ctrl+H |
| GPIO4 | Global: `AD5941_2_CS` | Ctrl+H |
| GPIO5 | Global: `AD5941_2_RST` | Ctrl+H |
| GPIO6 | Global: `SPI1_SCK` | Ctrl+H |
| GPIO7 | Global: `SPI1_MOSI` | Ctrl+H |
| GPIO8 | Global: `SPI1_MISO` | Ctrl+H |
| GPIO9 | Global: `AD5941_1_INT` | Ctrl+H |
| GPIO10 | Global: `AD5941_2_INT` | Ctrl+H |
| GPIO11 | Global: `I2C1_SDA` | Ctrl+H |
| GPIO12 | Global: `I2C1_SCL` | Ctrl+H |
| GPIO13 | Global: `HEATER_PWM` | Ctrl+H |
| GPIO14 | Global: `UV_LED_EN` | Ctrl+H |
| GPIO15 | Global: `BLUE_LED_EN` | Ctrl+H |
| GPIO16 | Global: `WHITE_LED_EN` | Ctrl+H |
| QSPI_SS | Wire to W25Q16 CS (pin 1) | Wire |
| QSPI_SCLK | Wire to W25Q16 CLK (pin 6) | Wire |
| QSPI_SD0 | Wire to W25Q16 DI (pin 5) | Wire |
| QSPI_SD1 | Wire to W25Q16 DO (pin 2) | Wire |
| QSPI_SD2 | Wire to W25Q16 WP (pin 3) + 10kΩ pullup to `3V3_D` | Wire |
| QSPI_SD3 | Wire to W25Q16 HOLD (pin 7) + 10kΩ pullup to `3V3_D` | Wire |
| SWDIO | Wire to J13 pin 2 (SWD debug connector) | Wire |
| SWCLK | Wire to J13 pin 4 (SWD debug connector) | Wire |

### UART Cross-Connect (CRITICAL)
```
ESP32 GPIO1 (TX) ──────→ RP2040 GPIO0 (RX)
ESP32 GPIO2 (RX) ←────── RP2040 GPIO1 (TX)
```

### W25Q16JV Flash (U3)
| Pin | Connect To |
|-----|-----------|
| 1 (CS) | RP2040 QSPI_SS |
| 2 (DO) | RP2040 QSPI_SD1 |
| 3 (WP) | 10kΩ to 3V3_D |
| 4 (GND) | GND |
| 5 (DI) | RP2040 QSPI_SD0 |
| 6 (CLK) | RP2040 QSPI_SCLK |
| 7 (HOLD) | 10kΩ to 3V3_D |
| 8 (VCC) | 3V3_D, 100nF to GND |

---

## Sheet 4: ELECTROCHEMICAL (2× AD5941)

### Components
| Ref | Symbol | Value |
|-----|--------|-------|
| U4 | (Generic IC 48-pin or custom) | AD5941 #1 |
| U5 | (Generic IC 48-pin or custom) | AD5941 #2 |
| J2-J9 | Connector:Conn_01x03_Pin | 8× sensor connectors |
| C13-C28 | Device:C | Bypass caps |
| R9-R12 | Device:R | RCAL 10kΩ |

### AD5941 #1 (U4) — Channels 1–4
| Pin | Connect To |
|-----|-----------|
| AVDD1 | 3V3_A, 100nF + 10µF to GND |
| AVDD2 | 3V3_A, 100nF to GND |
| DVDD | 3V3_D, 100nF to GND |
| IOVDD | 3V3_D, 100nF to GND |
| AGND | GND |
| DGND | GND |
| VREF_2V5 | 1µF to GND (internal ref bypass) |
| VREF_1V82 | 1µF to GND (internal ref bypass) |
| VBIAS_CAP | 1µF to GND |
| DVDD_REG_1V8 | 1µF to GND (internal regulator) |
| SCK | Global: SPI1_SCK |
| MOSI | Global: SPI1_MOSI |
| MISO | Global: SPI1_MISO |
| CS | Global: AD5941_1_CS |
| RESET | Global: AD5941_1_RST |
| INT0 | Global: AD5941_1_INT |
| AIN0 | J2 pin 1 (WE Ch1) |
| AIN1 | J3 pin 1 (WE Ch2) |
| AIN2 | J4 pin 1 (WE Ch3) |
| AIN3 | J5 pin 1 (WE Ch4) |
| CE0 | Sensor CE bus (Counter Electrode) |
| RE0 | Sensor RE bus (Reference Electrode) |
| SE0 | RTIA feedback |
| DE0 | Excitation out |
| RCAL0 | 10kΩ precision resistor |
| RCAL1 | Other end of 10kΩ |
| EP (exposed pad) | GND |

### AD5941 #2 (U5) — same wiring, different CS/RST/INT
- CS → AD5941_2_CS, RST → AD5941_2_RST, INT → AD5941_2_INT
- AIN0-3 → J6-J9 pin 1

### Sensor Connectors (J2–J9)
Each 3-pin connector:
| Pin | Signal |
|-----|--------|
| 1 | WE (Working Electrode) → AD5941 AINx |
| 2 | RE (Reference Electrode) → AD5941 RE0 |
| 3 | CE (Counter Electrode) → AD5941 CE0 |

---

## Sheet 5: OPTICAL

### Components
| Ref | Symbol | Value |
|-----|--------|-------|
| U6 | (Generic IC 8-pin) | AS7341 |
| LED1 | Device:LED | UV 365nm |
| LED2 | Device:LED | Blue 470nm |
| LED3 | Device:LED | White |
| R13-R15 | Device:R | Current limiting |
| Q3-Q5 | Transistor_FET:2N7002 | LED drivers |

### AS7341 (U6)
| Pin | Connect To |
|-----|-----------|
| VDD | 3V3_A, 100nF to GND |
| GND | GND |
| SDA | Global: I2C1_SDA |
| SCL | Global: I2C1_SCL |
| INT | Global: SPEC_INT (to RP2040 GPIO17 if available) |
| LDR | GPIO_LDR (optional) |
| NC pins | Leave unconnected |

### LED Drivers (each LED)
```
RP2040 GPIOx → 100Ω → 2N7002 Gate
                       2N7002 Source → GND
                       2N7002 Drain → LED cathode
                       LED anode → 3V3_D via current-limit R
```
| LED | Gate GPIO | Series R (anode) |
|-----|-----------|-----------------|
| UV 365nm | GPIO14 (UV_LED_EN) | 68Ω (20mA) |
| Blue 470nm | GPIO15 (BLUE_LED_EN) | 47Ω (20mA) |
| White | GPIO16 (WHITE_LED_EN) | 100Ω (15mA) |

---

## Sheet 6: THERMAL

### Components
| Ref | Symbol | Value |
|-----|--------|-------|
| U12 | (Generic IC 6-pin) | TMP117 |
| Q2 | Transistor_FET:AO3400 | Heater MOSFET |
| R16 | Device:R | 100Ω gate |
| R17 | Device:R | 10kΩ gate pulldown |

### TMP117 (U12)
| Pin | Connect To |
|-----|-----------|
| V+ | 3V3_A, 100nF to GND |
| GND | GND |
| SDA | Global: I2C1_SDA |
| SCL | Global: I2C1_SCL |
| ALERT | Global: TEMP_ALERT |
| ADD0 | GND (address 0x48) |

### Heater Driver
```
RP2040 GPIO13 (HEATER_PWM) → 100Ω → AO3400 Gate
                                     AO3400 Source → GND  
                                     AO3400 Drain → HTR1 pad
                                     HTR1 other pad → VSYS_3V3
10kΩ from Gate to GND (pulldown, heater OFF by default)
```

---

## Sheet 7: SENSORS & DISPLAY

### Components
| Ref | Symbol |
|-----|--------|
| U7 | Interface_I2C:TCA9548A |
| U8 | (Generic) MAX30102 |
| U9 | (Generic) MLX90614 |
| U10 | Timer:DS3231M |
| U11 | (Generic) LSM6DSO |
| J10 | Connector:Conn_01x14_Pin (TFT) |
| J11 | Connector:Conn_01x07_Pin (SD) |
| D1-D4 | LED:WS2812B |
| BZ1 | Device:Buzzer |
| Q1 | Transistor_FET:2N7002 |

### TCA9548A (U7) — I2C Mux
| Pin | Connect To |
|-----|-----------|
| SDA | Global: I2C_SDA |
| SCL | Global: I2C_SCL |
| VCC | 3V3_D, 100nF to GND |
| GND | GND |
| A0,A1,A2 | GND (address 0x70) |
| RESET | 3V3_D (always active) |
| SD0/SC0 | MAX30102 SDA/SCL |
| SD1/SC1 | MLX90614 SDA/SCL |
| SD2/SC2 | DS3231 SDA/SCL |
| SD3/SC3 | LSM6DSO SDA/SCL |
| SD4-SD7 | NC (spare) |

### Sensor Wiring (each gets 100nF bypass)
| Sensor | VDD | GND | I2C Channel |
|--------|-----|-----|------------|
| MAX30102 | 3V3_D | GND | Ch0 |
| MLX90614 | 3V3_D | GND | Ch1 |
| DS3231 | 3V3_D | GND | Ch2 |
| LSM6DSO | 3V3_D | GND | Ch3 |

### TFT Display (J10) — 14-pin FPC
| Pin | Signal |
|-----|--------|
| 1 | GND |
| 2 | 3V3_D |
| 3 | TFT_CS |
| 4 | TFT_DC |
| 5 | TFT_RST |
| 6 | SPI0_MOSI |
| 7 | SPI0_SCK |
| 8 | TFT_BL |
| 9-14 | GND |

### microSD (J11) — SPI mode
| Pin | Signal |
|-----|--------|
| 1 | SD_CS |
| 2 | SPI0_MOSI |
| 3 | GND |
| 4 | 3V3_D |
| 5 | SPI0_SCK |
| 6 | GND |
| 7 | SPI0_MISO |

### WS2812B Chain (D1→D2→D3→D4)
- D1 DIN ← Global: LED_DATA
- D1 DOUT → D2 DIN → D3 DIN → D4 DIN
- Each: VDD → 3V3_D, GND → GND, 100nF bypass per LED

### Buzzer
- GPIO4 → 100Ω → Q1 Gate
- Q1 Drain → BZ1 negative
- BZ1 positive → 3V3_D
- Q1 Source → GND

---

## ERC Checklist
1. Add PWR_FLAG on VBUS, BAT+, and any power net that has no driver
2. Add no-connect flags (Q) on unused pins
3. Run Inspect → ERC → fix ALL errors → target: 0
