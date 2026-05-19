# User Guide

## Overview

This guide covers common tasks and workflows for operating and extending the SpectraUV system.

## Binary Spectrum File Format

SpectraUV expects binary files in a specific format. Understanding this format is critical for troubleshooting and data validation.

### File Structure

```
Offset    Size    Description
────────────────────────────────────────
0         4       Magic Marker: 0xEFBEADDE
4         76      Metadata (header info, not currently parsed)
80        804     Spectral Data (201 × float32, little-endian)
884       4       Magic Marker: 0xEFBEADDE

Total:    888 bytes
```

### Validation

The `parsebinary()` function validates file integrity by checking:

1. **Start marker** (bytes 0-3): Must equal `0xEFBEADDE`
2. **End marker** (bytes 884-887): Must equal `0xEFBEADDE`
3. **Data length**: Exactly 804 bytes (201 × 4 bytes per float)

If markers are missing or incorrect, parsing raises `ValueError: Bad file markers`.

### Wavelength Mapping

Spectral values are indexed by wavelength position:

```python
wavelength_nm = 190 + index

spectrum[0]   # 190 nm
spectrum[100] # 290 nm
spectrum[200] # 390 nm
```

## Parsing Spectral Data

### Basic Usage

```python
from parselibrary.parsing_spectra import parsebinary

# Parse a spectrum file
spectrum = parsebinary('/path/to/spectrum.bin')

# spectrum is a tuple of 201 floats
print(f"Parsed {len(spectrum)} wavelength points")
print(f"190 nm: {spectrum[0]:.4f}")
print(f"390 nm: {spectrum[200]:.4f}")
```

### Storing in Redis

```python
import json
import redis
from parselibrary.parsing_spectra import parsebinary

# Parse and store
spectrum = parsebinary('/path/to/spectrum.bin')
r = redis.Redis(host='localhost', decode_responses=True)

# Convert tuple to list for JSON serialization
r.set('transmission_channel_1', json.dumps(list(spectrum)))

# Verify storage
stored = json.loads(r.get('transmission_channel_1'))
print(f"Stored {len(stored)} values in Redis")
```

### Advanced: Processing Multiple Spectra

```python
import os
import json
import redis
from parselibrary.parsing_spectra import parsebinary

spectrum_dir = '/path/to/spectrum/files'
r = redis.Redis(decode_responses=True)

for filename in os.listdir(spectrum_dir):
    if not filename.endswith('.bin'):
        continue
    
    try:
        spectrum = parsebinary(os.path.join(spectrum_dir, filename))
        
        # Create Redis key based on filename and channel
        key = f"transmission_channel_1_{filename}"
        r.set(key, json.dumps(list(spectrum)))
        
        print(f"✓ Stored {filename}")
    except ValueError as e:
        print(f"✗ Failed {filename}: {e}")
```

## Publishing via OPC UA

### How OPC UA Publishing Works

1. **OPC UA Server starts** and creates two channel objects (spectrouv_1, spectrouv_2)
2. **Server polling loop** runs every 1 second:
   - Scans Redis for keys matching `{datatype}*` (e.g., `transmission*`)
   - Parses JSON values from Redis
   - Updates corresponding OPC UA node variables
3. **OPC UA clients** receive notifications when values change

### Monitoring Published Data

Check which data types are available in Redis:

```python
import redis

r = redis.Redis(decode_responses=True)

datatypes = ['transmission', 'absorbance', 'onlinereference', 'sample', 'calibration']

for dtype in datatypes:
    keys = list(r.scan_iter(f"{dtype}*"))
    print(f"{dtype}: {keys}")

# Example output:
# transmission: ['transmission_channel_1', 'transmission_channel_2']
# absorbance: ['absorbance_channel_1']
# ...
```

### Connecting OPC UA Clients

Popular OPC UA clients:

- **UaExpert** (Unified Automation) — Windows GUI client
- **Python asyncua library** — Programmatic access
- **Kepware** — Enterprise gateway
- **Any standards-compliant OPC UA client**

Example Python client:

```python
import asyncio
from asyncua import Client

async def main():
    client = Client("opc.tcp://localhost:4841")
    async with client:
        # Get transmission spectrum for channel 1
        node = client.get_node("ns=1;s=transmission_channel_1")
        value = await node.read_value()
        print(f"Channel 1 Transmission: {value[:5]}...")  # First 5 values

asyncio.run(main())
```

## Troubleshooting

### Spectrum File Not Parsing

**Symptom:** `ValueError: Bad file markers`

**Causes:**
- File is corrupted or incomplete
- File is not in SpectraUV binary format
- File was truncated during transfer

**Solution:**
1. Verify file size: Should be exactly 888 bytes
2. Check file magic bytes:
   ```bash
   hexdump -C spectrum.bin | head -1  # Should show: ef be ad de
   ```
3. Re-download or regenerate the file from the spectrometer

### OPC UA Variables Not Updating

**Symptom:** Connected to OPC UA server but variables show all zeros or don't change

**Causes:**
- No spectral data in Redis
- Redis not accessible from OPC UA server
- Channel names don't match (e.g., using `channel_1` but storing as `ch1`)

**Solution:**
1. Check Redis has data:
   ```python
   import redis
   r = redis.Redis()
   print(r.keys("*"))  # List all keys
   ```
2. Verify Redis connection in OPC UA server logs
3. Ensure keys follow exact naming: `{datatype}_channel_{1|2}`

### High CPU Usage

**Symptom:** OPC UA server process using 100% CPU

**Causes:**
- Polling loop waiting for Redis connection
- Network latency causing retry loops
- Python asyncio event loop spinning

**Solution:**
- Check Redis connectivity
- Monitor network latency
- Review logs for connection errors

## Performance Considerations

- **Polling interval:** Currently 1 second; adjustable in `opcua_server.py:106`
- **Spectral data size:** 201 values × 4 bytes = 804 bytes per spectrum
- **Throughput:** Up to 1 spectrum/second with default 1s polling
- **Clients:** Server handles 10+ simultaneous OPC UA client connections

## Next Steps

- **[Spectral Parser API](api/parsing-spectra.md)** — `parsebinary()` function documentation
- **[OPC UA Server API](api/opcua-server.md)** — `opcua_loop()` function documentation
- **[Architecture](architecture.md)** — Deep dive into system design
- **[Troubleshooting](troubleshooting.md)** — More solutions and diagnostics
