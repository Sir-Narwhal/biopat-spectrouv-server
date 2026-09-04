# BioPAT® Spectro UV Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Docker: Ready](https://img.shields.io/badge/Docker-Compose-blue.svg)](compose.yaml)
[![Protocol: OPC UA](https://img.shields.io/badge/Protocol-OPC%20UA-orange.svg)](https://opcfoundation.org/)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--4391--135X-%23A6CE39?logo=orcid)](https://orcid.org/0009-0002-4391-135X)

**Real-Time 201-Wavelength UV-Vis Spectroscopy Ingestion & OPC UA Industrial Gateway for Sartorius BioPAT® Spectro UV / tec5 Spectrometers.**

---

## Overview

In modern bioprocess monitoring and Process Analytical Technology (PAT), standard spectroscopic integrations frequently limit operators to streaming only 1 to 4 discrete, hardcoded wavelengths into their SCADA or Distributed Control Systems (DCS).

**BioPAT® Spectro UV Server unlocks all 201 simultaneous wavelengths across the entire UV-Vis spectrum (190 nm to 390 nm in 1.0 nm increments)** in real-time. By ingesting high-frequency UDP broadcasts directly from the tec5 spectrometer/software, caching them in an in-memory Redis message bus, and exposing them over an open **OPC UA Server (Port 4841)**, this platform bridges industrial PAT spectroscopy into bioprocess automation (Ignition, Sartorius BioPAT, Emerson DeltaV, Siemens PCS 7, and Rockwell FactoryTalk).

---

## System Architecture

The server runs as a clean, decoupled **4-container microservices stack**:

![Architecture diagram: the tec5 spectrometer connects to the vendor tecSaaS MPT software, which broadcasts UDP datagrams to a Docker Compose stack of udpparser, redisserver, udphelper, and opcserver — all running on the same host PC — which publishes to SCADA and signals the Windows Tray App directly via Redis.](docs/assets/architecture.svg)

### Components

1. **`redisserver`**: Low-latency, in-memory state bus decoupling UDP packet ingestion from OPC UA publisher polling.
2. **`udpparser`**: High-throughput UDP socket listener. Unpacks 840-byte binary packets into 201-wavelength float arrays and writes them to Redis with auto-expiry (`ex=5s`) to prevent stale data display.
3. **`opcserver`**: Standard OPC UA server exposing `Channel 1` and `Channel 2` nodes with 201-element float arrays for Sample Intensity, Reference Intensity, Absorbance, Transmission, Calibration, and Wavelength Axis.
4. **`udphelper`**: Background watchdog that checks Channel 1 Absorbance freshness in Redis and sets an `mpt_refresh` signal key when data goes stale, so the optional [Windows tray companion](tray_app/README.md) can restart the spectrometer's measurement session automatically.

---

## Spectral Data Model

Each spectrometer channel exposes 201 floating-point values corresponding to each 1.0 nm increment from 190.0 nm to 390.0 nm:

| Data Type | tec5 Packet Type | Redis Key | OPC UA Node ID | Description |
| :--- | :---: | :--- | :--- | :--- |
| **Absorbance** | `9` | `absorbance_channel_1` | `ns=1;s=absorbance_channel_1` | Optical Absorbance (AU) across 201 wavelengths |
| **Sample Intensity** | `4` | `sample_channel_1` | `ns=1;s=sample_channel_1` | Raw measurement intensity counts |
| **Reference Intensity** | `5` | `onlinereference_channel_1` | `ns=1;s=onlinereference_channel_1` | Baseline reference intensity counts |
| **Transmission** | `7` | `transmission_channel_1` | `ns=1;s=transmission_channel_1` | Transmittance ratio ($I / I_0$) |
| **Calibration** | `11` | `calibration_channel_1` | `ns=1;s=calibration_channel_1` | Dark/factory calibration data |
| **Wavelengths** | Axis | *(not stored in Redis — computed by `opcserver`)* | `ns=1;s=Wavelength` | Read-only array: `[190.0, 191.0, ..., 390.0]` |

---

## Quick Start (Under 2 Minutes)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- *(Optional)* Python 3.10+ if running test scripts or native mode

### 1. Clone & Start the Stack

```bash
git clone https://github.com/Sir-Narwhal/biopat-spectrouv-server.git
cd biopat-spectrouv-server

# Start Redis, UDP Parser, OPC UA Server, and the Watchdog
docker compose up -d
```

Verify that all four services are running:

```bash
docker compose ps
```

### 2. Verify with Simulated Data (No Hardware Required!)

To test the complete stack without being connected to a physical spectrometer, run the included mock UDP emitter:

```bash
python -m parselibrary.mock_udp_emitter
```

This broadcasts authentic 840-byte tec5 UDP packets for Sample Intensity, Reference Intensity, and Absorbance to `127.0.0.1:20202`.

### 3. Connect Any OPC UA Client

Connect your favorite OPC UA client (e.g. [UaExpert](https://www.unified-automation.com/products/development-tools/uaexpert.html), Python `asyncua`, or SCADA tag browser) to:

```
opc.tcp://localhost:4841
```

Browse to `Root -> Objects -> spectrouv_1` to view live 201-point arrays updating in real time!

### 4. Install MPT Guardian (Required Once You Move Past a Demo)

The steps above are enough for a quick test with mock data. The moment you connect a **real** spectrometer for anything longer than a short trial, install [MPT Guardian](tray_app/README.md) on the same Windows PC as the Docker stack — run the installer (`MPTGuardianInstaller/Release/setup.exe`) or just launch `MPTGuardian/bin/Release/MPT Guardian.exe` directly, no build required.

> [!CAUTION]
> **Read this before you rely on MPT Guardian for anything — it is not optional and it is easy to accidentally break.**
>
> - **It is mandatory for any measurement session longer than ~6 hours.** tec5 tecSaaS MPT intermittently stops transmitting UDP data on its own during long runs, and MPT Guardian is the *only* thing that detects and restarts it. Without it, a long-running deployment will silently go stale with no automatic recovery.
> - **It will not work headless.** MPT Guardian uses **Windows UI Automation** to control the tecSaaS MPT desktop application, so tecSaaS MPT must be **running and visible on the Windows desktop session** the whole time. It will **not** work in a headless session or a minimized/disconnected RDP session without additional configuration — and if that condition silently breaks mid-run, MPT Guardian keeps running but can no longer actually recover a stalled session, defeating the entire point above.
>
> Verify both conditions hold for your actual deployment (not just your test setup) before trusting this for a production run. See [tray_app/README.md](tray_app/README.md) for full details.

---

## Native Python Execution (Without Docker)

If you prefer to run the services directly on your host machine:

```bash
# 1. Start a local Redis server
redis-server --port 6379

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the UDP Parser (Terminal 1)
python -m parselibrary.udp_parser

# 4. Launch the OPC UA Server (Terminal 2)
python -m parselibrary.opcua_server

# 5. Launch the Watchdog (Terminal 3, optional)
python -m parselibrary.spectrouv_helper
```

---

## Environment Configuration

Configuration is managed via environment variables. Copy `.env.example` to `.env` to override defaults:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `UDP_IP` | `0.0.0.0` | Listen address for tecSaaS MPT's UDP broadcast |
| `UDP_PORT` | `20202` | Port receiving tec5 UDP broadcasts |
| `UDP_CHANNEL_NAME` | `channel_1` | **Required, manual** — which channel this data gets tagged as (`channel_1` or `channel_2`). Not read from the packet; see warning below. |
| `OPC_IP_ADDRESS` | `0.0.0.0` | Bind address for OPC UA server |
| `OPC_PORT_NUMBER` | `4841` | Standard OPC UA TCP port |
| `REDIS_IP_ADDRESS` | `redisserver` (or `localhost`) | Hostname / IP address of Redis server |
| `REDIS_PORT_NUMBER` | `6379` | Port for Redis server |

> [!IMPORTANT]
> **`UDP_CHANNEL_NAME` must be set manually to match your actual spectrometer wiring — it is never auto-detected.** The UDP packet header does carry a channel index, but `udpparser` doesn't read it; every value gets tagged with whatever `UDP_CHANNEL_NAME` is set to, silently, with no error if it's wrong. If your instrument is on channel 2 and you leave the `channel_1` default, your data will land under the wrong Redis keys and OPC UA nodes. To ingest both channels at once, run a second `udpparser` service in `compose.yaml` with its own port and `UDP_CHANNEL_NAME=channel_2`. See [Setup & Deployment](docs/setup.md#channel-selection-required) for details.

---

## Instrument Setup (tec5 / Sartorius)

The recommended deployment runs this entire stack (via Docker Desktop) on the same Windows PC that runs the tec5 tecSaaS MPT software and is physically connected to the spectrometer — see [MPT Guardian's architecture note](tray_app/README.md#architecture) for why. Only the OPC UA port needs to be reachable from elsewhere on the network.

1. In the tec5 / tecSaaS MPT configuration, configure UDP broadcast transmission to target `127.0.0.1` (loopback) on port `20202`, since `udpparser` runs on this same PC. If you're instead running the Docker stack on a separate host, target that host's IP on the same subnet.
2. Install [MPT Guardian](tray_app/README.md) on this same PC — either via the installer or by running the included `.exe` directly, no build step required — so it can automatically monitor and restart the tec5 MPT measurement session in the background.

> [!IMPORTANT]
> **Sessions longer than ~6 hours require MPT Guardian.** The tec5 tecSaaS MPT software intermittently stops transmitting UDP data on its own during extended runs. Without MPT Guardian running to catch and restart it, a long-running deployment will silently go stale with no automatic recovery. It's optional for short test/demo sessions only.

> [!CAUTION]
> **MPT Guardian will not work headless.** It drives tecSaaS MPT using **Windows UI Automation**, which means tecSaaS MPT must be **running and visible on the Windows desktop session** at all times — MPT Guardian will **not** work in a headless session or a minimized/disconnected RDP session without additional configuration. This isn't a minor caveat: if it silently breaks, MPT Guardian keeps running but loses the ability to actually recover a stalled session, which quietly defeats the mandatory 6-hour protection above. See [tray_app/README.md](tray_app/README.md#limitations--notes) for details.

---

## Documentation

Full documentation is available in the [`docs/`](docs/) directory and can be served locally with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/):

```bash
pip install mkdocs-material
mkdocs serve
```

---

## License & Trademarks

- **License**: Released under the [MIT License](LICENSE).
- **Disclaimer**: *BioPAT®* is a registered trademark of Sartorius AG. *tec5* and *tecSaaS* are trademarks of tec5 AG. This independent open-source project is not affiliated with, endorsed by, or officially connected to Sartorius AG or tec5 AG.

---

## Citation

If you use this software in your research, please cite it — see [CITATION.cff](CITATION.cff) (or use GitHub's "Cite this repository" button, which reads directly from that file) for the up-to-date, machine-readable metadata. Plain-text form:

> Baarbé, J. (2025). *Sartorius BioPAT(R) Spectro UV OPC-UA Server* [Computer software]. https://github.com/Sir-Narwhal/biopat-spectrouv-server

*A DOI will be added here once the software is archived (e.g. via Zenodo) — until then, cite the repository URL above. Once a `doi:` field is added to [CITATION.cff](CITATION.cff), it will show up automatically via the "Cite this repository" button.*

```bibtex
@software{baarbe_biopat_spectro_uv,
  author  = {Baarbé, Joel},
  title   = {Sartorius BioPAT(R) Spectro UV OPC-UA Server},
  year    = {2025},
  license = {MIT},
  url     = {https://github.com/Sir-Narwhal/biopat-spectrouv-server}
}
```
