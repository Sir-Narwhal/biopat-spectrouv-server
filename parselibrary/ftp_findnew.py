'''
ftp_filemanagement.py 

@author:        Joel Baarbé
@date:          09/10/2025 

Finds newly entered files to FTP server. 

'''

import os 
import sys
import logging 
import asyncio 
import struct
import json 
import signal 
from typing import List, Literal 
from redis import Redis, RedisError, ConnectionError, DataError 
from ftplib import FTP, all_errors
from datetime import datetime, timezone


REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS", 
                                      "localhost") 
REDIS_PORT_NUMBER = os.environ.get("REDIS_PORT_NUMBER",
                                    6379)
FTP_ADDRESS = os.environ.get("FTP_ADDRESS", 
                                "192.168.0.180")  
FTP_PORT = int(os.environ.get("FTP_PORT", 
                                21))
FTP_NAME = os.environ.get("FTP_NAME", 
                            "SpectroFlowUV_001") 
FTP_PSWD = os.environ.get("FTP_PSWD", 
                            "etb425") 
FTP_FOLDERNAME = os.environ.get("FTP_FOLDERNAME", 
                                "server_data") 


def get_latest(ftp: FTP, path: str, search_type: Literal["<FILE>", "<DIR>"]) -> str: 
    try: 
        lines = [] 
        ftp.retrlines('LIST', lines.append) 

        if search_type == "<FILE>": 
            search_type = "888" 

        logging.info(f"[FTP]: Success retrieving directory listing: {lines[0].split()}")
        files = [] 
        for line in lines: 
            date, time, file_type, file_name = line.split()
            
            if file_type == "888": 
                time = file_name.split("_")[2]

            if search_type == file_type:
                datetime_str = f"{date}_{time}"
                if file_type == "888": 
                    datetime_obj = datetime.strptime(datetime_str, "%m-%d-%Y_%H%M%S").replace(tzinfo=timezone.utc)
                else: 
                    datetime_obj = datetime.strptime(datetime_str, "%m-%d-%Y_%H:%M%p").replace(tzinfo=timezone.utc)
                files.append((file_name, datetime_obj))

        logging.info(f"[FTP]: Found {len(files)} matching files.")
        files.sort(key=lambda x: x[1], reverse=True) 
        return files[0][0]
        # ftp_space = [
        #     (name, datetime.strptime(meta['modify'], '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc))
        #     for name, meta in ftp.mlsd(path)
        #     if meta == search_type and 'modify' in meta 
        # ]
        # return max(ftp_space, key=lambda f: f[1]) if ftp_space else None

    except all_errors as ex: 
        logging.warning(f"[FTP] Error experienced: {ex}")
        return None 

async def ftp_poll(ftp: FTP, r: Redis):
    try:        
        ftp_path = f'server_data/spectra'
        ftp.cwd("/")
        ftp.cwd(ftp_path)

       


        # Change to High, Mide Dir and Bin File
        high_dir = get_latest(ftp, "/", '<DIR>')
        r.set("high_dir", high_dir)
        ftp.cwd(high_dir)
        mid_dir = get_latest(ftp, high_dir, "<DIR>") 
        r.set("mid_dir", mid_dir)
        ftp.cwd(mid_dir)
        bin_file = get_latest(ftp, mid_dir, "<FILE>") 
        r.set("bin_file", bin_file)
    

        if bin_file.endswith(".bin") and "s9" in bin_file:    
            with open(bin_file, 'wb') as local_file: 
                ftp.retrbinary(f"RETR {bin_file}", local_file.write)
            spectral_data = parsebinary(bin_file)
            os.remove(bin_file)

            data = {
                    'spectrumdata': spectral_data,
                }  
            
            r.set("spectral_data", json.dumps(data))
            # r.json().set("spectral_data", "$", data)

    except all_errors as ex: 
        logging.warning(f"[FTP] Error Experienced: {ex}") 
    
    except (RedisError, ConnectionError, DataError) as ex: 
        logging.warning(f"[Redis] Error with Redis Server: {ex}") 
    
    except Exception as ex: 
        logging.warning(f"[Poll] Error with poller: {ex}") 
    

def parsebinary(binfile: str) -> List[float]: 
    with open(binfile, 'rb') as f: 
        raw = f.read() 

    if raw[:4] != b'\xef\xbe\xad\xde' or raw[-4:] != b'\xef\xbe\xad\xde':
        raise ValueError("Bad file markers")

    payload = raw[4:-4]

    spectral_bytes = payload[76:]
    spectral_data = struct.unpack("<" + "f" * (len(spectral_bytes) // 4), spectral_bytes)

    return spectral_data 

def sigterm_handler(signum): 
    logging.info(f"Received SIGTERM ({signum}). Initiating graceful shutdown... ")
    sys.exit(0)

async def main(): 
    logging.basicConfig(level=logging.INFO)

    # Login to FTP
    r = Redis(host=REDIS_IP_ADDRESS, port=REDIS_PORT_NUMBER, decode_responses=True)

    ftp = FTP() 
    ftp.connect(host=FTP_ADDRESS, port=FTP_PORT) 
    ftp.login(user=FTP_NAME, passwd=FTP_PSWD)

    signal.signal(signal.SIGTERM, lambda signum: sigterm_handler(signum))

    try: 
        while True: 
            await ftp_poll(ftp, r)
            await asyncio.sleep(0.5)
    except Exception as ex: 
        logging.error(f"[Main] While Loop Failed! {ex}")
    except KeyboardInterrupt: 
        pass
    finally: 
        sys.exit(0) 

if __name__ == "__main__": 
    asyncio.run(main()) 