# Setup & Deployment

## Deployment Modes

BioPAT® Spectro UV Server can be deployed in two modes:
1. **Containerized (Recommended)**: Using Docker Compose.
2. **Native**: Running Python processes directly on the host.

---

## Docker Deployment

### Configuration (`.env`)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Default settings:
```ini
UDP_IP=0.0.0.0
UDP_PORT=20202
UDP_CHANNEL_NAME=channel_1

OPC_IP_ADDRESS=0.0.0.0
OPC_PORT_NUMBER=4841

REDIS_IP_ADDRESS=redisserver
REDIS_PORT_NUMBER=6379
```

### Launching Services

```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f udpparser
docker compose logs -f opcserver

# Stop services
docker compose down
```

---

## Port Mappings

Ensure the following firewall ports are open on the server host:

| Port | Protocol | Service | Description |
| :--- | :---: | :--- | :--- |
| `20202` | UDP | `udpparser` | Receives spectrometer UDP broadcast |
| `4841` | TCP | `opcserver` | OPC UA server endpoint for SCADA clients |
| `6379` | TCP | `redisserver` | Internal Redis state bus |
