import clr 
import os
import sys 
import logging
import asyncio 
import signal 
from typing import List
from redis import Redis, RedisError, ConnectionError, DataError 
from mpt_interact.mpt_interface import MPTInterface

sys.path.append(r'.\cslibraries')
clr.AddReference(os.path.abspath(r".\cslibraries\MPTSaveSpectrumLibrary.dll"))
 
from MPTSaveSpectrumLibrary import SaveSpectrumUIHelper

'''
TODO's: 
    1. Startup MPT software on boot
        a. Connect to spectrometer 
        b. Send proper failure points and error codes when improper connectino occurs
    2. Connect to new file management container: 
        a. If new files stop coming from MPT software, start refresh instead of having this as a timed event 
'''

'''
Author: Joel Baarbe
Date: 09/10/2025 
'''

REDIS_IP_ADDRESS = os.environ.get("REDIS_IP_ADDRESS", 
                                      "localhost") 
REDIS_PORT_NUMBER = os.environ.get("REDIS_PORT_NUMBER",
                                    6379)
MPT_STOP_KEY = os.environ.get("MPT_STOP_KEY", 
                                  "mpt_stop")                     
MPT_REFRESH_KEY = os.environ.get("MPT_REFRESH_KEY",
                                 "mpt_refresh")
MPT_RESTART_KEY = os.environ.get("MPT_RESTART_KEY",
                                 "mpt_restart")
MPT_START_KEY = os.environ.get("MPT_START_KEY", 
                               "mpt_start") 
SAMPLE_INTERVAL = 1

async def control_logic(r: Redis, mpt_app: MPTInterface):

    true_list = ['true', 't', 1, 'y', 'yes']

    asyncio.gather(
        stop_logic(r, mpt_app, true_list), 
        start_logic(r, mpt_app, true_list), 
        restart_logic(r, mpt_app, true_list), 
        refresh_logic(r, mpt_app, true_list)
    ) 


async def restart_logic(r: Redis, mpt_app: MPTInterface, true_list: List[str | int]): 
    restart_bool = r.get(MPT_RESTART_KEY) 
    try: 
        if restart_bool.lower() in true_list: 
            restart_sucess = restart(mpt_app) 
            r.set(f"{MPT_RESTART_KEY}_state", str(restart_sucess).lower())
            if restart_sucess: 
                r.set(MPT_STOP_KEY, 'false') 
                r.set(MPT_RESTART_KEY, 'false') 
                r.set(MPT_START_KEY, 'false') 
                r.set(MPT_RESTART_KEY, 'false') 
                r.set(f"{MPT_STOP_KEY}_state", 'false') 
                r.set(f"{MPT_RESTART_KEY}_state", 'false') 
                r.set(f"{MPT_START_KEY}_state", 'true') 
                r.set(f"{MPT_RESTART_KEY}_state", 'false') 
                # r.set(MPT_RESTART_KEY, str(False).lower())
    except TypeError: 
        pass 
    except Exception as ex:
        logging.warning(f"[RESTART] Failed due to... {ex}")
    
    await asyncio.sleep(SAMPLE_INTERVAL)


async def refresh_logic(r: Redis, mpt_app: MPTInterface, true_list: List[str | int]): 
    refresh_bool = r.get(MPT_REFRESH_KEY) 
    try: 
        start_state = r.get(f"{MPT_START_KEY}_state") 
        if start_state is None: 
            raise TypeError
        if refresh_bool.lower() in true_list and (start_state in true_list): 
            refresh_success = refresh(r, mpt_app, true_list) 
            r.set(f"{MPT_REFRESH_KEY}_state", str(refresh_success).lower())
            r.set(f"{MPT_START_KEY}_state", str(not(refresh_success)).lower())
            r.set(f"{MPT_STOP_KEY}_state", str(refresh_success).lower())
            r.set(MPT_REFRESH_KEY, str(not(refresh_success)).lower())
    except Exception as ex:
        logging.warning(f"[REFRESH] Failed due to... {ex}")

    await asyncio.sleep(SAMPLE_INTERVAL)


async def stop_logic(r: Redis, mpt_app: MPTInterface, true_list: List[str | int]): 
    stop_bool = r.get(MPT_STOP_KEY)
    try: 
        start_state = r.get(f"{MPT_START_KEY}_state")
        if start_state is None: 
            raise TypeError
        if stop_bool.lower() in true_list and (start_state in true_list): 
            stop_success = stop(mpt_app)  
            r.set(f"{MPT_STOP_KEY}_state", str(stop_success).lower())
            r.set(f"{MPT_START_KEY}_state", str(not(stop_success)).lower())
            r.set(MPT_STOP_KEY, str(not(stop_success)).lower())
    except TypeError: 
        pass 
    except Exception as ex:
        logging.warning(f"[STOP] Failed due to... {ex}")
    
    await asyncio.sleep(SAMPLE_INTERVAL)


async def start_logic(r: Redis, mpt_app: MPTInterface, true_list: List[str | int]): 
    start_bool = r.get(MPT_START_KEY) 
    try: 
        stop_state = r.get(f"{MPT_STOP_KEY}_state")
        if stop_state is None: 
            logging.info(f"[START LOGIC] No Stop State")
            raise TypeError
        if start_bool.lower() in true_list and (stop_state in true_list): 
            logging.info(f"[START LOGIC] Conditions for Starting and Stoping Fulfilled")
            start_sucess = start(mpt_app) 
            r.set(f"{MPT_START_KEY}_state", str(start_sucess).lower())
            r.set(f"{MPT_STOP_KEY}_state", str(not(start_sucess)).lower())
            r.set(MPT_START_KEY, str(not(start_sucess)).lower())
    except TypeError: 
        pass 
    except Exception as ex:
        logging.warning(f"[START] Failed due to... {ex}")

    await asyncio.sleep(SAMPLE_INTERVAL)


def restart(mpt_app: MPTInterface) -> bool: 
    try: 
        # mpt_interface = MPTInterface(mpt_app) 
        mpt_app.kill()
        logging.info(f"[MPT-APP] Close Successful")
        mpt_app.start() 
        logging.info(f"[MPT-APP] Start Successful")
        return True 
    except Exception as ex:
        logging.warning(f"[MPT-APP] Restart Failed: {ex}")
        return False 


def stop(mpt_app: MPTInterface) -> bool: 
    try: 
        mpt_app.stop_monitor()    #StopMonitoringMeasurement()
        logging.info(f"[MPT-APP] Stop Successful")
        return True 
    except Exception as ex:
        logging.warning(f"[MPT-APP] Stop Failed: {ex}")
        return False     

def refresh(r: Redis, mpt_app: MPTInterface, true_list: List[str | int]) -> bool: 
    try: 
        mpt_app.stop_monitor()  #StopMonitoringMeasurement()
        mpt_app.start_monitor() #StartMonitoringMeasurement() 
        logging.info(f"[MPT-APP] Refresh Successful")
        return True 
    except Exception as ex:
        logging.warning(f"[MPT-APP] Refresh Failed: {ex}")
        return False 
    
def start(mpt_app: MPTInterface) -> bool: 
    try: 
        mpt_app.start_monitor()   #StartMonitoringMeasurement()    
        logging.info(f"[MPT-APP] Start Successful")
        return True 
    except Exception as ex:
        logging.warning(f"[MPT-APP] Start Failed: {ex}")
        return False 


def sigterm_handler(signum): 
    logging.info(f"Received SIGTERM ({signum}). Initiating graceful shutdown... ")
    sys.exit(0)


async def main(): 
    logging.basicConfig(level=logging.INFO)
    r = Redis(host=REDIS_IP_ADDRESS, port=REDIS_PORT_NUMBER, decode_responses=True)
    mpt_app = MPTInterface(SaveSpectrumUIHelper()) 
    r.set(MPT_STOP_KEY, 'false') 
    r.set(MPT_RESTART_KEY, 'false') 
    r.set(MPT_START_KEY, 'false') 
    r.set(MPT_RESTART_KEY, 'false') 
    r.set(f"{MPT_STOP_KEY}_state", 'true') 
    r.set(f"{MPT_RESTART_KEY}_state", 'false') 
    r.set(f"{MPT_START_KEY}_state", 'false') 
    r.set(f"{MPT_RESTART_KEY}_state", 'false') 

    signal.signal(signal.SIGTERM, lambda signum: sigterm_handler(signum))

    try: 
        while True: 
            await control_logic(r, mpt_app)
            await asyncio.sleep(0.3) 
    except Exception as ex: 
        logging.warning(f"[MAIN LOOP] While loop crashed: {ex}")
    except KeyboardInterrupt: 
        pass 
    finally: 
        sys.exit(0) 

if __name__ == "__main__": 
    asyncio.run(main())