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

The server runs as a clean, decoupled **3-container microservices stack**:

```
┌─────────────────────────────────────────────────────────────────┐
│        Sartorius BioPAT® Spectro UV / tec5 Spectrometer         │
│          Broadcasts 840-byte UDP Packets (Default: 20202)       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ UDP Datagrams
                                 ▼
 ┌───────────────────────────────────────────────────────────────┐
 │                   Docker Compose Stack                        │
 │                                                               │
 │  ┌──────────────────────┐  JSON Arrays  ┌──────────────────┐  │
 │  │   (ii) udpparser     ├──────────────►│ (i) redisserver  │  │
 │  │   - Binds :20202/udp │  Cache & TTL  │ - Redis 7 Alpine │  │
 │  │   - Unpacks 201 pts  │               │ - Port :6379     │  │
 │  └──────────────────────┘               └────────┬─────────┘  │
 │                                                  │            │
 │                                                  │ 1 Hz Poll  │
 │                                                  ▼            │
 │                                         ┌──────────────────┐  │
 │                                         │ (iii) opcserver  │  │
 │                                         │ - Port :4841     │  │
 │                                         │ - 201-pt Arrays  │  │
 │                                         └────────┬─────────┘  │
 └──────────────────────────────────────────────────┼────────────┘
                                                    │
                                                    ▼
                                   SCADA / Bioreactor Controllers
                                   (opc.tcp://<host>:4841)
```

### Components

1. **`redisserver`**: Low-latency, in-memory state bus decoupling UDP packet ingestion from OPC UA publisher polling.
2. **`udpparser`**: High-throughput UDP socket listener. Unpacks 840-byte binary packets into 201-wavelength float arrays and writes them to Redis with auto-expiry (`ex=5s`) to prevent stale data display.
3. **`opcserver`**: Standard OPC UA server exposing `Channel 1` and `Channel 2` nodes with 201-element float arrays for Sample Intensity, Reference Intensity, Absorbance, Transmission, Calibration, and Wavelength Axis.

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
| **Wavelengths** | Axis | `wavelengths_channel_1` | `ns=1;s=Wavelength` | Read-only array: `[190.0, 191.0, ..., 390.0]` |

---

## Quick Start (Under 2 Minutes)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- *(Optional)* Python 3.10+ if running test scripts or native mode

### 1. Clone & Start the Stack

```bash
git clone https://github.com/Sir-Narwhal/biopat-spectrouv-server-1.git
cd biopat-spectrouv-server-1

# Start Redis, UDP Parser, and OPC UA Server
docker compose up -d
```

Verify that all three services are running:

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
```

---

## Environment Configuration

Configuration is managed via environment variables. Copy `.env.example` to `.env` to override defaults:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `UDP_IP` | `0.0.0.0` | Listen address for spectrometer UDP datagrams |
| `UDP_PORT` | `20202` | Port receiving tec5 UDP broadcasts |
| `UDP_CHANNEL_NAME` | `channel_1` | Default channel identifier (`channel_1` or `channel_2`) |
| `OPC_IP_ADDRESS` | `0.0.0.0` | Bind address for OPC UA server |
| `OPC_PORT_NUMBER` | `4841` | Standard OPC UA TCP port |
| `REDIS_IP_ADDRESS` | `redisserver` (or `localhost`) | Hostname / IP address of Redis server |
| `REDIS_PORT_NUMBER` | `6379` | Port for Redis server |

---

## Instrument Setup (tec5 / Sartorius)

1. Ensure the spectrometer host computer is connected to the same local subnet as the server.
2. In the tec5 / tecSaaS MPT configuration, configure UDP broadcast transmission to target the IP of this server on port `20202`.
3. If running `MPTTrayApplication` on the Windows spectrometer PC, it will automatically monitor and maintain the tec5 MPT measurement session in the background.

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
