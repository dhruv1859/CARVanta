# Sentinel Mark II "HYDRA" — KiCad 10 Walkthrough (Part 2: Footprints → PCB → Order)

## Phase 3: Assign Footprints

Tools → Assign Footprints. Use this table:

### ICs & Modules
| Component | KiCad Footprint |
|-----------|----------------|
| ESP32-S3-WROOM-1 | RF_Module:ESP32-S3-WROOM-1 |
| RP2040 | Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm |
| W25Q16JV | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm |
| AD5941 (×2) | Package_CSP:LFCSP-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm |
| AS7341 | Custom or OLGA-8 (3.1×2mm) — download from SnapEDA |
| TCA9548A | Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm |
| MAX30102 | Package_DFN_QFN:OLGA-14_3.3x5.6mm_P0.8mm |
| MLX90614 | Package_TO_SOT_THT:TO-39-4_Window |
| DS3231 | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm |
| LSM6DSO | Package_DFN_QFN:LGA-14_3x2.5mm_P0.5mm |
| TMP117 | Package_DFN_QFN:DSBGA-6_1.5x1.0mm |
| BQ25895 | Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm |
| TPS63020 | Package_DFN_QFN:QFN-14-1EP_3.5x4.5mm_P0.65mm |
| TPS7A20 | Package_TO_SOT_SMD:SOT-23-5 |
| AMS1117 | Package_TO_SOT_SMD:SOT-223-3_TabPin2 |
| MAX17048 | Package_DFN_QFN:DFN-8-1EP_2x2mm_P0.5mm |

### Connectors
| Component | KiCad Footprint |
|-----------|----------------|
| USB-C (J1) | Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12 |
| Sensor 3-pin (J2-J9) | Connector_Molex:Molex_PicoBlade_53047-0310 |
| TFT FPC (J10) | Connector_FFC-FPC:Hirose_FH12-14S-0.5SH |
| microSD (J11) | Connector_Card:microSD_HC_Molex_104031-0811 |
| Battery (J12) | Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical |
| SWD Debug (J13) | Connector:Tag-Connect_TC2050-IDC |

### Passives
| Component | KiCad Footprint |
|-----------|----------------|
| All 0402 caps (≤1µF) | Capacitor_SMD:C_0402_1005Metric |
| 0805 caps (10µF, 22µF) | Capacitor_SMD:C_0805_2012Metric |
| All 0402 resistors | Resistor_SMD:R_0402_1005Metric |
| 4.7µH inductor | Inductor_SMD:L_Taiyo-Yuden_NR-40xx |
| Ferrite bead | Inductor_SMD:L_0402_1005Metric |
| 12MHz crystal | Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm |

### Actuation
| Component | KiCad Footprint |
|-----------|----------------|
| WS2812B (D1-D4) | LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm |
| UV/Blue/White LED | LED_SMD:LED_0805_2012Metric |
| Buzzer | Buzzer_Beeper:Buzzer_12x9.5RM7.6 |
| 2N7002 MOSFET | Package_TO_SOT_SMD:SOT-23 |
| AO3400 MOSFET | Package_TO_SOT_SMD:SOT-23 |
| Tactile switch | Button_Switch_SMD:SW_SPST_TL3342 |

Click Apply → OK.

---

## Phase 4: PCB Layout

### Step 4.1 — Import to PCB
1. Open PCB Editor
2. Tools → Update PCB from Schematic (F8)
3. Click Update PCB → Close
4. All components appear in a cluster

### Step 4.2 — Board Setup
1. File → Board Setup → Board Stackup → Physical Stackup
2. Set Copper Layers: **6**
3. Rename layers:
   - F.Cu → Digital_Signals
   - In1.Cu → GND_Plane
   - In2.Cu → Analog_Signals
   - In3.Cu → Power_Planes
   - In4.Cu → HighSpeed
   - B.Cu → Bottom_GND
4. Thickness: 1.6mm total (default is fine)
5. Click OK

### Step 4.3 — Design Rules
Board Setup → Design Rules → Net Classes:

| Name | Clearance | Track Width | Via Size | Via Hole |
|------|-----------|------------|----------|----------|
| Default | 0.15 | 0.2 | 0.3 | 0.3 |
| Power | 0.2 | 0.5 | 0.6 | 0.4 |
| Analog | 0.2 | 0.25 | 0.5 | 0.3 |
| USB_DP | 0.15 | 0.18 | 0.3 | 0.3 |
| HighCurrent | 0.25 | 0.8 | 0.6 | 0.5 |

Netclass Assignments:
| Pattern | Net Class |
|---------|-----------|
| 3V3* | Power |
| GND | Power |
| VBAT | Power |
| VSYS* | Power |
| USB_D* | USB_DP |
| *VOUT* | Analog |
| SPI1* | Analog |

### Step 4.4 — Board Outline
1. Select layer: Edge.Cuts
2. Place → Line → draw 100mm × 100mm rectangle
3. Start at (0,0), corners at (100,0), (100,100), (0,100)

### Step 4.5 — Component Placement

Place components using: Click component → Press E → type X, Y.

#### MCU Zone (top half)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| U1 (ESP32) | 25 | 15 | Antenna at top edge |
| U2 (RP2040) | 65 | 20 | Center-right |
| U3 (Flash) | 75 | 20 | Next to RP2040 |
| Y1 (Crystal) | 60 | 18 | Near RP2040 XIN/XOUT |
| SW1 | 12 | 28 | Reset button |
| SW2 | 12 | 33 | Boot button |
| J13 (SWD) | 80 | 15 | Debug header |

#### Power Zone (left side)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| J1 (USB-C) | 5 | 45 | Left edge |
| U13 (BQ25895) | 18 | 40 | Near USB |
| L1 (inductor) | 22 | 35 | Buck-boost inductor |
| U14 (TPS63020) | 30 | 40 | Buck-boost |
| U15 (TPS7A20) | 30 | 50 | Analog LDO |
| U16 (AMS1117) | 18 | 50 | Digital LDO |
| U17 (MAX17048) | 12 | 55 | Fuel gauge |
| J12 (Battery) | 5 | 55 | Battery connector |
| FB1 | 28 | 50 | Analog ferrite |

#### Electrochemical Zone (bottom-center)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| U4 (AD5941 #1) | 35 | 65 | Channels 1-4 |
| U5 (AD5941 #2) | 60 | 65 | Channels 5-8 |
| J2-J5 | 25,35,45,55 | 90 | Sensor ports 1-4 |
| J6-J9 | 55,65,75,85 | 90 | Sensor ports 5-8 |

#### Optical Zone (right side)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| U6 (AS7341) | 85 | 45 | Spectral sensor |
| LED1 (UV) | 82 | 40 | UV excitation |
| LED2 (Blue) | 85 | 40 | Blue excitation |
| LED3 (White) | 88 | 40 | White reference |
| Q3-Q5 | 82,85,88 | 38 | LED MOSFETs |

#### Thermal Zone (bottom-right)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| U12 (TMP117) | 85 | 80 | Precision temp |
| Q2 (Heater FET) | 80 | 78 | Heater driver |
| HTR1 zone | 75-95 | 82-98 | Copper meander area |

#### Sensor Array (right side)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| U7 (TCA9548A) | 55 | 45 | I2C mux |
| U8 (MAX30102) | 65 | 35 | SpO2 |
| U9 (MLX90614) | 75 | 35 | IR temp |
| U10 (DS3231) | 65 | 45 | RTC |
| U11 (LSM6DSO) | 75 | 45 | IMU |

#### Display Zone (top-right)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| J10 (TFT FPC) | 95 | 20 | Right edge |
| D1-D4 (WS2812B) | 50,57,64,71 | 8 | LED strip |
| BZ1 (Buzzer) | 45 | 5 | Top area |
| Q1 (Buzzer FET) | 43 | 8 | Near buzzer |
| J11 (microSD) | 90 | 55 | Right side |

### Step 4.6 — Copper Zones (Ground & Power Planes)

**Zone 1 — GND Plane:**
1. Select In1.Cu → Place → Draw Filled Zone
2. Net: GND, Clearance: 0.3mm → OK
3. Draw rectangle over entire board → press B

**Zone 2 — Power Plane:**
1. Select In3.Cu → Place → Draw Filled Zone
2. Net: VSYS_3V3, Clearance: 0.3mm → OK
3. Draw rectangle over entire board → press B

**Zone 3 — Bottom GND:**
1. Select B.Cu → Place → Draw Filled Zone
2. Net: GND, Clearance: 0.3mm → OK
3. Draw rectangle over entire board → press B

Press **B** to fill all zones.

### Step 4.7 — Heater Trace (Thermal Zone)
1. Select B.Cu layer
2. Place → Line (graphic line) on B.Cu in a serpentine/meander pattern
3. Area: 20mm × 15mm at bottom-right
4. Trace width: 1mm, spacing: 0.5mm
5. Connect both ends to pads of Q2 drain and VSYS

---

## Phase 5: Routing

### Option A — Freerouting (Auto)
1. Tools → Freerouting → Export DSN
2. If Freerouting crashes, remove copper zones first (Edit → Select All on In1.Cu → Delete), export DSN, then re-add zones after import
3. Launch standalone: `& "C:\Program Files\Eclipse Adoptium\jre-25.0.3.9-hotspot\bin\java.EXE" -jar "c:\Users\dhruv\CARVanta\hardware\sentinel\kicad\freerouting.jar"`
4. File → Open → select .dsn file
5. Click Autorouter → wait
6. File → Save As → .ses file
7. Back in KiCad: File → Import → Specctra Session

### Option B — Manual Routing
Press X to route. Priority order:
1. **Analog traces** (In2.Cu): AD5941 ↔ sensor connectors — keep short
2. **SPI buses**: RP2040 ↔ AD5941 (SPI1), ESP32 ↔ TFT/SD (SPI0)
3. **I2C buses**: ESP32 ↔ TCA9548A, RP2040 ↔ AS7341/TMP117
4. **UART**: ESP32 ↔ RP2040 cross-connect
5. **Power**: Wide traces (0.5mm+) for VBUS, VSYS, battery
6. **USB**: Differential pair on In4.Cu

Press V while routing to add a via (switch layer).

---

## Phase 6: DRC
1. Inspect → Design Rules Checker
2. Run DRC
3. Fix all errors → target: 0 errors, 0 warnings
4. Common fixes: clearance → move trace, unconnected → route it

---

## Phase 7: Manufacturing Files

### Gerbers
1. File → Fabrication Outputs → Gerbers
2. Select layers: F.Cu, In1.Cu, In2.Cu, In3.Cu, In4.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts
3. Output: `\gerber\` folder
4. Click Plot

### Drill Files
1. File → Fabrication Outputs → Drill Files
2. Format: Excellon, Units: mm
3. Click Generate

### BOM + CPL
1. File → Fabrication Outputs → Component Placement
2. Generates pick-and-place CSV

---

## Phase 8: Order from JLCPCB

1. Go to jlcpcb.com → Order Now
2. Upload Gerber ZIP
3. Settings:
   - Layers: **6**
   - Thickness: **1.6mm**
   - Surface Finish: **ENIG** (gold pads)
   - Solder Mask: **Black**
   - Silkscreen: **White**
   - Via Covering: **Tented**
   - Impedance Control: **Yes** (90Ω USB)
4. Enable SMT Assembly → upload BOM.csv + CPL.csv
5. Estimated cost: **$80-120 for 5 boards assembled**
6. Shipping: 5-7 days DHL

---

## Component Count Summary

| Category | Count |
|----------|-------|
| ICs/Modules | 17 |
| Connectors | 13 |
| Capacitors | ~45 |
| Resistors | ~20 |
| Inductors/Ferrites | 3 |
| LEDs (WS2812B) | 4 |
| LEDs (Excitation) | 3 |
| MOSFETs | 4 |
| Switches | 2 |
| Crystal | 1 |
| Buzzer | 1 |
| **TOTAL** | **~113** |
