# Troubleshooting

## Common Issues and Solutions

### Redis Connection Issues

#### Error: `Connection refused`

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Diagnosis:**
```bash
# Check if Redis is running
redis-cli ping
# If nothing: Redis is not running

# Check if port 6379 is listening
netstat -an | grep 6379
lsof -i :6379  (macOS/Linux)
netstat -ano | findstr :6379  (Windows)
```

**Solutions:**

1. **Start Redis**
   ```bash
   # Docker (recommended)
   docker run -d -p 6379:6379 redis:latest
   
   # Or native Redis
   redis-server --port 6379
   ```

2. **Verify from Python**
   ```python
   import redis
   r = redis.Redis(host='localhost', port=6379)
   print(r.ping())  # Should print: True
   ```

3. **Check firewall rules** (remote Redis)
   ```bash
   # Test connectivity
   nc -zv <REDIS_IP> 6379
   telnet <REDIS_IP> 6379
   ```

---

### Spectrum Parsing Failures

#### Error: `ValueError: Bad file markers`

**What it means:** The binary file doesn't have the correct magic bytes (0xEFBEADDE).

**Diagnosis:**
```bash
# Check file size (should be exactly 888 bytes)
wc -c spectrum.bin
ls -l spectrum.bin

# Check magic bytes
hexdump -C spectrum.bin | head -1
hexdump -C spectrum.bin | tail -1
# Both should show: ef be ad de
```

**Solutions:**

1. **File is corrupted** — Re-download or regenerate from spectrometer
2. **Wrong file format** — Ensure file comes from SpectraUV spectrometer, not generic binary
3. **Partial file transfer** — File transfer was incomplete
   ```bash
   # Check if file size is 888
   if [ $(stat -f%z spectrum.bin) -eq 888 ]; then echo "Size OK"; fi
   ```

4. **Byte order issue** — If you created the file programmatically, verify:
   ```python
   # Correct (little-endian float32)
   struct.pack('<f', 0.123)
   
   # Wrong (big-endian)
   struct.pack('>f', 0.123)
   ```

---

### OPC UA Server Issues

#### Error: `Permission denied` on port 4841

```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

1. **Use a port > 1024** (doesn't require root/admin)
   ```bash
   export OPC_PORT_NUMBER=8841
   python parselibrary/opcua_server.py
   ```

2. **Run with elevated privileges**
   ```bash
   # Linux/macOS
   sudo python parselibrary/opcua_server.py
   
   # Windows (Run as Administrator)
   python parselibrary/opcua_server.py
   ```

3. **Check if port is in use**
   ```bash
   lsof -i :4841         # macOS/Linux
   netstat -ano | findstr :4841  # Windows
   
   # Kill process using port
   kill -9 <PID>         # macOS/Linux
   taskkill /PID <PID> /F  # Windows
   ```

---

#### Error: Server starts but OPC UA clients can't connect

```
opc.tcp://localhost:4841 — Connection refused
```

**Solutions:**

1. **Verify server is listening**
   ```bash
   netstat -an | grep LISTEN | grep 4841
   ```

2. **Check network connectivity**
   ```bash
   ping localhost
   nc -zv localhost 4841
   ```

3. **Try connecting from another machine**
   ```bash
   # From remote machine, try:
   nc -zv <server_ip> 4841
   ```

4. **Firewall is blocking port**
   ```bash
   # Linux: Check iptables
   iptables -L | grep 4841
   
   # Windows: Check Windows Firewall
   # Settings → Security → Firewall → Allow app through firewall
   ```

---

#### Error: OPC UA variables show all zeros

**Diagnosis:**

1. **Check Redis has data**
   ```python
   import redis
   r = redis.Redis(decode_responses=True)
   
   # Should return a list of keys
   keys = r.keys('*')
   print(keys)
   
   # Check specific datatype
   transmission_keys = r.keys('transmission*')
   print(transmission_keys)
   ```

2. **Verify data is valid JSON**
   ```python
   import redis, json
   r = redis.Redis(decode_responses=True)
   
   data = r.get('transmission_channel_1')
   if data:
       parsed = json.loads(data)
       print(f"Values: {parsed[:5]}...")  # First 5 values
   ```

**Solutions:**

1. **Store test data in Redis**
   ```python
   import redis, json
   r = redis.Redis(decode_responses=True)
   
   # Store dummy spectrum
   dummy = [0.5] * 201  # 201 values
   r.set('transmission_channel_1', json.dumps(dummy))
   r.set('transmission_channel_2', json.dumps(dummy))
   ```

2. **Verify OPC UA server is reading Redis**
   - Check logs for "scan_iter" operations
   - Monitor Redis calls: `redis-cli --monitor`

3. **Check channel naming**
   - Must be exactly: `{datatype}_channel_{1|2}`
   - Not: `datatype_ch_1`, `datatype_ch1`, etc.

---

### Installation & Dependencies

#### Error: `ModuleNotFoundError: No module named 'asyncua'`

```python
from asyncua import Server
# ModuleNotFoundError: No module named 'asyncua'
```

**Solutions:**

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   
   # Or install specific package
   pip install asyncua==1.1.8
   ```

2. **Verify virtual environment**
   ```bash
   # Check which Python is being used
   which python  # macOS/Linux
   where python  # Windows
   
   # Should point to your venv directory
   ```

3. **Reinstall clean**
   ```bash
   # Remove and recreate venv
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

#### Error: `struct.error: unpack requires a buffer of X bytes`

```
struct.error: unpack requires a buffer of 804 bytes
```

**Meaning:** Binary file is truncated or has fewer spectral values than expected.

**Solutions:**

1. **Check file size**
   ```bash
   # Must be exactly 888 bytes total
   # 4 (start marker) + 76 (metadata) + 804 (data) + 4 (end marker)
   wc -c spectrum.bin
   ```

2. **Verify file completeness**
   ```python
   import struct
   
   with open('spectrum.bin', 'rb') as f:
       raw = f.read()
   
   print(f"Total bytes: {len(raw)}")
   print(f"Start marker valid: {raw[:4] == b'\\xef\\xbe\\xad\\xde'}")
   print(f"End marker valid: {raw[-4:] == b'\\xef\\xbe\\xad\\xde'}")
   print(f"Data section size: {len(raw[80:-4])} (should be 804)")
   ```

---

### Performance & Monitoring

#### High CPU Usage

**Diagnosis:**
```bash
# Monitor process
top -p <PID>    # macOS/Linux
# Or use Task Manager (Windows)

# Check if stuck in loop
strace -p <PID> # Linux
dtrace -p <PID> # macOS (requires sudo)
```

**Common causes:**

1. **Redis not accessible** — Server stuck retrying connection
   ```python
   # Check logs for connection errors
   # Verify Redis is running and accessible
   ```

2. **asyncio event loop spinning** — Check for exceptions in try/except blocks
   ```python
   # Look for: logger.warning() calls in opcua_loop
   ```

3. **Many OPC UA clients** — Disconnect idle clients

---

#### Memory Leak

**Monitor memory usage:**
```python
import psutil
import time

p = psutil.Process()
for _ in range(10):
    mem = p.memory_info().rss / 1024 / 1024  # MB
    print(f"{mem:.1f} MB")
    time.sleep(5)
```

**Common causes:**

1. **Large spectral arrays** not garbage collected
2. **Redis connection pool** growing unbounded
3. **Asyncio tasks** not properly cleaned up

---

## Diagnostic Commands

### Check System Status

```bash
# Redis health
redis-cli info server

# OPC UA connectivity
nc -zv localhost 4841

# Python dependencies
pip list | grep -E 'asyncua|redis|aiofiles'

# Process resource usage
ps aux | grep python
```

### Enable Debug Logging

```python
import logging

# Set to DEBUG level
logging.basicConfig(level=logging.DEBUG)

# Then run your code
from parselibrary.opcua_server import opcua_loop
# ...
```

### Trace Network Activity

```bash
# Monitor Redis commands
redis-cli --monitor

# Capture OPC UA traffic
tcpdump -i any -n "port 4841"

# Check open ports
netstat -an | grep -E '4841|6379'
```

---

## Getting Help

1. **Check logs** — OPC UA server logs to stdout and optionally syslog
2. **Review [User Guide](guide.md)** — Common workflows and best practices
3. **Check [Architecture](architecture.md)** — Understand data flow
4. **Review [Quick Start](quickstart.md)** — Verify your setup matches expected configuration
5. **Create issue** — Report to GitHub repository with diagnostic output
