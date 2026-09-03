# System Architecture

## Overview

The BioPAT® Spectro UV Server is designed around a decoupled, microservices architecture using **Docker Compose** and **Redis** as a real-time in-memory message bus.

---

## 3-Container Microservices Stack

```
┌─────────────────────────────────────────────────────────────────┐
│        Sartorius BioPAT® Spectro UV / tec5 Spectrometer         │
│          Broadcasts 840-byte UDP Packets (Default: 20202)       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ UDP Broadcast
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

---

## Data Flow

### 1. Ingestion (`udpparser`)
- Binds to `0.0.0.0:20202` (UDP).
- Receives 840-byte datagrams from the spectrometer.
- Parses the 36-byte header: verifies length (840), extracts point count (201), wavelength bounds (190.0–390.0 nm), and data type code.
- Unpacks 201 float32 values.
- Writes JSON arrays into Redis with a 5-second TTL (`ex=5`) to prevent stale measurements if transmission ceases.

### 2. State & Message Bus (`redisserver`)
- Operates in-memory on port 6379.
- Decouples high-frequency network packets from OPC UA client polling.

### 3. Industrial Publication (`opcserver`)
- Hosts standard OPC UA server on port 4841 (`opc.tcp://0.0.0.0:4841`).
- Namespace: `http://biopat/spectrouv`.
- Updates writable variables for each channel every 1 second.

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
