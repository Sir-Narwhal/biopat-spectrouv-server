# Setup & Installation

## System Requirements

- **Python:** 3.8 or later
- **OS:** Linux, macOS, or Windows
- **Redis:** 5.0 or later running and accessible on network
- **Memory:** 256 MB minimum (Redis + Python processes)
- **Disk:** 100 MB for code and dependencies

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/Sir-Narwhal/biopat-spectrouv-server-1.git
cd biopat-spectrouv-server-1
```

### 2. Create Virtual Environment

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key dependencies:**
- `redis` (7.1.0+) — Redis Python client
- `asyncua` (1.1.8+) — OPC UA server library
- `aiofiles` (25.1.0+) — Async file operations
- `cryptography` (46.0.3+) — SSL/TLS support

### 4. Verify Installation

```bash
# Test Redis connection
python -c "import redis; r = redis.Redis(); print(r.ping())"

# Test asyncua installation
python -c "import asyncua; print(asyncua.__version__)"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# Redis configuration
export REDIS_IP_ADDRESS=localhost      # or your Redis server IP
export REDIS_PORT_NUMBER=6379

# OPC UA configuration
export OPC_IP_ADDRESS=0.0.0.0          # Listen on all interfaces
export OPC_PORT_NUMBER=4841            # Standard OPC UA port

# Optional: FTP configuration (for full system)
export FTP_ADDRESS=192.168.0.180
export FTP_PORT=21
export FTP_NAME=SpectroFlowUV_001
export FTP_PSWD=your_password
export FTP_FOLDERNAME=server_data
```

### Configuration Files

No additional config files are required. All settings are environment variable-based for flexibility in containerized deployments.

## Running the System

### 1. Start Redis Server

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 redis:latest

# Or using native Redis
redis-server --port 6379
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 2. Run the OPC UA Server

```bash
python parselibrary/opcua_server.py
```

Expected output:
```
6
[OPC UA] Server Started
```

The server is now listening on `opc.tcp://localhost:4841` and waiting for spectral data in Redis.

### 3. Test with Sample Data

```bash
python parselibrary/parsing_spectra.py
```

This script processes binary `.bin` files and demonstrates the parser.

## Docker Deployment

### Build Image

```bash
docker build -t spectrouv:latest .
```

### Run Container

```bash
docker run -d \
  --name spectrouv-server \
  -e REDIS_IP_ADDRESS=redis-host \
  -e REDIS_PORT_NUMBER=6379 \
  -e OPC_IP_ADDRESS=0.0.0.0 \
  -e OPC_PORT_NUMBER=4841 \
  -p 4841:4841 \
  spectrouv:latest
```

### Using Docker Compose

```bash
docker-compose up -d
```

This starts Redis and the OPC UA server with default configuration.

## Troubleshooting Installation

### Redis Connection Refused

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379.
```

**Solution:** Ensure Redis is running and accessible on the configured host/port

```bash
redis-cli -h <REDIS_IP_ADDRESS> -p <REDIS_PORT_NUMBER> ping
```

### Module Not Found: asyncua

```
ModuleNotFoundError: No module named 'asyncua'
```

**Solution:** Reinstall dependencies

```bash
pip install --upgrade asyncua
```

### Permission Denied (Port 4841)

```
PermissionError: [Errno 13] Permission denied
```

**Solution:** Use higher port number (> 1024) or run with elevated privileges. Default port 4841 may be restricted on some systems.

```bash
export OPC_PORT_NUMBER=8841
python parselibrary/opcua_server.py
```

## Next Steps

- Follow the [Quick Start](quickstart.md) guide to parse your first spectrum
- Review the [User Guide](guide.md) for common tasks
- Consult the [API Reference](api/parsing-spectra.md) for function details
