# Contributing to CARVanta

Thank you for your interest in contributing to CARVanta! This project spans AI software, embedded firmware, and medical-grade PCB hardware — contributions are welcome across all domains.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Standards](#code-standards)
- [Hardware Contributions](#hardware-contributions)
- [Firmware Contributions](#firmware-contributions)
- [Pull Request Process](#pull-request-process)
- [Commit Message Convention](#commit-message-convention)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/CARVanta.git
   cd CARVanta
   ```
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
4. Make your changes, test thoroughly, and submit a pull request

---

## Development Environment

### Software (Python Backend + React Frontend)

**Prerequisites:**
- Python 3.12+
- Node.js 18+
- Git

```bash
# Backend setup
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your API keys

# Frontend setup
cd frontend-react
npm install

# Run locally
# Terminal 1: py -m uvicorn api.main:app --host 0.0.0.0 --port 8001
# Terminal 2: cd frontend-react && npm run dev
```

### Hardware (KiCad PCB Design)

**Prerequisites:**
- [KiCad 8.0+](https://www.kicad.org/download/) (schematic + PCB editor)

**Project location:** `hardware/sentinel/kicad/Sentinel_HYDRA/`

Open `Sentinel_HYDRA.kicad_pro` in KiCad to access all schematics and the PCB layout.

### Firmware (ESP32 + RP2040)

**Prerequisites:**
- [PlatformIO](https://platformio.org/install) (VS Code extension or CLI)

```bash
# ESP32 firmware
cd hardware/sentinel/firmware/esp32_hydra
pio run            # Build
pio run -t upload  # Flash

# RP2040 firmware
cd hardware/sentinel/firmware/rp2040_hydra
pio run            # Build
pio run -t upload  # Flash
```

---

## Code Standards

### Python (Backend, ML, API)

- Follow **PEP 8** style guidelines
- Use **type hints** for all function signatures
- Maximum line length: **120 characters**
- Docstrings: Use Google-style docstrings for all public functions and classes
- Use `pre-commit` hooks: `pre-commit install`

```python
def score_antigen(antigen_name: str, cancer_type: str | None = None) -> dict:
    """Score an antigen target for CAR-T viability.

    Args:
        antigen_name: HUGO gene symbol (e.g., "CD19", "BCMA").
        cancer_type: Optional cancer type filter.

    Returns:
        Dictionary containing CVS score, tier, and feature breakdown.
    """
```

### TypeScript / React (Frontend)

- Use **TypeScript** for all new components (`.tsx`)
- Functional components with hooks (no class components)
- CSS modules or dedicated `.css` files — no inline styles for complex styling
- Component naming: `PascalCase` (e.g., `GenomicProfiler.tsx`)

### C++ (Firmware)

- Follow the [Arduino/PlatformIO style guide](https://docs.arduino.cc/learn/contributions/arduino-writing-style-guide)
- Use `snake_case` for variables and functions, `PascalCase` for classes
- Header guards: `#pragma once`
- All hardware register access must use defined constants from `pins.h`
- Comment all ISR (interrupt service routine) functions with timing constraints
- Avoid `String` class — use `char[]` or `std::string` to prevent heap fragmentation

```cpp
#pragma once

class TMP117 {
public:
    bool begin(uint8_t address = 0x48);
    float read_temperature_c();
    bool set_conversion_mode(uint8_t mode);

private:
    uint8_t _address;
    bool write_register(uint8_t reg, uint16_t value);
    uint16_t read_register(uint8_t reg);
};
```

---

## Hardware Contributions

### PCB Design Rules

The Sentinel HYDRA is a **6-layer medical-grade PCB**. All hardware contributions must follow:

| Rule | Value |
|------|-------|
| Min trace width | 0.15mm (6mil) |
| Min clearance | 0.15mm |
| USB differential pair | 0.18mm trace, 0.15mm gap (90Ω) |
| Analog traces | 0.25mm minimum, guarded |
| Power traces | 0.5mm minimum |
| Via size | 0.3mm drill, 0.6mm pad |
| Surface finish | ENIG |

### Schematic Changes

- All new ICs must include a **datasheet link** in the symbol properties
- Assign correct power domains: `3V3_DIGITAL`, `3V3_ANALOG`, `1V8_CORE`, `VBAT`
- Run **ERC (Electrical Rules Check)** before submitting — zero errors required
- Add bypass capacitors per manufacturer recommendation

### PCB Layout Changes

- Run **DRC (Design Rules Check)** — zero errors, zero unconnected nets
- Maintain analog/digital ground separation
- Keep sensitive analog traces on Inner Layer 3 (Analog_Signals)
- High-speed signals (USB, RF) on Inner Layer 5 (HighSpeed)
- Generate and verify **Gerber files** after any layout change

---

## Firmware Contributions

### Architecture

The Sentinel HYDRA uses a **dual-MCU architecture**:

| MCU | Role | Firmware Location |
|-----|------|-------------------|
| ESP32-S3 | Main controller, WiFi, display, storage, cloud | `firmware/esp32_hydra/` |
| RP2040 | Real-time sensor acquisition, PID control | `firmware/rp2040_hydra/` |

### Guidelines

- **Inter-MCU communication** uses UART at 921600 baud — follow the existing packet protocol in `comms/`
- All sensor drivers must implement a `begin()` + `read()` interface pattern
- Use hardware timers for time-critical sampling — do not use `delay()` in sensor loops
- Power management: respect sleep/wake states in `system/power_manager.cpp`
- All floating-point sensor values must include units in variable names (e.g., `temperature_c`, `voltage_mv`)

---

## Pull Request Process

### Before Submitting

- [ ] Code compiles without warnings
- [ ] All existing tests pass
- [ ] New code has appropriate tests or manual verification steps
- [ ] Documentation updated if public API/interface changed
- [ ] Commit messages follow the convention below
- [ ] No secrets, API keys, or patient data in the diff
- [ ] For hardware: DRC passes with zero errors
- [ ] For firmware: builds for both ESP32 and RP2040 targets

### PR Description Template

```markdown
## What
Brief description of the change.

## Why
Motivation or issue number.

## How
Technical approach and key decisions.

## Testing
How this was verified.

## Screenshots / Gerber Renders (if applicable)
```

### Review Process

1. All PRs require at least **1 approval** before merging
2. Hardware/firmware PRs require review by a contributor familiar with the Sentinel platform
3. Changes to scoring algorithms or ML models require validation results in the PR description
4. Squash-merge to `main` — keep the commit history clean

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Build, CI, or tooling changes |
| `hw` | Hardware (schematic, PCB, BOM) changes |
| `fw` | Firmware changes |

### Scopes

`api`, `frontend`, `scoring`, `ml`, `genomics`, `digital-twin`, `sentinel`, `firmware`, `pcb`, `docs`

### Examples

```
feat(api): add FHIR R4 export for diagnostic reports
fix(scoring): correct adaptive weight calculation for missing TCGA data
hw(pcb): add TVS diodes to USB-C data lines
fw(esp32): implement deep sleep with RTC wakeup
docs: update README with Sentinel HYDRA hardware section
```

---

## Testing

### Backend

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=scoring --cov=features
```

### Frontend

```bash
cd frontend-react
npm run lint
npm run build  # Type-check + build verification
```

### Firmware

```bash
# Build verification (both targets)
cd hardware/sentinel/firmware/esp32_hydra && pio run
cd hardware/sentinel/firmware/rp2040_hydra && pio run
```

---

## Reporting Issues

### Bug Reports

Please include:
- Steps to reproduce
- Expected vs. actual behavior
- Environment (OS, Python version, browser, firmware version)
- Screenshots or logs if applicable

### Feature Requests

We welcome ideas! Please describe:
- The use case or problem you're solving
- Your proposed solution
- Any alternatives you've considered

### Security Vulnerabilities

**Do not open a public issue.** Email **dhruvagrawal1859@gmail.com** with `[SECURITY]` in the subject. See [SECURITY.md](security.md) for details.

---

## License

By contributing, you agree that your contributions will be licensed under the [BUSL-1.1 License](LICENSE).
