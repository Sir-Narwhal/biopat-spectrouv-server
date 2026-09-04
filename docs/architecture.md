# System Architecture

## Overview

The BioPAT® Spectro UV Server is designed around a decoupled, microservices architecture using **Docker Compose** and **Redis** as a real-time in-memory message bus.

---

## 4-Container Microservices Stack

![Architecture diagram: the tec5 spectrometer connects to the vendor tecSaaS MPT software, which broadcasts UDP datagrams to a Docker Compose stack of udpparser, redisserver, udphelper, and opcserver — all running on the same host PC — which publishes to SCADA and signals the Windows Tray App directly via Redis.](assets/architecture.svg)

---

## Data Flow

### 1. Ingestion (`udpparser`)
- Binds to `0.0.0.0:20202` (UDP).
- Receives 840-byte datagrams from the **tec5 tecSaaS MPT software** — the vendor application that drives the spectrometer and does the actual UDP broadcasting (the spectrometer hardware itself has no network interface here). Every acquisition cycle sends up to 5 of these datagrams, one per data type (sample, onlinereference, transmission, absorbance, calibration).
- Parses the 36-byte header: verifies length (840), extracts point count (201), wavelength bounds (190.0–390.0 nm), and data type code.
- Unpacks 201 float32 values.
- Writes JSON arrays into Redis with a 5-second TTL (`ex=5`) to prevent stale measurements if transmission ceases.
- **Channel assignment is manual, not auto-detected.** The packet header does carry a channel index (bytes 18–19, see below), but `udpparser` never reads it — every value it writes is tagged with whatever `UDP_CHANNEL_NAME` is set to in `compose.yaml`/`.env` (`channel_1` by default). Setting this correctly for your actual wiring is required; see [Setup & Deployment](setup.md#channel-selection-required).

### 2. State & Message Bus (`redisserver`)
- Operates in-memory on port 6379.
- Decouples high-frequency network packets from OPC UA client polling.

### 3. Industrial Publication (`opcserver`)
- Hosts standard OPC UA server on port 4841 (`opc.tcp://0.0.0.0:4841`).
- Namespace: `http://biopat/spectrouv`.
- Updates writable variables for each channel every 1 second.

### 4. Session Watchdog (`udphelper`)
- Polls the `absorbance_channel_1` key in Redis once per second.
- If the key is missing (expired TTL, meaning no fresh UDP data), sets `mpt_refresh = "true"` in Redis and logs a warning.
- Re-arms itself once fresh absorbance data reappears, so it can raise the flag again if data goes stale a second time. The `mpt_refresh` key itself is cleared by the tray application after it finishes handling the restart.
- Has no direct network exposure — it only communicates via Redis. The `mpt_refresh` key is polled by the [MPT Guardian tray companion](../tray_app/README.md), which reacts by restarting the tec5 measurement session. MPT Guardian, tecSaaS MPT, and this whole Docker Compose stack all run on the same Windows PC in the recommended deployment (via Docker Desktop) — Guardian talks to `redisserver` over `localhost`, not over the network.
- MPT Guardian is optional for short test sessions, but **mandatory for any session longer than ~6 hours** — the tec5 tecSaaS MPT software intermittently stops transmitting UDP data on its own over long runs, and this watchdog/tray-app pair is the only thing that detects and recovers from it automatically. Without MPT Guardian installed, `absorbance_channel_1` simply stays stale with no automatic recovery.

---

## UDP Packet Structure (840 Bytes)

```
Offset (Bytes)  Size    Type     Description
──────────────────────────────────────────────────────────
0-3             4       bytes    Magic Header ID (0x08200000)
4-7             4       uint32   Header Info
8-11            4       uint32   Payload Length (840 bytes)
12-15           4       uint32   Padding / Reserved
16-17           2       uint16   Spectrum Type (4=sample, 5=reference, 9=absorbance)
18-19           2       uint16   Channel Index (1=channel 1, 2=channel 2)
20-23           4       float32  Start Wavelength (190.0 nm)
24-27           4       float32  End Wavelength (390.0 nm)
28-31           4       float32  Wavelength Step (1.0 nm)
32-35           4       uint32   Number of Points (201 points)
36-839          804     float32  201 × 4-byte little-endian IEEE-754 floats
──────────────────────────────────────────────────────────
Total: 840 bytes
```
