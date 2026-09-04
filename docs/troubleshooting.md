# Troubleshooting

## Common Issues and Diagnostic Steps

---

### 1. UDP Ingestion Issues

#### Issue: `udpparser` shows socket timeout or receives no packets
```
[UDP Parser] Socket timeout waiting for UDP broadcast; retrying...
```

**Causes:**
1. The spectrometer host PC is sending UDP packets to a different IP or port.
2. A firewall is blocking UDP port `20202`.

**Solutions:**
- In the recommended single-PC deployment, verify tecSaaS MPT is configured to send UDP packets to `127.0.0.1` (loopback) on port `20202`, since `udpparser` runs on this same machine. If you're instead running the Docker stack on a separate host, verify it's targeting that host's IP on the same subnet.
- Check if port 20202 is open and listening:
  ```bash
  # Windows
  netstat -ano | findstr :20202
  # Linux
  ss -ulpn | grep 20202
  ```
- Send a test packet using the mock emitter:
  ```bash
  python -m parselibrary.mock_udp_emitter --host 127.0.0.1 --port 20202
  ```

---

### 2. Redis Connection Issues

#### Error: `redis.exceptions.ConnectionError`
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Solutions:**
1. Verify the Redis container is running:
   ```bash
   docker compose ps redisserver
   ```
2. Test connection with `redis-cli`:
   ```bash
   docker compose exec redisserver redis-cli ping
   # Expected: PONG
   ```
3. Inspect keys currently stored in Redis:
   ```bash
   docker compose exec redisserver redis-cli keys "*"
   ```

---

### 3. OPC UA Server Issues

#### Issue: Client connects but variables read `[0.0, 0.0, ...]`
**Causes:**
- No UDP packets have been received in the last 5 seconds (keys expired in Redis).
- `udpparser` is not running or connected to a different Redis instance.

**Solutions:**
1. Check `udpparser` logs:
   ```bash
   docker compose logs -f udpparser
   ```
2. Check if keys exist in Redis:
   ```bash
   docker compose exec redisserver redis-cli get absorbance_channel_1
   ```
3. Start the mock emitter to verify the pipeline:
   ```bash
   python -m parselibrary.mock_udp_emitter
   ```

---

### 4. Port Conflicts

If port `4841` (OPC UA) or `20202` (UDP) is already in use by another application:
1. Open `.env`.
2. Change the host port mappings:
   ```ini
   UDP_PORT=20205
   OPC_PORT_NUMBER=4845
   ```
3. Restart Docker Compose:
   ```bash
   docker compose up -d
   ```

---

### 5. Data Stops After Several Hours (Long-Running Sessions)

#### Issue: Spectral data was flowing fine, then silently went stale hours into a run
**Cause:** The tec5 tecSaaS MPT software intermittently stops transmitting UDP data on its own during long-running sessions (typically anywhere past ~6 hours). The `udphelper` watchdog will detect this (it sets `mpt_refresh = "true"` in Redis), but the Docker stack has no way to act on that signal by itself — something has to restart the tecSaaS MPT measurement session.

**Solution:**
1. Install and run the [MPT Guardian tray application](../tray_app/README.md) — either via the installer or by running the included `.exe` directly — on the **same Windows PC** that runs tecSaaS MPT and this Docker Compose stack (Guardian can't be split off onto a different machine; see [tray_app/README.md](../tray_app/README.md#architecture)). This is **mandatory for any session longer than ~6 hours**; short test/demo sessions can run without it.
2. Confirm it's running and polling by checking the `mpt_refresh` key:
   ```bash
   docker compose exec redisserver redis-cli get mpt_refresh
   ```
3. If MPT Guardian is already running and the feed is still stale, check its tray icon tooltip for `Status: Error` (Redis connection lost or state keys missing) and confirm `redisserver`'s port `6379` is published to the host (`docker compose ps`) so Guardian's `localhost:6379` connection can reach it.

---

### 6. Data Appears Under the Wrong Channel

#### Issue: Values show up under `..._channel_1` (or `_channel_2`) when you expected the other
**Cause:** `udpparser` does **not** read the channel index out of the UDP packet header — it tags every value it writes with whatever `UDP_CHANNEL_NAME` is set to in `compose.yaml`/`.env` (`channel_1` by default), regardless of what the spectrometer actually sent. This is a manual setting, not an auto-detected one, and there's no error if it's wrong — the data just lands under the wrong keys.

**Solutions:**
1. Confirm which channel your instrument is actually wired to, then set it explicitly:
   ```ini
   # .env
   UDP_CHANNEL_NAME=channel_2
   ```
2. Restart the stack so `udpparser` picks up the change:
   ```bash
   docker compose up -d
   ```
3. To ingest **both** channels at the same time, you need two `udpparser` instances — duplicate the service in `compose.yaml` with a different `UDP_PORT` and `UDP_CHANNEL_NAME=channel_2`, and point tecSaaS MPT's second channel broadcast at that port.
4. Verify the fix by checking which key actually has fresh data:
   ```bash
   docker compose exec redisserver redis-cli get absorbance_channel_2
   ```
