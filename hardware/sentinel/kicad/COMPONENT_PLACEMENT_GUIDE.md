# Main Component Placement Guide — ICs, Connectors & Active Parts

All coordinates in mm. Place each component: **Click → Press E → type X, Y**.

> [!IMPORTANT]
> Place **these main components FIRST**, then place passives using the separate Passive Placement Guide.
> All coordinates are calculated with footprint courtyard clearances to prevent DRC overlap errors.

> [!TIP]
> **Before placing anything**, go to **File → Board Setup → Design Rules → Constraints** and set:
> - Min annular width: **0.05mm**
> - Min through-hole diameter: **0.15mm**
> - Copper to edge clearance: **0.25mm**
>
> Then go to **Design Rules → Solder Mask/Paste** and set:
> - Solder mask min bridge width: **0mm**

---

## Footprint Size Reference

Know what you're placing — these are the courtyard sizes (width × height in mm):

| Footprint | Courtyard (W×H) | Components |
|-----------|-----------------|------------|
| ESP32-S3-WROOM-1 | 18×25.5 | U1 |
| QFN-56 7×7mm | 8.5×8.5 | U2 (RP2040) |
| QFN-49 7×7mm | 8.5×8.5 | U4, U5 (AD5941) |
| WQFN-24 4×4mm | 5.5×5.5 | U13 (BQ24075), U7 (TCA9548A) |
| TPS63020 DSJR | 4.5×3.5 | U14 |
| SOT-223-3 | 7.5×4 | U16 |
| SOT-23-5 | 3.5×2 | U15 |
| SOT-23 | 3.2×2 | Q1–Q5 |
| SOIC-8 | 6.2×5.2 | U3 (Flash) |
| SOIC-16W | 11.5×8 | U10 (DS3231) |
| OLGA-8 2×3.1mm | 3.5×4.5 | U6 (AS7341) |
| OLGA-14 3.3×5.6mm | 5×7 | U8 (MAX30102) |
| SON 2×2mm | 3×3 | U17 (MAX17048) |
| TO-254 (MLX90614) | 8×9 | U9 |
| WSON-6 2×2mm | 3.5×3.5 | U12 (TMP117) |
| USB-C HRO | 10×8 | J1 |
| Tag-Connect 2050 | 7×5 | J13 |
| WS2812B 5×5mm | 6.5×6.5 | D1–D4 |
| Crystal 3.2×1.5mm | 5×3 | Y1 |
| Buzzer 12mm | 14×11 | BZ1 |
| NR-40xx Inductor | 5×5 | L3, L4 |
| SW_SPST_TL3342 | 4.5×3.5 | SW1, SW2 |
| LED_0805 | 2.5×1.5 | LED1–3 |
| Molex PicoBlade 3-pin | 6×4 | J2–J9 |
| JST PH 2-pin | 7×5 | J12 |
| Hirose FH12-14S FPC | 12×4 | J10 |
| microSD Molex | 14×16 | J11 |
| 0402 (C/R) | 1.5×0.8 | Most caps/resistors |
| 0805 (C) | 2.5×1.8 | C1,C3,C6,C8,C10,etc. |
| L_0402 | 1.5×0.8 | FB1 |

---

## Zone 1 — MCU Zone (top half, Y = 5–30)

### ESP32-S3 (U1)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U1** | **25** | **18** | ESP32-S3-WROOM (18×25.5mm body). Antenna faces TOP edge. Keep 5mm above Y=5 for antenna clearance. |

> [!WARNING]
> U1 courtyard extends from X=16 to X=34, Y=5.25 to Y=30.75. Keep ALL other components outside this zone.

### RP2040 + Flash (U2, U3)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U2** | **65** | **20** | RP2040 QFN-56 (7×7mm body). Center of digital zone. |
| **U3** | **78** | **20** | W25Q128 Flash SOIC-8. 8mm right of U2 center (min clearance: body gap ~4mm). |
| **Y1** | **57** | **17** | 12MHz Crystal. 4mm left of U2 edge. Close enough for signal integrity, far enough for clearance. |

### SWD Debug Header
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **J13** | **74** | **12** | Tag-Connect 2050. Below D4, clear of BZ1 and U3. |

### TFT Display Connector
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **J10** | **95** | **22** | FPC-14 connector. Right edge of board. |

### Buttons
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **SW1** | **6** | **18** | Reset button. Left edge, far from U1. |
| **SW2** | **6** | **24** | Boot button. Below SW1, 6mm gap. |

---

## Zone 2 — Power Zone (left side, Y = 32–60)

### USB-C Connector
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **J1** | **1.5** | **44** | USB-C. Sticks out from left edge. Body extends X=0–10, Y=40–48. |

### Charger IC (BQ24075)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U13** | **18** | **40** | WQFN-24 (4×4mm). Courtyard: X=15–21, Y=37–43. |

### Inductors
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **L3** | **18** | **34** | Charger inductor (5×5mm). Above U13, 3mm gap. |
| **L4** | **26** | **34** | Buck-boost inductor (5×5mm). Right of L3, 3mm gap. |

### Buck-Boost (TPS63020)
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U14** | **30** | **40** | TPS63020 (4.5×3.5mm). Right of U13, 4mm gap. |

### LDOs & Power Management
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U16** | **18** | **50** | AMS1117 SOT-223 (7.5×4mm). Below U13, 4mm gap. |
| **U15** | **30** | **50** | TPS7A20 SOT-23-5 (3.5×2mm). Below U14. |
| **FB1** | **26** | **50** | Ferrite bead 0402. Between U16 and U15. |
| **U17** | **12** | **56** | MAX17048 fuel gauge (3×3mm). Below-left. |

### Battery Connector
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **J12** | **5** | **56** | JST PH 2-pin (7×5mm). Left edge, near U17. |

---

## Zone 3 — WS2812B LED Strip (top edge, Y = 3–10)

| Ref | X | Y | Notes |
|-----|---|---|-------|
| **D1** | **53** | **4** | WS2812B (5×5mm). Start after ESP32 antenna keepout zone ends at X=49. |
| **D2** | **60** | **4** | 7mm spacing (courtyard 6.5mm, so 0.5mm gap). |
| **D3** | **67** | **4** | Continues rightward. |
| **D4** | **74** | **4** | Last LED. Ends before BZ1 courtyard. |

### Buzzer
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **BZ1** | **87** | **7** | Buzzer (14×11mm). Top-right, shifted right and down to stay inside PCB. |
| **Q1** | **87** | **16** | Buzzer driver SOT-23. Directly below BZ1. |

---

## Zone 4 — Electrochemical (bottom-center, Y = 58–76)

| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U4** | **35** | **65** | AD5941 #1 QFN-49 (7×7mm). Courtyard: X=30.75–39.25, Y=60.75–69.25. |
| **U5** | **60** | **65** | AD5941 #2 QFN-49 (7×7mm). 25mm right of U4. Courtyard: X=55.75–64.25. |

---

## Zone 5 — Sensor Array (right-center, Y = 32–55)

| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U7** | **50** | **45** | TCA9548A I2C MUX VQFN-24 (4×4mm). |
| **U8** | **60** | **35** | MAX30102 OLGA-14 (3.3×5.6mm). |
| **U10** | **60** | **48** | DS3231 RTC SOIC-16W (7.5×10.3mm). Keep 6mm from U7. |
| **U9** | **74** | **35** | MLX90614 TO-254 (8×9mm). Large package, needs space. |
| **U11** | **74** | **48** | LSM6DSO PQFN-14 (2.5×3mm). |

---

## Zone 6 — Optical (far right, Y = 35–55)

| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U6** | **88** | **48** | AS7341 spectral sensor OLGA-8 (2×3.1mm). |
| **Q3** | **84** | **36** | UV LED MOSFET SOT-23. |
| **Q4** | **88** | **36** | Blue LED MOSFET SOT-23. 4mm right of Q3. |
| **Q5** | **92** | **36** | White LED MOSFET SOT-23. 4mm right of Q4. |
| **LED1** | **84** | **42** | UV indicator LED 0805. Below Q3. |
| **LED2** | **88** | **42** | Blue indicator LED 0805. Below Q4. |
| **LED3** | **92** | **42** | White indicator LED 0805. Below Q5. |

---

## Zone 7 — Thermal (bottom-right, Y = 75–95)

| Ref | X | Y | Notes |
|-----|---|---|-------|
| **U12** | **85** | **78** | TMP117 WSON-6 (2×2mm). |
| **Q2** | **80** | **78** | Heater MOSFET SOT-23. |

---

## Zone 8 — Sensor Connectors (bottom edge, Y = 92–96)

| Ref | X | Y | Notes |
|-----|---|---|-------|
| **J2** | **16** | **95** | Sensor port 1 |
| **J3** | **24** | **95** | Sensor port 2 (8mm spacing) |
| **J4** | **32** | **95** | Sensor port 3 |
| **J5** | **40** | **95** | Sensor port 4 |
| **J6** | **52** | **95** | Sensor port 5 |
| **J7** | **60** | **95** | Sensor port 6 |
| **J8** | **68** | **95** | Sensor port 7 |
| **J9** | **76** | **95** | Sensor port 8 |

### microSD + Debug
| Ref | X | Y | Notes |
|-----|---|---|-------|
| **J11** | **92** | **58** | microSD slot (14×16mm). Right edge. |

---

## Visual Board Map

```
 0        10       20       30       40       50       60       70       80       90      100
 ┌─────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
 │         │        │        │        │        │  D1    │D2 D3 D4│        │ BZ1    │        │ 5
 │ SW1     │        │        │        │        │        │  J13   │        │        │        │ 10
 │         │        │ U1     │        │        │        │ Y1  U2 │   U3   │        │ J10    │ 20
 │ SW2     │        │(ESP32) │        │        │        │        │        │        │        │ 25
 │         │        │        │ L3  L4 │        │        │        │        │        │        │ 35
 │ J1      │   U13  │   U14  │        │        │ U7     │ U8     │ U9     │ Q3 Q4 Q5       │ 40
 │(USB-C)  │        │        │        │        │        │        │        │LED1,2,3│        │ 45
 │         │   U16  │FB U15  │        │        │   U10  │        │ U11    │   U6   │        │ 50
 │ J12 U17 │        │        │        │        │        │        │        │        │  J11   │ 55
 │         │        │        │   U4   │        │        │   U5   │        │        │        │ 65
 │         │        │        │(AD5941)│        │        │(AD5941)│        │        │        │ 70
 │         │        │        │        │        │        │        │  Q2 U12│        │        │ 78
 │         │        │        │        │        │        │        │        │        │        │ 85
 │   J2    │  J3    │  J4    │  J5    │  J6    │  J7    │  J8    │  J9    │        │        │ 95
 └─────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```
