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
- Verify the spectrometer PC is configured to send UDP packets to the IP of the server on port `20202`.
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
