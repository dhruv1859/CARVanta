# CARVanta Sentinel v2.0 — 6-Layer Medical-Grade PCB
## Multi-Channel Antigen Escape Detection System

### Why 6 Layers?

This board monitors **4 antigens simultaneously** (CD19, CD22, BCMA, GPRC5D),
meaning 4 independent electrochemical channels that MUST be electrically isolated
from each other and from the digital noise of the ESP32 + WiFi radio.

A 2-layer board cannot achieve this. Here's why each layer exists:

```
Layer 1 (F.Cu)  — Digital signals: SPI, I2C, UART, USB, GPIO
Layer 2 (GND)   — Continuous ground plane (EMI shield between digital & analog)
Layer 3 (INNER1)— Analog signals: 4× potentiostat outputs, ADC inputs, sensor traces
Layer 4 (PWR)   — Power planes: 3.3V_DIGITAL, 3.3V_ANALOG, 1.8V_CORE, VBAT
Layer 5 (INNER2)— High-speed: USB 2.0 differential pair, WiFi RF routing
Layer 6 (B.Cu)  — Component pads, ground pour, thermal relief
```

### Board Specifications

| Parameter | v1.0 (old) | v2.0 (new) |
|-----------|-----------|-----------|
| Dimensions | 80×55mm | 95×65mm |
| Layers | 2 | **6** |
| Channels | 1 antigen | **4 simultaneous** |
| ADC | 1× ADS1115 (16-bit) | **1× ADS1256 (24-bit, 8ch)** |
| Potentiostat | 1× LMP91000 | **4× LMP91000** |
| Power domains | 1 (3.3V) | **4 (3.3V_D, 3.3V_A, 1.8V, VBAT)** |
| Analog isolation | None | **Split ground plane + ferrite bead** |
| Data logging | None | **microSD + RTC** |
| Patient vitals | None | **MAX30102 SpO2/HR + MLX90614 temp** |
| Impedance control | No | **90Ω USB, 50Ω RF** |
| ESD protection | No | **TVS diodes on all I/O** |
| Cost per unit | $17 | **~$45-55** |

### Stackup (6-Layer, 1.6mm FR4)

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: F.Cu (Signal - Digital)          35µm copper   │
│   └─ SPI bus, I2C bus, UART, GPIO, LED data            │
├─────────────────────────────────────────────────────────┤
│ Prepreg: 0.2mm FR4 (εr=4.5)                            │
├─────────────────────────────────────────────────────────┤
│ Layer 2: GND (Solid Ground Plane)         35µm copper   │
│   └─ Continuous pour, NO cuts, NO traces                │
│   └─ Acts as EMI shield between digital L1 & analog L3 │
├─────────────────────────────────────────────────────────┤
│ Core: 0.36mm FR4                                        │
├─────────────────────────────────────────────────────────┤
│ Layer 3: INNER1 (Signal - Analog)         35µm copper   │
│   └─ 4× LMP91000 VOUT traces (guarded)                 │
│   └─ ADS1256 analog inputs (star routing)               │
│   └─ Sensor connector traces (kelvin connection)        │
├─────────────────────────────────────────────────────────┤
│ Prepreg: 0.2mm FR4                                      │
├─────────────────────────────────────────────────────────┤
│ Layer 4: PWR (Power Planes)               35µm copper   │
│   └─ Zone 1: 3.3V_DIGITAL (ESP32, TFT, LEDs)          │
│   └─ Zone 2: 3.3V_ANALOG (LMP91000s, ADS1256)         │
│   └─ Zone 3: VBAT (battery direct)                      │
│   └─ Zone 4: 1.8V (ESP32 core, if needed)              │
├─────────────────────────────────────────────────────────┤
│ Core: 0.36mm FR4                                        │
├─────────────────────────────────────────────────────────┤
│ Layer 5: INNER2 (High-Speed Signals)      35µm copper   │
│   └─ USB D+/D- differential pair (90Ω impedance)       │
│   └─ ESP32 antenna feed (50Ω microstrip)                │
│   └─ SD card high-speed data lines                      │
├─────────────────────────────────────────────────────────┤
│ Prepreg: 0.2mm FR4                                      │
├─────────────────────────────────────────────────────────┤
│ Layer 6: B.Cu (Signal + Ground Pour)      35µm copper   │
│   └─ Component pads (bottom-side ICs)                   │
│   └─ Ground pour for thermal dissipation                │
│   └─ Mounting hole connections                          │
└─────────────────────────────────────────────────────────┘
Total thickness: ~1.6mm
```

### Design Rules (Medical Grade)

| Rule | Value | Reason |
|------|-------|--------|
| Min trace width | 0.15mm (6mil) | JLCPCB 6-layer capability |
| Min clearance | 0.15mm | IPC-2221 Class 2 |
| USB diff pair | 0.18mm trace, 0.15mm gap | 90Ω impedance on L5 |
| Analog traces | 0.25mm, guarded | Noise rejection |
| Power traces | 0.5mm minimum | Current handling |
| Via size | 0.3mm drill, 0.6mm pad | Standard via |
| Via-in-pad | Allowed (filled & capped) | For QFN packages |
| Copper weight | 1oz (35µm) all layers | Standard |
| Surface finish | ENIG (gold) | Corrosion resistance, biocompat |
| Solder mask | Matte black | Premium aesthetic |
| Silkscreen | White, both sides | Component labels |
