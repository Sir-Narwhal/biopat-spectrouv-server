'''
parsing_spectra.py

@author:        Joel Baarbe
@date:          08/14/2025

This script parses binary spectral data files (.bin) and extracts spectral absorption values.

'''

import struct
import os
import time
from typing import Tuple

import asyncio

def parsebinary(binfile: str) -> Tuple[float, ...]:
    """Parse a binary spectral data file and extract absorption values.

    Reads a binary file containing UV-Vis spectral data with magic byte markers,
    skips metadata, and extracts floating-point absorption values for wavelengths
    in the UV range.

    Args:
        binfile: Absolute path to the binary .bin file to parse.

    Returns:
        A tuple of floats representing absorption values across the wavelength range,
        typically 201 values spanning 190-400 nm.

    Raises:
        ValueError: If file does not have correct magic byte markers (0xEFBEADDE)
                   at start and end, indicating corrupted or incorrect file format.
        FileNotFoundError: If the specified file does not exist.
        IOError: If file cannot be read.

    Example:
        >>> data = parsebinary("/path/to/spectrum.bin")
        >>> print(len(data))
        201
        >>> print(data[0])  # First wavelength (190 nm)
        0.123
    """

    with open(binfile, "rb") as f:
        raw = f.read()

    # Validate file markers: 0xEFBEADDE is a magic number identifying valid spectrum files
    if raw[:4] != b'\xef\xbe\xad\xde' or raw[-4:] != b'\xef\xbe\xad\xde':
        raise ValueError("Bad file markers")

    # Strip 4-byte markers from start and end
    payload = raw[4:-4]

    # Skip metadata (first 76 bytes contain file header info we don't need)
    spectral_bytes = payload[76:]

    # Parse as little-endian 32-bit floats (one per wavelength point)
    spectral_data = struct.unpack("<" + "f" * (len(spectral_bytes) // 4), spectral_bytes)

    return spectral_data 

if __name__ == "__main__":

    filepath = r'C:\Users\SpectroFlowUV_001\Documents\rawdata\temp_data\spectra\0000\0000'

    for iter, eachfile in enumerate(os.listdir(filepath)):
        if not(eachfile.endswith('.bin')):
            continue

        starttime = time.time()
        parsebinary(os.path.abspath(os.path.join(filepath, eachfile)))
        endtime = time.time()-starttime

        print(f"Total Time:\t{endtime}")

        if iter == 10:
            break

    # binfile = r"s9_20150501_000758_199.bin"
    # parsebinary(binfile)