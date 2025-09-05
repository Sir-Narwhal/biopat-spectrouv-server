'''
ftp_filemanagement.py 

@author:        Joel Baarbé
@date:          08/18/2025 

This program provides the needed file management of the ftp server
    while remaining memory efficient. 

'''

import os 
import asyncio
import logging 
import redis 
import struct

from parsing_spectra import parsebinary 

from ftplib import FTP 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS")
REDIS_PORT_NUMBER = os.environ.get("REDIS_PORT_NUMBER")
FTP_ADDRESS = os.environ.get("FTP_ADDRESS") 
FTP_PORT = int(os.environ.get("FTP_PORT"))
FTP_NAME = os.environ.get("FTP_NAME") 
FTP_PSWD = os.environ.get("FTP_PSWD") 
FTP_FOLDERNAME = os.environ.get("FTP_FOLDERNAME") 

async def bin_file_changes(r, ftp):
    high_dir = r.get("high_dir")
    mid_dir = r.get("mid_dir") 
    cwd_path = f'server_data/spectra/{high_dir}/{mid_dir}'
    ftp.cwd('/') 
    ftp.cwd(cwd_path)  

    previous_directory = set(ftp.nlst()) 

    while True: 
        high_dir = r.get("high_dir")
        mid_dir = r.get("mid_dir") 
        cwd_path = f'server_data/spectra/{high_dir}/{mid_dir}'

        ftp.cwd('/') 
        ftp.cwd(cwd_path)

        current_directory = set(ftp.nlst())         
        new_folders = current_directory - previous_directory 

        for folder in new_folders: 
            r.set("bin_file", folder) 

        previous_directory = current_directory
        await asyncio.sleep(0.5)


async def mid_level_changes(r, ftp):
    high_dir = r.get("high_dir")
    cwd_path = f'server_data/spectra/{high_dir}' 

    ftp.cwd('/')
    ftp.cwd(cwd_path)  

    previous_directory = set(ftp.nlst()) 

    while True: 
        high_dir = r.get("high_dir")
        cwd_path = f'server_data/spectra/{high_dir}' 

        ftp.cwd('/')
        ftp.cwd(cwd_path)  

        current_directory = set(ftp.nlst())         
        new_folders = current_directory - previous_directory 

        for folder in new_folders: 
            r.set("mid_dir", folder) 

        previous_directory = current_directory
        await asyncio.sleep(0.5)
     

async def high_level_changes(r, ftp):
    cwd_path = f'server_data/spectra' 

    ftp.cwd('/')
    ftp.cwd(cwd_path)  

    previous_directory = set(ftp.nlst()) 

    while True: 
        cwd_path = f'server_data/spectra' 

        ftp.cwd('/')
        ftp.cwd(cwd_path) 

        current_directory = set(ftp.nlst())         
        new_folders = current_directory - previous_directory 

        for folder in new_folders: 
            r.set("high_dir", folder) 

        previous_directory = current_directory
        await asyncio.sleep(0.5)


async def monitory_for_new_files(r, ftp): 
    # try: 
    

    # ftp.cwd('server_data/spectra/0000/0000') 
    
    while True: 
        high_dir = r.get('high_dir') 
        mid_dir = r.get('mid_dir')
        bin_file = r.get('bin_file') 

        cwd_path = f'/server_data/spectra/{high_dir}/{mid_dir}'
        ftp.cwd('/')
        ftp.cwd(cwd_path) 
        
        try: 
            if not(bin_file.endswith(".bin")) or not("s9" in bin_file): 
                await asyncio.sleep(0.2)
                continue 
            
            with open(bin_file, 'wb') as local_file: 
                ftp.retrbinary(f"RETR {bin_file}", local_file.write)

            spectral_data = parsebinary(bin_file)
            os.remove(bin_file)
        except Exception as ex: 
            logging.warning(f"[FTP] File Not Found. Error: {ex}")
        
        try: 
            data = {
                'spectrumdata': spectral_data,
            }  
            
            r.json().set("spectral_data", "$", data)
        except Exception as ex: 
            logger.warning(f'[REDIS] Error experienced: {ex}')
        
        await asyncio.sleep(0.2)


async def change_mid_dir(r): 
    old_file = r.get('bin_file') 
    await asyncio.sleep(2) 
    while True: 
        new_file = r.get('bin_file') 
        exit_condition = r.get('exit') 

        if exit_condition is None: 
            exit_condition = False 
        else: 
            exit_condition = bool(exit_condition) 

        if new_file == old_file: 
            mid_level = int(r.get('mid_dir'))
            mid_level += 1 
            mid_level = r.set('mid_dir', f"{mid_level:04d}")

        old_file = new_file  
        await asyncio.sleep(10) 


def parsebinary(binfile):
    with open(binfile, 'rb') as f: 
        raw = f.read() 

    if raw[:4] != b'\xef\xbe\xad\xde' or raw[-4:] != b'\xef\xbe\xad\xde':
        raise ValueError("Bad file markers")

    payload = raw[4:-4]

    spectral_bytes = payload[76:]
    spectral_data = struct.unpack("<" + "f" * (len(spectral_bytes) // 4), spectral_bytes)

    return spectral_data 


async def main(): 
    r = redis.Redis(host=REDIS_IP_ADDRESS, port=REDIS_PORT_NUMBER, decode_responses=True)

    ftp = FTP() 
    ftp.connect(host=FTP_ADDRESS, port=FTP_PORT) 
    ftp.login(user=FTP_NAME, passwd=FTP_PSWD)

    if r.get('high_dir') is None: 
        r.set("high_dir", "0000") 
        r.set("mid_dir", "0000") 
        r.set("bin_file", "")
    try: 
        await asyncio.gather(monitory_for_new_files(r, ftp), 
                         bin_file_changes(r, ftp),
                         mid_level_changes(r, ftp), 
                         high_level_changes(r, ftp), 
                         change_mid_dir(r))
    except Exception as ex: 
        logger.warning(f'[FTP Manager] Error Occured:\t{ex}') 
    finally: 
        r.set('exit', True) 
        

if __name__ == "__main__":
    asyncio.run(main())