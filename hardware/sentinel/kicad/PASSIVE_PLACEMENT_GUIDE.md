# Passive Component Placement Guide — Capacitors, Resistors & Small Parts

All coordinates in mm. Place each component: **Click → Press E → type X, Y**.

> [!IMPORTANT]
> Place ALL **main ICs first** using the [Component Placement Guide](file:///C:/Users/dhruv/CARVanta/hardware/sentinel/kicad/COMPONENT_PLACEMENT_GUIDE.md), then use this file to place passives.

> [!TIP]
> **Minimum spacing rules used in this guide:**
> - 0402 to 0402: **1.5mm** center-to-center minimum (courtyard 1.5×0.8mm)
> - 0805 to 0805: **3mm** center-to-center minimum (courtyard 2.5×1.8mm)
> - 0402 to IC edge: **1.5mm** from IC courtyard boundary
> - 0805 to IC edge: **2mm** from IC courtyard boundary
>
> All coordinates below respect these minimums.

---

## Power Section — USB Area

### Near J1 (USB-C at 1.5, 44) — courtyard X=0–10, Y=40–48

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| R1 | 5.1kΩ | 0402 | 12 | 42 | J1 CC1 pulldown |
| R2 | 5.1kΩ | 0402 | 12 | 46 | J1 CC2 pulldown |
| C2 | 1µF | 0402 | 12 | 44 | J1 VBUS bypass |
| C21 | 10µF | 0805 | 12 | 40 | VBUS bulk cap |

> [!NOTE]
> R1/R2 are placed 2mm right of J1 courtyard edge (X=10). Vertical spacing is 2mm.

---

## Power Section — BQ24075 Charger Area

### Near U13 (18, 40) — courtyard X=15–21, Y=37–43

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C1 | 10µF | 0805 | 13 | 38 | U13 VBUS input cap |
| C4 | 1µF | 0402 | 23 | 38 | U13 REGN cap |
| C5 | 100nF | 0402 | 15 | 34 | U13 BTST cap (near L3) |
| R3 | 10kΩ | 0402 | 23 | 42 | U13 CE pulldown |
| R4 | 10kΩ | 0402 | 13 | 44 | U13 OTG pulldown |
| R5 | 10kΩ | 0402 | 13 | 36 | U13 QON pullup |

> [!NOTE]
> C1 (0805) is placed 2mm left of U13 courtyard. C4 is 2mm right. R3/R4 are below U13.

---

## Power Section — TPS63020 Buck-Boost Area

### Near U14 (30, 40) — courtyard X=27.75–32.25, Y=38.25–41.75

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C3 | 10µF | 0805 | 26 | 43 | U14 VIN cap (input side) |
| C6 | 22µF | 0805 | 34 | 38 | U14 VOUT cap |
| C7 | 100nF | 0402 | 34 | 40 | U14 VOUT bypass |
| C8 | 22µF | 0805 | 34 | 43 | U14 output bulk cap |
| C9 | 100nF | 0402 | 26 | 38 | U14 VIN bypass |
| R3 | 10kΩ | 0402 | 34 | 45 | FB top divider |
| R4 | 10kΩ | 0402 | 36 | 45 | FB bottom divider |

---

## Power Section — TLV733 / AMS1117 LDO Area

### Near U16 (18, 50) — courtyard X=14.25–21.75, Y=48–52

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C10 | 10µF | 0805 | 12 | 50 | U16 input cap |
| C11 | 100nF | 0402 | 12 | 48 | U16 input bypass |
| C12 | 10µF | 0805 | 24 | 50 | U16 output cap (3V3_D) |
| C20 | 22µF | 0805 | 24 | 53 | U16 output bulk cap |

### Near U15 (30, 50) — courtyard X=28.25–31.75, Y=49–51

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C16 | 1µF | 0402 | 28 | 53 | U15 input cap |
| C17 | 1µF | 0402 | 32 | 53 | U15 output cap |

### Extra Power Caps

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C18 | 100nF | 0402 | 32 | 48 | Power rail bypass |
| C19 | 10µF | 0805 | 28 | 48 | Power rail bypass |

---

## Power Section — MAX17048 Fuel Gauge Area

### Near U17 (12, 56) — courtyard X=10.5–13.5, Y=54.5–57.5

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C13 | 100nF | 0402 | 9 | 54 | U17 VDD bypass |
| C14 | 10µF | 0805 | 9 | 58 | Battery bypass |
| C15 | 100nF | 0402 | 9 | 60 | Battery bypass |
| R6 | 10kΩ | 0402 | 15 | 58 | U17 QSTRT pullup |

---

## ESP32 Section

### Near U1 (25, 18) — courtyard X=16–34, Y=5.25–30.75

> [!WARNING]
> U1 is the LARGEST component (18×25.5mm courtyard). Passives must go OUTSIDE X=16–34, Y=5.25–30.75.

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C22 | 100nF | 0402 | 14 | 14 | U1 3V3 bypass 1 (near Pin 1) |
| C23 | 100nF | 0402 | 14 | 16 | U1 3V3 bypass 2 |
| C24 | 100nF | 0402 | 36 | 14 | U1 3V3 bypass 3 |
| C25 | 100nF | 0402 | 14 | 18 | U1 EN bypass (near Pin 3) |
| C26 | 100nF | 0402 | 36 | 17 | U1 3V3 bypass 4 |
| C27 | 22µF | 0805 | 36 | 21 | U1 bulk bypass |
| R7 | 10kΩ | 0402 | 4 | 16 | U1 EN pullup (near SW1) |
| R8 | 10kΩ | 0402 | 4 | 22 | U1 GPIO0 pullup (near SW2) |

> [!NOTE]
> Caps are split: C22, C23, C25 are on the left (X=14) and C24, C26, C27 are on the right (X=36), all placed below Y=13 to remain completely outside the ESP32 footprint's built-in antenna keepout zone. R7/R8 at X=4 (left of SW1/SW2).

---

## RP2040 Section

### Near U2 (65, 20) — courtyard X=60.75–69.25, Y=15.75–24.25

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C28 | 100nF | 0402 | 59 | 14 | U2 IOVDD bypass |
| C29 | 100nF | 0402 | 59 | 26 | U2 VREG_VIN bypass |
| C30 | 1µF | 0402 | 71 | 14 | U2 VREG_VOUT/DVDD cap |
| C31 | 1µF | 0402 | 71 | 26 | U2 DVDD cap |
| C34 | 15pF | 0402 | 55 | 15 | Y1 crystal load cap 1 |
| C35 | 15pF | 0402 | 55 | 19 | Y1 crystal load cap 2 |
| R9 | 10kΩ | 0402 | 59 | 26 | U2 RUN pullup |

> [!NOTE]
> C28–C31 are placed 1.5mm outside U2 courtyard edges. C34/C35 flanking Y1 at X=55.

### Near U3 (78, 20) — courtyard X=74.9–81.1, Y=17.4–22.6

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C32 | 100nF | 0402 | 73 | 16 | U2 USB_VDD bypass |
| C33 | 100nF | 0402 | 73 | 24 | U2 ADC_AVDD bypass |
| C36 | 100nF | 0402 | 82 | 18 | U3 Flash VCC bypass |
| R10 | 10kΩ | 0402 | 82 | 20 | U3 WP pullup |
| R11 | 10kΩ | 0402 | 82 | 22 | U3 HOLD pullup |
| R12 | 10kΩ | 0402 | 73 | 20 | U2 spare pullup |

> [!NOTE]
> C32/C33 at X=73 (left of U3). C36/R10/R11 at X=82 (right of U3). All clear of J13 at (85, 10).

---

## Electrochemical Section

### Near U4 (35, 65) — courtyard X=30.75–39.25, Y=60.75–69.25

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C37 | 100nF | 0402 | 29 | 59 | U4 AVDD1 bypass |
| C38 | 10nF | 0402 | 29 | 71 | U4 AVDD1 small cap |
| C39 | 100nF | 0402 | 41 | 59 | U4 AVDD2 bypass |
| C40 | 100nF | 0402 | 41 | 71 | U4 DVDD bypass |
| C41 | 1µF | 0402 | 29 | 61 | U4 VREF_2V5 cap |
| C42 | 1µF | 0402 | 41 | 61 | U4 VREF_1V82 cap |
| C43 | 1µF | 0402 | 29 | 69 | U4 VBIAS cap |
| C44 | 1µF | 0402 | 41 | 69 | U4 DVDD_REG cap |
| R13 | 10kΩ | 0402 | 35 | 73 | U4 RCAL precision |

> [!NOTE]
> Passives placed in a ring 1.5mm outside U4's courtyard. 2mm clear of each other.

### Near U5 (60, 65) — courtyard X=55.75–64.25, Y=60.75–69.25

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C45 | 100nF | 0402 | 54 | 59 | U5 AVDD1 bypass |
| C46 | 10nF | 0402 | 54 | 71 | U5 AVDD1 small cap |
| C47 | 100nF | 0402 | 66 | 59 | U5 AVDD2 bypass |
| C48 | 1µF | 0402 | 54 | 61 | U5 VREF_2V5 cap |
| C49 | 100nF | 0402 | 66 | 71 | U5 DVDD bypass |
| C50 | 1µF | 0402 | 66 | 61 | U5 VREF_1V82 cap |
| C51 | 1µF | 0402 | 54 | 69 | U5 VBIAS cap |
| C52 | 1µF | 0402 | 66 | 69 | U5 DVDD_REG cap |
| R14 | 10kΩ | 0402 | 60 | 73 | U5 RCAL precision |

---

## Optical Section

### Near U6 (88, 48) — courtyard X=86.25–89.75, Y=45.95–50.05

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C53 | 100nF | 0402 | 91 | 48 | U6 VDD bypass |

### LED Driver Resistors — near Q3–Q5 and LED1–3

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| R15 | 100Ω | 0402 | 84 | 34 | Q3 gate resistor (UV) |
| R16 | 100Ω | 0402 | 88 | 34 | Q4 gate resistor (Blue) |
| R17 | 100Ω | 0402 | 92 | 34 | Q5 gate resistor (White) |
| R18 | 68Ω | 0402 | 84 | 44 | LED1 current limit |
| R19 | 47Ω | 0402 | 88 | 44 | LED2 current limit |
| R20 | 100Ω | 0402 | 92 | 44 | LED3 current limit |

> [!NOTE]
> R15–R17 are 2mm above Q3–Q5. R18–R20 are 2mm below LED1–3. Aligned to same X as their MOSFETs/LEDs.

---

## Thermal Section

### Near Q2 (80, 78) and U12 (85, 78)

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| R21 | 100Ω | 0402 | 78 | 76 | Q2 gate resistor |
| R22 | 10kΩ | 0402 | 82 | 76 | Q2 gate pulldown |
| C59 | 100nF | 0402 | 87 | 76 | U12 VDD bypass |

---

## Sensors & Display Section

### Sensor IC Bypass Caps

| Ref | Value | Size | X | Y | Belongs To | Near IC |
|-----|-------|------|---|---|------------|---------|
| C54 | 100nF | 0402 | 48 | 43 | U7 VCC bypass | U7 (50,45) |
| C55 | 100nF | 0402 | 58 | 33 | U8 VDD bypass | U8 (60,35) |
| C56 | 100nF | 0402 | 72 | 33 | U9 VDD bypass | U9 (74,35) |
| C57 | 100nF | 0402 | 58 | 50 | U10 VCC bypass | U10 (60,48) |
| C58 | 100nF | 0402 | 72 | 50 | U11 VDD bypass | U11 (74,48) |

> [!NOTE]
> Each bypass cap is placed 2mm left of its parent IC, at the same Y or 2mm above. All are well separated.

### WS2812B LED Bypass Caps — near D1–D4

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| C60 | 100nF | 0402 | 53 | 9 | D1 bypass (D1 at 53, 4) |
| C61 | 100nF | 0402 | 60 | 9 | D2 bypass (D2 at 60, 4) |
| C62 | 100nF | 0402 | 67 | 9 | D3 bypass (D3 at 67, 4) |
| C63 | 100nF | 0402 | 74 | 9 | D4 bypass (D4 at 74, 4) |

> [!NOTE]
> Caps placed 5mm below LED center (Y=4+5=9). Same X as parent LED. WS2812B courtyard extends ±3.25mm, so Y=9 is clear of courtyard Y=0.75–7.25.

### Buzzer MOSFET Resistor

| Ref | Value | Size | X | Y | Belongs To |
|-----|-------|------|---|---|------------|
| R24 | 100Ω | 0402 | 82 | 16 | Q1 gate resistor (Q1 at 87, 16) |

---

## Quick Reference — All Passives Sorted by Ref

| Ref | X | Y | | Ref | X | Y | | Ref | X | Y |
|-----|---|---|-|-----|---|---|-|-----|---|---|
| C1 | 13 | 38 | | C22 | 14 | 14 | | C43 | 29 | 69 |
| C2 | 12 | 44 | | C23 | 14 | 16 | | C44 | 41 | 69 |
| C3 | 26 | 43 | | C24 | 36 | 14 | | C45 | 54 | 59 |
| C4 | 23 | 38 | | C25 | 14 | 18 | | C46 | 54 | 71 |
| C5 | 15 | 34 | | C26 | 36 | 17 | | C47 | 66 | 59 |
| C6 | 34 | 38 | | C27 | 36 | 21 | | C48 | 54 | 61 |
| C7 | 34 | 40 | | C28 | 59 | 14 | | C49 | 66 | 71 |
| C8 | 34 | 43 | | C29 | 59 | 26 | | C50 | 66 | 61 |
| C9 | 26 | 38 | | C30 | 71 | 14 | | C51 | 54 | 69 |
| C10 | 12 | 50 | | C31 | 71 | 26 | | C52 | 66 | 69 |
| C11 | 12 | 48 | | C32 | 73 | 16 | | C53 | 91 | 48 |
| C12 | 24 | 50 | | C33 | 73 | 24 | | C54 | 48 | 43 |
| C13 | 9 | 54 | | C34 | 55 | 15 | | C55 | 58 | 33 |
| C14 | 9 | 58 | | C35 | 55 | 19 | | C56 | 72 | 33 |
| C15 | 9 | 60 | | C36 | 82 | 18 | | C57 | 58 | 50 |
| C16 | 28 | 53 | | C37 | 29 | 59 | | C58 | 72 | 50 |
| C17 | 32 | 53 | | C38 | 29 | 71 | | C59 | 87 | 76 |
| C18 | 32 | 48 | | C39 | 41 | 59 | | C60 | 53 | 9 |
| C19 | 28 | 48 | | C40 | 41 | 71 | | C61 | 60 | 9 |
| C20 | 24 | 53 | | C41 | 29 | 61 | | C62 | 67 | 9 |
| C21 | 12 | 40 | | C42 | 41 | 61 | | C63 | 74 | 9 |

| Ref | X | Y | | Ref | X | Y |
|-----|---|---|-|-----|---|---|
| R1 | 12 | 42 | | R13 | 35 | 73 |
| R2 | 12 | 46 | | R14 | 60 | 73 |
| R3 | 34 | 45 | | R15 | 84 | 34 |
| R4 | 36 | 45 | | R16 | 88 | 34 |
| R5 | 13 | 36 | | R17 | 92 | 34 |
| R6 | 15 | 58 | | R18 | 84 | 44 |
| R7 | 4 | 16 | | R19 | 88 | 44 |
| R8 | 4 | 22 | | R20 | 92 | 44 |
| R9 | 59 | 26 | | R21 | 78 | 76 |
| R10 | 82 | 20 | | R22 | 82 | 76 |
| R11 | 82 | 22 | | R24 | 82 | 16 |
| R12 | 73 | 20 | | FB1 | 26 | 50 |
