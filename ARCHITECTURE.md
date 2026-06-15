# CARVanta — System Architecture

> Comprehensive technical architecture of the CARVanta AI Immunotherapy Platform and Sentinel HYDRA biosensor hardware.

---

## System Overview

CARVanta is a **closed-loop immunotherapy intelligence system** comprising two tightly integrated subsystems:

1. **Software Platform** — Cloud-deployed AI engine for antigen target scoring, genomic analysis, digital twin simulation, and clinical decision support
2. **Sentinel HYDRA** — Bedside biosensor hardware for real-time multi-channel antigen monitoring with cloud telemetry

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PATIENT INTERFACE                                    │
│                                                                              │
│   [Fingerprick Blood Sample]  ──►  [Disposable Sensor Strip]                │
│                                            │                                 │
│                                            ▼                                 │
│   ┌──────────────────────────────────────────────────────────┐              │
│   │              SENTINEL HYDRA (Bedside Device)              │              │
│   │                                                           │              │
│   │   RP2040 ◄──UART──► ESP32-S3                             │              │
│   │   • 4× LMP91000      • WiFi/BLE                          │              │
│   │   • ADS1256 24-bit    • TFT Display                      │              │
│   │   • AS7341 Spectral   • SD Logging                       │              │
│   │   • TMP117/MLX90614   • Cloud Upload                     │              │
│   │   • MAX30102 SpO2     • OTA Updates                      │              │
│   └──────────────┬───────────────────────────────────────────┘              │
│                  │ WiFi (TLS 1.2+)                                           │
│                  ▼                                                           │
│   ┌──────────────────────────────────────────────────────────┐              │
│   │           CARVANTA CLOUD PLATFORM                         │              │
│   │                                                           │              │
│   │   FastAPI Backend ◄──REST──► React Frontend               │              │
│   │   • CVS Scoring Engine       • 45 UI Pages                │              │
│   │   • ML Ensemble (RF+XGB)     • Clinical Precision UI      │              │
│   │   • LLM Integration          • Real-time Dashboards       │              │
│   │   • Digital Twin Engine      • Genomic Profiler           │              │
│   │   • Genomic Pipeline         • 3D Neural Bridge           │              │
│   │   • Trial Matcher            • Report Generator           │              │
│   └──────────────┬───────────────────────────────────────────┘              │
│                  │                                                           │
│                  ▼                                                           │
│   [Doctor's Dashboard] ──► [Alert: "CD19 dropping — escape risk"]           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Software Architecture

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python + FastAPI | 3.12+ / 0.104+ |
| Frontend | React + Vite + TypeScript | 18 / 5.x |
| ML Models | scikit-learn + XGBoost | 1.3 / 2.0 |
| Deep Learning | PyTorch (autoencoder, attention) | 2.x |
| LLM Integration | Grok / Groq / Gemini / OpenAI | Multi-provider |
| Database | SQLite (dev) / PostgreSQL (prod) | — |
| Deployment | Railway (backend) + Vercel (frontend) | — |

### Backend Architecture

```
api/
├── main.py                    # FastAPI app entrypoint (v5)
├── auth.py                    # JWT + PBKDF2 authentication
├── auth_router.py             # Auth endpoints (register, login, profile)
├── validation_router.py       # Model validation + certification
├── deep_learning_router.py    # Autoencoder + neural scoring
├── genomics_router.py         # Variant calling, HLA, TMB
├── digital_twin_router.py     # Patient simulation
├── trials_router.py           # Clinical trial intelligence
├── audit_logger.py            # HIPAA-aligned audit middleware
└── ... (28 routers total)

scoring/                        # CVS v3 Scoring Engine
├── cvs_engine.py              # 8-feature adaptive weighted scoring
├── adaptive_weights.py        # Dynamic weight adjustment
└── tier_classifier.py         # Score → Tier mapping

models/                         # ML Pipeline
├── train_pipeline.py          # 5-fold CV training
├── car_t_model.pkl            # Random Forest classifier
└── car_t_ranker.pkl           # XGBoost regression ranker

features/                       # Feature Engineering + Services
├── tumor_features.py          # TCGA/GTEx/HPA feature generation
├── llm_insight.py             # Multi-provider LLM integration
├── explainability.py          # SHAP-based feature attribution
├── drug_interactions.py       # Drug-antigen interaction checker
├── fhir_export.py             # HL7 FHIR R4 diagnostic reports
└── notation_standards.py      # HUGO/NCBI/UniProt gene mappings
```

### Scoring Pipeline

```
Input: Antigen Name (e.g., "CD19")
         │
         ▼
┌──────────────────────┐
│  Feature Generation  │ ◄── TCGA, GTEx, HPA, ClinicalTrials.gov
│  (8 dimensions)      │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ CVS v3  │ │   ML    │
│ Rule-   │ │ RF+XGB  │
│ Based   │ │ Trained │
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼
┌──────────────────────┐
│   Adaptive Blend     │
│ Score = (1-α)·CVS    │
│       + α·ML_score   │
│ α = 0.20 – 0.40      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Tier Classification │
│  Tier 1: ≥ 75        │
│  Tier 2: 50–74       │
│  Tier 3: < 50        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LLM Clinical        │ ◄── Grok → Groq → DeepSeek (fallback chain)
│  Reasoning           │
└──────────────────────┘
```

### CVS Feature Weights

| Feature | Weight | Data Source |
|---------|--------|-------------|
| Tumor Specificity | 25% | TCGA differential expression |
| Safety Score | 20% | GTEx normal tissue risk (inverted) |
| Stability | 12% | Expression consistency across samples |
| Evidence | 10% | Published clinical trial support |
| Immunogenicity | 10% | Immune recognition potential |
| Surface Accessibility | 8% | UniProt/HPA membrane localization |
| Tissue Risk | 8% | GTEx organ-level heatmap |
| Protein Validation | 7% | HPA protein-level confirmation |

### Frontend Architecture

```
frontend-react/
├── src/
│   ├── pages/              # 45 page modules
│   │   ├── Dashboard.tsx           # Main scoring dashboard
│   │   ├── SingleAnalysis.tsx      # Deep-dive single antigen
│   │   ├── GenomicProfiler.tsx     # Genomic variant analysis
│   │   ├── DigitalTwin.tsx         # Patient simulation
│   │   ├── NeuralBridge.tsx        # 3D knowledge graph
│   │   ├── DrugInteractions.tsx    # Drug-antigen interactions
│   │   ├── ClinicalTrials.tsx      # Trial matcher
│   │   └── ...
│   ├── context/
│   │   └── AuthContext.tsx         # Authentication state
│   ├── styles/                     # CSS modules
│   └── App.tsx                     # Root with routing
├── vite.config.ts
└── package.json
```

### API Architecture

- **28 routers** serving **30+ endpoints** under `/api/v5/`
- Async request handling with FastAPI
- CORS middleware with configurable allowed origins
- Rate limiting per endpoint
- Audit logging middleware for HIPAA compliance
- Swagger UI auto-generated at `/docs`

---

## Hardware Architecture — Sentinel HYDRA

### Physical Specifications

| Parameter | Value |
|-----------|-------|
| Board Dimensions | 95mm × 65mm |
| Layer Count | 6 (signal/ground/analog/power/high-speed/bottom) |
| Thickness | 1.6mm FR4 |
| Surface Finish | ENIG (Immersion Gold) |
| Solder Mask | Matte Black |
| Components | 135 (123 SMD + 11 THT + 1 unspecified) |
| Vias | 225 through-hole |
| Pads | 641 SMD + 72 through-hole + 9 NPTH |
| Cost per Unit | ~$79 (complete with battery + display + sensor) |

### PCB Layer Stackup

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1 (F.Cu) — "Digital_Signals"            35µm copper   │
│   SPI, I2C, UART, GPIO, LED data, display interface        │
├─────────────────────────────────────────────────────────────┤
│ Prepreg: 0.2mm FR4 (εr=4.5)                                │
├─────────────────────────────────────────────────────────────┤
│ Layer 2 (In1.Cu) — "GND_Plane"               35µm copper   │
│   Continuous ground pour — EMI shield (digital ↔ analog)    │
├─────────────────────────────────────────────────────────────┤
│ Core: 0.36mm FR4                                            │
├─────────────────────────────────────────────────────────────┤
│ Layer 3 (In2.Cu) — "Analog_Signals"          35µm copper   │
│   4× LMP91000 outputs, ADS1256 inputs, sensor traces       │
├─────────────────────────────────────────────────────────────┤
│ Prepreg: 0.2mm FR4                                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 4 (In3.Cu) — "Power_Planes"            35µm copper   │
│   3.3V_DIGITAL, 3.3V_ANALOG, 1.8V_CORE, VBAT              │
├─────────────────────────────────────────────────────────────┤
│ Core: 0.36mm FR4                                            │
├─────────────────────────────────────────────────────────────┤
│ Layer 5 (In4.Cu) — "HighSpeed"               35µm copper   │
│   USB D+/D- (90Ω), ESP32 antenna (50Ω), SD card data       │
├─────────────────────────────────────────────────────────────┤
│ Prepreg: 0.2mm FR4                                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 6 (B.Cu) — "Bottom_GND"                35µm copper   │
│   Component pads, ground pour, thermal relief               │
└─────────────────────────────────────────────────────────────┘
Total thickness: ~1.6mm
```

### Dual-MCU Architecture

The Sentinel HYDRA uses a **dual-processor architecture** to separate real-time sensor acquisition from application-level processing:

```
┌──────────────────────────────┐     UART (921600 baud)     ┌──────────────────────────────┐
│         RP2040               │ ◄────────────────────────► │         ESP32-S3             │
│   (Sensor Coprocessor)       │                             │   (Main Controller)          │
│                              │                             │                              │
│ • 4× LMP91000 potentiostat   │   Sensor data packets      │ • WiFi + BLE radio           │
│ • ADS1256 24-bit ADC         │   ──────────────────►       │ • 2.4" TFT display (ST7789)  │
│ • AS7341 11-ch spectral      │                             │ • microSD data logging       │
│ • TMP117 temperature         │   Commands + config         │ • Cloud client (HTTPS)       │
│ • MAX30102 SpO2/HR           │   ◄──────────────────       │ • OTA firmware updates       │
│ • Impedance measurement      │                             │ • User interface + alerts    │
│ • PID heater control         │                             │ • Power management           │
│ • LSM6DSO IMU                │                             │ • DS3231 RTC                 │
│                              │                             │                              │
│ Priority: Deterministic      │                             │ Priority: Connectivity       │
│           real-time sampling │                             │           + user experience   │
└──────────────────────────────┘                             └──────────────────────────────┘
```

### I2C Bus Topology

```
ESP32-S3 (I2C Master)
    │
    ├── TCA9548A I2C Multiplexer (U14, addr: 0x70)
    │       ├── Ch0: LMP91000 #1 (0x48) — Antigen Channel 1
    │       ├── Ch1: LMP91000 #2 (0x48) — Antigen Channel 2
    │       ├── Ch2: LMP91000 #3 (0x48) — Antigen Channel 3
    │       ├── Ch3: LMP91000 #4 (0x48) — Antigen Channel 4
    │       └── Ch4: MAX30102 (0x57) — SpO2 / Heart Rate
    │
    ├── DS3231 RTC (0x68) — Timestamping
    ├── MAX17048 Fuel Gauge (0x36) — Battery SOC
    └── MLX90614 IR Temp (0x5A) — Contactless temperature

RP2040 (I2C Master — separate bus)
    │
    ├── TMP117 (0x48) — Precision temperature
    ├── AS7341 (0x39) — 11-channel spectral sensor
    └── LSM6DSO (0x6A) — Accelerometer + gyroscope
```

### SPI Bus Sharing

```
ESP32-S3 SPI Bus (VSPI)
    │
    ├── GPIO2  (CS) ──► ADS1256 24-bit ADC
    ├── GPIO8  (CS) ──► ST7789 TFT Display
    └── GPIO14 (CS) ──► microSD Card
    
    Shared lines:
    • GPIO11 — MOSI
    • GPIO12 — SCK
    • GPIO13 — MISO
```

### Power Architecture

```
USB-C (5V) or LiPo Battery (3.7V)
    │
    ├── BQ24075 (U3) — Battery charger + power path management
    │       │
    │       ├── MAX17048 (U7) — Battery fuel gauge (I2C)
    │       └── BQ29700 (U8) — Battery protection (OVP/UVP/OCP)
    │
    ├── TPS7A2033 (U4) ──► 3.3V_DIGITAL
    │       └── ESP32-S3, TFT, LEDs, SD card, digital ICs
    │
    ├── TPS7A4533 (U5) ──► 3.3V_ANALOG
    │       └── LMP91000s, ADS1256, analog sensors
    │
    ├── AP2112K-1.8 (U6) ──► 1.8V_CORE
    │       └── ESP32 core (optional)
    │
    └── Ferrite bead (L1) — AGND ↔ DGND bridge
            └── Single-point ground connection
```

### Sensor Subsystems

| Subsystem | Sensors | Channels | Resolution | Interface |
|-----------|---------|----------|------------|-----------|
| Electrochemical | 4× LMP91000 + ADS1256 | 4 antigens | 24-bit | I2C (muxed) + SPI |
| Optical/Spectral | AS7341 | 11 wavelengths | 16-bit | I2C |
| Pulse Oximetry | MAX30102 | SpO2 + HR | 18-bit | I2C |
| Temperature | TMP117 + MLX90614 | Ambient + IR | 16-bit | I2C |
| Motion/Fall | LSM6DSO | 6-axis IMU | 16-bit | I2C |
| Impedance | Custom analog front-end | Cell health | 24-bit (ADC) | Analog |

---

## Firmware Architecture

### ESP32-S3 Firmware (`firmware/esp32_hydra/`)

```
src/
├── main.cpp              # Boot sequence, task orchestration, FreeRTOS
├── config.h              # System-wide configuration constants
├── pins.h                # GPIO assignments (all 30+ pins)
├── comms/
│   ├── cloud_client.cpp/h    # HTTPS POST to CARVanta cloud API
│   ├── wifi_manager.cpp/h    # WiFi provisioning + reconnection
│   └── uart_bridge.cpp/h     # RP2040 ↔ ESP32 packet protocol
├── sensors/
│   ├── lmp91000.cpp/h        # Potentiostat driver (4-channel muxed)
│   ├── max30102.cpp/h        # SpO2 + heart rate sensor
│   ├── ds3231.cpp/h          # Real-time clock
│   ├── lsm6dso.cpp/h         # IMU (fall detection)
│   └── mlx90614.cpp/h        # Contactless IR temperature
├── storage/
│   ├── sd_logger.cpp/h       # SD card CSV data logging
│   └── config_store.cpp/h    # NVS persistent settings
├── system/
│   ├── power_manager.cpp/h   # Sleep modes, battery monitoring
│   └── ota_updater.cpp/h     # Over-the-air firmware updates
└── ui/
    ├── display.cpp/h         # ST7789 TFT rendering
    ├── led_status.cpp/h      # WS2812B status LEDs
    └── buzzer.cpp/h          # Audio alerts
```

### RP2040 Firmware (`firmware/rp2040_hydra/`)

```
src/
├── main.cpp              # Sensor loop, timer interrupts, UART TX
├── config.h              # Sampling rates, calibration constants
├── pins.h                # RP2040 GPIO assignments
├── drivers/
│   ├── ads1256.cpp/h         # 24-bit ADC driver (SPI, 30kSPS)
│   ├── as7341.cpp/h          # 11-channel spectral sensor
│   ├── tmp117.cpp/h          # ±0.1°C precision temperature
│   └── impedance.cpp/h       # Impedance spectroscopy front-end
├── control/
│   ├── pid_heater.cpp/h      # PID temperature controller
│   ├── led_driver.cpp/h      # Sensor excitation LEDs
│   └── calibration.cpp/h     # Auto-calibration routines
└── comms/
    └── uart_protocol.cpp/h   # Packet framing + CRC for ESP32 link
```

### Inter-MCU Communication Protocol

```
Packet Format (UART @ 921600 baud):
┌──────┬──────┬────────┬───────────────┬───────┬──────┐
│ SYNC │ TYPE │ LENGTH │    PAYLOAD    │  CRC  │ END  │
│ 0xAA │ 1B   │  2B    │  0–512 bytes  │  2B   │ 0x55 │
└──────┴──────┴────────┴───────────────┴───────┴──────┘

Message Types:
  0x01 — Electrochemical data (4× antigen levels)
  0x02 — Spectral data (11 channels)
  0x03 — Temperature data (ambient + IR)
  0x04 — SpO2 + heart rate
  0x05 — Impedance measurement
  0x06 — IMU data (accelerometer + gyro)
  0x10 — Config update (ESP32 → RP2040)
  0x11 — Calibration command
  0xFF — Error / status report
```

---

## Data Flow

### Measurement Cycle (30 seconds)

```
1. RP2040 initiates sensor scan
   ├── Potentiostat sweep (4 channels × 200 points)
   ├── Spectral acquisition (11 channels)
   ├── Temperature reading (TMP117 + MLX90614)
   └── Impedance measurement

2. RP2040 → ESP32 via UART
   └── Packetized sensor data with CRC

3. ESP32 processes + displays
   ├── TFT display update (real-time waveforms)
   ├── SD card logging (timestamped CSV)
   ├── Local anomaly detection
   └── WS2812B status LED update

4. ESP32 → CARVanta Cloud via WiFi
   ├── HTTPS POST to /api/v5/sentinel/upload
   ├── Payload: JSON with all sensor readings
   └── Response: AI analysis + alerts

5. Cloud processes + alerts
   ├── Trend analysis (antigen escape detection)
   ├── Digital twin update
   ├── Doctor notification (if thresholds exceeded)
   └── Dashboard update (real-time)
```

---

## Deployment Architecture

```
┌─────────────────────┐      ┌─────────────────────┐
│   Railway            │      │   Vercel / Netlify   │
│   (Backend)          │      │   (Frontend)         │
│                      │      │                      │
│   FastAPI + Uvicorn  │◄────►│   React + Vite       │
│   SQLite / PG        │ REST │   Static SPA         │
│   ML Models (.pkl)   │      │   VITE_API_URL       │
│                      │      │                      │
│   Port: 8001         │      │   CDN-distributed    │
└──────────┬───────────┘      └──────────────────────┘
           │
           │ HTTPS
           │
┌──────────┴───────────┐
│   Sentinel HYDRA     │
│   (Edge Device)      │
│   ESP32-S3 WiFi      │
└──────────────────────┘
```

---

## Directory Structure

```
CARVanta/
├── api/                        # 28 FastAPI routers (v5)
├── scoring/                    # CVS v3 scoring engine
├── models/                     # ML pipeline (RF + XGBoost)
├── features/                   # Feature engineering + LLM + FHIR
├── validation/                 # Model validation + ISO certification
├── deep_learning/              # Autoencoder, attention, neural models
├── genomics/                   # Variant calling, HLA, TMB, neoantigen
├── digital_twin/               # Patient simulation engine
├── discovery/                  # Drug discovery, scFv design
├── copilot/                    # Research assistant, RAG engine
├── trials/                     # Clinical trial intelligence
├── collab/                     # Research collaboration hub
├── disease_atlas/              # Global disease epidemiology
├── health_econ/                # Cost-effectiveness analysis
├── omics/                      # Multi-omics integration
├── biomarker/                  # Biomarker data processing
├── safety/                     # Safety monitoring
├── regulatory/                 # Regulatory compliance documents
├── frontend-react/             # React 18 + Vite + TypeScript (45 pages)
├── data/                       # Biomarker database + reports
├── db/                         # Database models + migrations
├── config/                     # Application configuration
├── scripts/                    # Utility scripts
├── hardware/
│   └── sentinel/
│       ├── kicad/
│       │   └── Sentinel_HYDRA/         # KiCad project (6-layer PCB)
│       │       ├── *.kicad_sch         # 7 schematic sheets
│       │       ├── Sentinel_HYDRA.kicad_pcb
│       │       ├── gerbers/            # Production Gerber files
│       │       └── Sentinel_HYDRA_Gerbers.zip
│       ├── firmware/
│       │   ├── esp32_hydra/            # ESP32-S3 firmware (PlatformIO)
│       │   └── rp2040_hydra/           # RP2040 firmware (PlatformIO)
│       ├── BOM.md                      # Bill of materials
│       └── README.md                   # Hardware documentation
├── .github/
│   └── workflows/                      # CI/CD, CodeQL, release
├── ARCHITECTURE.md                     # This file
├── README.md                           # Project overview
├── CODE_OF_CONDUCT.md                  # Contributor Covenant v2.1
├── contributing.md                     # Contribution guidelines
├── security.md                         # Security policy
├── CHANGELOG.md                        # Version history
├── ROADMAP.md                          # Future plans
├── LICENSE                             # BUSL-1.1
└── requirements.txt                    # Python dependencies
```

---

## Security Architecture

### Authentication Flow

```
Client                    API                    Database
  │                        │                        │
  ├── POST /auth/register ─►│                        │
  │   (email, password)    │── PBKDF2 hash ────────►│
  │                        │                        │
  ├── POST /auth/login ───►│                        │
  │   (email, password)    │── Verify hash ◄────────│
  │◄── JWT token ──────────│                        │
  │                        │                        │
  ├── GET /api/v5/score ──►│                        │
  │   (Authorization: JWT) │── Verify + decode ─────│
  │◄── Response ───────────│                        │
```

### Defense Layers

| Layer | Mechanism |
|-------|-----------|
| Transport | HTTPS / TLS 1.2+ (all endpoints) |
| Authentication | JWT with configurable expiry |
| Password Storage | PBKDF2 with per-user salt |
| API Protection | Rate limiting + CORS whitelist |
| Input Validation | Pydantic models for all endpoints |
| SQL Injection | Parameterized queries (SQLAlchemy) |
| Audit Trail | SQLite-backed request logging |
| LLM Safety | Output labeling (LLM vs. Rule-Based) |
| Firmware | TLS for cloud uploads, CRC for UART |

---

*Last updated: June 2026*
