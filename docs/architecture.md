# System Architecture

## Overview

SpectraUV is a distributed system for acquiring and publishing UV-Vis spectral data in real-time. The architecture centers around **Redis** as a message bus, enabling decoupled, scalable inter-process communication.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Redis (State & Message Bus)                  │
│                  Port 6379 (default)                         │
└──────────────────┬──────────────────────┬────────────────────┘
                   │                      │
         ┌─────────┴─────────┐  ┌─────────┴──────────┐
         │                   │  │                    │
    ┌────▼──────────┐   ┌────▼──────────┐   ┌───────▼──────┐
    │  Spectral     │   │   OPC UA      │   │  Data File   │
    │  Parser       │   │   Server      │   │  Sources     │
    │               │   │               │   │              │
    │ parsing_      │   │ opcua_        │   │ .bin files   │
    │ spectra.py    │   │ server.py     │   │              │
    └───────────────┘   └───────────────┘   └──────────────┘
         Reads                Writes                Reads
       .bin files          OPC UA vars             from FTP
         from FTP           in Redis               / local
```

## Data Flow

### 1. Spectral Data Acquisition
- Binary spectral files (`.bin`) are retrieved from FTP or local storage
- `parsing_spectra.parsebinary()` parses the binary format:
  - Validates magic byte markers (0xEFBEADDE)
  - Extracts 201 floating-point absorption values
  - Returns tuple spanning wavelengths 190-391 nm (1 nm steps)
- Parsed data is stored in Redis with keys like `transmission_channel_1`

### 2. Data Publication (OPC UA)
- `opcua_server.opcua_loop()` runs an async loop every 1 second
- Polls Redis for updates to spectral data keys
- Updates OPC UA server variables with latest absorption values
- SCADA systems and industrial clients subscribe to these variables

### 3. Inter-Process Communication
- **Redis** serves as the central hub for state management
- Processes communicate asynchronously without tight coupling
- Enables horizontal scaling (add new readers/writers without modifying existing code)

## Data Format

### Input: Binary Spectrum File (.bin)

```
Bytes     Content
─────────────────────────────────
0-3       Magic marker: 0xEFBEADDE
4-79      Metadata (file header info)
80-...    Spectral data (float32 values, little-endian)
          Total: 201 values × 4 bytes = 804 bytes
...       (content)
-4-(-1)   Magic marker: 0xEFBEADDE
```

**Wavelength mapping:** Each float value corresponds to 1 nm steps starting at 190 nm
- Value[0] → 190 nm
- Value[1] → 191 nm
- ...
- Value[200] → 390 nm

### Output: OPC UA Variables

Each spectrometer channel exposes:
- **transmission** — Raw transmission spectrum (201 floats)
- **absorbance** — Calculated absorbance (A = -log10(transmission))
- **onlinereference** — Reference spectrum from latest calibration
- **sample** — Active sample measurement
- **calibration** — Calibration data used for normalization
- **wavelengths** — Wavelength axis (190.0 to 390.0 nm, read-only)

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Message Bus | Redis | State storage, inter-process communication |
| Spectral Parsing | Python struct module | Binary data deserialization |
| OPC UA Server | asyncua (1.1.8+) | Industrial protocol for SCADA integration |
| Async Runtime | asyncio | Concurrent I/O operations |
| Process Communication | JSON over Redis | Serialize complex data types |

## Scalability Considerations

- **Single-threaded Python** with asyncio handles concurrent operations efficiently
- **Redis** can scale horizontally with Redis Cluster for distributed deployments
- **OPC UA** clients can connect independently; server scales with client connections
- Each component (parser, OPC server) can run on separate machines sharing Redis

## Environment Configuration

Key environment variables:

```bash
REDIS_IP_ADDRESS=10.20.20.11          # Redis host
REDIS_PORT_NUMBER=6379                 # Redis port
OPC_IP_ADDRESS=0.0.0.0                 # OPC UA listen address
OPC_PORT_NUMBER=4841                   # OPC UA port (standard)
```

## Security Notes

- OPC UA server runs without authentication by default
- Redis access is unauthenticated by default
- For production: Use firewall rules, VPN, or configure Redis password authentication
- Binary file validation uses magic bytes, not cryptographic signatures
