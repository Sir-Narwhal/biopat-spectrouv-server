'''
parsing_spectra.py 

@author:        Joel Baarbe 
@date:          08/14/2025 

This script will export data from specified file. 

'''

import struct
import os 
import time 

import asyncio 

def parsebinary(binfile): 

    with open(binfile, "rb") as f:
        raw = f.read()

    # Check markers
    if raw[:4] != b'\xef\xbe\xad\xde' or raw[-4:] != b'\xef\xbe\xad\xde':
        raise ValueError("Bad file markers")

    # Strip markers
    payload = raw[4:-4]

    # Extract metadata (first 76 bytes in this guess)
    # metadata = payload[:76]
    
    print(f"spectral data")
    spectral_bytes = payload[76:]

    # Parse floats
    spectral_data = struct.unpack("<" + "f" * (len(spectral_bytes) // 4), spectral_bytes)

    # Wavelength axis
    # wavelengths = [190 + i for i in range(len(spectral_data))]
    # data = {}
    # for wl, absorb in zip(wavelengths, spectral_data):
    #     # print(f"{wl:.0f} nm: {absorb:.4f}")
    #     data[wl] = absorb

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