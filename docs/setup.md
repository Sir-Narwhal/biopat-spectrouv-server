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

### Channel Selection (Required)

> [!IMPORTANT]
> `UDP_CHANNEL_NAME` is **not** read from the incoming UDP packets — `udpparser` never inspects the channel index in the packet header (bytes 18–19). It's decided entirely by this environment variable, so you must set it to match your actual spectrometer wiring:
>
> - Wired to **channel 1**: leave `UDP_CHANNEL_NAME=channel_1` (the default).
> - Wired to **channel 2**: set `UDP_CHANNEL_NAME=channel_2` in `.env` before starting the stack.
> - **Both channels simultaneously**: add a second `udpparser` service to `compose.yaml` (duplicate the existing one) with its own `UDP_PORT` and `UDP_CHANNEL_NAME=channel_2`, and configure tecSaaS MPT to send that channel's UDP broadcast to the second port.
>
> Getting this wrong doesn't error — it silently labels your data under the wrong channel's Redis keys and OPC UA nodes, so verify it explicitly rather than trusting the default.

### Launching Services

```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f udpparser
docker compose logs -f opcserver
docker compose logs -f udphelper

# Stop services
docker compose down
```

---

## Windows Tray App (Long-Running Deployments)

The [MPT Guardian tray application](../tray_app/README.md) is optional for short test sessions, but **mandatory for any measurement session longer than ~6 hours** — the tec5 tecSaaS MPT software intermittently stops transmitting UDP data on its own over extended runs, and MPT Guardian is what detects and restarts it. Install it via the installer, or run the included `.exe` directly with no build/install step.

MPT Guardian must run on the **same Windows PC** as the tec5 tecSaaS MPT software and this Docker Compose stack — it talks to `redisserver` over `localhost` and drives tecSaaS MPT via Windows UI Automation on the same desktop session, so it can't be split off onto a separate machine. In practice this means: when MPT Guardian is in use, deploy the whole stack via Docker Desktop on that same PC rather than on a separate Linux host.

---

## Offline / Air-Gapped Deployment

If the Windows PC can't reach Docker Hub (for example a locked-down lab PC), **don't build on it** — `docker compose up --build` has to download base images and Python packages, and fails with errors like `lookup registry-1.docker.io: no such host`. Instead, build once on a machine with internet access, export the images to `.tar` files, and load them on the offline PC.

**On a machine with internet and Docker running:**

```bat
export-docker-images.bat          rem or: export-docker-images.bat 1.0.1
```

This builds the `udpparser`, `opcserver` and `udphelper` images from `app/Dockerfile`, pulls `redis:7-alpine`, and saves each as a `.tar` in `dist\docker-images\`.

**On the offline PC** (copy the `dist\docker-images` folder and the repo, including `compose.offline.yaml`, across):

```bat
import-docker-images.bat           rem loads every .tar with "docker load"
run-docker-offline.bat             rem or: run-docker-offline.bat 1.0.1
```

`run-docker-offline.bat` starts the stack from `compose.offline.yaml`, which uses the loaded images (`pull_policy: never`) and never builds or pulls. The image tag must match the one used when exporting (`latest` if you didn't pass one). Use this instead of `run-docker.bat` on the offline PC.

> `compose.offline.yaml` mirrors the service settings in `compose.yaml` — keep the two in sync when changing ports, environment variables, or services.

---

## Port Mappings

Ensure the following firewall ports are open on the server host:

| Port | Protocol | Service | Description |
| :--- | :---: | :--- | :--- |
| `20202` | UDP | `udpparser` | Receives UDP broadcast from tecSaaS MPT |
| `4841` | TCP | `opcserver` | OPC UA server endpoint for SCADA clients |
| `6379` | TCP | `redisserver` | Internal Redis state bus |

The `udphelper` (watchdog) service exposes no ports — it only talks to `redisserver` over the internal Docker network.
