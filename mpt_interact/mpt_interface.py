''' 
_win32_background_trial.py 

@author:        Joel Baarbe


This is the testing ground for developing the code required to interact with the TecSaas MPT software
    using python via pywinauto debug counsel 

'''

import os 
import sys
import time
import traceback 
import psutil
import gc 
import logging

import clr 

# sys.path.append(os.path.abspath(r'.\cslibraries'))
# sys.path.append(os.path.abspath(f'.\\cslibraries\\'))

# clr.AddReference(os.path.abspath(f".\\cslibraries\\MPTSaveSpectrumLibrary.dll"))
# sys.path.append('.')
# clr.AddReference(r".\MPTSaveSpectrumLibrary.dll")
# clr.AddReference("MPTSaveSpectrumLibrary.dll")

def resource_path(filename:str) -> str: 
    if getattr(sys, 'frozen', False): 
        base_file = sys._MEIPASS
    else:    
        base_file = os.path.abspath(r".\cslibraries")
    return os.path.join(base_file, filename)

dll_path = resource_path("MPTSaveSpectrumLibrary.dll")
clr.AddReference(dll_path)


from MPTSaveSpectrumLibrary import SaveSpectrumUIHelper
from MPTSaveSpectrumLibrary import WindowForceCloser
# from MPTSaveSpectrumLibrary import StartMonitoringMeasurement
# from MPTSaveSpectrumLibrary import StopMonitoringMeasurement


class MPTInterface(): 
    '''
    class:          MPTInterface 

    @author:        Joel Baarbe 
    @date:          01/23/2025

    This class will connect with the TecSaas MPT Program, provide the framework to modify the program, and allow
        the spectra to be saved in a timely fashion (less than 500 ms). 

    This class can only handle one channel. 
    
    '''

    def __init__(self, mpt_app: SaveSpectrumUIHelper, **kwargs): 
        '''
        Method:                 MPTIterface.__init__ 

        @author:                Joel Baarbe 

        Initialization method for class MPTItnerface. Essential attributes are defined here without need for 
            specification by the user. 
        '''
        # logging = debug_logger
        self.mpt_app = mpt_app 
        # self.start()
        
    def start(self):
        '''
        Method:                 MPTInterface.start

        @author:                Joel Baarbe
        @date:                  05/08/2025

        This method will start the MPT program

        '''

        self.ready = self.mpt_app.StartProgram()
        self.pid = self.mpt_app.GetProgramId()
        self.retries = 10
        
        counter = 0 
        
        while self.ready != True: 
            # Do something 
            try: 
                self.mpt_app.ConnectDevice(self.pid) 
                time.sleep(5) 
            except: 
                time.sleep(2) 
                counter += 1

            self.ready = self.mpt_app.IsReady(self.pid) 
            print(f"Program is not ready") 
            logging.warning(f"Program is not ready")

            if counter > self.retries:
                print(f"Program cannot get to ready state after {self.retries} tries")
                logging.warning(f"Program cannot get to ready state after {self.retries} tries. Restarting Program")

                self.mpt_app.RestartProgram()
                self.ready = self.mpt_app.StartProgram()
                self.pid = self.mpt_app.GetProgramId()

                counter = 0



    def kill(self): 
        '''
        Method:                 MPTInterface.kill 

        @author:                Joel Baarbe 
        @date:                  02/06/2025

        This method will kill the program, so that it can be restarted. 

        '''
        
        self.mpt_app.RestartProgram()

    # def 
    
    def savespectrum(self, savename): 
        '''
        Method:                 MPTInterface.savespectrum

        @author:                Joel Baarbe/ 
        @date:                  01/23/2025

        This method will save the spectrum file to the indicated director with the name provided.        
        
        '''

        try: 
            WindowForceCloser.ForceCloseSaveAsDialogs() 
            self.mpt_app.FillSaveAsDialog(self.pid, savename)
        except Exception as e: 
            print(f"Python caught exception from c# .dll:\t{e}")
            print(traceback.format_exc())
            logging.error(f"Python caught exception from c# .dll:\t{e}")
        # try: 
        #     # SaveSpectrumUIHelper.ClickControl(self.pid, "automationid", "ExportButton")
        #     # savename = os.path.join(os.path.abspath(filedir), filename)
        #     # print(f"Savename:\t{savename}") 
        #     SaveSpectrumUIHelper.FillSaveAsDialog(self.pid, savename)
        #     print(f"Clicking Save Spectrum Successful") 

        # except: 
        #     print(f"Failed Clicking Save Spectrum ") 
        #     exit() 

    def garbage_collect(self): 
        '''
        Method:         MPTInterface.garbage_collect

        @author:        Joel Baarbe 
        @date:          04/08/2025 

        This function will do a garbage collection. 
            
        '''
        gc.collect() 
        self.mpt_app.ForceGC() 
        
    def stop_monitor(self): 
        self.mpt_app.StopMonitoringMeasurement()

    def start_monitor(self): 
        self.mpt_app.StartMonitoringMeasurement()

    def refresh(self): 
        self.mpt_app.stop_monitor() 
        self.mpt_app.start_monitor()


def test_refresh(): 
    x = SaveSpectrumUIHelper()
    x.StopMonitoringMeasurement() 
    x.StartMonitoringMeasurement() 

def test_spectrum_time(): 
    # x = MPTInterface() 

    times = [] 
    # while True: 
    for loop in range(50): 
        starttime = time.time() 
        test_refresh()
        # x.savespectrum(os.path.abspath(os.path.join("temp_data", "helloworld.txt"))) 
        endtime = time.time() - starttime
        times.append(endtime) 

    print(times) 


def monitor_memory(pid, debug_logger): 
    '''
    Function:       montior_memory

    @author:        Joel Baarbe 
    @date:          04/08/2025

    This function will monitor the memory of the MPT software and 
        report the total memory used. 

    This is a diagnostic tool. 
    
    '''

    process = psutil.Process(pid) 
    mem = process.memory_info().rss/1024/1024 

    print(f"Memory Usage: {mem:.2f} MB") 
    debug_logger.info(f"Memory Usage: {mem:.2f} MB")  


if __name__ == "__main__":
    test_spectrum_time()
   
