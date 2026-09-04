# UDP Parser Service API

## Module: `parselibrary.udp_parser`

The UDP Parser service receives, validates, and decodes incoming 840-byte UDP spectral broadcast datagrams from the tec5 tecSaaS MPT software (the vendor control application, not the spectrometer hardware itself — see [Architecture](../architecture.md)). Each acquisition cycle sends up to 5 separate 840-byte datagrams, one per data type (sample, onlinereference, transmission, absorbance, calibration).

### Functions

#### `unpack_udp(binary_string: bytes) -> List[float]`
Extracts the 201 float32 values from an incoming 840-byte datagram payload.

#### `collect_mpt_spectra(udp: socket.socket) -> Dict[str, List[float]]`
Reads a batch of datagrams from the UDP socket and maps tec5 packet type integers to spectral identifiers:
- Type 4 → `sample` (Sample Intensity)
- Type 5 → `onlinereference` (Reference Intensity)
- Type 7 → `transmission`
- Type 9 → `absorbance`
- Type 11 → `calibration`

Skips control datagrams (144 or 72 bytes) and any packet that isn't exactly 840 bytes or doesn't carry a recognized type.

#### `main_loop(r: Redis, udp: socket.socket) -> None`
Runs one ingestion cycle: calls `collect_mpt_spectra`, then writes each spectral array to Redis as `{type}_{UDP_CHANNEL_NAME}` with a 5-second TTL (`ex=5`). `sample` is also mirrored to `intensity_{channel}` and `onlinereference` to `reference_intensity_{channel}` for more intuitive SCADA tag names.

### Configuration

Configured via environment variables (see [Setup & Deployment](../setup.md)):

| Variable | Default | Purpose |
|----------|---------|---------|
| `UDP_IP` | `0.0.0.0` | Listen address for spectrometer UDP datagrams |
| `UDP_PORT` | `20202` | Port receiving tec5 UDP broadcasts |
| `UDP_CHANNEL_NAME` | `channel_1` | Redis key suffix identifying this channel |
| `REDIS_IP_ADDRESS` | `localhost` | Redis host (`redisserver` inside Docker Compose) |
| `REDIS_PORT_NUMBER` | `6379` | Redis port |

> [!IMPORTANT]
> **`UDP_CHANNEL_NAME` is not auto-detected — you must set it manually.** Every tec5 UDP packet does carry a channel index in its header (byte offset 18–19, see [Architecture](../architecture.md#udp-packet-structure-840-bytes)), but `collect_mpt_spectra`/`unpack_udp` never read it. The channel a given `udpparser` instance writes to is decided *entirely* by this environment variable. If your spectrometer is wired to channel 2 and you leave `UDP_CHANNEL_NAME` at its `channel_1` default, the data will silently land under `..._channel_1` keys — verify this setting in `compose.yaml`/`.env` for your actual hardware before trusting any channel-tagged data. To ingest both channels simultaneously, run a second `udpparser` instance (a duplicated Compose service) with `UDP_CHANNEL_NAME=channel_2` and a distinct `UDP_PORT`.
