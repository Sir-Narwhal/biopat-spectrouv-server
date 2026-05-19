# Quick Start

Get the SpectraUV system running in 5 minutes!

## Prerequisites

- Python 3.8+ with pip
- Redis running on `localhost:6379` (or configured via `REDIS_IP_ADDRESS`)
- Binary spectrum file (`.bin`) for testing

## Step 1: Install Dependencies (2 min)

```bash
git clone https://github.com/Sir-Narwhal/biopat-spectrouv-server-1.git
cd biopat-spectrouv-server-1

python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

pip install -r requirements.txt
```

## Step 2: Start Redis (1 min)

```bash
# Option A: Docker (recommended)
docker run -d -p 6379:6379 redis:latest

# Option B: Native Redis (if installed)
redis-server --port 6379
```

Verify Redis is running:
```bash
redis-cli ping
# Expected: PONG
```

## Step 3: Start OPC UA Server (1 min)

In a new terminal:

```bash
cd /path/to/biopat-spectrouv-server-1
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

python parselibrary/opcua_server.py
```

Expected output:
```
6
[OPC UA] Server Started
```

The OPC UA server is now running on `opc.tcp://localhost:4841` and reading from Redis.

## Step 4: Parse Spectral Data (1 min)

In another terminal:

```bash
cd /path/to/biopat-spectrouv-server-1
source venv/bin/activate

python -c "
from parselibrary.parsing_spectra import parsebinary
import json
import redis

# Parse a spectrum (update path to your .bin file)
spectrum = parsebinary('/path/to/your/spectrum.bin')

# Store in Redis
r = redis.Redis(decode_responses=True)
r.set('transmission_channel_1', json.dumps(list(spectrum)))

print(f'Stored {len(spectrum)} wavelength points in Redis')
print(f'Range: {spectrum[0]:.4f} to {spectrum[-1]:.4f}')
"
```

## Step 5: Connect OPC UA Client

Connect any OPC UA client to `opc.tcp://localhost:4841` and you should see:

```
Root
├── spectrouv_1
│   ├── transmission_channel_1 (transmission spectrum, 201 values)
│   ├── absorbance_channel_1
│   ├── onlinereference_channel_1
│   ├── sample_channel_1
│   ├── calibration_channel_1
│   └── Wavelength (190-391 nm, 201 values)
└── spectrouv_2
    ├── transmission_channel_2
    ├── absorbance_channel_2
    ├── onlinereference_channel_2
    ├── sample_channel_2
    ├── calibration_channel_2
    └── Wavelength
```

## Verification Checklist

- [ ] Redis server is running (`redis-cli ping` returns PONG)
- [ ] OPC UA server started without errors and shows "Server Started"
- [ ] Spectrum file was parsed and stored in Redis
- [ ] OPC UA client connected successfully
- [ ] OPC UA variables are visible and update every second

## Common Issues

### OPC UA server won't start

```
Connection refused: No address associated with hostname
```

Check Redis is accessible:
```bash
redis-cli -h localhost ping
```

### Spectrum parse fails

```
ValueError: Bad file markers
```

Ensure your `.bin` file is valid (starts and ends with magic bytes 0xEFBEADDE).

### OPC UA client can't connect

- Check firewall rules on port 4841
- Verify server is running: `ps aux | grep opcua_server.py`
- Check network connectivity to server host

## Next Steps

- **[Setup Guide](setup.md)** — Full installation and configuration
- **[User Guide](guide.md)** — Detailed examples and workflows
- **[Spectral Parser API](api/parsing-spectra.md)** — Complete `parsebinary()` documentation
- **[OPC UA Server API](api/opcua-server.md)** — Complete `opcua_loop()` documentation
- **[Troubleshooting](troubleshooting.md)** — Solutions for common problems
