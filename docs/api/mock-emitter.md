# Mock UDP Emitter API

## Module: `parselibrary.mock_udp_emitter`

Testing utility for broadcasting synthetic 840-byte tec5 UDP datagrams without physical spectrometer hardware.

### Usage

```bash
python -m parselibrary.mock_udp_emitter --host 127.0.0.1 --port 20202 --interval 1.0
```

### Options

- `--host`: Target host (default: `127.0.0.1`)
- `--port`: Target UDP port (default: `20202`)
- `--interval`: Broadcast cycle interval in seconds (default: `1.0`)
- `--channel`: Channel index (default: `1`)
