# Spectral Parser API

## Module: `parselibrary.parsing_spectra`

This module provides functions for parsing binary UV-Vis spectral data files.

---

## Function: `parsebinary()`

```python
def parsebinary(binfile: str) -> Tuple[float, ...]:
```

### Description

Parse a binary spectral data file (.bin) and extract absorption values.

Reads a binary file containing UV-Vis spectral data with magic byte markers, validates file integrity, skips metadata, and extracts floating-point absorption values for wavelengths in the UV range (190-391 nm).

### Parameters

**`binfile: str`**
- Absolute path to the binary .bin file to parse
- Example: `"/data/spectra/spectrum_001.bin"`

### Returns

**`Tuple[float, ...]`**
- Tuple of 201 floating-point numbers representing absorption values
- Index maps to wavelength: `wavelength_nm = 190 + index`
- Values are unitless absorption coefficients (typically 0.0 to 2.5)

### Raises

**`ValueError`**
- Raised if file does not have correct magic byte markers (0xEFBEADDE) at start and end
- Indicates corrupted, incomplete, or incorrect file format
- Message: `"Bad file markers"`

**`FileNotFoundError`**
- Raised if the specified file does not exist

**`IOError`**
- Raised if file cannot be read due to permissions or I/O errors

### File Format Requirements

Input file must follow exact binary format:

```
Byte Range    Size    Content
────────────────────────────────────
0-3           4       Magic marker: 0xEFBEADDE
4-79          76      Metadata (file header, not parsed)
80-883        804     Spectral data (201 × 4-byte float32, little-endian)
884-887       4       Magic marker: 0xEFBEADDE

Total:        888 bytes
```

### Examples

#### Basic Usage

```python
from parselibrary.parsing_spectra import parsebinary

# Parse a spectrum file
spectrum = parsebinary("/data/sample_001.bin")

# Access wavelength data
print(f"190 nm: {spectrum[0]:.4f}")     # First value
print(f"290 nm: {spectrum[100]:.4f}")   # Middle value
print(f"390 nm: {spectrum[200]:.4f}")   # Last value
```

#### Error Handling

```python
from parselibrary.parsing_spectra import parsebinary

try:
    spectrum = parsebinary("/data/corrupted.bin")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Invalid spectrum file: {e}")
```

#### Processing Multiple Files

```python
import os
from parselibrary.parsing_spectra import parsebinary

spectrum_dir = "/data/spectra"
spectra = {}

for filename in os.listdir(spectrum_dir):
    if not filename.endswith('.bin'):
        continue
    
    try:
        path = os.path.join(spectrum_dir, filename)
        spectrum = parsebinary(path)
        spectra[filename] = spectrum
        print(f"✓ Loaded {filename}")
    except (ValueError, FileNotFoundError) as e:
        print(f"✗ Failed {filename}: {e}")

print(f"Loaded {len(spectra)} spectra")
```

#### Integration with OPC UA

```python
import json
import redis
from parselibrary.parsing_spectra import parsebinary

# Parse and publish to Redis for OPC UA server
spectrum = parsebinary("/data/sample.bin")

# Store as JSON for Redis
r = redis.Redis(decode_responses=True)
r.set("transmission_channel_1", json.dumps(list(spectrum)))

# OPC UA server will read this and publish via OPC UA
print("Spectrum published to Redis")
```

### Performance Notes

- **Parsing time:** ~1-5 ms per file (single-threaded)
- **Memory usage:** ~2 KB per spectrum tuple (201 floats)
- **Throughput:** Can parse ~100-200 files/second with asyncio

### Wavelength Mapping

The returned tuple maps directly to wavelengths:

| Index | Wavelength (nm) |
|-------|-----------------|
| 0     | 190             |
| 1     | 191             |
| ...   | ...             |
| 100   | 290             |
| ...   | ...             |
| 200   | 390             |

### Data Type Details

- **Values:** Single-precision floating-point (32-bit)
- **Byte order:** Little-endian (standard Intel/x86)
- **Range:** Typically 0.0 to 2.5 (absorption coefficient)
- **Precision:** ~6 significant decimal digits

### Related Functions

- [`opcua_server.opcua_loop()`](opcua-server.md) — Publishes parsed spectra via OPC UA

### See Also

- [User Guide](../guide.md) — Workflow examples
- [Troubleshooting](../troubleshooting.md) — Common troubleshooting issues
