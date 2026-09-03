# OPC UA Server API

## Module: `parselibrary.opcua_server`

This module implements an OPC UA server that publishes UV-Vis spectral data for real-time access by industrial control systems and SCADA platforms.

---

## Function: `opcua_loop()`

```python
async def opcua_loop(redis_server: redis.Redis) -> None:
```

### Description

Run the OPC UA server and continuously publish spectral data from Redis to connected SCADA clients.

Creates an OPC UA server with a BioPal SpectraUV namespace containing two spectrometer channels (spectrouv_1, spectrouv_2). Each channel exposes five spectral data types (transmission, absorbance, reference, sample, calibration) plus a wavelength axis. The server polls Redis every 1 second for updated spectral values and pushes them to OPC UA clients, enabling real-time subscription and monitoring.

### Parameters

**`redis_server: redis.Redis`**
- An active Redis connection (authenticated and validated)
- Port: 6379 (default) or as configured
- Must have `decode_responses=True` for string operations
- Example: `redis.Redis(host="localhost", port=6379, decode_responses=True)`

### Returns

**`None`**
- Function runs indefinitely until process termination
- Blocks the calling coroutine

### Behavior

The function executes an infinite async loop with these steps:

1. **Initialization** (runs once)
   - Creates OPC UA Server instance
   - Registers BioPal SpectraUV namespace
   - Creates two channel objects (spectrouv_1, spectrouv_2)
   - For each channel and datatype, creates writable OPC UA variables
   - Creates read-only wavelength axis variable (190-391 nm)

2. **Polling Loop** (repeats every 1 second)
   - Scans Redis for keys matching patterns: `transmission*`, `absorbance*`, etc.
   - For each key found:
     - Retrieves JSON-encoded spectral data from Redis
     - Identifies target channel (channel_1 or channel_2)
     - Updates corresponding OPC UA variable with new values
   - Sleeps 1 second before next poll
   - Catches and logs exceptions (continues operating if errors occur)

### Data Model

#### OPC UA Namespace Structure

```
ns=1 (BioPal SpectraUV)
├── spectrouv_1 (Object)
│   ├── transmission_channel_1 (Variable, 201 floats)
│   ├── absorbance_channel_1 (Variable, 201 floats)
│   ├── onlinereference_channel_1 (Variable, 201 floats)
│   ├── sample_channel_1 (Variable, 201 floats)
│   ├── calibration_channel_1 (Variable, 201 floats)
│   └── Wavelength (Variable, 201 floats, read-only)
└── spectrouv_2 (Object)
    ├── transmission_channel_2 (Variable, 201 floats)
    ├── absorbance_channel_2 (Variable, 201 floats)
    ├── onlinereference_channel_2 (Variable, 201 floats)
    ├── sample_channel_2 (Variable, 201 floats)
    ├── calibration_channel_2 (Variable, 201 floats)
    └── Wavelength (Variable, 201 floats, read-only)
```

#### Data Type Definitions

Each datatype variable contains 201 floating-point values:

| Datatype | Meaning | Source |
|----------|---------|--------|
| transmission | Raw transmission spectrum (I/I₀) | Direct measurement |
| absorbance | Calculated absorbance (A = -log₁₀T) | Derived from transmission |
| onlinereference | Reference/calibration spectrum | Stored calibration |
| sample | Active sample measurement | Current measurement |
| calibration | Calibration data used | Reference baseline |

#### Wavelength Axis

- **201 values** from 190.0 to 390.0 nm
- **Spacing:** 1.0 nm between consecutive values
- **Read-only:** Cannot be modified via OPC UA clients

### Redis Key Naming Convention

The server scans Redis for keys following this pattern:

```
{datatype}_{channel}

Examples:
transmission_channel_1
absorbance_channel_2
onlinereference_channel_1
```

**Valid pattern components:**

| Component | Valid Values |
|-----------|--------------|
| {datatype} | transmission, absorbance, onlinereference, sample, calibration |
| {channel} | channel_1, channel_2 |

### Configuration

Configuration is via environment variables:

```python
REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS", "10.20.20.11")
REDIS_PORT_NUMBER = int(os.environ.get("REDIS_PORT_NUMBER", 6379))
OPC_IP_ADDRESS = os.environ.get("OPC_IP_ADDRESS", "0.0.0.0")
OPC_PORT_NUMBER = int(os.environ.get("OPC_PORT_NUMBER", 4841))
```

| Variable | Default | Purpose |
|----------|---------|---------|
| REDIS_IP_ADDRESS | 10.20.20.11 | Redis host IP |
| REDIS_PORT_NUMBER | 6379 | Redis port |
| OPC_IP_ADDRESS | 0.0.0.0 | OPC UA listen address (0.0.0.0 = all interfaces) |
| OPC_PORT_NUMBER | 4841 | OPC UA port (standard) |

### Exceptions & Error Handling

The function catches and logs exceptions internally, allowing the server to continue operating even if errors occur:

**Common exceptions:**

| Exception | Cause | Recovery |
|-----------|-------|----------|
| `redis.ConnectionError` | Redis unavailable | Retries next poll |
| `json.JSONDecodeError` | Invalid JSON in Redis | Logs warning, skips key |
| `KeyError` | Channel not recognized | Logs warning, skips value |
| `Exception` | General error | Logged, server continues |

All exceptions are logged via Python `logging` at WARNING level.

### Examples

#### Basic Startup

```python
import redis
import asyncio
from parselibrary.opcua_server import opcua_loop

async def main():
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Run OPC UA server
    await opcua_loop(r)

# Run forever
asyncio.run(main())
```

#### Command-line Execution

```bash
# With environment variables
export REDIS_IP_ADDRESS=192.168.1.10
export OPC_PORT_NUMBER=8841
python -m parselibrary.opcua_server
```

#### Docker Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY parselibrary/ parselibrary/
ENV REDIS_IP_ADDRESS=redis
ENV OPC_IP_ADDRESS=0.0.0.0
CMD ["python", "-m", "parselibrary.opcua_server"]
```

#### Publishing Data to Redis

```python
import json
import redis
from parselibrary.parsing_spectra import parsebinary

# Parse spectrum
spectrum = parsebinary("/data/sample.bin")

# Connect to Redis
r = redis.Redis(decode_responses=True)

# Publish to Redis for OPC UA server to read
r.set("transmission_channel_1", json.dumps(list(spectrum)))

# Server will pick this up in next polling cycle (~1 second)
print("Spectrum published")
```

#### Connecting OPC UA Client

```python
import asyncio
from asyncua import Client

async def connect():
    client = Client("opc.tcp://localhost:4841")
    async with client:
        # Browse namespace
        root = client.get_root_node()
        objects = await root.get_children()
        
        # Get transmission data for channel 1
        node = client.get_node("ns=1;s=transmission_channel_1")
        value = await node.read_value()
        
        print(f"Got {len(value)} wavelength points")
        print(f"First 5 values: {value[:5]}")
        
        # Subscribe to changes
        async def on_change(node, var):
            print(f"Value changed: {var}")
        
        handler = await node.subscribe_value(on_change)
        
        # Keep connection open
        await asyncio.sleep(10)

asyncio.run(connect())
```

### Performance Characteristics

- **Polling latency:** ~1 second (configurable in source code, line 106)
- **OPC UA update frequency:** 1 Hz
- **Redis scan time:** ~5-50 ms per poll (depends on key count)
- **Memory overhead:** ~5 MB for 2 channels × 5 datatypes × 201 values
- **Max concurrent clients:** 10-50 (asyncio limited)

### Logging

Events are logged at level WARNING (configured in source):

```python
logging.basicConfig(level=logging.WARNING)
```

Change level for more verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Related Functions

- [`parsing_spectra.parsebinary()`](parsing-spectra.md) — Parse spectrum files for storage in Redis

### See Also

- [Architecture](../architecture.md) — System data flow
- [User Guide](../guide.md) — Publishing workflows
- [Troubleshooting](../troubleshooting.md) — Common OPC UA issues
- [Quick Start](../quickstart.md) — Get running in 2 minutes
