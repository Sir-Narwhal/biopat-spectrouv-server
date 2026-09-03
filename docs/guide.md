# User Guide

## Overview

This guide explains how to operate the BioPAT® Spectro UV Server, configure spectrometer UDP broadcasts, and consume live 201-wavelength data in industrial SCADA and PAT platforms.

---

## The 201-Wavelength UV Spectrum

The spectrometer measures optical signals from **190.0 nm to 390.0 nm in 1.0 nm increments**, yielding an array of exactly **201 float32 values**:

```python
wavelength_nm = 190.0 + index

spectrum[0]    # 190.0 nm
spectrum[90]   # 280.0 nm (UV protein absorption peak)
spectrum[200]  # 390.0 nm
```

---

## Data Types

The spectrometer emits several spectral data types, each mapped to a specific tec5 type identifier:

| Data Type | Packet Type | Redis Key | OPC UA Tag | Description |
| :--- | :---: | :--- | :--- | :--- |
| **Absorbance** | `9` | `absorbance_channel_1` | `absorbance_channel_1` | Optical Absorbance ($A$) across 201 wavelengths |
| **Sample Intensity** | `4` | `sample_channel_1` | `sample_channel_1` | Raw measurement intensity counts ($I$) |
| **Reference Intensity** | `5` | `onlinereference_channel_1`| `onlinereference_channel_1` | Baseline reference intensity counts ($I_0$) |
| **Transmission** | `7` | `transmission_channel_1` | `transmission_channel_1` | Transmittance ratio ($I / I_0$) |
| **Calibration** | `11` | `calibration_channel_1` | `calibration_channel_1` | Dark / factory calibration baseline |
| **Wavelengths** | Axis | `wavelengths_channel_1` | `Wavelength` | Axis array `[190.0, 191.0, ..., 390.0]` |

---

## Connecting OPC UA Clients

The OPC UA server listens on `opc.tcp://<host>:4841` under namespace index `1` (`http://biopat/spectrouv`).

### Python Client Example (`asyncua`)

```python
import asyncio
from asyncua import Client

async def read_spectrum():
    url = "opc.tcp://localhost:4841"
    async with Client(url=url) as client:
        # Access Channel 1 Absorbance variable node
        node = client.get_node("ns=1;s=absorbance_channel_1")
        absorbance_values = await node.read_value()

        # Access Wavelength axis
        wl_node = client.get_node("ns=1;s=Wavelength")
        wavelengths = await wl_node.read_value()

        print(f"Acquired {len(absorbance_values)} wavelength points:")
        print(f"  {wavelengths[90]} nm: {absorbance_values[90]:.4f} AU")

asyncio.run(read_spectrum())
```

### SCADA & Bioreactor Systems (Ignition, DeltaV, PCS 7)
1. Add an OPC UA connection to `opc.tcp://<server_ip>:4841` (Security: None / Anonymous or configured).
2. Browse to `Objects -> spectrouv_1`.
3. Map `absorbance_channel_1` as a 201-element float array tag.

---

## Testing with Mock Emitter

When testing without a physical spectrometer attached:

```bash
python -m parselibrary.mock_udp_emitter --host 127.0.0.1 --port 20202
```

This broadcasts authentic 840-byte UDP packets containing simulated protein absorbance peaks at 280 nm.
