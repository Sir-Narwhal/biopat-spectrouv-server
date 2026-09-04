# Watchdog Service API

## Module: `parselibrary.spectrouv_helper`

This module implements a lightweight Redis watchdog that detects when live spectral data has gone stale and signals the optional [Windows tray companion](../../tray_app/README.md) to restart the spectrometer's measurement session. It runs as the `udphelper` container in the Docker Compose stack.

---

## Function: `watchdog_cycle()`

```python
async def watchdog_cycle(r_spectrouv: Redis, set_mptrefresh: bool) -> bool:
```

### Description

Runs a single watchdog check and returns the updated `set_mptrefresh` flag for the caller to pass into the next cycle.

### Parameters

**`r_spectrouv: Redis`**
- An active Redis connection
- Must have `decode_responses=True` for string operations

**`set_mptrefresh: bool`**
- Tracks whether a refresh has already been requested for the current stale period, so the flag is only raised once per outage
- Pass `False` on the first call

### Returns

**`bool`**
- The updated `set_mptrefresh` state to pass into the next call

### Behavior

1. Reads the `absorbance_channel_1` key from Redis.
2. If the key is missing (expired TTL — no fresh UDP data in the last 5 seconds) and a refresh hasn't already been requested, sets `mpt_refresh = "true"` in Redis, logs a warning, and marks `set_mptrefresh = True`.
3. If the key is present, logs the point count at DEBUG level and resets `set_mptrefresh = False`, re-arming the watchdog so it can raise the flag again if data goes stale a second time.
4. Sleeps 1 second before returning.

Note that `watchdog_cycle` only ever *sets* `mpt_refresh` to `"true"` — it never clears it back to `"false"`. The tray application is responsible for clearing the key once it has handled the refresh.

### Configuration

Configured via environment variables (see [Setup & Deployment](../setup.md)):

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDIS_IP_ADDRESS` | `localhost` | Redis host (`redisserver` inside Docker Compose) |
| `REDIS_PORT_NUMBER` | `6379` | Redis port |

### Example

```python
import asyncio
from redis import Redis
from parselibrary.spectrouv_helper import watchdog_cycle

async def main():
    r = Redis(host="localhost", port=6379, decode_responses=True)
    set_mptrefresh = False
    while True:
        set_mptrefresh = await watchdog_cycle(r, set_mptrefresh)

asyncio.run(main())
```

### See Also

- [OPC UA Server](opcua-server.md) — Publishes the same `absorbance_channel_1` data this watchdog monitors
- [Windows Tray Companion](../../tray_app/README.md) — Consumes the `mpt_refresh` signal key
- [Architecture](../architecture.md) — System data flow
